"""Lista los prompts de train sin ninguna respuesta correcta en las corridas dadas.

Uso:
    python scripts/pending_prompts.py results/kaggle_qwen17b/trazas_qwen17b --out pendientes.json
    python scripts/pending_prompts.py ... --out prueba.json --limit 9

Sirve para correr el modelo profesor (Qwen3-8B) solo donde falta una respuesta correcta,
con `run_pilot.py --stage trazas --only pendientes.json`. "Correcta" es lo mismo que en
build_training_data: recompensa 1 y llamadas validas, tras normalizar y reevaluar.
La lista va intercalada por celda (familia, dificultad, condicion), empezando por las
celdas con mas pendientes: con --limit, la prueba toma pares de celdas distintas.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_training_data import load_run  # noqa: E402
from inventory_harness.reward import InstanceStore  # noqa: E402
from inventory_harness.schema import CONDITIONS  # noqa: E402
from inventory_harness.training_data import collect  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", type=Path, help="carpetas de run_pilot sobre train")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, help="solo los primeros N pares, intercalados por celda")
    args = parser.parse_args(argv)

    instances, rows, datasets = [], [], []
    for folder in args.runs:
        manifest, run_instances, run_rows = load_run(folder)
        datasets.append(manifest["dataset"])
        instances += run_instances
        rows += run_rows
    if any(d["fingerprint"] != datasets[0]["fingerprint"] for d in datasets):
        raise SystemExit("Las corridas son de datasets distintos.")

    solved = {
        (c.instance.id, c.condition)
        for c in collect(rows, InstanceStore(instances), Counter())
        if c.correct
    }
    by_cell: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    seen = set()
    for instance in instances:
        for condition in CONDITIONS:
            key = (instance.id, condition)
            if key in solved or key in seen:
                continue
            seen.add(key)
            by_cell[(instance.family, instance.difficulty, condition)].append({
                "instance_id": instance.id,
                "condition": condition,
                "family": instance.family,
                "difficulty": instance.difficulty,
            })
    # Primero las celdas con mas pendientes: una prueba chica cae donde mas falta.
    cells = [by_cell[name] for name in sorted(by_cell, key=lambda name: (-len(by_cell[name]), name))]
    pending = [cell[i] for i in range(max(map(len, cells), default=0)) for cell in cells if i < len(cell)]
    total = len(pending)
    if args.limit:
        pending = pending[: args.limit]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "corridas": [folder.name for folder in args.runs],
        "dataset": datasets[0],
        "pendientes_totales": total,
        "pending": pending,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Pares sin respuesta correcta: {total}; en el archivo: {len(pending)}")
    for (family, difficulty, condition), count in sorted(
        Counter((p["family"], p["difficulty"], p["condition"]) for p in pending).items()
    ):
        print(f"  {family}|{difficulty}|{condition}: {count}")
    print(f"Salida en {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
