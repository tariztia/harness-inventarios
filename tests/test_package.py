from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import package_for_colab  # noqa: E402


def test_el_zip_no_lleva_salidas_de_corridas(tmp_path, monkeypatch):
    for name in (
        "pyproject.toml",
        "src/inventory_harness/a.py",
        "scripts/b.py",
        "tests/test_c.py",
        "docs/guia.md",
        "tests/salida/rollouts_m.jsonl",
        "tests/salida/manifest.json",
        "tests/salida/summary.json",
        "docs/datos/sft.jsonl",
        "src/inventory_harness/__pycache__/a.cpython-313.pyc",
    ):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")
    monkeypatch.setattr(package_for_colab, "ROOT", tmp_path)

    names = sorted(p.relative_to(tmp_path).as_posix() for p in package_for_colab.files_to_package())
    assert names == [
        "docs/guia.md",
        "pyproject.toml",
        "scripts/b.py",
        "src/inventory_harness/a.py",
        "tests/test_c.py",
    ]


def test_el_zip_real_trae_lo_que_corren_los_cuadernos():
    names = {p.relative_to(ROOT).as_posix() for p in package_for_colab.files_to_package()}
    for needed in (
        "tests/test_solver.py", "tests/test_numbers_es.py", "tests/test_verifier.py",
        "tests/test_generator.py", "tests/test_tools.py", "tests/adversarial_cases.py",
        "scripts/run_pilot.py", "scripts/analyze_results.py", "scripts/build_training_data.py",
    ):
        assert needed in names
