"""Ejecuta los casos adversariales contra verify_final_text y escribe el informe de robustez.

Uso: uv run python scripts/robustness_report.py [--out docs/robustez_verificador.md]

Un caso acierta si el verificador acepta o rechaza como indica `should_pass`. Se informa
ademas si coincide el error_type esperado, cuando el caso lo declara. Los casos citados en
KNOWN_LIMITATIONS fallan a proposito y se muestran aparte: no se ocultan ni se descuentan.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from adversarial_cases import CASES, KNOWN_LIMITATIONS, categories  # noqa: E402

from inventory_harness.schema import FAMILIES, Instance  # noqa: E402
from inventory_harness.verifier import verify_final_text  # noqa: E402


def make_instance(family: str, expected: dict[str, Any]) -> Instance:
    return Instance(
        id="caso",
        seed=0,
        family=family,
        difficulty="easy",
        split="test",
        template_id="t",
        inventory=(),
        orders=(),
        product_ids=(),
        location_ids=(),
        request="",
        expected=expected,
        required_records=(),
    )


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    verdict = verify_final_text(case["text"], make_instance(case["family"], case["expected"]))
    accepted = verdict.reward == 1.0
    wanted_error = case["expected_error_type"]
    return {
        **case,
        "accepted": accepted,
        "hit": accepted == case["should_pass"],
        "error_type": verdict.error_type,
        "error_match": None if wanted_error is None else verdict.error_type == wanted_error,
    }


def percent(part: int, total: int) -> str:
    return f"{100 * part / total:.1f} %" if total else "n/d"


def render(results: list[dict[str, Any]]) -> str:
    limited = {e["case_id"] for e in KNOWN_LIMITATIONS if e.get("case_id")}
    hits = sum(r["hit"] for r in results)
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        by_category[result["category"]].append(result)

    lines = [
        "# Robustez del verificador",
        "",
        "Archivo generado por `scripts/robustness_report.py`; no editar a mano.",
        "",
        f"Casos: {len(results)}. Aciertos: {hits} ({percent(hits, len(results))}). "
        f"Fallos: {len(results) - hits}, de los cuales "
        f"{sum(not r['hit'] and r['id'] in limited for r in results)} son limitaciones "
        "conocidas y "
        f"{sum(not r['hit'] and r['id'] not in limited for r in results)} son fallos no documentados.",
        "",
        "Un acierto significa que el verificador acepta o rechaza como indica el caso. "
        "Estos casos fueron escritos por el equipo: miden las equivalencias y trampas "
        "previstas, no la variedad de respuestas de un modelo real. Esa parte se revisa con "
        "`muestra_errores.jsonl` del piloto.",
        "",
        "## Aciertos por categoría",
        "",
        "| Categoría | Casos | Deben pasar | Deben rechazarse | Aciertos | Tasa | Falsos positivos | Falsos negativos |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for category in categories():
        group = by_category[category]
        ok = sum(r["hit"] for r in group)
        should = sum(r["should_pass"] for r in group)
        false_pos = sum(r["accepted"] and not r["should_pass"] for r in group)
        false_neg = sum(not r["accepted"] and r["should_pass"] for r in group)
        lines.append(
            f"| {category} | {len(group)} | {should} | {len(group) - should} | {ok} | "
            f"{percent(ok, len(group))} | {false_pos} | {false_neg} |"
        )

    checked = [r for r in results if r["error_match"] is not None]
    matched = sum(r["error_match"] is True for r in checked)
    lines += [
        "",
        "## Tipo de error",
        "",
        f"De {len(checked)} casos que declaran un `error_type`, {matched} coinciden "
        f"({percent(matched, len(checked))}).",
        "",
        "## Fallos",
        "",
    ]
    failures = [r for r in results if not r["hit"] or r["error_match"] is False]
    if not failures:
        lines.append("Ninguno.")
    else:
        lines += ["| Caso | Categoría | Debía pasar | Aceptado | error_type | Limitación conocida |", "|---|---|---|---|---|---|"]
        for r in failures:
            lines.append(
                f"| `{r['id']}` | {r['category']} | {'sí' if r['should_pass'] else 'no'} | "
                f"{'sí' if r['accepted'] else 'no'} | `{r['error_type']}` | "
                f"{'sí' if r['id'] in limited else 'NO'} |"
            )

    lines += ["", "## Limitaciones conocidas", ""]
    for entry in KNOWN_LIMITATIONS:
        case_id = entry.get("case_id")
        prefix = f"`{case_id}`" if case_id else "Sin caso asociado"
        lines.append(f"- **{prefix}.** {entry['description']}")

    lines += [
        "",
        "## Cobertura por familia",
        "",
        "| Familia | Casos | Deben pasar | Deben rechazarse | Categorías cubiertas | Categorías sin casos |",
        "|---|---:|---:|---:|---:|---|",
    ]
    all_categories = categories()
    for family in FAMILIES:
        group = [r for r in results if r["family"] == family]
        covered = {r["category"] for r in group}
        missing = [c for c in all_categories if c not in covered]
        should = sum(r["should_pass"] for r in group)
        lines.append(
            f"| {family} | {len(group)} | {should} | {len(group) - should} | {len(covered)} | "
            f"{', '.join(missing) if missing else '—'} |"
        )
    counts = Counter(r["family"] for r in results)
    weakest = min(FAMILIES, key=lambda family: counts[family])
    lines += [
        "",
        f"La familia con menos casos es `{weakest}` ({counts[weakest]}). Una categoría sin "
        "casos en una familia no implica que el verificador falle ahí; implica que esa "
        "combinación no está medida.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "robustez_verificador.md")
    args = parser.parse_args()
    results = [evaluate_case(case) for case in CASES]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(results), encoding="utf-8")
    hits = sum(r["hit"] for r in results)
    print(f"{hits}/{len(results)} aciertos; informe en {args.out}")


if __name__ == "__main__":
    main()
