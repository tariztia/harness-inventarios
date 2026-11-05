"""Solucionador de referencia: calcula `expected` segun docs/reglas_negocio.md.

Independiente del generador: no importa nada de el. Solo lee `family`,
`inventory`, `orders` y `location_ids`, por lo que acepta cualquier objeto con
esos atributos (`Instance` o una vista equivalente).

La lectura del stock es perezosa a proposito: un registro solo se consulta si
la regla lo necesita (en cascada, una sucursal posterior no se lee cuando la
linea ya quedo cubierta). Si falta un registro necesario, lanza `KeyError`.
"""
from __future__ import annotations

from typing import Any


def solve(instance: Any) -> dict[str, Any]:
    """Devuelve `expected` con la forma de docs/contrato.md para la familia dada."""
    if instance.family == "availability":
        return _solve_availability(instance)
    if instance.family == "selection":
        return _solve_selection(instance)
    if instance.family == "composition":
        return _solve_composition(instance)
    raise ValueError(f"familia desconocida: {instance.family!r}")


def _available_by_pair(instance: Any) -> dict[tuple[str, str], int]:
    return {(r.product_id, r.location_id): r.available for r in instance.inventory}


def _single_order(instance: Any) -> Any:
    if len(instance.orders) != 1:
        raise ValueError(f"{instance.family} requiere exactamente 1 pedido")
    return instance.orders[0]


def _solve_availability(instance: Any) -> dict[str, Any]:
    order = _single_order(instance)
    if len(order.location_ids) != 1:
        raise ValueError("availability requiere exactamente 1 sucursal")
    location = order.location_ids[0]
    available = _available_by_pair(instance)
    missing = 0
    for line in order.lines:
        covered = min(line.quantity, available[(line.product_id, location)])
        missing += line.quantity - covered
    return {"can_fulfill": missing == 0, "missing_units": missing}


def _location_rank(location_id: str) -> tuple[int, str]:
    """Orden natural de IDs: S2 antes que S10."""
    digits = location_id.lstrip("Ss")
    return (int(digits), location_id) if digits.isdigit() else (10**9, location_id)


def _solve_selection(instance: Any) -> dict[str, Any]:
    order = _single_order(instance)
    available = _available_by_pair(instance)
    requested = sum(line.quantity for line in order.lines)
    best_location, best_coverage = None, -1
    for location in sorted(instance.location_ids, key=_location_rank):
        coverage = sum(
            min(line.quantity, available[(line.product_id, location)])
            for line in order.lines
        )
        # Estricto: ante empate se conserva la primera, que tiene el ID menor.
        if coverage > best_coverage:
            best_location, best_coverage = location, coverage
    return {
        "location_id": best_location,
        "covered_units": best_coverage,
        "pending_units": requested - best_coverage,
    }


def _solve_composition(instance: Any) -> dict[str, Any]:
    remaining = _available_by_pair(instance)
    results: dict[str, dict[str, int]] = {}
    total_pending = 0
    for order in instance.orders:
        covered = pending = 0
        for line in order.lines:
            unassigned = line.quantity
            for location in order.location_ids:
                if unassigned == 0:
                    break
                pair = (line.product_id, location)
                taken = min(unassigned, remaining[pair])
                remaining[pair] -= taken
                unassigned -= taken
            covered += line.quantity - unassigned
            pending += unassigned
        results[order.order_id] = {"covered_units": covered, "pending_units": pending}
        total_pending += pending
    return {"orders": results, "total_pending": total_pending}
