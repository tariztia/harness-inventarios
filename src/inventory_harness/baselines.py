"""Reglas triviales y errores razonables, para saber si un acierto supera al azar informado.

Solo stdlib. Cada regla produce un texto de respuesta por instancia y se evalua con
`verify_final_text`, igual que un modelo. Ninguna lee `instance.expected`, salvo el control
`control_expected`, marcado con `uses_expected=True` y excluido de las comparaciones.

Tres clases:
- `trivial`: no mira el inventario. Solo usa lo que el modelo ve en el enunciado.
- `azar`: como `trivial`, con una eleccion al azar reproducible por instancia.
- `error_razonable`: SI usa el inventario, pero con un error plausible del razonamiento.
  No mide azar: mide si el acierto del modelo se puede explicar por ese error.

Estas reglas evaluan solo el texto final. En la condicion `tools` un modelo necesita ademas
la evidencia de las llamadas, de modo que la comparacion le es desfavorable al modelo.
"""
from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, replace
from typing import Any, Callable, Iterable, Sequence

from inventory_harness.schema import Instance, InventoryRecord
from inventory_harness.solver import solve
from inventory_harness.verifier import verify_final_text

DEFAULT_RANDOM_SEED = 2026


def _requested(instance: Instance) -> int:
    return sum(line.quantity for order in instance.orders for line in order.lines)


def format_answer(family: str, answer: dict[str, Any]) -> str:
    """Bloque <answer> canonico para un resultado con la forma de `expected`."""
    if family == "availability":
        fields = [
            ("alcanza", "si" if answer["can_fulfill"] else "no"),
            ("faltan", answer["missing_units"]),
        ]
    elif family == "selection":
        fields = [
            ("sucursal", answer["location_id"]),
            ("cubiertas", answer["covered_units"]),
            ("pendientes", answer["pending_units"]),
        ]
    elif family == "composition":
        fields = []
        for order_id, result in answer["orders"].items():
            fields.append((f"{order_id}_atendidas", result["covered_units"]))
            fields.append((f"{order_id}_pendientes", result["pending_units"]))
        fields.append(("total_pendientes", answer["total_pending"]))
    else:
        raise ValueError(f"familia desconocida: {family!r}")
    body = "\n".join(f"{key}: {value}" for key, value in fields)
    return f"<answer>\n{body}\n</answer>"


# --- Reglas: devuelven un resultado canonico, o None si no aplican a la familia -----


def _always_enough(instance: Instance, seed: int) -> dict[str, Any] | None:
    if instance.family != "availability":
        return None
    return {"can_fulfill": True, "missing_units": 0}


def _never_enough(instance: Instance, seed: int) -> dict[str, Any] | None:
    if instance.family != "availability":
        return None
    return {"can_fulfill": False, "missing_units": _requested(instance)}


def _blind_selection(instance: Instance, location: str) -> dict[str, Any]:
    # Sin mirar el stock, la unica cantidad defendible es "cubre todo".
    return {"location_id": location, "covered_units": _requested(instance), "pending_units": 0}


def _with_coverage(instance: Instance, location: str) -> dict[str, Any]:
    """Cobertura real de una sucursal elegida sin comparar con las demas."""
    return solve(replace(instance, location_ids=(location,)))


def _first_location(instance: Instance, seed: int) -> dict[str, Any] | None:
    if instance.family != "selection":
        return None
    return _blind_selection(instance, instance.location_ids[0])


def _random_pick(instance: Instance, seed: int) -> str:
    # Semilla por texto: no depende de PYTHONHASHSEED ni del orden de las instancias.
    return random.Random(f"{seed}|{instance.id}").choice(list(instance.location_ids))


def _random_location(instance: Instance, seed: int) -> dict[str, Any] | None:
    if instance.family != "selection":
        return None
    return _blind_selection(instance, _random_pick(instance, seed))


def _first_location_counted(instance: Instance, seed: int) -> dict[str, Any] | None:
    if instance.family != "selection":
        return None
    return _with_coverage(instance, instance.location_ids[0])


def _random_location_counted(instance: Instance, seed: int) -> dict[str, Any] | None:
    if instance.family != "selection":
        return None
    return _with_coverage(instance, _random_pick(instance, seed))


def _everything_served(instance: Instance, seed: int) -> dict[str, Any] | None:
    if instance.family != "composition":
        return None
    orders = {
        order.order_id: {
            "covered_units": sum(line.quantity for line in order.lines),
            "pending_units": 0,
        }
        for order in instance.orders
    }
    return {"orders": orders, "total_pending": 0}


def _ignore_reserves(instance: Instance, seed: int) -> dict[str, Any] | None:
    inventory = tuple(
        InventoryRecord(r.product_id, r.location_id, r.physical_stock, 0)
        for r in instance.inventory
    )
    return solve(replace(instance, inventory=inventory))


