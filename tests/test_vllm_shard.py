"""VLLMBackend (con un motor falso, sin GPU ni vllm), --backend y --shard de run_pilot."""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

from inventory_harness.backends import (
    DEFAULT_STOP_STRINGS,
    Backend,
    VLLMBackend,
    finish_vllm_row,
)

ROOT = Path(__file__).resolve().parents[1]


def user(text):
    return [{"role": "user", "content": text}]


class FakeParams:
    def __init__(self, **options):
        self.options = options


class FakeTokenizer:
    chat_template = "{% if enable_thinking %}"

    def __init__(self):
        self.rendered = []

    def apply_chat_template(self, messages, **options):
        self.rendered.append(options)
        return messages[0]["content"]

    def __call__(self, text, add_special_tokens=True):
        assert add_special_tokens is False
        return {"input_ids": list(range(len(text.split())))}


class FakeLLM:
    """Responde con `replies[i]` = (texto, n_tokens, finish_reason) para la fila i."""

    def __init__(self, replies):
        self.replies = replies
        self.tokenizer = FakeTokenizer()
        self.calls = []

    def get_tokenizer(self):
        return self.tokenizer

    def generate(self, prompts, params, use_tqdm=True):
        self.calls.append((prompts, params, use_tqdm))
        outputs = []
        for index in range(len(prompts)):
            text, tokens, reason = self.replies[index]
            completion = SimpleNamespace(text=text, token_ids=list(range(tokens)), finish_reason=reason)
            outputs.append(SimpleNamespace(outputs=[completion]))
        return outputs


def backend(replies):
    llm = FakeLLM(replies)
    return VLLMBackend("modelo", llm=llm, sampling_params_cls=FakeParams, name="falso"), llm


# --- finish_vllm_row ------------------------------------------------------------


@pytest.mark.parametrize(
    "text, finish, expected",
    [
        ("pienso <answer>x</answer> basura", "stop", ("pienso <answer>x</answer>", "answer")),
        ("<tool_call>{}</tool_call><tool_result>inventado", "stop", ("<tool_call>{}</tool_call><tool_result>", "tool_result")),
        ("sin parada", "stop", ("sin parada", "eos")),
        ("cortado", "length", ("cortado", "length")),
        # Una parada nombrada dentro de <think> no cuenta.
        ("<think>escribo </answer> aqui</think>listo", "stop", ("<think>escribo </answer> aqui</think>listo", "eos")),
    ],
)
def test_finish_vllm_row(text, finish, expected):
    out, tokens, reason = finish_vllm_row(text, 7, finish, DEFAULT_STOP_STRINGS)
    assert (out, reason) == expected and tokens == 7


# --- VLLMBackend ----------------------------------------------------------------


def test_is_a_backend_and_does_not_import_vllm_when_injected():
    instance, _ = backend([("a", 1, "stop")])
    assert isinstance(instance, Backend)
    assert "vllm" not in sys.modules


def test_generate_keeps_order_and_reports_usage():
    instance, llm = backend(
        [("uno <answer>1</answer> resto", 5, "stop"), ("dos", 9, "length"), ("tres", 2, "stop")]
    )
    texts = instance.generate([user("a b"), user("c"), user("d e f")], {"max_new_tokens": 9}, 3)
    assert texts == ["uno <answer>1</answer>", "dos", "tres"]
    assert [u["stop_reason"] for u in instance.last_usage] == ["answer", "length", "eos"]
    assert [u["new_tokens"] for u in instance.last_usage] == [5, 9, 2]
    prompts, params, use_tqdm = llm.calls[0]
    assert use_tqdm is False
    # Ids ya tokenizados, uno por palabra del prompt de juguete.
    assert [len(p["prompt_token_ids"]) for p in prompts] == [2, 1, 3]
    assert len(params) == 3


def test_each_row_gets_its_own_stable_seed():
    instance, llm = backend([("a", 1, "stop")] * 4)
    instance.generate([user("x")] * 4, {}, 11)
    seeds = [p.options["seed"] for p in llm.calls[0][1]]
    assert len(set(seeds)) == 4
    other, other_llm = backend([("a", 1, "stop")] * 4)
    other.generate([user("x")] * 4, {}, 11)
    assert [p.options["seed"] for p in other_llm.calls[0][1]] == seeds
    other.generate([user("x")] * 4, {}, 12)
    assert [p.options["seed"] for p in other_llm.calls[1][1]] != seeds


def test_thinking_does_not_pass_stops_but_non_thinking_does():
    instance, llm = backend([("a", 1, "stop")])
    instance.generate([user("x")], {"enable_thinking": True}, 0)
    thinking = llm.calls[-1][1][0].options
    assert "stop" not in thinking and "include_stop_str_in_output" not in thinking
    instance.generate([user("x")], {"enable_thinking": False}, 0)
    plain = llm.calls[-1][1][0].options
    assert plain["stop"] == list(DEFAULT_STOP_STRINGS) and plain["include_stop_str_in_output"] is True


def test_thinking_is_recut_after_generation():
    reply = "<think>razono</think><tool_call>{}</tool_call><tool_result>inventado</tool_result>"
    instance, _ = backend([(reply, 20, "stop")])
    [text] = instance.generate([user("x")], {"enable_thinking": True}, 0)
    assert text.endswith("<tool_result>") and "inventado" not in text
    assert instance.last_usage[0]["stop_reason"] == "tool_result"


