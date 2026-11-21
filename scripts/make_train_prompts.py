"""Genera instancias nuevas de `train` para GRPO, sin repetir ninguna de eval ni de test.

Uso:
    python scripts/make_train_prompts.py --n-per-cell 40 --out data/train_extra.jsonl

Los 180 prompts de `train` que tienen trazas SFT son pocos para RL. Aqui se generan mas con
otra semilla (por omision 5151, la del piloto es 2026) y se descartan las que coinciden por
huella (`generator.fingerprint`) con eval, test o el train del piloto, tanto con 10 como con 40
instancias por celda. No se regenera `eval`: cambiar su tamano cambiaria sus instancias y
rompe la comparacion con la linea base.

La salida es deterministica: la misma semilla produce el mismo archivo, por eso `data/` no se
versiona.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from inventory_harness import training_prep as prep  # noqa: E402
from inventory_harness.generator import fingerprint  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n-per-cell", type=int, default=40, help="instancias por familia y dificultad")
    parser.add_argument("--base-seed", type=int, default=prep.EXTRA_BASE_SEED)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "train_extra.jsonl")
    args = parser.parse_args(argv)

    instances = prep.extra_train_instances(args.n_per_cell, args.base_seed)
    protected = prep.protected_fingerprints()
    repeated = sum(fingerprint(instance) in protected for instance in instances)
    if repeated:
        raise SystemExit(f"{repeated} instancias coinciden con eval, test o el train del piloto.")
    count = prep.write_instances(args.out, instances)
    cells = Counter((i.family, i.difficulty) for i in instances)
    print(f"{count} instancias en {args.out} (semilla {args.base_seed}); 0 repetidas de eval, test o el train del piloto.")
    for (family, difficulty), n in sorted(cells.items()):
        print(f"  {family}|{difficulty}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