def _no_discount(instance: Instance, seed: int) -> dict[str, Any] | None:
    if instance.family != "composition":
        return None
    orders: dict[str, dict[str, int]] = {}
    for order in instance.orders:
        orders.update(solve(replace(instance, orders=(order,)))["orders"])
    total = sum(result["pending_units"] for result in orders.values())
    return {"orders": orders, "total_pending": total}


def _control_expected(instance: Instance, seed: int) -> dict[str, Any] | None:
    return instance.expected


@dataclass(frozen=True)
class Baseline:
    name: str
    kind: str  # "trivial", "azar", "error_razonable" o "control"
    description: str
    rule: Callable[[Instance, int], dict[str, Any] | None]
    uses_inventory: bool = False
    uses_expected: bool = False


BASELINES: tuple[Baseline, ...] = (
    Baseline(
        "siempre_alcanza", "trivial", "Disponibilidad: siempre alcanza, 0 faltantes.", _always_enough
    ),
    Baseline(
        "nunca_alcanza",
        "trivial",
        "Disponibilidad: nunca alcanza, faltante igual a lo pedido.",
        _never_enough,
    ),
    Baseline(
        "primera_sucursal",
        "trivial",
        "Seleccion: primera sucursal candidata, declarando todo cubierto.",
        _first_location,
    ),
    Baseline(
        "sucursal_azar",
        "azar",
        "Seleccion: sucursal al azar con semilla, declarando todo cubierto.",
        _random_location,
    ),
    Baseline(
        "todo_atendido",
        "trivial",
        "Composicion: todos los pedidos atendidos, nada pendiente.",
        _everything_served,
    ),
    Baseline(
        "primera_sucursal_contada",
        "error_razonable",
        "Seleccion: primera sucursal, sin comparar, con su cobertura real.",
        _first_location_counted,
        uses_inventory=True,
    ),
    Baseline(
        "sucursal_azar_contada",
        "azar",
        "Seleccion: sucursal al azar con su cobertura real. Azar informado: lee el inventario.",
        _random_location_counted,
        uses_inventory=True,
    ),
    Baseline(
        "ignorar_reservas",
        "error_razonable",
        "Todas: usa physical_stock como si fuese disponible. Error razonable, no azar.",
        _ignore_reserves,
        uses_inventory=True,
    ),
    Baseline(
        "no_descontar_stock",
        "error_razonable",
        "Composicion: cada pedido ve el stock inicial. Error razonable, no azar.",
        _no_discount,
        uses_inventory=True,
    ),
    Baseline(
        "control_expected",
        "control",
        "Control positivo: formatea `expected`. Debe dar 100 %; no es una linea base.",
        _control_expected,
        uses_expected=True,
    ),
)


def answer_text(baseline: Baseline, instance: Instance, seed: int = DEFAULT_RANDOM_SEED) -> str | None:
    answer = baseline.rule(instance, seed)
    return None if answer is None else format_answer(instance.family, answer)


def evaluate_baselines(
    instances: Iterable[Instance],
    baselines: Sequence[Baseline] = BASELINES,
    seed: int = DEFAULT_RANDOM_SEED,
) -> list[dict[str, Any]]:
    """Acierto por regla × familia × dificultad. Solo filas donde la regla aplica."""
    tally: dict[tuple[str, str, str], list[int]] = defaultdict(lambda: [0, 0])
    instances = list(instances)
    for baseline in baselines:
        for instance in instances:
            text = answer_text(baseline, instance, seed)
            if text is None:
                continue
            counts = tally[(baseline.name, instance.family, instance.difficulty)]
            counts[0] += verify_final_text(text, instance).reward == 1.0
            counts[1] += 1
    by_name = {baseline.name: baseline for baseline in baselines}
    return [
        {
            "baseline": name,
            "clase": by_name[name].kind,
            "usa_inventario": by_name[name].uses_inventory,
            "usa_expected": by_name[name].uses_expected,
            "family": family,
            "difficulty": difficulty,
            "aciertos": wins,
            "n": n,
            "tasa": wins / n if n else None,
        }
        for (name, family, difficulty), (wins, n) in sorted(tally.items())
    ]


def best_by_cell(
    results: Iterable[dict[str, Any]], include_reasonable_errors: bool = False
) -> dict[tuple[str, str], dict[str, Any]]:
    """Mejor regla por (familia, dificultad). Nunca incluye controles.

    Por defecto solo las reglas que no leen el inventario, que son el piso de azar. Los
    errores razonables y el azar informado se comparan aparte.
    """
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for row in results:
        if row["usa_expected"] or row["tasa"] is None:
            continue
        if row["usa_inventario"] and not include_reasonable_errors:
            continue
        cell = (row["family"], row["difficulty"])
        if cell not in best or row["tasa"] > best[cell]["tasa"]:
            best[cell] = row
    return best
