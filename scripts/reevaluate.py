"""Vuelve a evaluar los rollouts guardados de una corrida con el verificador actual.

Uso:
    python scripts/reevaluate.py results/kaggle_qwen17b/linea_base_qwen17b
    python scripts/reevaluate.py <carpeta> --dry-run     # solo informa que cambiaria

No corre ningun modelo: los mensajes guardados se evaluan de nuevo contra la instancia
protegida. Sirve cuando el verificador cambia despues de una corrida. Reescribe los
rollouts_*.jsonl en su lugar; cada fila cuyo veredicto cambia conserva el anterior en
`verdict_anterior`, y manifest.json anota la reevaluacion. Despues hay que regenerar el
informe con analyze_results.py.

Solo es valido si los prompts y las observaciones no cambiaron desde la corrida: una fila
cuyo prompt ya no se reconoce se deja igual y se cuenta aparte.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import run_pilot  # noqa: E402
from inventory_harness.reward import InstanceStore, evaluate_trajectory  # noqa: E402


def load_store(manifest: dict[str, Any]) -> InstanceStore:
    dataset = manifest["dataset"]
    instances = run_pilot.build_dataset(dataset["split"], dataset["n_per_cell"], dataset["base_seed"])
    if run_pilot.dataset_fingerprint(instances) != dataset["fingerprint"]:
        raise SystemExit("el dataset regenerado no coincide con el de la corrida")
    return InstanceStore(instances)


def reevaluate_row(row: dict[str, Any], store: InstanceStore, counts: Counter) -> dict[str, Any]:
    """Fila con el veredicto actual. Las de `internal_error` y las desconocidas no se tocan."""
    old = row.get("verdict") or {}
    if old.get("error_type") == "internal_error":
        counts["error_interno_sin_tocar"] += 1
        return row
    found = store.lookup(row.get("prompt", ""))
    if found is None:
        counts["prompt_desconocido_sin_tocar"] += 1
        return row
    instance, condition = found
    new = evaluate_trajectory(instance, condition, row["messages"]).to_dict()
    counts["evaluadas"] += 1
    if new == old:
        return row
    counts["veredicto_distinto"] += 1
    was, now = old.get("reward") == 1.0, new["reward"] == 1.0
    if was != now:
        counts["de_0_a_1" if now else "de_1_a_0"] += 1
        counts[f"{old.get('error_type')} -> {new['error_type']}"] += 1
    updated = dict(row)
    # Se conserva el veredicto de la corrida, no el de una reevaluacion intermedia.
    updated.setdefault("verdict_anterior", old)
    updated["verdict"] = new
    return updated


def reevaluate_file(path: Path, store: InstanceStore, counts: Counter, write: bool) -> None:
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            counts["linea_ilegible_sin_tocar"] += 1
            lines.append(line)
            continue
        lines.append(json.dumps(reevaluate_row(row, store, counts), ensure_ascii=False))
    if write:
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="\n")
        os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", type=Path, help="carpeta de una corrida de run_pilot")
    parser.add_argument("--dry-run", action="store_true", help="no escribe nada")
    args = parser.parse_args(argv)

    manifest_path = args.folder / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"{args.folder} no tiene manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    store = load_store(manifest)
    counts: Counter = Counter()
    for path in sorted(args.folder.glob("rollouts_*.jsonl")):
        reevaluate_file(path, store, counts, write=not args.dry_run)

    print(f"{args.folder}: {dict(counts)}")
    if counts["prompt_desconocido_sin_tocar"]:
        print("AVISO: hay prompts que el codigo actual no reconoce; esas filas no se reevaluaron.")
    if not args.dry_run:
        manifest.setdefault("reevaluaciones", []).append(
            {"fecha": run_pilot.now(), "code_hash": run_pilot.code_hash(), "conteos": dict(counts)}
        )
        run_pilot.write_manifest(args.folder, manifest)
        print("Rollouts reescritos. Regenera el informe: python scripts/analyze_results.py", args.folder)
    return 0


if __name__ == "__main__":
    sys.exit(main())