def test_sampling_options_follow_gen_config():
    instance, llm = backend([("a", 1, "stop")])
    config = {"max_new_tokens": 4096, "temperature": 0.7, "top_p": 0.95, "top_k": 50, "repetition_penalty": 1.0}
    instance.generate([user("x")], config, 0)
    options = llm.calls[-1][1][0].options
    assert options["max_tokens"] == 4096 and options["temperature"] == 0.7
    assert options["top_p"] == 0.95 and options["top_k"] == 50 and options["repetition_penalty"] == 1.0
    instance.generate([user("x")], {"do_sample": False, "temperature": 0.7}, 0)
    greedy = llm.calls[-1][1][0].options
    assert greedy["temperature"] == 0.0 and "top_p" not in greedy


def test_omitted_thinking_means_off_for_templates_that_support_it():
    instance, llm = backend([("a", 1, "stop")])
    instance.generate([user("x")], {}, 0)
    assert llm.tokenizer.rendered[-1]["enable_thinking"] is False
    instance.generate([user("x")], {"enable_thinking": True}, 0)
    assert llm.tokenizer.rendered[-1]["enable_thinking"] is True
    llm.tokenizer.chat_template = "plantilla sin la variable"
    instance.generate([user("x")], {"enable_thinking": True}, 0)
    assert "enable_thinking" not in llm.tokenizer.rendered[-1]


def test_output_count_mismatch_raises():
    instance, llm = backend([("a", 1, "stop")])
    llm.generate = lambda prompts, params, use_tqdm=True: []
    with pytest.raises(ValueError):
        instance.generate([user("x")], {}, 0)


# --- run_pilot: --shard y --backend ---------------------------------------------


@pytest.fixture(scope="module")
def run_pilot():
    sys.path.insert(0, str(ROOT / "scripts"))
    import run_pilot as module

    return module


def test_parse_shard(run_pilot):
    assert run_pilot.parse_shard("2/3") == (2, 3)
    for bad in ("0/3", "4/3", "1", "a/b", "1/0", "-1/2"):
        with pytest.raises(SystemExit):
            run_pilot.parse_shard(bad)


@pytest.mark.parametrize("count", [1, 2, 3, 4])
def test_shards_are_disjoint_complete_and_balanced_per_cell(run_pilot, count):
    instances = run_pilot.build_dataset("train", 12, 2026)
    parts = [run_pilot.shard_instances(instances, i, count) for i in range(1, count + 1)]
    ids = [instance.id for part in parts for instance in part]
    assert len(ids) == len(set(ids)) == len(instances)
    assert set(ids) == {instance.id for instance in instances}
    for part in parts:
        per_cell = Counter((i.family, i.difficulty) for i in part)
        assert len(per_cell) == 9  # ninguna celda queda fuera de una parte
        assert max(per_cell.values()) - min(per_cell.values()) <= 1


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_pilot.py"), *args],
        capture_output=True, text=True, cwd=ROOT,
    )


def read_rows(folder):
    rows = []
    for path in sorted(folder.glob("rollouts_*.jsonl")):
        rows += [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows


def test_dry_run_with_vllm_backend_and_shards_cover_the_dataset(tmp_path):
    common = ["--stage", "trazas", "--dry-run", "--n-per-cell", "4", "--n-samples", "2",
              "--models", "Qwen/Qwen3-8B", "--thinking", "on", "--backend", "vllm"]
    seen = set()
    fingerprints = set()
    for index in (1, 2):
        out = tmp_path / f"parte{index}"
        done = run_cli(*common, "--shard", f"{index}/2", "--out", str(out))
        assert done.returncode == 0, done.stderr + done.stdout
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["backend"] == "vllm" and manifest["shard"] == f"{index}/2"
        assert manifest["gen_configs"]["Qwen/Qwen3-8B+think"]["backend"] == "vllm"
        assert manifest["gen_configs"]["Qwen/Qwen3-8B+think"]["batch_size"] == 64
        fingerprints.add(manifest["dataset"]["fingerprint"])
        keys = {row["key"] for row in read_rows(out)}
        assert not keys & seen  # partes disjuntas
        seen |= keys
    assert len(fingerprints) == 1  # misma huella: las partes se pueden juntar
    # 9 celdas x 4 instancias x 2 condiciones x 2 muestras
    assert len(seen) == 9 * 4 * 2 * 2


def test_hf_runs_keep_the_old_gen_config(tmp_path, run_pilot):
    done = run_cli("--stage", "trazas", "--dry-run", "--limit", "9", "--n-samples", "1",
                   "--models", "Qwen/Qwen3-1.7B", "--out", str(tmp_path))
    assert done.returncode == 0, done.stderr + done.stdout
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    config = next(iter(manifest["gen_configs"].values()))
    assert "backend" not in config  # igual que las corridas anteriores a vLLM
    assert manifest["backend"] == "hf" and manifest["shard"] is None


def test_a_folder_made_with_hf_refuses_to_resume_with_vllm(tmp_path):
    base = ["--stage", "trazas", "--dry-run", "--limit", "9", "--n-samples", "1",
            "--models", "Qwen/Qwen3-1.7B", "--out", str(tmp_path)]
    assert run_cli(*base).returncode == 0
    again = run_cli(*base, "--backend", "vllm")
    assert "OMITIDO" in again.stdout  # configuracion de generacion distinta
    assert again.returncode == 1
