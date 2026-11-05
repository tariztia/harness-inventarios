"""Solucionador: casos a mano y comparacion con implementaciones ingenuas."""
from __future__ import annotations

import random
from pathlib import Path

import pytest

from inventory_harness.generator import generate_instance
from inventory_harness.schema import DIFFICULTIES, Instance, InventoryRecord, Order, OrderLine
from inventory_harness.solver import solve


def make(family, stock, orders, location_ids=None):
    """stock: {(producto, sucursal): (fisico, reservado)}."""
    inventory = tuple(InventoryRecord(p, l, f, r) for (p, l), (f, r) in stock.items())
    if location_ids is None:
        location_ids = tuple(sorted({l for _, l in stock}))
    return Instance(
        id="x", seed=0, family=family, difficulty="easy", split="train", template_id="t",
        inventory=inventory, orders=tuple(orders),
        product_ids=tuple(sorted({p for p, _ in stock})), location_ids=location_ids,
        request="", expected={}, required_records=(),
    )


def order(order_id, lines, locations=()):
    return Order(order_id, tuple(OrderLine(p, q) for p, q in lines), tuple(locations))


# --- Disponibilidad -------------------------------------------------------


def test_availability_example_from_proposal():
    instance = make("availability", {("A", "S1"): (20, 11)}, [order("O1", [("A", 12)], ["S1"])])
    assert solve(instance) == {"can_fulfill": False, "missing_units": 3}


def test_availability_exact_boundary_is_fulfilled():
    instance = make("availability", {("P01", "S1"): (20, 8)}, [order("O1", [("P01", 12)], ["S1"])])
    assert solve(instance) == {"can_fulfill": True, "missing_units": 0}


def test_availability_sums_pending_over_lines_and_uses_only_given_location():
    stock = {
        ("P01", "S1"): (10, 7), ("P02", "S1"): (5, 5), ("P03", "S1"): (30, 0),
        ("P01", "S2"): (60, 0), ("P02", "S2"): (60, 0), ("P03", "S2"): (60, 0),
    }
    instance = make(
        "availability", stock,
        [order("O1", [("P01", 5), ("P02", 4), ("P03", 9)], ["S1"])],
    )
    assert solve(instance) == {"can_fulfill": False, "missing_units": 6}


# --- Seleccion ------------------------------------------------------------


def test_selection_uses_available_not_physical():
    stock = {("P01", "S1"): (30, 25), ("P01", "S2"): (9, 2)}
    instance = make("selection", stock, [order("O1", [("P01", 10)])])
    assert solve(instance) == {"location_id": "S2", "covered_units": 7, "pending_units": 3}


def test_selection_tie_goes_to_lowest_id():
    stock = {("P01", "S1"): (4, 4), ("P01", "S2"): (8, 1), ("P01", "S3"): (7, 0)}
    instance = make("selection", stock, [order("O1", [("P01", 9)])])
    assert solve(instance) == {"location_id": "S2", "covered_units": 7, "pending_units": 2}


def test_selection_tie_ignores_declared_order_and_compares_ids_numerically():
    stock = {("P01", "S2"): (5, 0), ("P01", "S10"): (5, 0)}
    instance = make(
        "selection", stock, [order("O1", [("P01", 5)])], location_ids=("S10", "S2")
    )
    assert solve(instance)["location_id"] == "S2"


def test_selection_caps_surplus_on_a_line():
    # S1 tiene mas disponible total, pero el exceso de P01 no cubre P02.
    stock = {
        ("P01", "S1"): (50, 0), ("P02", "S1"): (0, 0),
        ("P01", "S2"): (6, 0), ("P02", "S2"): (6, 0),
    }
    instance = make("selection", stock, [order("O1", [("P01", 6), ("P02", 6)])])
    assert solve(instance) == {"location_id": "S2", "covered_units": 12, "pending_units": 0}


# --- Composicion ----------------------------------------------------------


def test_composition_priority_and_discount():
    instance = make(
        "composition", {("P01", "S1"): (10, 4)},
        [order("O1", [("P01", 5)], ["S1"]), order("O2", [("P01", 5)], ["S1"])],
    )
    assert solve(instance) == {
        "orders": {
            "O1": {"covered_units": 5, "pending_units": 0},
            "O2": {"covered_units": 1, "pending_units": 4},
        },
        "total_pending": 4,
    }


def test_composition_later_order_gets_nothing():
    instance = make(
        "composition", {("P01", "S1"): (6, 0)},
        [order("O1", [("P01", 9)], ["S1"]), order("O2", [("P01", 3)], ["S1"])],
    )
    result = solve(instance)
    assert result["orders"]["O1"] == {"covered_units": 6, "pending_units": 3}
    assert result["orders"]["O2"] == {"covered_units": 0, "pending_units": 3}
    assert result["total_pending"] == 6


def test_composition_cascade_takes_first_location_then_next():
    stock = {("P01", "S1"): (5, 2), ("P01", "S2"): (6, 2), ("P01", "S3"): (9, 0)}
    instance = make(
        "composition", stock,
        [
            order("O1", [("P01", 5)], ["S1", "S2"]),  # 3 de S1 y 2 de S2
            order("O2", [("P01", 3)], ["S2"]),  # solo quedan 2 en S2
            order("O3", [("P01", 12)], ["S2", "S1", "S3"]),  # S2 y S1 agotadas
        ],
    )
    assert solve(instance) == {
        "orders": {
            "O1": {"covered_units": 5, "pending_units": 0},
            "O2": {"covered_units": 2, "pending_units": 1},
            "O3": {"covered_units": 9, "pending_units": 3},
        },
        "total_pending": 4,
    }


