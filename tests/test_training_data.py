from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

from inventory_harness.generator import generate_instance
from inventory_harness.prompts import render_prompt
from inventory_harness.reward import InstanceStore, make_reward
from inventory_harness.training_data import build, collect, normalize_tool_message
from test_reward import final_text, observations, required_products  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

INSTANCE = generate_instance("availability", "medium", "train", 5)
PROMPT = render_prompt(INSTANCE, "tools")
STORE = InstanceStore([INSTANCE])


def untagged_calls(instance):
    return "\n".join(f'get_inventory("{product}")' for product in required_products(instance))


def wrong_text(instance):
    expected = dict(instance.expected)
    expected["missing_units"] += 1
    return final_text(instance, expected)


def row(model, sample, final, calls=None, stops=("eos", "answer")):
    calls = calls if calls is not None else untagged_calls(INSTANCE)
    messages = [
        {"role": "assistant", "content": f"<think>razono</think>\n\n{calls}\nResultado: inventado"},
        {"role": "user", "content": observations(INSTANCE, calls)},
        {"role": "assistant", "content": final},
    ]
    return {"model": model, "sample": sample, "prompt": PROMPT, "messages": messages,
            "verdict": {"error_type": "ok"}, "usage": {"stop_reasons": list(stops)}}


def test_normaliza_llamadas_y_conserva_el_razonamiento():
    text = '<think>pienso</think>\n\nLlamo get_inventory("P01", "S1") y supongo 50.'
    assert normalize_tool_message(text) == (
        '<think>pienso</think>\n\n<tool_call>{"name": "get_inventory", '
        '"arguments": {"product_id": "P01", "location_id": "S1"}}</tool_call>'
    )


@pytest.mark.parametrize("text", ["<answer>\nfaltan: 3\n</answer>", "sin llamadas", "<tool_call>{roto}</tool_call>"])
def test_mensajes_sin_llamadas_legibles_no_cambian(text):
    assert normalize_tool_message(text) == text


def test_profesor_elegido_y_error_del_alumno_rechazado():
    rows = [
        row("chico", 0, final_text(INSTANCE)),
        row("chico", 1, wrong_text(INSTANCE)),
        row("grande", 0, final_text(INSTANCE)),
        row("chico", 2, "Pienso y pienso", stops=("length",)),
    ]
    sft, dpo, stats = build(collect(rows, STORE, Counter()), teacher="grande")
    assert [r["source_model"] for r in sft] == ["grande"]
    assert sft[0]["messages"][0] == {"role": "user", "content": PROMPT}
    assert "<tool_call>" in sft[0]["messages"][1]["content"]
    assert "inventado" not in sft[0]["messages"][1]["content"]
    assert len(dpo) == 1 and dpo[0]["chosen_model"] == "grande" and dpo[0]["rejected_model"] == "chico"
    assert dpo[0]["rejected_error_type"] == "wrong_value"
    reward = make_reward(STORE)
    assert reward(PROMPT, json.dumps(dpo[0]["chosen"])) == 1.0
    assert reward(PROMPT, json.dumps(dpo[0]["rejected"])) == 0.0
    assert stats["por_celda"]["availability|medium|tools"]["sft"] == 1


def test_sin_profesor_el_par_sale_del_mismo_modelo():
    rows = [row("chico", 0, wrong_text(INSTANCE)), row("chico", 1, final_text(INSTANCE))]
    _, dpo, _ = build(collect(rows, STORE, Counter()), teacher="grande")
    assert (dpo[0]["chosen_model"], dpo[0]["rejected_model"]) == ("chico", "chico")


def test_respuesta_cortada_no_es_rechazada_y_sin_correcta_no_hay_par():
    rows = [row("chico", 0, "Pienso y pienso", stops=("length",)), row("chico", 1, wrong_text(INSTANCE))]
    sft, dpo, _ = build(collect(rows, STORE, Counter()))
    assert sft == [] and dpo == []


