"""Lectura indulgente de rollouts: ¿el modelo falla por formato o por cálculo?

Busca cada clave del contrato (`alcanza:`, `faltan:`, `O1_atendidas:`...) en cualquier parte
del texto final, sin exigir el bloque <answer>, toma su última aparición y compara el
valor con `expected`. No es una recompensa: solo sirve para diagnosticar.

Uso:
    uv run python scripts/lectura_indulgente.py \
        results/kaggle_otros_modelos/linea_base_sin_think/rollouts_unsloth_Llama-3.2-1B-Instruct.jsonl \
        results/kaggle_otros_modelos/linea_base_sin_think/rollouts_Qwen_Qwen3-1.7B.jsonl

Las instancias se regeneran con la configuración de la línea base (semilla 2026, 10 por celda).
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from inventory_harness.generator import generate_dataset  # noqa: E402
from inventory_harness.numbers_es import (  # noqa: E402
    parse_bool_value,
    parse_int_value,
    parse_location_value,
)
from inventory_harness.reward import InstanceStore  # noqa: E402
from inventory_harness.verifier import _strip_think  # noqa: E402

CONFIG = {"base_seed": 2026, "n_per_cell": {"train": 10, "eval": 10, "test": 10}}
KEY_RE = re.compile(
    r"^[\s\-*•`]*\**\s*(alcanza|faltan|sucursal|cubiertas|pendientes|total_pendientes|"
    r"O\d+_atendidas|O\d+_pendientes)\s*\**\s*:\s*\**\s*(.+?)\s*\**\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _load(value):
    return ast.literal_eval(value) if isinstance(value, str) else value


def _fields(instance) -> list[tuple[str, object, object]]:
    """(clave, parser, valor esperado) de cada campo de la instancia."""
    expected = instance.expected
    if instance.family == "availability":
        return [
            ("alcanza", parse_bool_value, expected["can_fulfill"]),
            ("faltan", parse_int_value, expected["missing_units"]),
        ]
    if instance.family == "selection":
        return [
            ("sucursal", parse_location_value, expected["location_id"]),
            ("cubiertas", parse_int_value, expected["covered_units"]),
            ("pendientes", parse_int_value, expected["pending_units"]),
        ]
    fields = []
    for order, values in expected["orders"].items():
        fields.append((f"{order.lower()}_atendidas", parse_int_value, values["covered_units"]))
        fields.append((f"{order.lower()}_pendientes", parse_int_value, values["pending_units"]))
    fields.append(("total_pendientes", parse_int_value, expected["total_pending"]))
    return fields


def lenient(text: str, instance) -> dict[str, bool | None]:
    """Por campo: True/False si el modelo lo escribió, None si no aparece."""
    found = {key.lower(): value for key, value in KEY_RE.findall(_strip_think(text))}
    result: dict[str, bool | None] = {}
    for key, parser, want in _fields(instance):
        if key not in found:
            result[key] = None
            continue
        try:
            result[key] = parser(found[key]) == want
        except Exception:
            result[key] = False
    return result


def main(paths: list[str]) -> None:
    store = InstanceStore(generate_dataset(CONFIG))
    for path in paths:
        total = Counter()
        for line in Path(path).open(encoding="utf-8"):
            row = json.loads(line)
            found = store.lookup(row["prompt"])
            if found is None:
                total["sin_instancia"] += 1
                continue
            instance, _ = found
            final = _load(row["messages"])[-1]["content"]
            fields = lenient(final, instance)
            present = [v for v in fields.values() if v is not None]
            total["respuestas"] += 1
            total["todo_correcto"] += bool(fields) and all(v is True for v in fields.values())
            total["campos_escritos"] += len(present)
            total["campos_correctos"] += sum(present)
            if instance.family == "availability" and fields["alcanza"] is not None:
                total["alcanza_escrito"] += 1
                total["alcanza_correcto"] += fields["alcanza"]
        print(f"\n{path}")
        for key, value in total.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main(sys.argv[1:])