def test_composition_cascade_order_is_the_declared_one():
    stock = {("P01", "S1"): (4, 0), ("P01", "S2"): (4, 0)}
    instance = make(
        "composition", stock,
        [order("O1", [("P01", 3)], ["S2", "S1"]), order("O2", [("P01", 2)], ["S2"])],
    )
    # O1 agota casi toda S2, asi que O2 queda corto aunque S1 este intacta.
    assert solve(instance)["orders"]["O2"] == {"covered_units": 1, "pending_units": 1}


def test_composition_lines_of_one_order_share_stock_in_sequence():
    stock = {("P01", "S1"): (7, 0), ("P02", "S1"): (2, 1)}
    instance = make(
        "composition", stock,
        [order("O1", [("P01", 4), ("P02", 3)], ["S1"]), order("O2", [("P01", 4)], ["S1"])],
    )
    assert solve(instance) == {
        "orders": {
            "O1": {"covered_units": 5, "pending_units": 2},
            "O2": {"covered_units": 3, "pending_units": 1},
        },
        "total_pending": 3,
    }


def test_unknown_family_raises():
    with pytest.raises(ValueError):
        solve(make("filtering", {("P01", "S1"): (1, 0)}, []))


def test_solver_does_not_depend_on_generator():
    source = Path(solve.__code__.co_filename).read_text(encoding="utf-8")
    assert "generator" not in source.split('"""', 2)[2]


# --- Implementaciones ingenuas --------------------------------------------


def brute_force_composition(instance):
    """Asigna unidad por unidad, recorriendo la ruta completa para cada una."""
    units = {}
    for record in instance.inventory:
        units[(record.product_id, record.location_id)] = max(
            0, record.physical_stock - record.reserved_stock
        )
    orders = {}
    for current in instance.orders:
        covered = pending = 0
        for line in current.lines:
            for _ in range(line.quantity):
                source = next(
                    (l for l in current.location_ids if units[(line.product_id, l)] > 0),
                    None,
                )
                if source is None:
                    pending += 1
                else:
                    units[(line.product_id, source)] -= 1
                    covered += 1
        orders[current.order_id] = {"covered_units": covered, "pending_units": pending}
    return {
        "orders": orders,
        "total_pending": sum(o["pending_units"] for o in orders.values()),
    }


def brute_force_availability(instance):
    current = instance.orders[0]
    location = current.location_ids[0]
    missing = 0
    for line in current.lines:
        record = next(
            r for r in instance.inventory
            if r.product_id == line.product_id and r.location_id == location
        )
        pile = ["x"] * (record.physical_stock - record.reserved_stock)
        for _ in range(line.quantity):
            if pile:
                pile.pop()
            else:
                missing += 1
    return {"can_fulfill": missing == 0, "missing_units": missing}


def brute_force_selection(instance):
    current = instance.orders[0]
    requested = sum(line.quantity for line in current.lines)
    scored = []
    for location in instance.location_ids:
        coverage = 0
        for line in current.lines:
            record = next(
                r for r in instance.inventory
                if r.product_id == line.product_id and r.location_id == location
            )
            coverage += sum(
                1 for unit in range(line.quantity)
                if unit < record.physical_stock - record.reserved_stock
            )
        scored.append((-coverage, int(location[1:]), location))
    coverage, _, location = sorted(scored)[0]
    return {
        "location_id": location,
        "covered_units": -coverage,
        "pending_units": requested + coverage,
    }


BRUTE = {
    "availability": brute_force_availability,
    "selection": brute_force_selection,
    "composition": brute_force_composition,
}


def random_composition(rng):
    """Instancia sin filtros de degeneracion, con stock cero y reservas totales."""
    products = [f"P{i:02d}" for i in range(1, rng.randint(2, 4))]
    locations = [f"S{i}" for i in range(1, rng.randint(2, 5))]
    stock = {}
    for p in products:
        for l in locations:
            physical = rng.choice([0, rng.randint(1, 30)])
            stock[(p, l)] = (physical, rng.choice([0, physical, rng.randint(0, physical)]))
    orders = []
    for index in range(rng.randint(1, 6)):
        lines = [(p, rng.randint(1, 25)) for p in rng.sample(products, rng.randint(1, len(products)))]
        route = rng.sample(locations, rng.randint(1, len(locations)))
        orders.append(order(f"O{index + 1}", lines, route))
    return make("composition", stock, orders)


def test_composition_matches_brute_force_on_unfiltered_random_instances():
    rng = random.Random(7)
    for _ in range(2000):
        instance = random_composition(rng)
        assert solve(instance) == brute_force_composition(instance)


@pytest.mark.parametrize("family", sorted(BRUTE))
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_solver_matches_brute_force_on_generated_instances(family, difficulty):
    for seed in range(150):
        instance = generate_instance(family, difficulty, "train", seed)
        assert solve(instance) == BRUTE[family](instance), instance.id