def test_llamadas_invalidas_no_entran_a_sft():
    calls = 'get_inventory("P99")\n' + untagged_calls(INSTANCE)
    sft, _, _ = build(collect([row("chico", 0, final_text(INSTANCE), calls=calls)], STORE, Counter()))
    assert sft == []


def test_prompt_desconocido_se_descarta_y_eval_se_rechaza():
    dropped = Counter()
    unknown = {**row("chico", 0, final_text(INSTANCE)), "prompt": "otro"}
    assert collect([unknown], STORE, dropped) == [] and dropped["prompt_desconocido"] == 1
    other = generate_instance("availability", "medium", "eval", 5)
    eval_row = {**row("chico", 0, final_text(INSTANCE)), "prompt": render_prompt(other, "tools")}
    with pytest.raises(ValueError):
        collect([eval_row], InstanceStore([other]), Counter())


def test_train_de_trazas_no_comparte_instancias_con_eval_ni_test():
    import run_pilot

    from inventory_harness.generator import fingerprint

    stage = run_pilot.STAGES["trazas"]
    assert stage["split"] == "train" and stage["base_seed"] == run_pilot.STAGES["piloto"]["base_seed"]
    train = {fingerprint(i) for i in run_pilot.build_dataset("train", 10, 2026)}
    for split, n in (("eval", 10), ("eval", 20), ("eval", 40), ("test", 40)):
        assert not train & {fingerprint(i) for i in run_pilot.build_dataset(split, n, 2026)}


def test_script_de_punta_a_punta_con_dry_run(tmp_path):
    import build_training_data
    import run_pilot

    runs = tmp_path / "trazas"
    assert run_pilot.main([
        "--stage", "trazas", "--dry-run", "--limit", "9", "--n-samples", "3",
        "--models", "m/chico", "m/grande", "--out", str(runs),
    ]) == 0
    out = tmp_path / "datos"
    assert build_training_data.main([str(runs), "--out", str(out), "--teacher", "m/grande"]) == 0

    store = InstanceStore(run_pilot.build_dataset("train", 10, 2026))
    reward = make_reward(store)
    sft = [json.loads(line) for line in (out / "sft.jsonl").read_text(encoding="utf-8").splitlines()]
    dpo = [json.loads(line) for line in (out / "dpo.jsonl").read_text(encoding="utf-8").splitlines()]
    assert sft and dpo
    for item in sft:
        prompt, *rest = item["messages"]
        assert reward(prompt["content"], json.dumps(rest)) == 1.0
    for item in dpo:
        assert reward(item["prompt"], json.dumps(item["chosen"])) == 1.0
        assert reward(item["prompt"], json.dumps(item["rejected"])) == 0.0
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["profesor"] == "m/grande" and manifest["sft"] == len(sft)
    assert manifest["avisos"] == []


def test_script_avisa_si_la_corrida_uso_otro_codigo(tmp_path, capsys):
    import build_training_data
    import run_pilot

    runs = tmp_path / "trazas"
    assert run_pilot.main([
        "--stage", "trazas", "--dry-run", "--limit", "9", "--n-samples", "1",
        "--models", "m/chico", "--out", str(runs),
    ]) == 0
    path = runs / "manifest.json"
    run_manifest = json.loads(path.read_text(encoding="utf-8"))
    run_manifest.update(code_hash="otro", hashes_anteriores=["viejo"])
    path.write_text(json.dumps(run_manifest), encoding="utf-8")
    capsys.readouterr()

    out = tmp_path / "datos"
    assert build_training_data.main([str(runs), "--out", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "AVISO: trazas: la corrida uso el codigo otro" in printed
    assert "mezcla versiones" in printed
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["avisos"]) == 2


def test_script_rechaza_corridas_que_no_son_de_train(tmp_path):
    import build_training_data
    import run_pilot

    runs = tmp_path / "piloto"
    assert run_pilot.main([
        "--stage", "piloto", "--dry-run", "--limit", "9", "--n-samples", "1",
        "--models", "m/chico", "--out", str(runs),
    ]) == 0
    with pytest.raises(SystemExit):
        build_training_data.main([str(runs), "--out", str(tmp_path / "datos")])
