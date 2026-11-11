"""Metricas con rollouts sinteticos cuyos valores se calcularon a mano."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from inventory_harness.metrics import (
    aggregate,
    group_instances,
    load_rollouts,
    max_samples,
    pass_at_k,
    proportion,
    summarize_rows,
    wilson_interval,
)


def row(instance: str, sample: int, reward: float = 0.0, *, model="m", condition="tools", **verdict):
    return {
        "key": f"{model}|{condition}|{instance}|{sample}",
        "model": model,
        "condition": condition,
        "instance_id": instance,
        "family": "availability",
        "difficulty": "easy",
        "split": "eval",
        "sample": sample,
        "verdict": {"reward": reward, "error_type": "ok" if reward else "wrong_value", **verdict},
        "usage": {"new_tokens": 10, "seconds": 0.5},
    }


def grid(pattern: dict[str, list[int]]) -> list[dict]:
    return [
        row(instance, sample, float(hit))
        for instance, hits in pattern.items()
        for sample, hit in enumerate(hits)
    ]


# --- Wilson ---------------------------------------------------------------


@pytest.mark.parametrize(
    "successes,n,low,high",
    [
        # Calculados a mano: (p + z²/2n ± z·sqrt(p(1-p)/n + z²/4n²)) / (1 + z²/n), z=1.96.
        (5, 10, 0.2366, 0.7634),
        (0, 10, 0.0, 0.2775),
        (10, 10, 0.7225, 1.0),
        (20, 40, 0.3520, 0.6480),
        (1, 1, 0.2065, 1.0),
    ],
)
def test_wilson_known_values(successes, n, low, high):
    got_low, got_high = wilson_interval(successes, n)
    assert got_low == pytest.approx(low, abs=5e-4)
    assert got_high == pytest.approx(high, abs=5e-4)


def test_wilson_without_data():
    assert wilson_interval(0, 0) == (None, None)


def test_wilson_rejects_impossible_counts():
    with pytest.raises(ValueError):
        wilson_interval(4, 3)


# --- pass@1 y pass@k ------------------------------------------------------


def test_pass_at_1_uses_sample_zero_not_the_mean():
    # A acierta solo en la muestra 1; B solo en la 0. La media por muestra es 2/6.
    rows = grid({"A": [0, 1, 0], "B": [1, 0, 0]})
    summary = summarize_rows(rows, ks=(1, 3))
    assert summary["pass@1"]["aciertos"] == 1
    assert summary["pass@1"]["n"] == 2
    assert summary["pass@1"]["tasa"] == 0.5
    assert summary["tasa_media_muestra"] == {"aciertos": 2, "n": 6, "tasa": pytest.approx(1 / 3)}


def test_pass_at_k_is_any_success_in_first_k():
    rows = grid({"A": [0, 0, 1], "B": [0, 1, 0], "C": [0, 0, 0], "D": [1, 0, 0]})
    summary = summarize_rows(rows, ks=(1, 2, 3))
    assert (summary["pass@1"]["aciertos"], summary["pass@1"]["n"]) == (1, 4)
    assert (summary["pass@2"]["aciertos"], summary["pass@2"]["n"]) == (2, 4)
    assert (summary["pass@3"]["aciertos"], summary["pass@3"]["n"]) == (3, 4)


def test_pass_at_k_ignores_samples_beyond_k():
    summary = summarize_rows(grid({"A": [0, 0, 1]}), ks=(2,))
    assert summary["pass@2"]["aciertos"] == 0


def test_sample_order_in_file_does_not_matter():
    rows = list(reversed(grid({"A": [1, 0, 0], "B": [0, 0, 1]})))
    assert summarize_rows(rows, ks=(1,))["pass@1"]["aciertos"] == 1


def test_interval_is_computed_over_instances():
    rows = grid({f"I{i}": [1 if i < 5 else 0] * 3 for i in range(10)})
    result = summarize_rows(rows, ks=(1,))["pass@1"]
    assert result["n"] == 10
    assert result["ic95"][0] == pytest.approx(0.2366, abs=5e-4)


def test_missing_samples_leave_the_denominator_and_are_reported():
    # B tiene 2 de 3 muestras y un acierto; C no tiene la muestra 0.
    rows = grid({"A": [0, 0, 1], "B": [1, 0]})
    rows += [row("C", 1, 1.0), row("C", 2, 0.0)]
    summary = summarize_rows(rows, ks=(1, 3))
    assert (summary["pass@1"]["aciertos"], summary["pass@1"]["n"]) == (1, 2)
    assert (summary["pass@3"]["aciertos"], summary["pass@3"]["n"]) == (1, 1)
    assert summary["incompletas"]["k=1"] == {"n": 1, "instancias": ["C"]}
    assert summary["incompletas"]["k=3"] == {"n": 2, "instancias": ["B", "C"]}


def test_k_larger_than_the_data_gives_no_rate_instead_of_zero():
    summary = summarize_rows(grid({"A": [1, 1]}), ks=(5,))
    assert summary["pass@5"]["n"] == 0
    assert summary["pass@5"]["tasa"] is None
    assert summary["pass@5"]["ic95"] == [None, None]
    assert summary["incompletas"]["k=5"]["n"] == 1


def test_pass_at_k_rejects_k_zero():
    with pytest.raises(ValueError):
        pass_at_k(group_instances(grid({"A": [1]})), 0)


def test_max_samples():
    assert max_samples(grid({"A": [1, 0], "B": [1, 0, 0]})) == 3
    assert max_samples([]) == 0


# --- Diagnosticos ---------------------------------------------------------


def test_tool_rates_ignore_not_applicable():
    rows = [
        row("A", 0, valid_tool_call=True, correct_tool_arguments=False, retrieved_required_data=None),
        row("B", 0, valid_tool_call=False, correct_tool_arguments=None, retrieved_required_data=None),
        row("C", 0, valid_tool_call=None, correct_tool_arguments=True, retrieved_required_data=True),
    ]
    summary = summarize_rows(rows, ks=(1,))
    assert summary["valid_tool_call"] == {"si": 1, "n": 2}
    assert summary["correct_tool_arguments"] == {"si": 1, "n": 2}
    assert summary["retrieved_required_data"] == {"si": 1, "n": 1}


def test_parser_error_and_correct_without_reward():
    rows = [
        row("A", 0, parser_error=True),
        row("B", 0, parser_error=False, correct_final_answer=True),
        row("C", 0, 1.0, parser_error=False, correct_final_answer=True),
    ]
    summary = summarize_rows(rows, ks=(1,))
    assert summary["parser_error"] == {"si": 1, "n": 3}
    assert summary["correcta_sin_recompensa"] == {"si": 1, "n": 3}


def test_error_types_include_internal_and_unknown_values():
    rows = [row("A", 0), row("B", 0), row("C", 0), row("D", 0)]
    rows[0]["verdict"]["error_type"] = "internal_error"
    rows[1]["verdict"]["error_type"] = "valor_que_no_existe"
    rows[2]["verdict"]["error_type"] = None
    del rows[3]["verdict"]
    types = summarize_rows(rows, ks=(1,))["error_types"]
    assert types == {
        "internal_error": 1,
        "valor_que_no_existe": 1,
        "sin_error_type": 1,
        "sin_veredicto": 1,
    }


def test_odd_reward_is_a_failure():
    rows = [row("A", 0), row("B", 0), row("C", 0)]
    rows[0]["verdict"]["reward"] = None
    rows[1]["verdict"]["reward"] = True
    rows[2]["verdict"]["reward"] = "1.0"
    assert summarize_rows(rows, ks=(1,))["pass@1"]["aciertos"] == 0


def test_tokens_and_time():
    usage = summarize_rows(grid({"A": [1, 0], "B": [0, 0]}), ks=(1,))["uso"]
    assert usage["tokens_nuevos"] == 40
    assert usage["tokens_por_muestra"] == 10
    assert usage["segundos"] == 2.0
    assert usage["segundos_por_muestra"] == 0.5


def test_token_limit_is_flagged():
    rows = [row("A", 0), row("B", 0)]
    rows[0].update(usage={"new_tokens": 512}, gen_config={"max_new_tokens": 512})
    rows[1].update(usage={"new_tokens": 30}, gen_config={"max_new_tokens": 512})
    assert summarize_rows(rows, ks=(1,))["tope_de_tokens"] == {"si": 1, "n": 2}


def test_missing_usage_does_not_break():
    rows = [row("A", 0)]
    del rows[0]["usage"]
    assert summarize_rows(rows, ks=(1,))["uso"]["tokens_nuevos"] == 0


# --- Agregacion -----------------------------------------------------------


def test_aggregate_separates_every_dimension():
    rows = [
        row("A", 0, 1.0, model="m1", condition="tools"),
        row("A", 0, 0.0, model="m1", condition="visible"),
        row("A", 0, 0.0, model="m2", condition="tools"),
    ]
    rows.append({**row("B", 0, 1.0, model="m1", condition="tools"), "family": "selection"})
    rows.append({**row("C", 0, 1.0, model="m1", condition="tools"), "difficulty": "hard"})
    groups = aggregate(rows, ks=(1,))
    assert len(groups) == 5
    cell = next(g for g in groups if g["model"] == "m1" and g["condition"] == "visible")
    assert (cell["family"], cell["difficulty"]) == ("availability", "easy")
    assert cell["pass@1"]["aciertos"] == 0


def test_marginal_aggregate_counts_same_instance_once_per_condition():
    rows = [row("A", 0, 1.0, condition="tools"), row("A", 0, 0.0, condition="visible")]
    group = aggregate(rows, ks=(1,), group_by=("model",))[0]
    assert group["n_instancias"] == 2
    assert group["pass@1"]["n"] == 2


def test_aggregate_is_json_serializable():
    json.dumps(aggregate(grid({"A": [1, 0]}), ks=(1, 2)))


# --- Carga ----------------------------------------------------------------


def write_lines(path, lines, *, end="\n"):
    path.write_text("\n".join(lines) + end, encoding="utf-8")
    return path


def test_load_tolerates_truncated_final_line(tmp_path):
    good = [json.dumps(row("A", 0, 1.0)), json.dumps(row("A", 1))]
    path = write_lines(tmp_path / "r.jsonl", [*good, good[0][:25]], end="")
    loaded = load_rollouts(path)
    assert len(loaded.rows) == 2
    assert loaded.truncated_final_line == 1
    assert loaded.corrupt_lines == 0


def test_load_reports_corruption_in_the_middle(tmp_path):
    good = [json.dumps(row("A", s)) for s in range(2)]
    path = write_lines(tmp_path / "r.jsonl", [good[0], "{roto", good[1]])
    loaded = load_rollouts(path)
    assert len(loaded.rows) == 2
    assert loaded.corrupt_lines == 1
    assert loaded.truncated_final_line == 0


def test_load_deduplicates_keeping_the_first(tmp_path):
    lines = [json.dumps(row("A", 0, 1.0)), json.dumps(row("A", 0, 0.0))]
    loaded = load_rollouts(write_lines(tmp_path / "r.jsonl", lines))
    assert loaded.duplicates == 1
    assert summarize_rows(loaded.rows, ks=(1,))["pass@1"]["aciertos"] == 1


def test_load_counts_rows_without_required_fields(tmp_path):
    bad = {"model": "m", "condition": "tools"}
    negative = {**row("B", 0), "sample": -1}
    lines = [json.dumps(row("A", 0)), json.dumps(bad), json.dumps(negative), "[1, 2]"]
    loaded = load_rollouts(write_lines(tmp_path / "r.jsonl", lines))
    assert len(loaded.rows) == 1
    assert loaded.malformed_rows == 3


def test_load_several_files_and_empty_file(tmp_path):
    a = write_lines(tmp_path / "a.jsonl", [json.dumps(row("A", 0))])
    b = tmp_path / "b.jsonl"
    b.write_text("", encoding="utf-8")
    assert len(load_rollouts([a, b]).rows) == 1


# --- De extremo a extremo: run_pilot, analyze_results, cuaderno --------------

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "piloto_colab.ipynb"
sys.path.insert(0, str(ROOT / "scripts"))


def dry_run(out, *extra):
    import run_pilot

    return run_pilot.main(
        ["--stage", "exploracion", "--dry-run", "--limit", "9", "--n-samples", "2",
         "--models", "m/uno", "--out", str(out), *extra]
    )


def keys_in(path):
    return [json.loads(line)["key"] for line in path.read_text(encoding="utf-8").splitlines()]


def test_dry_run_end_to_end(tmp_path, monkeypatch):
    import analyze_results

    assert dry_run(tmp_path) == 0
    files = list(tmp_path.glob("rollouts_*.jsonl"))
    assert [f.name for f in files] == ["rollouts_m_uno.jsonl"]
    keys = keys_in(files[0])
    assert len(keys) == len(set(keys)) == 9 * 2 * 2

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["dry_run"] is True
    assert manifest["seeds"]["dataset"] == 11
    assert manifest["modelos"]["m/uno"]["estado"] == "completo"
    assert manifest["code_hash"]
    assert manifest["gen_configs"]["m/uno"]["max_new_tokens"] == 768

    rows = load_rollouts(files[0]).rows
    assert any(r["verdict"]["reward"] == 1.0 for r in rows)
    assert any(r["verdict"]["reward"] == 0.0 for r in rows)
    tools = [r for r in rows if r["condition"] == "tools"]
    assert all(r["verdict"]["valid_tool_call"] for r in tools)
    assert all(r["verdict"]["retrieved_required_data"] for r in tools)

    monkeypatch.setattr(sys, "argv", ["analyze_results.py", str(tmp_path)])
    analyze_results.main()
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "DRY-RUN" in report
    assert "no existe pass@5" in report
    assert "orientativa" in report
    assert "IC muy ancho" in report
    assert "siempre_alcanza" in report
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["k"] == 2
    assert summary["n_rollouts"] == 36
    assert summary["aviso_baselines"] is None
    assert (tmp_path / "muestra_errores.jsonl").stat().st_size > 0


def test_dry_run_resumes_without_duplicating(tmp_path):
    assert dry_run(tmp_path) == 0
    path = tmp_path / "rollouts_m_uno.jsonl"
    first = keys_in(path)

    lines = path.read_text(encoding="utf-8").splitlines(True)
    # Corte en plena escritura: quedan 20 lineas y un fragmento de la 21.
    path.write_text("".join(lines[:20]) + lines[20][:40], encoding="utf-8")
    assert dry_run(tmp_path) == 0
    resumed = keys_in(path)
    assert len(resumed) == len(set(resumed)) == 36
    assert set(resumed) == set(first)
    assert resumed[:20] == first[:20]

    before = path.read_bytes()
    assert dry_run(tmp_path) == 0
    assert path.read_bytes() == before


def test_thinking_variants_get_separate_files_and_keys(tmp_path):
    assert dry_run(tmp_path, "--models", "Qwen/Qwen3-1.7B", "--thinking", "both") == 0
    plain = tmp_path / "rollouts_Qwen_Qwen3-1.7B.jsonl"
    think = tmp_path / "rollouts_Qwen_Qwen3-1.7B+think.jsonl"
    assert len(keys_in(plain)) == len(keys_in(think)) == 36
    assert all(k.startswith("Qwen/Qwen3-1.7B+think|") for k in keys_in(think))
    config = json.loads(think.read_text(encoding="utf-8").splitlines()[0])["gen_config"]
    assert config["enable_thinking"] is True
    assert config["max_new_tokens"] == 4096


def test_thinking_skipped_for_models_without_it():
    import run_pilot

    variants, notes = run_pilot.expand_variants(["google/gemma-3-1b-it"], "both")
    assert [v["label"] for v in variants] == ["google/gemma-3-1b-it"]
    assert notes


def test_folder_refuses_other_dataset(tmp_path):
    assert dry_run(tmp_path) == 0
    with pytest.raises(SystemExit, match="otra corrida"):
        dry_run(tmp_path, "--n-per-cell", "6")


def test_changed_gen_config_is_not_mixed(tmp_path):
    assert dry_run(tmp_path) == 0
    before = (tmp_path / "rollouts_m_uno.jsonl").read_bytes()
    assert dry_run(tmp_path, "--max-new-tokens", "99") == 1
    assert (tmp_path / "rollouts_m_uno.jsonl").read_bytes() == before


def test_model_that_fails_to_load_is_skipped(tmp_path, monkeypatch):
    import run_pilot

    real = run_pilot.make_backend

    def fake(variant, dry, instances):
        if variant["model"] == "m/restringido":
            raise OSError("gated repo")
        return real(variant, dry, instances)

    monkeypatch.setattr(run_pilot, "make_backend", fake)
    assert dry_run(tmp_path, "--models", "m/restringido", "m/uno") == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["modelos"]["m/restringido"]["estado"] == "no_cargo"
    assert "gated repo" in manifest["modelos"]["m/restringido"]["error"]
    assert manifest["modelos"]["m/uno"]["estado"] == "completo"


def test_stages_use_distinct_data():
    import run_pilot

    from inventory_harness.generator import fingerprint

    assert run_pilot.STAGES["exploracion"]["base_seed"] == 11
    assert run_pilot.STAGES["piloto"]["base_seed"] == 2026
    assert run_pilot.STAGES["piloto"]["split"] == "eval"
    assert "test" not in {stage["split"] for stage in run_pilot.STAGES.values()}
    explore = run_pilot.build_dataset("train", 5, 11)
    pilot = run_pilot.build_dataset("eval", 40, 2026)
    assert (len(explore), len(pilot)) == (45, 360)
    assert not {fingerprint(i) for i in explore} & {fingerprint(i) for i in pilot}


def test_interleaving_covers_every_cell_first():
    import run_pilot

    first = run_pilot.build_dataset("train", 5, 11)[:9]
    assert len({(i.family, i.difficulty) for i in first}) == 9


def test_analyze_tolerates_missing_manifest_and_condition(tmp_path):
    import analyze_results

    lines = [json.dumps(row("A", s, float(s))) for s in range(3)]
    (tmp_path / "rollouts_m.jsonl").write_text("\n".join(lines) + "\n{cor", encoding="utf-8")
    result = analyze_results.analyze(tmp_path)
    text = analyze_results.render_report(result, 0)
    assert result["k"] == 3
    assert result["problemas_de_carga"]["linea_final_truncada"] == 1
    assert "manifest.json" in text
    assert result["clasificacion_entre_condiciones"][0]["categoria"] == "falta_condicion"


def test_analyze_empty_folder(tmp_path):
    import analyze_results

    assert "No hay rollouts" in analyze_results.render_report(analyze_results.analyze(tmp_path), 0)


@pytest.mark.parametrize(
    "p1,pk,category,certainty",
    [
        ((40, 40), (40, 40), "cerca_de_100", "firme"),
        ((37, 40), (39, 40), "cerca_de_100", "tentativa"),
        ((5, 5), (5, 5), "cerca_de_100", "ic_muy_ancho"),
        ((0, 40), (0, 40), "cerca_de_0", "firme"),
        ((0, 5), (0, 5), "cerca_de_0", "ic_muy_ancho"),
        # Ganancia 14/40: IC de la ganancia [0.22, 0.50], entero sobre 0.15.
        ((16, 40), (30, 40), "zona_aprendible", "firme"),
        # Ganancia 10/40: IC [0.14, 0.40]; el limite inferior no llega a 0.15.
        ((16, 40), (26, 40), "zona_aprendible", "tentativa"),
        # Ganancia 2/40: IC [0.01, 0.17]; no descarta una ganancia apreciable.
        ((20, 40), (22, 40), "intermedio_sin_ganancia", "tentativa"),
        # Sin ganancia: IC [0, 0.09], entero bajo 0.15.
        ((20, 40), (20, 40), "intermedio_sin_ganancia", "firme"),
        # pass@1 casi 0 con ganancia 8/40: no es zona aprendible. IC de la ganancia [0.11, 0.35].
        ((0, 40), (8, 40), "casi_0_con_senal", "tentativa"),
        # pass@1 IC [0, 0.04] y ganancia IC [0.22, 0.40]: ambos dentro de la categoria.
        ((0, 100), (30, 100), "casi_0_con_senal", "firme"),
    ],
)
def test_classification_respects_the_interval(p1, pk, category, certainty):
    import analyze_results

    result = analyze_results.classify_condition(proportion(*p1), proportion(*pk), 5)
    assert (result["categoria"], result["certeza"]) == (category, certainty)
    assert result["motivo"] is None


def test_classification_ignores_pass_at_k_with_another_denominator():
    import analyze_results

    # Con el mismo denominador seria casi_0_con_senal; aqui faltan 2 instancias en pass@5.
    result = analyze_results.classify_condition(proportion(0, 40), proportion(8, 38), 5)
    assert (result["categoria"], result["certeza"]) == ("cerca_de_0", "firme")
    assert "denominadores distintos" in result["motivo"]
    assert result["ancho_ic_max"] == pytest.approx(analyze_results.width(proportion(0, 40)))


def test_classification_label_shows_when_only_pass_at_1_was_used():
    import analyze_results

    base = {"model": "m", "condition": "tools", "family": "availability", "difficulty": "easy",
            "frente_a_trivial": "n/d"}
    cells = [
        {**base, **analyze_results.classify_condition(proportion(0, 40), proportion(8, 38), 5)},
        {**base, "difficulty": "medium",
         **analyze_results.classify_condition(proportion(0, 40), proportion(0, 40), 5)},
    ]
    lines = analyze_results.render_classification(
        {"clasificacion": cells, "clasificacion_entre_condiciones": []}
    )
    easy = next(line for line in lines if "| easy |" in line)
    medium = next(line for line in lines if "| medium |" in line)
    assert "Éxito cercano a 0 % (solo pass@1)" in easy
    assert "incluso con k intentos" not in easy
    assert "Éxito cercano a 0 % incluso con k intentos |" in medium


def test_interface_problem_and_bad_in_both():
    import analyze_results

    pair = analyze_results.classify_pair(proportion(8, 40), proportion(36, 40))
    assert (pair["categoria"], pair["certeza"]) == ("problema_de_interfaz", "firme")
    # Visible 28/40 tiene IC [0.55, 0.82]: el limite inferior queda bajo 0.70.
    pair = analyze_results.classify_pair(proportion(8, 40), proportion(28, 40))
    assert (pair["categoria"], pair["certeza"]) == ("problema_de_interfaz", "tentativa")
    pair = analyze_results.classify_pair(proportion(2, 40), proportion(3, 40))
    assert (pair["categoria"], pair["certeza"]) == ("mal_en_ambas", "firme")
    # 9/40 tiene IC [0.12, 0.38]: el limite superior pasa de 0.30.
    pair = analyze_results.classify_pair(proportion(5, 40), proportion(9, 40))
    assert (pair["categoria"], pair["certeza"]) == ("mal_en_ambas", "tentativa")
    assert analyze_results.classify_pair(None, proportion(1, 2))["categoria"] == "falta_condicion"


def test_baseline_comparison_uses_each_model_instances(tmp_path):
    import analyze_results
    import run_pilot

    from inventory_harness.baselines import best_by_cell, evaluate_baselines

    assert dry_run(tmp_path, "--limit", "18", "--models", "m/uno", "m/dos") == 0
    partial = tmp_path / "rollouts_m_dos.jsonl"
    rows = [json.loads(line) for line in partial.read_text(encoding="utf-8").splitlines()]
    first = {}
    for r in rows:
        first.setdefault((r["family"], r["difficulty"]), r["instance_id"])
    kept = [r for r in rows if r["instance_id"] in set(first.values())]
    partial.write_text("".join(json.dumps(r) + "\n" for r in kept), encoding="utf-8")

    result = analyze_results.analyze(tmp_path)
    instances = run_pilot.build_dataset("train", 5, 11)[:18]
    own = [i for i in instances if i.id in set(first.values())]
    expected = {
        "m/uno": best_by_cell(evaluate_baselines(instances)),
        "m/dos": best_by_cell(evaluate_baselines(own)),
    }
    assert expected["m/uno"] != expected["m/dos"]
    for cell in result["clasificacion"]:
        key = (cell["family"], cell["difficulty"])
        assert cell["regla_trivial"] == expected[cell["model"]].get(key)
        if cell["model"] == "m/dos" and cell["regla_trivial"]:
            assert cell["regla_trivial"]["n"] <= 1


def test_availability_chance_level_does_not_beat_trivial_rule():
    import analyze_results

    baseline = {"tasa": 0.5}
    assert analyze_results.compare_with_baseline(proportion(22, 40), baseline) == "no_distinguible"
    assert analyze_results.compare_with_baseline(proportion(36, 40), baseline) == "supera"


QWEN_NOTEBOOK = ROOT / "notebooks" / "qwen_objetivo_colab.ipynb"
KAGGLE_NOTEBOOK = ROOT / "notebooks" / "qwen_objetivo_kaggle.ipynb"


@pytest.mark.skipif(not NOTEBOOK.exists(), reason="el zip de Colab no trae el cuaderno")
@pytest.mark.parametrize(
    "path, needed",
    [
        (NOTEBOOK, ("EJECUTAR_PILOTO = False", "userdata.get", "drive.mount", "resultados_inventory_harness.zip")),
        (QWEN_NOTEBOOK, ("drive.mount", "--stage\", \"piloto", "--stage\", \"trazas", "build_training_data.py",
                         "resultados_qwen17b.zip")),
        (KAGGLE_NOTEBOOK, ("/kaggle/input", "--stage\", \"piloto", "--stage\", \"trazas", "CUDA_VISIBLE_DEVICES",
                           "build_training_data.py", "resultados_qwen17b.zip")),
    ],
)
def test_notebook_is_valid_and_code_compiles(path, needed):
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    code_cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
    assert code_cells
    text = "\n".join("".join(c["source"]) for c in notebook["cells"])
    for cell in code_cells:
        assert not cell["outputs"]
        lines = [
            "pass" if line.lstrip().startswith(("!", "%")) else line
            for line in "".join(cell["source"]).splitlines()
        ]
        compile("\n".join(lines), "celda", "exec")
    for piece in needed:
        assert piece.replace("\\", "") in text
    assert "print(_token" not in text


def test_tope_de_tokens_usa_stop_reasons_si_existen():
    from inventory_harness.metrics import _hit_token_limit

    config = {"max_new_tokens": 512}
    assert _hit_token_limit({"gen_config": config, "usage": {"new_tokens": 100, "stop_reasons": ["eos", "length"]}})
    assert not _hit_token_limit({"gen_config": config, "usage": {"new_tokens": 900, "stop_reasons": ["eos", "answer"]}})
    assert _hit_token_limit({"gen_config": config, "usage": {"new_tokens": 512}})
