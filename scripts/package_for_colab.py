"""Empaqueta el proyecto en dist/inventory_harness_colab.zip y prueba el zip en una carpeta vacia.

Uso: uv run python scripts/package_for_colab.py

No incluye data/ ni results/: los datasets se regeneran de forma determinista desde semillas.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE_DIRS = ("src", "scripts", "tests", "docs")
INCLUDE_FILES = ("pyproject.toml",)
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
# Salidas de corridas: un `--out tests/salida` o un sft.jsonl en docs/ no deben viajar en el
# zip. Los datos se regeneran desde semillas y los resultados viven en Drive.
DATA_SUFFIXES = {".jsonl", ".tmp"}
DATA_NAMES = {"manifest.json", "summary.json", "stats.json"}
# Sin dependencias externas: comprueba que el zip trae todo el nucleo y las etapas.
SELF_CHECK = (
    "import sys; sys.path.insert(0, 'src');"
    "import inventory_harness.metrics, inventory_harness.baselines, inventory_harness.verifier;"
    "import inventory_harness.rollout, inventory_harness.backends;"
    "from inventory_harness.generator import generate_dataset;"
    "print(len(generate_dataset({'n_per_cell': {'eval': 1}, 'base_seed': 2026})))"
)


def files_to_package() -> list[Path]:
    paths = [ROOT / name for name in INCLUDE_FILES]
    for directory in INCLUDE_DIRS:
        for path in sorted((ROOT / directory).rglob("*")):
            if not path.is_file() or path.suffix in EXCLUDED_SUFFIXES:
                continue
            if EXCLUDED_PARTS & set(path.relative_to(ROOT).parts):
                continue
            if path.suffix in DATA_SUFFIXES or path.name in DATA_NAMES:
                continue
            paths.append(path)
    return paths


def untracked(names: list[str]) -> list[str]:
    """Archivos del zip que git no sigue. Vacio si no hay git: es solo un aviso."""
    try:
        done = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", *INCLUDE_DIRS],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if done.returncode != 0:
        return []
    others = set(done.stdout.split())
    return [name for name in names if name in others]


def build(out: Path) -> list[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files_to_package():
            name = path.relative_to(ROOT).as_posix()
            archive.write(path, name)
            names.append(name)
    return names


def check_in_empty_folder(out: Path) -> None:
    """Descomprime en una carpeta vacia y ejecuta el proyecto sin nada del repositorio."""
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        with zipfile.ZipFile(out) as archive:
            bad = archive.testzip()
            if bad:
                raise SystemExit(f"zip corrupto: {bad}")
            archive.extractall(folder)
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        for command in (
            [sys.executable, "-c", SELF_CHECK],
            [sys.executable, "scripts/run_pilot.py", "--help"],
        ):
            subprocess.run(command, cwd=folder, env=env, check=True, capture_output=True, text=True)
        dry = subprocess.run(
            [
                sys.executable, "scripts/run_pilot.py", "--stage", "exploracion", "--dry-run",
                "--limit", "3", "--n-samples", "1", "--out", "salida",
            ],
            cwd=folder, env=env, check=True, capture_output=True, text=True,
        )
        if not list((folder / "salida").glob("rollouts_*.jsonl")):
            raise SystemExit(f"el dry-run no dejo rollouts:\n{dry.stdout}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / "inventory_harness_colab.zip")
    parser.add_argument("--skip-check", action="store_true")
    args = parser.parse_args()
    names = build(args.out)
    forbidden = [n for n in names if n.startswith(("data/", "results/")) or "__pycache__" in n]
    if forbidden:
        raise SystemExit(f"archivos que no deben ir en el zip: {forbidden[:5]}")
    extra = untracked(names)
    if extra:
        print(f"AVISO: {len(extra)} archivos sin seguimiento de git van en el zip: {extra[:5]}")
    if not args.skip_check:
        check_in_empty_folder(args.out)
    digest = hashlib.sha256(args.out.read_bytes()).hexdigest()[:12]
    print(f"{args.out}: {len(names)} archivos, {args.out.stat().st_size / 1024:.0f} KiB, sha256 {digest}")
    if args.skip_check:
        print("Comprobacion omitida.")
    else:
        print("Comprobado desde una carpeta vacia.")


if __name__ == "__main__":
    main()
