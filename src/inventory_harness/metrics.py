"""Agrega rollouts (JSONL) a pass@1, pass@k y diagnosticos, con denominadores e IC de Wilson.

Solo stdlib. Formato de cada linea en docs/contrato.md, "Rollouts (JSONL)".

Definiciones:
- Unidad estadistica: la instancia dentro de (modelo, condicion). Las muestras de una
  misma instancia no son independientes; por eso el IC se calcula sobre instancias.
- `pass@1`: fraccion de instancias acertadas en la muestra 0, no el promedio de muestras.
- `pass@k`: fraccion de instancias con al menos un acierto entre las muestras 0..k-1.
- `tasa_media_muestra`: aciertos / muestras. Se informa sin IC: las muestras estan
  correlacionadas y un Wilson sobre ellas seria demasiado estrecho.
- Instancia incompleta para k: le falta alguna de las muestras 0..k-1. No entra al
  denominador de pass@k (un acierto parcial la sesgaria) y queda listada en `incompletas`.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

GROUP_FIELDS: tuple[str, ...] = ("model", "condition", "family", "difficulty")
Z_95 = 1.959963984540054
REQUIRED_ROW_FIELDS = ("model", "condition", "instance_id", "sample")
TOOL_DIAGNOSTICS = (
    "valid_tool_call",
    "correct_tool_arguments",
    "retrieved_required_data",
    "forged_observation",
    "tool_limit_exceeded",
)


@dataclass
class LoadResult:
    """Filas validas y cuenta de lo que no se pudo usar. Nada se descarta en silencio."""

    rows: list[dict[str, Any]] = field(default_factory=list)
    truncated_final_line: int = 0
    corrupt_lines: int = 0
    malformed_rows: int = 0
    duplicates: int = 0

    def extend(self, other: "LoadResult") -> None:
        self.rows.extend(other.rows)
        self.truncated_final_line += other.truncated_final_line
        self.corrupt_lines += other.corrupt_lines
        self.malformed_rows += other.malformed_rows
        self.duplicates += other.duplicates

    def problems(self) -> dict[str, int]:
        return {
            "linea_final_truncada": self.truncated_final_line,
            "lineas_corruptas": self.corrupt_lines,
            "filas_sin_campos_requeridos": self.malformed_rows,
            "duplicados_descartados": self.duplicates,
        }


def _row_id(row: dict[str, Any]) -> tuple[Any, ...]:
    return (row["model"], row["condition"], row["instance_id"], row["sample"])


def _row_is_usable(row: Any) -> bool:
    if not isinstance(row, dict) or any(row.get(name) is None for name in REQUIRED_ROW_FIELDS):
        return False
    sample = row["sample"]
    return isinstance(sample, int) and not isinstance(sample, bool) and sample >= 0


def load_rollouts(paths: Path | str | Iterable[Path | str]) -> LoadResult:
    """Lee uno o varios JSONL. Tolera una linea final truncada y deduplica por clave.

    Una desconexion puede cortar la ultima linea, asi que esa se cuenta aparte. Una linea
    invalida en otra posicion es corrupcion real y tambien se cuenta. De un duplicado se
    conserva la primera aparicion, que es la que una reanudacion habria respetado.
    """
    if isinstance(paths, (str, Path)):
        paths = [paths]
    result = LoadResult()
    seen: set[tuple[Any, ...]] = set()
    for path in paths:
        with Path(path).open(encoding="utf-8", errors="replace", newline="\n") as handle:
            lines = handle.read().split("\n")
        # Tras la ultima linea terminada, split deja "". Si no, la final quedo sin cerrar.
        last_index = max((i for i, line in enumerate(lines) if line.strip()), default=-1)
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                if index == last_index:
                    result.truncated_final_line += 1
                else:
                    result.corrupt_lines += 1
                continue
            if not _row_is_usable(row):
                result.malformed_rows += 1
                continue
            row_id = _row_id(row)
            if row_id in seen:
                result.duplicates += 1
                continue
            seen.add(row_id)
            result.rows.append(row)
    return result


def wilson_interval(successes: int, n: int, z: float = Z_95) -> tuple[float | None, float | None]:
    """Intervalo de Wilson. Con n=0 no hay intervalo: devuelve (None, None)."""
    if n <= 0:
        return None, None
    if not 0 <= successes <= n:
        raise ValueError(f"aciertos fuera de rango: {successes}/{n}")
    p = successes / n
    z2 = z * z
    denominator = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denominator
    # En los extremos el limite exacto es 0 o 1; evita residuos de punto flotante.
    low = 0.0 if successes == 0 else max(0.0, center - half)
    high = 1.0 if successes == n else min(1.0, center + half)
    return low, high


def proportion(successes: int, n: int) -> dict[str, Any]:
    low, high = wilson_interval(successes, n)
    return {
        "aciertos": successes,
        "n": n,
        "tasa": successes / n if n else None,
        "ic95": [low, high],
    }


def verdict_of(row: dict[str, Any]) -> dict[str, Any]:
    verdict = row.get("verdict")
    return verdict if isinstance(verdict, dict) else {}


def is_success(row: dict[str, Any]) -> bool:
    reward = verdict_of(row).get("reward")
    if isinstance(reward, bool) or not isinstance(reward, (int, float)):
        return False
    return reward >= 1.0


def error_type_of(row: dict[str, Any]) -> str:
    verdict = verdict_of(row)
    if not verdict:
        return "sin_veredicto"
    value = verdict.get("error_type")
    return value if isinstance(value, str) and value else "sin_error_type"


def _number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value) if math.isfinite(value) else 0.0


def group_instances(rows: Iterable[dict[str, Any]]) -> dict[tuple[str, str, str], dict[int, bool]]:
    """(modelo, condicion, instancia) -> {muestra: acierto}."""
    instances: dict[tuple[str, str, str], dict[int, bool]] = defaultdict(dict)
    for row in rows:
        unit = (str(row["model"]), str(row["condition"]), str(row["instance_id"]))
        instances[unit].setdefault(row["sample"], is_success(row))
    return instances


def pass_at_k(
    instances: dict[tuple[str, str, str], dict[int, bool]], k: int
) -> tuple[dict[str, Any], list[str]]:
    """Proporcion pass@k e instancias incompletas para ese k."""
    if k < 1:
        raise ValueError("k debe ser >= 1")
    successes = n = 0
    incomplete: list[str] = []
    for unit, samples in sorted(instances.items()):
        if all(sample in samples for sample in range(k)):
            n += 1
            successes += any(samples[sample] for sample in range(k))
        else:
            incomplete.append(unit[2])
    return proportion(successes, n), incomplete


def _flag_rate(rows: Sequence[dict[str, Any]], name: str) -> dict[str, Any]:
    """Tasa de un booleano del veredicto. `None` (no aplica) queda fuera del denominador."""
    values = [verdict_of(row).get(name) for row in rows]
    applicable = [value for value in values if value is not None]
    return {"si": sum(value is True for value in applicable), "n": len(applicable)}


def _hit_token_limit(row: dict[str, Any]) -> bool:
    """Alguna generacion se quedo sin tokens.

    Sin `stop_reasons` (rollouts antiguos o backend sin ese dato) es solo una cota inferior:
    `new_tokens` acumula las rondas.
    """
    usage, config = row.get("usage"), row.get("gen_config")
    if not isinstance(usage, dict) or not isinstance(config, dict):
        return False
    reasons = usage.get("stop_reasons")
    if isinstance(reasons, list) and reasons:
        return "length" in reasons
    limit = _number(config.get("max_new_tokens"))
    return limit > 0 and _number(usage.get("new_tokens")) >= limit


def summarize_rows(rows: Sequence[dict[str, Any]], ks: Sequence[int] = (1, 5)) -> dict[str, Any]:
    instances = group_instances(rows)
    summary: dict[str, Any] = {"n_instancias": len(instances), "n_muestras": len(rows)}
    wins = sum(is_success(row) for row in rows)
    summary["tasa_media_muestra"] = {
        "aciertos": wins,
        "n": len(rows),
        "tasa": wins / len(rows) if rows else None,
    }
    summary["incompletas"] = {}
    for k in ks:
        result, incomplete = pass_at_k(instances, k)
        summary[f"pass@{k}"] = result
        summary["incompletas"][f"k={k}"] = {
            "n": len(incomplete),
            "instancias": sorted(set(incomplete)),
        }
    for name in (*TOOL_DIAGNOSTICS, "parser_error", "contradictory_answer", "correct_final_answer"):
        summary[name] = _flag_rate(rows, name)
    # Respuesta final correcta pero recompensa 0: sin evidencia, falsificada o fuera de limite.
    summary["correcta_sin_recompensa"] = {
        "si": sum(
            verdict_of(row).get("correct_final_answer") is True and not is_success(row)
            for row in rows
        ),
        "n": len(rows),
    }
    summary["error_types"] = dict(Counter(error_type_of(row) for row in rows).most_common())
    summary["tope_de_tokens"] = {"si": sum(_hit_token_limit(row) for row in rows), "n": len(rows)}
    usages = [row["usage"] if isinstance(row.get("usage"), dict) else {} for row in rows]
    tokens = sum(_number(usage.get("new_tokens")) for usage in usages)
    seconds = sum(_number(usage.get("seconds")) for usage in usages)
    summary["uso"] = {
        "tokens_nuevos": tokens,
        "tokens_por_muestra": tokens / len(rows) if rows else None,
        "segundos": seconds,
        "segundos_por_muestra": seconds / len(rows) if rows else None,
    }
    return summary


def aggregate(
    rows: Iterable[dict[str, Any]],
    ks: Sequence[int] = (1, 5),
    group_by: Sequence[str] = GROUP_FIELDS,
) -> list[dict[str, Any]]:
    """Una entrada por combinacion de `group_by`, en orden estable."""
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(name, "?")) for name in group_by)].append(row)
    return [
        {**dict(zip(group_by, key)), **summarize_rows(members, ks)}
        for key, members in sorted(groups.items())
    ]


def max_samples(rows: Iterable[dict[str, Any]]) -> int:
    """Muestras por instancia observadas: el mayor k posible en estos datos."""
    return max((row["sample"] + 1 for row in rows), default=0)
