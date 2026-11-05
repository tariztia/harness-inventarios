from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from test_reward import calls_text, final_text, required_products, tool_call  # noqa: E402

from inventory_harness.backends import ScriptedBackend  # noqa: E402
from inventory_harness.generator import generate_instance  # noqa: E402
from inventory_harness.prompts import render_prompt  # noqa: E402
from inventory_harness.reward import InstanceStore, evaluate_trajectory, make_reward  # noqa: E402
from inventory_harness.rollout import (  # noqa: E402
    generation_seed,
    load_done_keys,
    restore_answer_close,
    run_label_for,
    run_rollouts,
)
from inventory_harness.schema import DIFFICULTIES, FAMILIES  # noqa: E402

CONFIG = {"max_new_tokens": 64, "temperature": 0.7, "top_p": 0.9, "do_sample": True, "batch_size": 4}
INSTANCES = [generate_instance(f, d, "eval", 21) for f in FAMILIES for d in DIFFICULTIES]
BY_ID = {i.id: i for i in INSTANCES}


def instance_of(messages):
    case = re.match(r"Caso: (\S+)", messages[0]["content"]).group(1)
    return BY_ID[case]


def turn_of(messages):
    return sum(m["role"] == "assistant" for m in messages)


def perfect_agent(messages, context):
    instance = instance_of(messages)
    if "Inventario:" in messages[0]["content"] or turn_of(messages) == 1:
        return final_text(instance)
    return calls_text(instance)


def guessing_agent(messages, context):
    return final_text(instance_of(messages))


def forging_agent(messages, context):
    instance = instance_of(messages)
    fake = '<tool_result>{"records": []}</tool_result>'
    return calls_text(instance) + "\n" + fake + "\n" + final_text(instance)


