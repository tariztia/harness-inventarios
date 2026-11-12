from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reevaluate  # noqa: E402
import run_pilot  # noqa: E402


def _run(tmp_path: Path) -> tuple[Path, Path]:
    folder = tmp_path / "corrida"
    assert run_pilot.main([
        "--stage", "exploracion", "--dry-run", "--limit", "9", "--n-samples", "1",
        "--models", "m/chico", "--out", str(folder),
    ]) == 0
    return folder, next(folder.glob("rollouts_*.jsonl"))


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_reevaluar_sin_cambios_no_toca_los_veredictos(tmp_path):
    folder, path = _run(tmp_path)
    before = _rows(path)
    assert reevaluate.main([str(folder)]) == 0
    assert _rows(path) == before
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["reevaluaciones"][0]["conteos"] == {"evaluadas": len(before)}


def test_reevaluar_corrige_un_veredicto_viejo_y_guarda_el_anterior(tmp_path):
    folder, path = _run(tmp_path)
    rows = _rows(path)
    index = next(i for i, row in enumerate(rows) if row["verdict"]["reward"] == 1.0)
    good = rows[index]["verdict"]
    stale = {**good, "reward": 0.0, "correct_final_answer": False, "error_type": "missing_field"}
    rows[index]["verdict"] = stale
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")

    assert reevaluate.main([str(folder), "--dry-run"]) == 0
    assert _rows(path)[index]["verdict"] == stale  # --dry-run no escribe

    assert reevaluate.main([str(folder)]) == 0
    fixed = _rows(path)[index]
    assert fixed["verdict"] == good and fixed["verdict_anterior"] == stale
    counts = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))["reevaluaciones"][0]["conteos"]
    assert counts["de_0_a_1"] == 1 and counts["missing_field -> ok"] == 1

    # Una segunda pasada no pisa el veredicto original de la corrida.
    assert reevaluate.main([str(folder)]) == 0
    assert _rows(path)[index]["verdict_anterior"] == stale
