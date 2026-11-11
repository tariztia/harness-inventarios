"""Analiza una carpeta de resultados: escribe report.md, summary.json y muestra_errores.jsonl.

Uso: uv run python scripts/analyze_results.py results/exploracion_prompt_corregido

Tolera modelos o condiciones ausentes, corridas parciales y lineas truncadas. Toda cifra
sale de los rollouts o de reglas evaluadas sobre las mismas instancias. Los umbrales de
clasificacion son nuestros: la propuesta (§6) da categorias, no numeros.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from inventory_harness.baselines import best_by_cell, evaluate_baselines  # noqa: E402
from inventory_harness.metrics import (  # noqa: E402
    aggregate,
    error_type_of,
    is_success,
    load_rollouts,
    max_samples,
    wilson_interval,
)
from inventory_harness.schema import CONDITIONS, DIFFICULTIES, FAMILIES  # noqa: E402

# Umbrales orientativos, elegidos por nosotros. NO son del curso ni de la propuesta.
NEAR_ONE = 0.90
NEAR_ZERO = 0.10
APPRECIABLE_GAIN = 0.15
VISIBLE_GOOD = 0.70
CONDITION_GAP = 0.30
BOTH_BAD = 0.30
WIDE_INTERVAL = 0.30

CATEGORY_TEXT = {
    "cerca_de_100": ("Éxito cercano a 100 %", "Poco margen: aumentar composición o variedad"),
    "cerca_de_0": ("Éxito cercano a 0 % incluso con k intentos", "Señal escasa: simplificar, SFT o reconsiderar"),
    "casi_0_con_senal": ("pass@1 cercano a 0 %, pero pass@k mayor", "Señal escasa pero presente: candidata a SFT antes de RL"),
    "zona_aprendible": ("Acierto intermedio y pass@k mayor que pass@1", "Posible zona aprendible: profundizar"),
    "intermedio_sin_ganancia": ("Acierto intermedio sin ganancia apreciable", "Fuera de la tabla de §6: revisar a mano"),
    "sin_datos": ("Sin datos", "No clasificar"),
}
PAIR_TEXT = {
    "problema_de_interfaz": ("Bien con datos visibles, mal con herramientas", "Priorizar harness y protocolo"),
    "mal_en_ambas": ("Mal en ambas condiciones", "Aislar operaciones y ajustar niveles"),
    "sin_patron": ("Ningún patrón de §6 entre condiciones", "—"),
    "falta_condicion": ("Falta una condición", "No comparable"),
}
CERTAINTY_TEXT = {
    "firme": "firme",
    "tentativa": "tentativa",
    "ic_muy_ancho": "IC muy ancho, no concluir",
    "sin_datos": "sin datos",
}


def order_key(value: str, known: tuple[str, ...]) -> tuple[int, str]:
    return (known.index(value), value) if value in known else (len(known), value)


def group_key(group: dict[str, Any]) -> tuple[Any, ...]:
    return (
        group["model"],
        order_key(group["condition"], CONDITIONS),
        order_key(group["family"], FAMILIES),
        order_key(group["difficulty"], DIFFICULTIES),
    )


def width(result: dict[str, Any]) -> float | None:
    low, high = result["ic95"]
    return None if low is None else high - low


def gain_interval(p1: dict[str, Any], pk: dict[str, Any]) -> tuple[float | None, float | None]:
    """IC de Wilson de las instancias ganadas entre pass@1 y pass@k, si son comparables."""
    if p1["n"] != pk["n"] or not p1["n"]:
        return None, None
    return wilson_interval(pk["aciertos"] - p1["aciertos"], p1["n"])


def classify_condition(p1: dict[str, Any], pk: dict[str, Any], k: int) -> dict[str, Any]:
    """Fila de §6 para una celda en una condicion, con cuanto la respaldan los datos.

    `firme` exige que el IC completo caiga en la categoria y, si la categoria depende de
    la ganancia pass@k - pass@1, tambien el IC de la ganancia. pass@k solo se usa si tiene
    el mismo denominador que pass@1. Si el IC es mas ancho que WIDE_INTERVAL, la categoria
    solo se muestra como lectura provisional.
    """
    if not p1["n"]:
        return {"categoria": "sin_datos", "certeza": "sin_datos", "motivo": "pass@1 sin denominador"}
    low, high = p1["ic95"]
    rate = p1["tasa"]
    has_k = k > 1 and pk["n"] > 0 and pk["n"] == p1["n"]
    if has_k:
        motive = None
    elif k > 1 and pk["n"] > 0:
        motive = (
            f"pass@1 y pass@{k} tienen denominadores distintos (instancias incompletas): "
            "se clasifica solo con pass@1"
        )
    else:
        motive = f"sin pass@{k} utilizable: se clasifica solo con pass@1"
    pk_rate = pk["tasa"] if has_k else rate
    pk_high = pk["ic95"][1] if has_k else high
    gain_low, gain_high = gain_interval(p1, pk) if has_k else (None, None)
    if rate >= NEAR_ONE:
        category, firm = "cerca_de_100", low >= NEAR_ONE
    elif has_k and pk_rate - rate >= APPRECIABLE_GAIN:
        gain_firm = gain_low >= APPRECIABLE_GAIN
        if rate <= NEAR_ZERO:
            category, firm = "casi_0_con_senal", gain_firm and high <= NEAR_ZERO
        else:
            category = "zona_aprendible"
            firm = gain_firm and low > NEAR_ZERO and high < NEAR_ONE
    elif pk_rate <= NEAR_ZERO:
        category, firm = "cerca_de_0", pk_high <= NEAR_ZERO
    else:
        category = "intermedio_sin_ganancia"
        firm = low > NEAR_ZERO and high < NEAR_ONE and (not has_k or gain_high < APPRECIABLE_GAIN)
    widths = [w for w in (width(p1), width(pk) if has_k else None) if w is not None]
    widest = max(widths)
    if widest > WIDE_INTERVAL:
        certainty = "ic_muy_ancho"
    else:
        certainty = "firme" if firm else "tentativa"
    return {"categoria": category, "certeza": certainty, "ancho_ic_max": widest, "motivo": motive}


def classify_pair(
    tools: dict[str, Any] | None, visible: dict[str, Any] | None
) -> dict[str, Any]:
    if tools is None or visible is None or not tools["n"] or not visible["n"]:
        return {"categoria": "falta_condicion", "certeza": "sin_datos"}
    t_rate, v_rate = tools["tasa"], visible["tasa"]
    t_low, t_high = tools["ic95"]
    v_low, v_high = visible["ic95"]
    wide = max(width(tools), width(visible)) > WIDE_INTERVAL
    if v_rate >= VISIBLE_GOOD and v_rate - t_rate >= CONDITION_GAP:
        category = "problema_de_interfaz"
        firm = v_low >= VISIBLE_GOOD and v_low - t_high >= CONDITION_GAP
    elif v_rate <= BOTH_BAD and t_rate <= BOTH_BAD:
        category, firm = "mal_en_ambas", max(v_high, t_high) <= BOTH_BAD
    else:
        category, firm = "sin_patron", False
    if wide:
        certainty = "ic_muy_ancho"
    elif category == "sin_patron":
        certainty = "tentativa"
    else:
        certainty = "firme" if firm else "tentativa"
    return {"categoria": category, "certeza": certainty}


def compare_with_baseline(
    p1: dict[str, Any], baseline: dict[str, Any] | None
) -> str:
    """Compara con la tasa de la regla, que es exacta sobre estas mismas instancias."""
    if baseline is None or not p1["n"]:
        return "n/d"
    if p1["ic95"][0] > baseline["tasa"]:
        return "supera"
    if p1["ic95"][1] < baseline["tasa"]:
        return "por_debajo"
    return "no_distinguible"


# --- Formato --------------------------------------------------------------


def pct(value: float | None) -> str:
    return "n/d" if value is None else f"{100 * value:.1f} %"


def prop_cell(result: dict[str, Any]) -> str:
    if not result["n"]:
        return "n/d (n=0)"
    low, high = result["ic95"]
    return (
        f"{pct(result['tasa'])} ({result['aciertos']}/{result['n']}; "
        f"IC95 {100 * low:.0f}–{100 * high:.0f})"
    )


def flag_cell(flag: dict[str, Any]) -> str:
    return "n/a" if not flag["n"] else f"{pct(flag['si'] / flag['n'])} ({flag['si']}/{flag['n']})"


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return lines + [""]


# --- Carga ----------------------------------------------------------------


def read_manifest(folder: Path) -> dict[str, Any] | None:
    path = folder / "manifest.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def regenerate_instances(manifest: dict[str, Any] | None) -> tuple[list[Any], str | None]:
    """Instancias de la corrida, regeneradas desde semillas. Devuelve (instancias, aviso)."""
    if not manifest or not isinstance(manifest.get("dataset"), dict):
        return [], "Sin manifest.json con la configuración del dataset: no se evalúan líneas base."
    try:
        from run_pilot import build_dataset, dataset_fingerprint

        dataset = manifest["dataset"]
        instances = build_dataset(dataset["split"], dataset["n_per_cell"], dataset["base_seed"])
        if dataset_fingerprint(instances) != dataset.get("fingerprint"):
            return [], (
                "El dataset regenerado no coincide con la huella del manifest (¿cambió el "
                "generador?): no se evalúan líneas base."
            )
        return instances, None
    except Exception as exc:  # Un analisis parcial vale mas que ninguno.
        return [], f"No se pudo regenerar el dataset ({type(exc).__name__}): no se evalúan líneas base."


def sample_failures(
    rows: list[dict[str, Any]], per_stratum: int, seed: int
) -> list[dict[str, Any]]:
    """Fallos por modelo × condicion × familia × dificultad × error_type. Determinista."""
    strata: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not is_success(row):
            key = tuple(str(row.get(f)) for f in ("model", "condition", "family", "difficulty"))
            strata[(*key, error_type_of(row))].append(row)
    rng = random.Random(seed)
    sample: list[dict[str, Any]] = []
    for key in sorted(strata):
        members = sorted(
            strata[key], key=lambda r: (str(r["instance_id"]), r["sample"])
        )
        rng.shuffle(members)
        for row in members[:per_stratum]:
            sample.append({"estrato": "|".join(key), **row})
    return sample


# --- Analisis e informe ---------------------------------------------------


def group_baselines(
    rows: list[dict[str, Any]], instances: list[Any]
) -> dict[tuple[str, str], tuple[dict[Any, Any], dict[Any, Any]]]:
    """Mejores reglas (trivial, informada) por (modelo, condicion), sobre sus instancias.

    Usa las instancias con muestra 0, que son el denominador de pass@1. Asi un modelo
    parcial se compara con la tasa de la regla en sus propias instancias.
    """
    by_id = {instance.id: instance for instance in instances}
    ids: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in rows:
        if row["sample"] == 0:
            ids[(str(row["model"]), str(row["condition"]))].add(str(row["instance_id"]))
    cache: dict[frozenset[str], tuple[dict[Any, Any], dict[Any, Any]]] = {}
    result = {}
    for key, members in ids.items():
        known = frozenset(members & by_id.keys())
        if known not in cache:
            evaluated = evaluate_baselines([by_id[i] for i in sorted(known)]) if known else []
            cache[known] = (
                best_by_cell(evaluated),
                best_by_cell(evaluated, include_reasonable_errors=True),
            )
        result[key] = cache[known]
    return result


def analyze(folder: Path, per_stratum: int = 3, seed: int = 2026) -> dict[str, Any]:
    paths = sorted(folder.glob("rollouts_*.jsonl"))
    loaded = load_rollouts(paths)
    manifest = read_manifest(folder)
    rows = loaded.rows
    planned = (manifest or {}).get("n_samples")
    k = planned if isinstance(planned, int) and planned > 0 else max(max_samples(rows), 1)
    ks = (1, k) if k > 1 else (1,)

    groups = sorted(aggregate(rows, ks=ks), key=group_key)
    overall = aggregate(rows, ks=ks, group_by=("model", "condition"))

    instances, warning = regenerate_instances(manifest)
    used = {str(row["instance_id"]) for row in rows}
    instances = [i for i in instances if i.id in used]
    # La tabla descriptiva de reglas usa la union; la comparacion, las instancias de cada grupo.
    baseline_rows = evaluate_baselines(instances) if instances else []
    rules_by_group = group_baselines(rows, instances)

    pk_name = f"pass@{k}"
    cells = []
    for group in groups:
        p1, pk = group["pass@1"], group.get(pk_name, group["pass@1"])
        cell = (group["family"], group["difficulty"])
        trivial, informed = rules_by_group.get((group["model"], group["condition"]), ({}, {}))
        cells.append(
            {
                **{name: group[name] for name in ("model", "condition", "family", "difficulty")},
                **classify_condition(p1, pk, k),
                "regla_trivial": trivial.get(cell),
                "frente_a_trivial": compare_with_baseline(p1, trivial.get(cell)),
                "regla_informada": informed.get(cell),
                "frente_a_informada": compare_with_baseline(p1, informed.get(cell)),
            }
        )

    by_cell = {(g["model"], g["family"], g["difficulty"], g["condition"]): g for g in groups}
    pairs = []
    for model, family, difficulty in sorted({key[:3] for key in by_cell}):
        tools = by_cell.get((model, family, difficulty, "tools"))
        visible = by_cell.get((model, family, difficulty, "visible"))
        pairs.append(
            {
                "model": model,
                "family": family,
                "difficulty": difficulty,
                **classify_pair(
                    tools["pass@1"] if tools else None, visible["pass@1"] if visible else None
                ),
            }
        )

    return {
        "k": k,
        "carpeta": str(folder),
        "archivos": [path.name for path in paths],
        "problemas_de_carga": loaded.problems(),
        "manifest": manifest,
        "aviso_baselines": warning,
        "grupos": groups,
        "por_modelo_condicion": overall,
        "clasificacion": cells,
        "clasificacion_entre_condiciones": pairs,
        "baselines": baseline_rows,
        "umbrales": {
            "cerca_de_100": NEAR_ONE,
            "cerca_de_0": NEAR_ZERO,
            "ganancia_apreciable": APPRECIABLE_GAIN,
            "visible_bueno": VISIBLE_GOOD,
            "brecha_condiciones": CONDITION_GAP,
            "mal_en_ambas": BOTH_BAD,
            "ic_muy_ancho": WIDE_INTERVAL,
        },
        "_rows": rows,
        "_per_stratum": per_stratum,
        "_seed": seed,
    }


def render_header(result: dict[str, Any]) -> list[str]:
    manifest = result["manifest"] or {}
    lines = ["# Informe del piloto", ""]
    if manifest.get("dry_run"):
        lines += [
            "> **DRY-RUN.** Estos resultados vienen de un backend programado, no de un modelo. "
            "Sirven solo para probar el pipeline; no deben citarse.",
            "",
        ]
    if not manifest:
        lines += ["> No se encontró `manifest.json`: faltan etapa, semillas y entorno.", ""]
    else:
        environment = manifest.get("entorno", {})
        dataset = manifest.get("dataset", {})
        lines += [
            f"- Etapa: `{manifest.get('stage')}`; split `{dataset.get('split')}`; "
            f"semilla base {dataset.get('base_seed')}; {dataset.get('n_per_cell')} por celda; "
            f"{manifest.get('n_samples')} muestras.",
            f"- Entorno: GPU {environment.get('gpu')}; torch {environment.get('torch')}; "
            f"transformers {environment.get('transformers')}.",
            f"- Código: `{manifest.get('code_hash')}`; fecha {manifest.get('updated_at')}.",
        ]
    lines += [
        f"- Archivos leídos: {len(result['archivos'])}. Rollouts válidos: {len(result['_rows'])}.",
    ]
    problems = {key: value for key, value in result["problemas_de_carga"].items() if value}
    lines += [
        "- Problemas de carga: "
        + (", ".join(f"{key}={value}" for key, value in problems.items()) if problems else "ninguno."),
        "",
    ]
    internal = sum(g["error_types"].get("internal_error", 0) for g in result["por_modelo_condicion"])
    if internal:
        lines += [
            f"> **{internal} muestras terminaron en `internal_error`**: fallaron por el harness, no "
            "por el modelo, y cuentan como no acertadas. Vuelve a ejecutar la etapa para reintentarlas.",
            "",
        ]
    states = manifest.get("modelos") or {}
    if states:
        rows = [
            [
                f"`{label}`",
                state.get("estado"),
                f"{state.get('hechos', 'n/d')}/{state.get('esperados', 'n/d')}",
                state.get("segundos_por_rollout") or "n/d",
                state.get("error") or "—",
            ]
            for label, state in states.items()
        ]
        lines += ["## Estado por modelo", ""]
        lines += table(["Modelo", "Estado", "Rollouts", "s/rollout (reloj)", "Error"], rows)
    return lines


def render_passes(result: dict[str, Any]) -> list[str]:
    k = result["k"]
    lines = [
        "## Resultados por modelo, condición, familia y dificultad",
        "",
        f"pass@1 usa la muestra 0 de cada instancia. pass@{k} cuenta las instancias con al "
        f"menos un acierto entre las primeras {k} muestras. El IC95 es de Wilson sobre "
        "instancias. La tasa por muestra se da sin IC porque las muestras están correlacionadas.",
        "",
    ]
    if k < 5:
        lines += [
            f"**Esta corrida tiene {k} muestras por instancia, así que aquí no existe pass@5.** "
            f"pass@{k} no es comparable con pass@5.",
            "",
        ]
    models = sorted({group["model"] for group in result["grupos"]})
    if not models:
        return lines + ["No hay rollouts que analizar.", ""]
    for model in models:
        rows = []
        for group in result["grupos"]:
            if group["model"] != model:
                continue
            pk = group.get(f"pass@{k}")
            rows.append(
                [
                    group["condition"],
                    group["family"],
                    group["difficulty"],
                    group["n_instancias"],
                    prop_cell(group["pass@1"]),
                    prop_cell(pk) if pk and k > 1 else "—",
                    pct(group["tasa_media_muestra"]["tasa"]),
                    group["incompletas"].get(f"k={k}", {}).get("n", 0),
                ]
            )
        lines += [f"### `{model}`", ""]
        lines += table(
            ["Condición", "Familia", "Nivel", "n inst.", "pass@1", f"pass@{k}", "Tasa por muestra", f"Incompletas k={k}"],
            rows,
        )
    return lines


def render_conditions(result: dict[str, Any]) -> list[str]:
    k = result["k"]
    lines = ["## Comparación con y sin herramientas", ""]
    index = {(g["model"], g["family"], g["difficulty"], g["condition"]): g for g in result["grupos"]}
    rows = []
    for pair in result["clasificacion_entre_condiciones"]:
        key = (pair["model"], pair["family"], pair["difficulty"])
        tools, visible = index.get((*key, "tools")), index.get((*key, "visible"))
        difference = "n/d"
        if tools and visible and tools["pass@1"]["n"] and visible["pass@1"]["n"]:
            delta = tools["pass@1"]["tasa"] - visible["pass@1"]["tasa"]
            difference = f"{100 * delta:+.1f} pts"
        pk_name = f"pass@{k}"
        rows.append(
            [
                f"`{pair['model']}`",
                pair["family"],
                pair["difficulty"],
                prop_cell(visible["pass@1"]) if visible else "ausente",
                prop_cell(tools["pass@1"]) if tools else "ausente",
                difference,
                prop_cell(visible[pk_name]) if visible and k > 1 else "—",
                prop_cell(tools[pk_name]) if tools and k > 1 else "—",
            ]
        )
    if not rows:
        return lines + ["Sin datos.", ""]
    lines += table(
        ["Modelo", "Familia", "Nivel", "Visible pass@1", "Herramientas pass@1", "Dif. (h − v)", f"Visible pass@{k}", f"Herramientas pass@{k}"],
        rows,
    )
    lines += ["### Diagnóstico de herramientas (por muestra)", ""]
    rows = []
    for group in result["grupos"]:
        if group["condition"] != "tools":
            continue
        rows.append(
            [
                f"`{group['model']}`",
                group["family"],
                group["difficulty"],
                flag_cell(group["valid_tool_call"]),
                flag_cell(group["correct_tool_arguments"]),
                flag_cell(group["retrieved_required_data"]),
                flag_cell(group["tool_limit_exceeded"]),
                flag_cell(group["correcta_sin_recompensa"]),
            ]
        )
    if rows:
        lines += table(
            ["Modelo", "Familia", "Nivel", "Llamadas válidas", "Argumentos correctos", "Datos requeridos", "Límite excedido", "Correcta sin recompensa"],
            rows,
        )
        lines += [
            "`Correcta sin recompensa` cuenta respuestas finales correctas que no recibieron "
            "recompensa, por ejemplo sin haber obtenido los datos: una señal de adivinación.",
            "",
        ]
    else:
        lines += ["No hay rollouts en condición `tools`.", ""]
    return lines


def render_baselines(result: dict[str, Any]) -> list[str]:
    lines = ["## Comparación con líneas base", ""]
    if result["aviso_baselines"]:
        lines += [result["aviso_baselines"], ""]
    rows_in = result["baselines"]
    if not rows_in:
        return lines + ["Sin líneas base evaluadas.", ""]
    lines += [
        "Cada regla se evalúa con `verify_final_text` sobre las mismas instancias que los "
        "rollouts. Las triviales y de azar no leen el inventario. Las marcadas como "
        "`error_razonable` o azar contado sí lo leen: son errores plausibles, no azar. El "
        "control usa `expected` y solo valida el formato; no se compara con los modelos. "
        "Las reglas miden solo el texto final; en `tools` el modelo necesita además evidencia.",
        "",
    ]
    names = sorted({row["baseline"] for row in rows_in})
    classes = {row["baseline"]: row["clase"] for row in rows_in}
    index = {(r["baseline"], r["family"], r["difficulty"]): r for r in rows_in}
    cells = sorted(
        {(r["family"], r["difficulty"]) for r in rows_in},
        key=lambda c: (order_key(c[0], FAMILIES), order_key(c[1], DIFFICULTIES)),
    )
    rows = []
    for name in names:
        row = [f"`{name}`", classes[name]]
        for family, difficulty in cells:
            entry = index.get((name, family, difficulty))
            row.append(f"{entry['aciertos']}/{entry['n']}" if entry else "—")
        rows.append(row)
    lines += table(["Regla", "Clase", *[f"{f[:5]}/{d}" for f, d in cells]], rows)
    control = [r for r in rows_in if r["usa_expected"]]
    if any(r["aciertos"] != r["n"] for r in control):
        lines += ["**El control no llegó a 100 %: revisar el verificador antes de leer este informe.**", ""]

    rows = []
    for cell in result["clasificacion"]:
        trivial, informed = cell["regla_trivial"], cell["regla_informada"]
        rows.append(
            [
                f"`{cell['model']}`",
                cell["condition"],
                cell["family"],
                cell["difficulty"],
                f"{trivial['baseline']} {pct(trivial['tasa'])}" if trivial else "n/d",
                cell["frente_a_trivial"],
                f"{informed['baseline']} {pct(informed['tasa'])}" if informed else "n/d",
                cell["frente_a_informada"],
            ]
        )
    lines += [
        "Cada fila se compara con la tasa de la regla sobre las mismas instancias de ese modelo "
        "y condición. `supera` significa que el límite inferior del IC de pass@1 queda sobre la "
        "tasa de la regla; `no_distinguible`, que la regla cae dentro del IC. Son muchas "
        "comparaciones con IC95 sin corrección por multiplicidad: algún `supera` puede ser casual.",
        "",
    ]
    lines += table(
        ["Modelo", "Condición", "Familia", "Nivel", "Mejor sin inventario", "pass@1 frente a ella", "Mejor con inventario", "pass@1 frente a ella"],
        rows,
    )
    return lines


def render_errors(result: dict[str, Any]) -> list[str]:
    lines = ["## Distribución de errores", ""]
    rows = []
    for group in result["por_modelo_condicion"]:
        total = group["n_muestras"]
        for error, count in group["error_types"].items():
            rows.append([f"`{group['model']}`", group["condition"], f"`{error}`", count, pct(count / total)])
    if not rows:
        return lines + ["Sin datos.", ""]
    lines += table(["Modelo", "Condición", "error_type", "Muestras", "Porcentaje"], rows)
    rows = [
        [
            f"`{g['model']}`",
            g["condition"],
            g["n_muestras"],
            flag_cell(g["parser_error"]),
            flag_cell(g["contradictory_answer"]),
        ]
        for g in result["por_modelo_condicion"]
    ]
    lines += table(["Modelo", "Condición", "Muestras", "parser_error", "Contradicción"], rows)
    return lines


def render_cost(result: dict[str, Any]) -> list[str]:
    rows = []
    for group in result["por_modelo_condicion"]:
        usage = group["uso"]
        per_token = usage["tokens_por_muestra"]
        per_second = usage["segundos_por_muestra"]
        rows.append(
            [
                f"`{group['model']}`",
                group["condition"],
                group["n_muestras"],
                f"{per_token:.0f}" if per_token is not None else "n/d",
                f"{per_second:.2f}" if per_second is not None else "n/d",
                f"{usage['segundos'] / 3600:.2f}",
                flag_cell(group["tope_de_tokens"]),
            ]
        )
    lines = ["## Costo", ""]
    if not rows:
        return lines + ["Sin datos.", ""]
    return lines + table(
        ["Modelo", "Condición", "Muestras", "Tokens nuevos por muestra", "s por muestra", "Horas (suma de `usage.seconds`)", "Llegó al tope de tokens"],
        rows,
    ) + [
        "`Llegó al tope de tokens` cuenta las muestras con alguna generación cortada por "
        "`max_new_tokens`, según `usage.stop_reasons`. En rollouts sin ese campo es una cota "
        "inferior. Un valor alto, sobre todo con thinking, indica respuestas cortadas.",
        "",
    ]


def render_classification(result: dict[str, Any]) -> list[str]:
    lines = [
        "## Clasificación según §6 de la propuesta (orientativa)",
        "",
        "**Es una lectura orientativa, no una decisión ni un umbral del curso.** La propuesta "
        "define las categorías; los números son nuestros y están en `summary.json`. La "
        "certeza es `firme` solo si el IC completo cae en la categoría (y, si la categoría "
        "depende de la ganancia de pass@k sobre pass@1, también el IC de esa ganancia). Con un "
        f"IC más ancho que {100 * WIDE_INTERVAL:.0f} puntos se marca `IC muy ancho`: esa "
        "categoría es una lectura provisional y no debe usarse para decidir. `(solo pass@1)` "
        "indica que no hubo pass@k utilizable (sin muestras o con denominador distinto por "
        "instancias incompletas); el motivo está en `summary.json`.",
        "",
    ]
    rows = []
    wide = 0
    for cell in result["clasificacion"]:
        wide += cell["certeza"] == "ic_muy_ancho"
        label, action = CATEGORY_TEXT[cell["categoria"]]
        if cell.get("motivo") and cell["categoria"] != "sin_datos":
            if cell["categoria"] == "cerca_de_0":
                label = "Éxito cercano a 0 %"
            label += " (solo pass@1)"
        rows.append(
            [
                f"`{cell['model']}`",
                cell["condition"],
                cell["family"],
                cell["difficulty"],
                label,
                CERTAINTY_TEXT[cell["certeza"]],
                cell["frente_a_trivial"],
                action,
            ]
        )
    if not rows:
        return lines + ["Sin datos.", ""]
    if wide:
        lines += [
            f"**{wide} de {len(rows)} celdas tienen un IC muy ancho.** Hacen falta más "
            "instancias antes de sacar conclusiones de ellas.",
            "",
        ]
    lines += table(
        ["Modelo", "Condición", "Familia", "Nivel", "Lectura", "Certeza", "Frente a regla trivial", "Acción sugerida"],
        rows,
    )
    rows = []
    for pair in result["clasificacion_entre_condiciones"]:
        label, action = PAIR_TEXT[pair["categoria"]]
        rows.append(
            [f"`{pair['model']}`", pair["family"], pair["difficulty"], label, CERTAINTY_TEXT[pair["certeza"]], action]
        )
    lines += ["### Entre condiciones", ""]
    lines += table(["Modelo", "Familia", "Nivel", "Lectura", "Certeza", "Acción sugerida"], rows)
    return lines


def render_incomplete(result: dict[str, Any]) -> list[str]:
    k = result["k"]
    rows = [
        [f"`{g['model']}`", g["condition"], g["family"], g["difficulty"], g["incompletas"][f"k={k}"]["n"], g["n_instancias"]]
        for g in result["grupos"]
        if g["incompletas"].get(f"k={k}", {}).get("n")
    ]
    lines = ["## Instancias incompletas", ""]
    if not rows:
        return lines + [f"Ninguna: todas las instancias vistas tienen {k} muestras.", ""]
    lines += [
        f"Estas instancias tienen menos de {k} muestras y quedan fuera del denominador de "
        f"pass@{k}. La lista completa está en `summary.json`.",
        "",
    ]
    return lines + table(["Modelo", "Condición", "Familia", "Nivel", "Incompletas", "Vistas"], rows)


def render_report(result: dict[str, Any], n_errors: int) -> str:
    lines = render_header(result)
    lines += render_passes(result)
    lines += render_conditions(result)
    lines += render_baselines(result)
    lines += render_errors(result)
    lines += render_classification(result)
    lines += render_cost(result)
    lines += render_incomplete(result)
    lines += [
        "## Revisión manual",
        "",
        f"`muestra_errores.jsonl` tiene {n_errors} rollouts fallidos, estratificados por modelo, "
        f"condición, familia, dificultad y error_type (hasta {result['_per_stratum']} por "
        "estrato). Sirve para verificar a mano si el verificador rechazó bien.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--per-stratum", type=int, default=3)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if not args.folder.is_dir():
        raise SystemExit(f"no existe la carpeta: {args.folder}")

    result = analyze(args.folder, args.per_stratum, args.seed)
    errors = sample_failures(result["_rows"], args.per_stratum, args.seed)
    with (args.folder / "muestra_errores.jsonl").open("w", encoding="utf-8") as handle:
        for row in errors:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    (args.folder / "report.md").write_text(render_report(result, len(errors)), encoding="utf-8")
    summary = {key: value for key, value in result.items() if not key.startswith("_")}
    summary["n_rollouts"] = len(result["_rows"])
    summary["n_muestra_errores"] = len(errors)
    (args.folder / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"{len(result['_rows'])} rollouts; informe en {args.folder / 'report.md'}")


if __name__ == "__main__":
    main()
