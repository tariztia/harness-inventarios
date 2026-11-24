"""Muestra de respuestas con recompensa 1 para auditarlas a mano (hoja CSV).

Uso:
    python scripts/audit_sample.py results/kaggle_qwen17b/linea_base_qwen17b --n 50 --out auditoria.csv
    python scripts/audit_sample.py runs/grpo/completions.jsonl --n 50     # respuestas de GRPO

El enunciado pide revisar a mano una muestra de trazas "exitosas" y estimar cuantos aciertos son
genuinos (como SWE-Bench+). La muestra se reparte parejo entre las celdas (condicion, familia,
dificultad) y es reproducible con --seed. Para cada fila, abre la respuesta completa en
`archivo` (la linea indicada) y rellena las columnas vacias:
  - datos_ok:   en `tools`, pidio los registros necesarios y los uso; en `visible`, leyo la tabla.
  - razon_ok:   el razonamiento llega a la respuesta por las razones correctas.
  - genuino:    si / no (acierto por azar, copia del formato, razonamiento incoherente...).
  - comentario: lo que llamo la atencion.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path


def read_rows(source: Path) -> list[dict]:
    """Respuestas exitosas de una carpeta de rollouts o de un completions.jsonl de GRPO."""
    files = sorted(source.glob("rollouts_*.jsonl")) if source.is_dir() else [source]
    if not files:
        raise SystemExit(f"{source}: no hay rollouts_*.jsonl")
    rows = []
    for path in files:
        with path.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                reward = row.get("reward", (row.get("verdict") or {}).get("reward"))
                if reward != 1.0:
                    continue
                messages = row.get("messages")
                final = messages[-1]["content"] if messages else row.get("completion", "")
                rows.append({
                    "archivo": path.name, "linea": number,
                    "modelo": row.get("model", "grpo"), "condicion": row.get("condition", "visible"),
                    "familia": row.get("family"), "dificultad": row.get("difficulty"),
                    "instancia": row.get("instance_id"), "muestra": row.get("sample", ""),
                    "respuesta_final": " ".join(final.split())[-600:],
                })
    return rows


def stratified(rows: list[dict], n: int, seed: int) -> list[dict]:
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        cells[(row["modelo"], row["condicion"], row["familia"], row["dificultad"])].append(row)
    rng = random.Random(seed)
    for members in cells.values():
        rng.shuffle(members)
    chosen: list[dict] = []
    keys = sorted(cells, key=str)
    while len(chosen) < n and any(cells[k] for k in keys):
        for key in keys:
            if cells[key] and len(chosen) < n:
                chosen.append(cells[key].pop())
    return chosen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path, help="carpeta con rollouts_*.jsonl, o un completions.jsonl")
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--out", type=Path, default=Path("auditoria.csv"))
    args = parser.parse_args(argv)

    rows = read_rows(args.source)
    sample = stratified(rows, args.n, args.seed)
    columns = ["archivo", "linea", "modelo", "condicion", "familia", "dificultad", "instancia", "muestra",
               "respuesta_final", "datos_ok", "razon_ok", "genuino", "comentario"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows({**row, "datos_ok": "", "razon_ok": "", "genuino": "", "comentario": ""} for row in sample)
    print(f"{len(sample)} de {len(rows)} respuestas exitosas en {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
