"""Curvas de entrenamiento a partir de `train_log.json` (y `reward_errors.jsonl` de GRPO).

Uso:
    python scripts/plot_training.py runs/grpo --out runs/grpo/curvas.png
    python scripts/plot_training.py runs/grpo runs/sft_grpo --out comparacion.png --metric reward

Sin matplotlib escribe solo un CSV con las mismas series. Cada carpeta es la salida de un
script `train_*.py`. `--metric` por omision es `reward` si la corrida es de GRPO y `loss` si
no; tambien sirven `completions/mean_length`, `rewards/margins` (DPO) y cualquier otra clave
del registro.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def series(folder: Path, metric: str | None) -> tuple[str, list[tuple[float, float]]]:
    history = json.loads((folder / "train_log.json").read_text(encoding="utf-8"))
    kind = "grpo" if any("reward" in row for row in history) else "otro"
    key = metric or ("reward" if kind == "grpo" else "loss")
    points = [(row.get("step", index + 1), row[key]) for index, row in enumerate(history) if key in row]
    if not points:
        raise SystemExit(f"{folder}: no hay valores de `{key}` en train_log.json")
    return key, [(float(x), float(y)) for x, y in points]


def smooth(values: list[float], window: int) -> list[float]:
    if window <= 1:
        return values
    out = []
    for index in range(len(values)):
        chunk = values[max(0, index - window + 1) : index + 1]
        out.append(sum(chunk) / len(chunk))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folders", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--metric", help="clave del registro; por omision reward (GRPO) o loss")
    parser.add_argument("--smooth", type=int, default=1, help="media movil de N puntos")
    args = parser.parse_args(argv)

    data = {}
    key = ""
    for folder in args.folders:
        key, points = series(folder, args.metric)
        data[folder.name] = points

    csv_path = args.out.with_suffix(".csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["corrida", "paso", key])
        for name, points in data.items():
            writer.writerows((name, int(x), y) for x, y in points)
    print(f"Serie en {csv_path}")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no esta instalado: solo se escribio el CSV.")
        return 0
    fig, ax = plt.subplots(figsize=(7, 4))
    for name, points in data.items():
        xs = [x for x, _ in points]
        ax.plot(xs, smooth([y for _, y in points], args.smooth), label=name)
    ax.set_xlabel("paso")
    ax.set_ylabel(key)
    ax.grid(alpha=0.3)
    if len(data) > 1:
        ax.legend()
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    print(f"Figura en {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