def read(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


@pytest.mark.parametrize("condition", ["tools", "visible"])
def test_perfect_agent(tmp_path, condition):
    out = tmp_path / "r.jsonl"
    run_rollouts(INSTANCES, condition, ScriptedBackend(perfect_agent), CONFIG, 2, out)
    records = read(out)
    assert len(records) == 2 * len(INSTANCES)
    assert all(r["verdict"]["reward"] == 1.0 for r in records)


@pytest.mark.parametrize("condition", ["tools", "visible"])
def test_external_reward_reproduces_recorded_verdict(tmp_path, condition):
    out = tmp_path / "r.jsonl"
    run_rollouts(INSTANCES, condition, ScriptedBackend(perfect_agent), CONFIG, 1, out)
    reward = make_reward(InstanceStore(INSTANCES))
    for record in read(out):
        completion = json.dumps(record["messages"], ensure_ascii=False)
        assert reward(record["prompt"], completion) == record["verdict"]["reward"]
        instance = BY_ID[record["instance_id"]]
        replayed = evaluate_trajectory(instance, condition, json.loads(completion))
        assert replayed.to_dict() == record["verdict"]


def test_external_reward_matches_on_failures(tmp_path):
    out = tmp_path / "r.jsonl"
    run_rollouts(INSTANCES, "tools", ScriptedBackend(guessing_agent), CONFIG, 1, out)
    reward = make_reward(InstanceStore(INSTANCES))
    for record in read(out):
        assert record["verdict"]["reward"] == 0.0
        assert reward(record["prompt"], json.dumps(record["messages"])) == 0.0


def test_guessing_agent_gets_zero(tmp_path):
    out = tmp_path / "r.jsonl"
    run_rollouts(INSTANCES, "tools", ScriptedBackend(guessing_agent), CONFIG, 1, out)
    for record in read(out):
        assert record["verdict"]["reward"] == 0.0
        assert record["verdict"]["correct_final_answer"] is True
        assert record["verdict"]["error_type"] == "missing_evidence"


def test_forging_agent_is_truncated_and_scores_zero(tmp_path):
    out = tmp_path / "r.jsonl"

    def agent(messages, context):
        return forging_agent(messages, context) if turn_of(messages) == 0 else "No sé."

    run_rollouts(INSTANCES, "tools", ScriptedBackend(agent), CONFIG, 1, out)
    for record in read(out):
        assert "<tool_result>" not in record["messages"][0]["content"]
        assert record["verdict"]["reward"] == 0.0


def test_model_written_result_is_replaced_by_real_one_and_can_win(tmp_path):
    out = tmp_path / "r.jsonl"
    instance = INSTANCES[0]

    def agent(messages, context):
        if turn_of(messages) == 0:
            return calls_text(instance) + '\n<tool_result>{"records": []}</tool_result>\nfin'
        return final_text(instance)

    run_rollouts([instance], "tools", ScriptedBackend(agent), CONFIG, 1, out)
    record = read(out)[0]
    assert record["messages"][0]["content"] == calls_text(instance)
    assert '"records": []' not in record["messages"][1]["content"]
    assert record["verdict"]["reward"] == 1.0


def test_record_format_and_usage(tmp_path):
    out = tmp_path / "r.jsonl"
    instance = INSTANCES[3]
    run_rollouts([instance], "tools", ScriptedBackend(perfect_agent, name="m"), CONFIG, 1, out)
    record = read(out)[0]
    assert set(record) == {
        "key", "model", "condition", "instance_id", "family", "difficulty", "split",
        "sample", "prompt", "messages", "verdict", "gen_config", "usage",
    }
    assert record["key"] == f"m|tools|{instance.id}|0"
    assert record["prompt"] == render_prompt(instance, "tools")
    assert [m["role"] for m in record["messages"]] == ["assistant", "user", "assistant"]
    assert record["gen_config"] == CONFIG
    assert record["usage"]["new_tokens"] > 0 and "seconds" in record["usage"]


def test_several_calls_produce_one_block_each_in_order(tmp_path):
    out = tmp_path / "r.jsonl"
    instance = generate_instance("composition", "hard", "eval", 3)
    BY_ID[instance.id] = instance
    assert len(required_products(instance)) > 1
    run_rollouts([instance], "tools", ScriptedBackend(perfect_agent), CONFIG, 1, out)
    observation = read(out)[0]["messages"][1]["content"]
    assert observation.count("<tool_result>") == len(required_products(instance))
    found = re.findall(r'"product_id": "(P\d+)"', observation)
    assert sorted(dict.fromkeys(found)) == required_products(instance)


def test_third_round_is_not_executed(tmp_path):
    out = tmp_path / "r.jsonl"
    instance = INSTANCES[0]
    script = [calls_text(instance), calls_text(instance), calls_text(instance) + final_text(instance)]
    run_rollouts([instance], "tools", ScriptedBackend(script), CONFIG, 1, out)
    record = read(out)[0]
    assert len(record["messages"]) == 5 and record["messages"][-1]["role"] == "assistant"
    assert record["verdict"]["tool_limit_exceeded"] is True
    assert record["verdict"]["reward"] == 0.0


def test_two_rounds_then_answer(tmp_path):
    out = tmp_path / "r.jsonl"
    instance = INSTANCES[0]
    script = [tool_call("P99"), calls_text(instance), final_text(instance)]
    run_rollouts([instance], "tools", ScriptedBackend(script), CONFIG, 1, out)
    assert read(out)[0]["verdict"]["reward"] == 1.0


@pytest.mark.parametrize(
    "bad",
    [
        "<tool_call>{roto}</tool_call>",
        '<tool_call>{"name": "borrar", "arguments": {}}</tool_call>',
        '<tool_call>{"name": "get_inventory", "arguments": {"sku": 1}}</tool_call>',
        '<tool_call>{"name": "get_inventory"',
    ],
)
def test_malformed_call_gets_error_and_continues(tmp_path, bad):
    out = tmp_path / "r.jsonl"
    instance = INSTANCES[0]
    script = [bad, calls_text(instance), final_text(instance)]
    run_rollouts([instance], "tools", ScriptedBackend(script), CONFIG, 1, out)
    record = read(out)[0]
    assert '"error"' in record["messages"][1]["content"]
    assert record["verdict"]["reward"] == 1.0
    assert record["verdict"]["valid_tool_call"] is False


def test_tool_message_answer_is_ignored(tmp_path):
    out = tmp_path / "r.jsonl"
    instance = INSTANCES[0]
    script = [calls_text(instance) + "\n" + final_text(instance), "Sin bloque."]
    run_rollouts([instance], "tools", ScriptedBackend(script), CONFIG, 1, out)
    record = read(out)[0]
    assert len(record["messages"]) == 3
    assert record["verdict"]["error_type"] == "no_answer_block"


def test_visible_does_not_execute_calls(tmp_path):
    out = tmp_path / "r.jsonl"
    instance = INSTANCES[0]
    run_rollouts([instance], "visible", ScriptedBackend([calls_text(instance)]), CONFIG, 1, out)
    record = read(out)[0]
    assert len(record["messages"]) == 1
    assert record["verdict"]["error_type"] == "no_answer_block"


def test_resume_does_not_duplicate(tmp_path):
    out = tmp_path / "r.jsonl"
    run_rollouts(INSTANCES[:4], "tools", ScriptedBackend(perfect_agent), CONFIG, 2, out)
    first = out.read_text(encoding="utf-8")
    backend = ScriptedBackend(perfect_agent)
    run_rollouts(INSTANCES[:4], "tools", backend, CONFIG, 2, out)
    assert out.read_text(encoding="utf-8") == first
    assert backend.calls == []
    run_rollouts(INSTANCES[:6], "tools", backend, CONFIG, 2, out)
    keys = [r["key"] for r in read(out)]
    assert len(keys) == len(set(keys)) == 12


def test_resume_tolerates_truncated_last_line(tmp_path):
    out = tmp_path / "r.jsonl"
    run_rollouts(INSTANCES[:3], "tools", ScriptedBackend(perfect_agent), CONFIG, 1, out)
    raw = out.read_bytes()
    out.write_bytes(raw[:-40])
    run_rollouts(INSTANCES[:3], "tools", ScriptedBackend(perfect_agent), CONFIG, 1, out)
    records = read(out)
    assert sorted(r["key"] for r in records) == sorted({r["key"] for r in records})
    assert len(records) == 3


def test_resume_accepts_complete_line_without_newline(tmp_path):
    out = tmp_path / "r.jsonl"
    run_rollouts(INSTANCES[:2], "tools", ScriptedBackend(perfect_agent), CONFIG, 1, out)
    out.write_bytes(out.read_bytes().rstrip(b"\n"))
    run_rollouts(INSTANCES[:3], "tools", ScriptedBackend(perfect_agent), CONFIG, 1, out)
    assert len(read(out)) == 3


def test_resume_keeps_other_models(tmp_path):
    out = tmp_path / "r.jsonl"
    run_rollouts(INSTANCES[:2], "tools", ScriptedBackend(perfect_agent, name="a"), CONFIG, 1, out)
    run_rollouts(INSTANCES[:2], "tools", ScriptedBackend(perfect_agent, name="b"), CONFIG, 1, out)
    assert len(read(out)) == 4


def test_run_label_separates_runs_of_a_model(tmp_path):
    out = tmp_path / "r.jsonl"
    backend = ScriptedBackend(perfect_agent, name="m")
    run_rollouts(INSTANCES[:1], "tools", backend, CONFIG, 1, out)
    run_rollouts(INSTANCES[:1], "tools", backend, CONFIG, 1, out, run_label="m-think")
    assert [r["model"] for r in read(out)] == ["m", "m-think"]
    assert read(out)[1]["key"].startswith("m-think|tools|")


def test_thinking_without_label_does_not_collide():
    backend = ScriptedBackend([], name="m")
    assert run_label_for(backend, {}, None) == "m"
    assert run_label_for(backend, {"enable_thinking": False}, None) == "m"
    assert run_label_for(backend, {"enable_thinking": True}, None) == "m+think"
    assert run_label_for(backend, {"enable_thinking": True}, "x") == "x"


def test_failing_trajectory_does_not_stop_the_run(tmp_path):
    out = tmp_path / "r.jsonl"
    poisoned = INSTANCES[2].id

    def agent(messages, context):
        if instance_of(messages).id == poisoned:
            raise RuntimeError("fallo")
        return perfect_agent(messages, context)

    run_rollouts(INSTANCES, "tools", ScriptedBackend(agent), CONFIG, 1, out)
    records = read(out)
    assert len(records) == len(INSTANCES)
    errors = [r for r in records if r["verdict"]["error_type"] == "internal_error"]
    assert [r["instance_id"] for r in errors] == [poisoned]
    assert sum(r["verdict"]["reward"] for r in records) == len(INSTANCES) - 1


def test_internal_errors_are_retried_on_resume(tmp_path):
    out = tmp_path / "r.jsonl"

    def failing(messages, context):
        raise RuntimeError("caida")

    run_rollouts(INSTANCES[:3], "tools", ScriptedBackend(failing), CONFIG, 1, out)
    assert len(read(out)) == 3
    run_rollouts(INSTANCES[:3], "tools", ScriptedBackend(perfect_agent), CONFIG, 1, out)
    records = read(out)
    assert len(records) == 3 and all(r["verdict"]["reward"] == 1.0 for r in records)


def test_oom_sample_is_internal_error(tmp_path):
    out = tmp_path / "r.jsonl"

    class OutOfMemory(ScriptedBackend):
        def generate(self, batch, gen_config, seed):
            self.last_usage = [{"new_tokens": 0, "seconds": 0.0, "stop_reason": "oom"} for _ in batch]
            return ["" for _ in batch]

    run_rollouts(INSTANCES[:1], "tools", OutOfMemory([]), CONFIG, 1, out)
    assert read(out)[0]["verdict"]["error_type"] == "internal_error"


def test_writes_are_incremental(tmp_path):
    out = tmp_path / "r.jsonl"
    seen = []

    def agent(messages, context):
        seen.append(len(out.read_text(encoding="utf-8").splitlines()) if out.exists() else 0)
        return perfect_agent(messages, context)

    backend = ScriptedBackend(agent)
    run_rollouts(INSTANCES[:4], "visible", backend, {**CONFIG, "batch_size": 1}, 1, out, cohort_size=1)
    assert seen == [0, 1, 2, 3]


def test_default_cohort_is_bounded(tmp_path):
    backend = ScriptedBackend(perfect_agent)
    out = tmp_path / "r.jsonl"
    run_rollouts(INSTANCES, "visible", backend, {**CONFIG, "batch_size": 2}, 1, out)
    assert max(call["n"] for call in backend.calls) == 8


def test_progress_is_printed(tmp_path, capsys):
    out = tmp_path / "r.jsonl"
    run_rollouts(INSTANCES[:3], "visible", ScriptedBackend(perfect_agent), CONFIG, 1, out, progress_every=1)
    printed = capsys.readouterr().out
    assert "3/3" in printed and "ETA" in printed


def test_unknown_condition_raises(tmp_path):
    with pytest.raises(ValueError):
        run_rollouts(INSTANCES, "otra", ScriptedBackend([]), CONFIG, 1, tmp_path / "r.jsonl")


# ------------------------------------------------------------------------------ semillas


def sampling_agent(messages, context):
    """Imita una fila real: su ruido depende solo de la semilla del lote y de la fila."""
    return f"muestra {random.Random(f'{context.seed}|{context.row}').random()}"


@pytest.mark.parametrize("batch_size, cohort", [(1, None), (1, 1), (5, None), (2, 3), (8, 1)])
def test_samples_of_an_instance_differ(tmp_path, batch_size, cohort):
    out = tmp_path / "r.jsonl"
    config = {**CONFIG, "batch_size": batch_size}
    run_rollouts(
        INSTANCES[:1], "visible", ScriptedBackend(sampling_agent), config, 5, out, cohort_size=cohort
    )
    texts = [r["messages"][0]["content"] for r in read(out)]
    assert len(texts) == 5 and len(set(texts)) == 5


def test_seeds_are_reproducible(tmp_path):
    config = {**CONFIG, "batch_size": 2}
    outputs = []
    for name in ("a", "b"):
        out = tmp_path / f"{name}.jsonl"
        run_rollouts(INSTANCES[:2], "visible", ScriptedBackend(sampling_agent), config, 3, out)
        outputs.append([r["messages"][0]["content"] for r in read(out)])
    assert outputs[0] == outputs[1]


def test_base_seed_changes_samples(tmp_path):
    outputs = []
    for base in (0, 1):
        out = tmp_path / f"{base}.jsonl"
        run_rollouts(INSTANCES[:1], "visible", ScriptedBackend(sampling_agent), CONFIG, 1, out, base_seed=base)
        outputs.append(read(out)[0]["messages"][0]["content"])
    assert outputs[0] != outputs[1]


def test_generation_seed_depends_on_round_and_sample():
    base = generation_seed(0, "m", "tools", 0, ["k|0"])
    assert generation_seed(0, "m", "tools", 1, ["k|0"]) != base
    assert generation_seed(0, "m", "tools", 0, ["k|1"]) != base
    assert generation_seed(0, "m", "visible", 0, ["k|0"]) != base
    assert generation_seed(0, "m", "tools", 0, ["k|0"]) == base


# ------------------------------------------------------------------ cierre de la respuesta


def test_answer_close_is_restored_only_when_backend_stopped_there():
    text = "<answer>\nfaltan: 3\n"
    assert restore_answer_close(text, "answer") == text + "</answer>"
    for reason in ("length", "eos", "tool_result", None):
        assert restore_answer_close(text, reason) == text
    closed = text + "</answer>"
    assert restore_answer_close(closed, "answer") == closed


def test_rollout_applies_restoration(tmp_path):
    instance = INSTANCES[0]
    closed = final_text(instance)
    opened = closed[: -len("</answer>")]

    class LosesStop(ScriptedBackend):
        def __init__(self, reason):
            super().__init__([])
            self.reason = reason

        def generate(self, batch, gen_config, seed):
            self.last_usage = [{"new_tokens": 1, "seconds": 0.0, "stop_reason": self.reason}]
            return [opened]

    for reason, reward, error in (
        ("answer", 1.0, "ok"),
        ("length", 0.0, "multiple_answer_blocks"),
    ):
        out = tmp_path / f"{reason}.jsonl"
        run_rollouts([instance], "visible", LosesStop(reason), CONFIG, 1, out)
        verdict = read(out)[0]["verdict"]
        assert (verdict["reward"], verdict["error_type"]) == (reward, error)


def test_stop_string_is_kept_end_to_end(tmp_path):
    instance = INSTANCES[0]
    out = tmp_path / "r.jsonl"
    text = final_text(instance) + "\nbasura que el modelo siguio escribiendo"
    run_rollouts([instance], "visible", ScriptedBackend([text]), CONFIG, 1, out)
    record = read(out)[0]
    assert record["messages"][0]["content"].endswith("</answer>")
    assert record["verdict"]["reward"] == 1.0


def test_done_keys_of_missing_file(tmp_path):
    assert load_done_keys(tmp_path / "no.jsonl") == set()


def test_nombrar_etiquetas_al_razonar_no_cuesta_la_recompensa_y_se_guarda_la_parada(tmp_path):
    import json

    from inventory_harness.backends import Backend
    from inventory_harness.generator import generate_instance
    from inventory_harness.rollout import run_rollouts
    from inventory_harness.tools import truncate_at_tool_result

    instance = generate_instance("availability", "easy", "eval", 3)
    line = instance.orders[0].lines[0]
    location = instance.orders[0].location_ids[0]
    call = (
        '<tool_call>{"name": "get_inventory", "arguments": '
        f'{{"product_id": "{line.product_id}", "location_id": "{location}"}}}}</tool_call>'
    )
    expected = instance.expected
    final = (
        "<think>escribire </answer> y luego <tool_result> no llega aqui</think>\n"
        f"<answer>\nalcanza: {'sí' if expected['can_fulfill'] else 'no'}\n"
        f"faltan: {expected['missing_units']}\n</answer>"
    )
    assert truncate_at_tool_result(final) == final

    class Thinker(Backend):
        name = "pensador"

        def generate(self, batch, gen_config, seed):
            self.last_usage = []
            texts = []
            for messages in batch:
                texts.append(call if len(messages) == 1 else final)
                self.last_usage.append(
                    {"new_tokens": 5, "seconds": 0.1,
                     "stop_reason": "eos" if len(messages) == 1 else "answer"}
                )
            return texts

    out = tmp_path / "r.jsonl"
    run_rollouts([instance], "tools", Thinker(), {"batch_size": 1, "enable_thinking": True}, 1, out)
    record = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert record["verdict"]["reward"] == 1.0, record["verdict"]
    assert record["usage"]["stop_reasons"] == ["eos", "answer"]
