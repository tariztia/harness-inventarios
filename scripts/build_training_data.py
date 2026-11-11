"""Arma trazas SFT y pares DPO a partir de corridas de run_pilot sobre train.

Uso:
    python scripts/build_training_data.py results/trazas --out results/datos_derivados
    python scripts/build_training_data.py results/trazas_8b results/trazas_17b --out results/datos

Acepta varias carpetas: por ejemplo, las del profesor (Qwen3-8B) y del modelo objetivo.
Rechaza cualquier corrida que no sea de train. Escribe sft.jsonl, dpo.jsonl y
manifest.json, con el procedimiento y los conteos. Ver docs/contrato.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import run_pilot  # noqa: E402
from inventory_harness.reward import InstanceStore  # noqa: E402
from inventory_harness.training_data import build, collect  # noqa: E402

PROCEDURE = [
    "Cada modelo resuelve instancias de train con run_pilot (etapa trazas).",
    "Cada rollout se normaliza: las llamadas pasan a <tool_call>{json}</tool_call> y se "
    "descarta el texto que las acompana; el razonamiento <think> se conserva.",
    "El verificador vuelve a evaluar cada rollout normalizado contra la instancia protegida.",
    "SFT: rollouts con recompensa 1 y llamadas validas, priorizando al profesor.",
    "DPO: por prompt, una respuesta correcta (priorizando al profesor) y una incorrecta "
    "(priorizando otros modelos y errores de valor). Se excluyen las respuestas cortadas "
    "por el tope de tokens.",
]


def load_run(folder: Path) -> tuple[dict[str, Any], list, list[dict[str, Any]]]:
    path = folder / "manifest.json"
    if not path.exists():
        raise SystemExit(f"{folder} no tiene manifest.json: no es una corrida de run_pilot")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    dataset = manifest["dataset"]
    if dataset["split"] != "train":
        raise SystemExit(f"{folder} es del split {dataset['split']}: solo se usa train")
    instances = run_pilot.build_dataset("train", dataset["n_per_cell"], dataset["base_seed"])
    if run_pilot.dataset_fingerprint(instances) != dataset["fingerprint"]:
        raise SystemExit(f"{folder}: el dataset regenerado no coincide con el de la corrida")
    rows = []
    for rollouts in sorted(folder.glob("rollouts_*.jsonl")):
        for line in rollouts.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return manifest, instances, rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", type=Path, help="carpetas de run_pilot sobre train")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "datos_derivados")
    parser.add_argument("--teacher", default=f"{run_pilot.LARGE_MODEL}+think",
                        help="etiqueta del modelo profesor, con prioridad como respuesta correcta")
    parser.add_argument("--max-sft-per-prompt", type=int, default=1)
    args = parser.parse_args(argv)

    instances, rows, runs = [], [], []
    for folder in args.runs:
        manifest, run_instances, run_rows = load_run(folder)
        instances += run_instances
        rows += run_rows
        runs.append({
            "carpeta": folder.name,
            "stage": manifest.get("stage"),
            "dry_run": manifest.get("dry_run"),
            "dataset": manifest["dataset"],
            "gen_configs": manifest.get("gen_configs", {}),
        })

    dropped: Counter = Counter()
    candidates = collect(rows, InstanceStore(instances), dropped)
    sft, dpo, stats = build(candidates, args.teacher, args.max_sft_per_prompt)

    args.out.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out / "sft.jsonl", sft)
    write_jsonl(args.out / "dpo.jsonl", dpo)
    teacher_present = any(c.model == args.teacher for c in candidates)
    summary = {
        "created_at": run_pilot.now(),
        "code_hash": run_pilot.code_hash(),
        "corridas": runs,
        "profesor": args.teacher if teacher_present else None,
        "max_sft_por_prompt": args.max_sft_per_prompt,
        "procedimiento": PROCEDURE,
        "rollouts_leidos": len(rows),
        "descartados": dict(dropped),
        **stats,
    }
    (args.out / "manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Rollouts leidos: {len(rows)}; descartados: {dict(dropped) or 0}")
    if not teacher_present:
        print(f"AVISO: no hay rollouts de {args.teacher}; las trazas SFT son de los otros modelos.")
    print(f"Prompts: {stats['prompts']}; SFT: {stats['sft']}; DPO: {stats['dpo']}")
    print("Por celda (familia|dificultad|condicion): prompts, con correcta, SFT, DPO")
    for name, counts in stats["por_celda"].items():
        print(f"  {name}: {counts.get('prompts', 0)}, {counts.get('con_correcta', 0)}, "
              f"{counts.get('sft', 0)}, {counts.get('dpo', 0)}")
    print(f"Salida en {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
