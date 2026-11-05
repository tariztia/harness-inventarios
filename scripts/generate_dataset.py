"""Genera train/eval/test en JSONL y stats.json.

Uso: uv run python scripts/generate_dataset.py --n-per-cell 40 --base-seed 2026 --out data/v1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from inventory_harness.generator import dataset_stats, generate_dataset  # noqa: E402
from inventory_harness.schema import SPLITS  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-per-cell", type=int, required=True)
    parser.add_argument("--base-seed", type=int, default=2026)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    config = {
        "n_per_cell": {split: args.n_per_cell for split in SPLITS},
        "base_seed": args.base_seed,
    }
    instances = generate_dataset(config)
    args.out.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        with (args.out / f"{split}.jsonl").open("w", encoding="utf-8") as handle:
            for instance in instances:
                if instance.split == split:
                    handle.write(json.dumps(instance.to_dict(), ensure_ascii=False) + "\n")
    stats = {"config": config, **dataset_stats(instances)}
    (args.out / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"{stats['total']} instancias en {args.out}")


if __name__ == "__main__":
    main()
