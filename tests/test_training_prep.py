"""Tests de los datos y la recompensa de entrenamiento (sin torch ni transformers)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from inventory_harness import training_prep as prep
from inventory_harness.baselines import format_answer
from inventory_harness.generator import fingerprint, generate_instance
from inventory_harness.prompts import render_prompt
from inventory_harness.reward import InstanceStore

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

INSTANCE = generate_instance("availability", "medium", "train", 5)
PROMPT = render_prompt(INSTANCE, "visible")
STORE = InstanceStore([INSTANCE])


def right_text(instance=INSTANCE) -> str:
    return "Calculo el resultado.\n\n" + format_answer(instance.family, instance.expected)


def wrong_text() -> str:
    expected = dict(INSTANCE.expected)
    expected["missing_units"] += 1
    return "Calculo el resultado.\n\n" + format_answer(INSTANCE.family, expected)


# --- SFT ---------------------------------------------------------------------


def test_cada_mensaje_del_asistente_es_un_ejemplo():
    tools = [
        {"role": "user", "content": "pedido"},
        {"role": "assistant", "content": "<think>a</think><tool_call>{}</tool_call>"},
        {"role": "user", "content": "<tool_result>{}</tool_result>"},
        {"role": "assistant", "content": "<think>b</think><answer>x</answer>"},
    ]
    examples = prep.conversation_examples(tools)
    assert [len(e) for e in examples] == [2, 4]
    assert all(e[-1]["role"] == "assistant" for e in examples)
    visible = prep.conversation_examples(tools[:2])
    assert len(visible) == 1 and visible[0] == tools[:2]


@pytest.mark.parametrize(
    "messages",
    [[], [{"role": "assistant", "content": "x"}], [{"role": "user", "content": "x"}],
     [{"role": "user", "content": "x"}, {"role": "system", "content": "y"}]],
)
def test_conversaciones_invalidas_se_rechazan(messages):
    with pytest.raises(ValueError):
        prep.conversation_examples(messages)


class FakeTokenizer:
    """ChatML a mano y una palabra por token, con offsets, como un tokenizer rapido."""

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False):
        assert tokenize is False
        return "".join(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in messages)

    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        spans = [match.span() for match in re.finditer(r"\S+|\s+", text)]
        out = {"input_ids": list(range(len(spans)))}
        if return_offsets_mapping:
            out["offset_mapping"] = spans
        return out


def test_la_perdida_cae_solo_en_el_ultimo_mensaje_del_asistente():
    conversation = [
        {"role": "user", "content": "uno dos"},
        {"role": "assistant", "content": "tres cuatro"},
        {"role": "user", "content": "cinco seis"},
        {"role": "assistant", "content": "siete ocho"},
    ]
    tokenizer = FakeTokenizer()
    example = prep.tokenize_example(tokenizer, conversation, max_length=200)
    text = tokenizer.apply_chat_template(conversation)
    tokens = [m.group() for m in re.finditer(r"\S+|\s+", text)]
    learned = "".join(token for token, label in zip(tokens, example["labels"]) if label != -100)
    assert learned == "siete ocho<|im_end|>"
    assert len(example["input_ids"]) == len(example["labels"]) == len(example["attention_mask"])
    # Lo no aprendido incluye el primer mensaje del asistente y el rol del ultimo.
    assert example["labels"][0] == -100


def test_un_ejemplo_demasiado_largo_se_descarta():
    conversation = [{"role": "user", "content": "uno"}, {"role": "assistant", "content": "dos tres"}]
    assert prep.tokenize_example(FakeTokenizer(), conversation, max_length=3) is None


def test_assistant_spans_incluye_el_cierre():
    rendered = "<|im_start|>user\nhola<|im_end|>\n<|im_start|>assistant\nrespuesta<|im_end|>\n"
    (start, end), = prep.assistant_spans(rendered)
    assert rendered[start:end] == "respuesta<|im_end|>"


def test_filtros_de_dificultad_y_condicion():
    rows = [
        {"difficulty": "easy", "condition": "visible"},
        {"difficulty": "hard", "condition": "tools"},
        {"difficulty": "medium", "condition": "tools"},
    ]
    assert len(prep.keep_difficulties(rows, ["easy", "medium"])) == 2
    assert prep.keep_difficulties(rows, None) == rows
    assert len(prep.keep_conditions(rows, "tools")) == 2
    assert prep.keep_conditions(rows, "all") == rows
    with pytest.raises(ValueError):
        prep.keep_difficulties(rows, ["imposible"])
    with pytest.raises(ValueError):
        prep.keep_conditions(rows, "otra")


def test_los_datos_reales_de_sft_se_leen_y_cada_uno_tiene_un_ejemplo_por_ronda():
    path = ROOT / "results" / "kaggle_qwen8b" / "datos_derivados_qwen8b" / "sft.jsonl"
    if not path.exists():
        pytest.skip("sft.jsonl no esta en este checkout")
    rows = prep.load_jsonl(path)
    for row in rows:
        examples = prep.conversation_examples(row["messages"])
        assert len(examples) == (2 if row["condition"] == "tools" else 1)


# --- DPO ---------------------------------------------------------------------


def test_dpo_en_formato_conversacional():
    row = {"prompt": "pedido", "chosen": [{"role": "assistant", "content": "bien"}],
           "rejected": [{"role": "assistant", "content": "mal"}]}
    assert prep.dpo_example(row) == {
        "prompt": [{"role": "user", "content": "pedido"}],
        "chosen": [{"role": "assistant", "content": "bien"}],
        "rejected": [{"role": "assistant", "content": "mal"}],
    }


# --- Instancias extra --------------------------------------------------------


def test_instancias_extra_no_repiten_eval_ni_test_ni_el_train_del_piloto():
    instances = prep.extra_train_instances(3)
    assert len(instances) == 27
    assert len({i.id for i in instances}) == 27
    assert all(i.id.startswith("train2_") and i.split == "train" for i in instances)
    protected = prep.protected_fingerprints()
    assert not any(fingerprint(i) in protected for i in instances)
    # Mismas semillas, mismas instancias.
    assert [i.to_dict() for i in instances] == [i.to_dict() for i in prep.extra_train_instances(3)]


def test_instancias_extra_se_escriben_y_se_leen(tmp_path):
    instances = prep.extra_train_instances(1)
    path = tmp_path / "extra.jsonl"
    assert prep.write_instances(path, instances) == 9
    assert [i.to_dict() for i in prep.read_instances(path)] == [i.to_dict() for i in instances]


def test_la_semilla_extra_no_es_la_del_piloto():
    assert prep.EXTRA_BASE_SEED != 2026


# --- GRPO --------------------------------------------------------------------


def test_filas_de_grpo_solo_visible_y_con_filtro_de_dificultad():
    instances = prep.extra_train_instances(1)
    rows = prep.grpo_rows(instances)
    assert len(rows) == 9
    assert all(r["prompt"][0]["role"] == "user" for r in rows)
    assert all("Formato de respuesta" in r["prompt"][0]["content"] for r in rows)
    assert all("get_inventory" not in r["prompt"][0]["content"].split("Solicitud:")[0] for r in rows)
    easy = prep.grpo_rows(instances, ["easy", "medium"])
    assert len(easy) == 6 and {r["difficulty"] for r in easy} == {"easy", "medium"}


def test_la_recompensa_de_grpo_acepta_mensajes_y_texto():
    reward = prep.make_grpo_reward(STORE)
    prompts = [[{"role": "user", "content": PROMPT}]] * 2 + [PROMPT]
    completions = [
        [{"role": "assistant", "content": right_text()}],
        [{"role": "assistant", "content": wrong_text()}],
        right_text(),
    ]
    assert reward(prompts, completions) == [1.0, 0.0, 1.0]
    assert reward.summary()["respuestas"] == 3
    assert reward.summary()["errores"] == {"ok": 2, "wrong_value": 1}


def test_la_recompensa_de_grpo_da_cero_a_lo_desconocido_y_no_lanza():
    reward = prep.make_grpo_reward(STORE)
    out = reward([[{"role": "user", "content": "otro prompt"}], [{"role": "user", "content": PROMPT}]],
                 [[{"role": "assistant", "content": right_text()}], [{"role": "assistant", "content": ""}]])
    assert out == [0.0, 0.0]
    assert reward.errors["prompt_desconocido"] == 1


def test_una_respuesta_cortada_por_el_tope_de_tokens_da_cero():
    reward = prep.make_grpo_reward(STORE)
    cut = "<think>\nrazono mucho\n" * 5
    assert reward([PROMPT], [[{"role": "assistant", "content": cut}]]) == [0.0]
    assert reward.errors["no_answer_block"] == 1


def test_la_recompensa_guarda_las_respuestas_para_auditarlas(tmp_path):
    path = tmp_path / "sub" / "completions.jsonl"
    reward = prep.make_grpo_reward(STORE, trace_path=path, trace_every=1)
    reward([PROMPT, PROMPT], [right_text(), wrong_text()])
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [r["reward"] for r in rows] == [1.0, 0.0]
    assert rows[0]["instance_id"] == INSTANCE.id and rows[1]["error_type"] == "wrong_value"
    assert "faltan" in rows[1]["completion"]


def test_trace_every_guarda_una_de_cada_n(tmp_path):
    path = tmp_path / "c.jsonl"
    reward = prep.make_grpo_reward(STORE, trace_path=path, trace_every=2)
    reward([PROMPT] * 4, [right_text()] * 4)
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2


def test_el_grupo_con_la_misma_recompensa_no_da_senal():
    # Lo que GRPO necesita: dentro de un grupo, respuestas con recompensas distintas.
    reward = prep.make_grpo_reward(STORE)
    group = reward([PROMPT] * 4, [right_text(), right_text(), wrong_text(), right_text()])
    assert len(set(group)) == 2


# --- Evaluacion de modelos entrenados ----------------------------------------


def test_la_etapa_eval_final_mide_las_mismas_instancias_que_la_linea_base():
    import run_pilot

    stage = run_pilot.STAGES["eval_final"]
    assert (stage["split"], stage["n_per_cell"], stage["base_seed"], stage["n_samples"]) == ("eval", 10, 2026, 5)
    baseline = ROOT / "results" / "kaggle_qwen17b" / "linea_base_qwen17b" / "manifest.json"
    if baseline.exists():
        recorded = json.loads(baseline.read_text(encoding="utf-8"))["dataset"]["fingerprint"]
        instances = run_pilot.build_dataset(stage["split"], stage["n_per_cell"], stage["base_seed"])
        assert run_pilot.dataset_fingerprint(instances) == recorded


def test_la_etiqueta_de_un_adaptador_no_se_confunde_con_la_del_modelo_base():
    import run_pilot

    base, _ = run_pilot.expand_variants(["Qwen/Qwen3-1.7B"], "on")
    tuned, _ = run_pilot.expand_variants(["Qwen/Qwen3-1.7B"], "on", adapter="runs/sft/adapter")
    assert base[0]["label"] == "Qwen/Qwen3-1.7B+think" and base[0]["adapter"] is None
    assert tuned[0]["label"] == "Qwen/Qwen3-1.7B+think+lora:sft"
    named, _ = run_pilot.expand_variants(["Qwen/Qwen3-1.7B"], "on", adapter="x/adapter", adapter_name="dpo_beta0.1")
    assert named[0]["label"].endswith("+lora:dpo_beta0.1")
    assert run_pilot.rollouts_path(Path("out"), tuned[0]["label"]) != run_pilot.rollouts_path(Path("out"), base[0]["label"])


def test_adapter_exige_un_solo_modelo(tmp_path):
    import run_pilot

    with pytest.raises(SystemExit):
        run_pilot.main(["--stage", "eval_final", "--models", "a", "b", "--adapter", "x", "--dry-run",
                        "--out", str(tmp_path / "salida")])


def test_evaluar_un_adaptador_en_seco_guarda_los_rollouts_con_su_propia_etiqueta(tmp_path):
    import run_pilot

    out = tmp_path / "salida"
    assert run_pilot.main([
        "--stage", "eval_final", "--models", "Qwen/Qwen3-1.7B", "--thinking", "on", "--dry-run",
        "--adapter", str(tmp_path / "sft" / "adapter"), "--limit", "2", "--n-samples", "1",
        "--conditions", "visible", "--out", str(out),
    ]) == 0
    files = sorted(path.name for path in out.glob("rollouts_*.jsonl"))
    assert files == ["rollouts_Qwen_Qwen3-1.7B+think+lora_sft.jsonl"]
    row = json.loads((out / files[0]).read_text(encoding="utf-8").splitlines()[0])
    assert row["model"] == "Qwen/Qwen3-1.7B+think+lora:sft"


# --- Auditoria ---------------------------------------------------------------


def test_la_muestra_de_auditoria_solo_trae_aciertos_y_es_reproducible(tmp_path):
    import csv

    import audit_sample

    rows = []
    for index in range(12):
        rows.append({"model": "m", "condition": "visible" if index % 2 else "tools", "family": "availability",
                     "difficulty": "easy", "instance_id": f"i{index}", "sample": 0,
                     "messages": [{"role": "assistant", "content": f"respuesta {index}"}],
                     "verdict": {"reward": 1.0 if index % 3 else 0.0}})
    folder = tmp_path / "corrida"
    folder.mkdir()
    (folder / "rollouts_m.jsonl").write_text("
".join(json.dumps(r) for r in rows), encoding="utf-8")
    out1, out2 = tmp_path / "a.csv", tmp_path / "b.csv"
    assert audit_sample.main([str(folder), "--n", "5", "--out", str(out1)]) == 0
    assert audit_sample.main([str(folder), "--n", "5", "--out", str(out2)]) == 0
    first = list(csv.DictReader(out1.open(encoding="utf-8-sig")))
    assert len(first) == 5 and out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")
    assert not {r["instancia"] for r in first} & {"i0", "i3", "i6", "i9"}  # los que fallaron
    assert {r["condicion"] for r in first} == {"visible", "tools"}  # reparte entre celdas
    assert all(r["genuino"] == "" for r in first)
