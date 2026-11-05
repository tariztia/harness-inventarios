"""Lineas base: reglas por instancia, sin `expected`, con valores conocidos a mano."""
from __future__ import annotations

import random
from dataclasses import replace

import pytest

from inventory_harness.baselines import (
    BASELINES,
    answer_text,
    best_by_cell,
    evaluate_baselines,
    format_answer,
)
from inventory_harness.generator import generate_dataset
from inventory_harness.schema import DIFFICULTIES, FAMILIES, Instance, InventoryRecord, Order, OrderLine
from inventory_harness.solver import solve
from inventory_harness.verifier import parse_answer, verify_final_text

BY_NAME = {baseline.name: baseline for baseline in BASELINES}


def instance_of(family, inventory, orders, locations, id_="i") -> Instance:
    draft = Instance(
        id=id_, seed=0, family=family, difficulty="easy", split="eval", template_id="t",
        inventory=tuple(InventoryRecord(*r) for r in inventory),
        orders=orders,
        product_ids=tuple(sorted({r[0] for r in inventory})),
        location_ids=locations,
        request="", expected={}, required_records=(),
    )
    return replace(draft, expected=solve(draft))


AVAILABILITY = instance_of(
    "availability",
    [("P01", "S1", 10, 4)],  # disponible 6, pedido 8: faltan 2. Sin reservas alcanza.
    (Order("O1", (OrderLine("P01", 8),), ("S1",)),),
    ("S1",),
)
SELECTION = instance_of(
    "selection",
    [("P01", "S1", 5, 0), ("P01", "S2", 9, 1), ("P01", "S3", 10, 9)],  # disponible 5, 8, 1
    (Order("O1", (OrderLine("P01", 10),)),),
    ("S1", "S2", "S3"),
)
COMPOSITION = instance_of(
    "composition",
    [("P01", "S1", 12, 2)],  # disponible 10; O1 toma 7; a O2 le quedan 3 de 6.
    (
        Order("O1", (OrderLine("P01", 7),), ("S1",)),
        Order("O2", (OrderLine("P01", 6),), ("S1",)),
    ),
    ("S1",),
)
ALL = (AVAILABILITY, SELECTION, COMPOSITION)


@pytest.fixture(scope="module")
def dataset():
    instances = generate_dataset({"n_per_cell": {"eval": 20}, "base_seed": 2026})
    return [i for i in instances if i.split == "eval"]


def parsed(name: str, instance: Instance) -> dict:
    text = answer_text(BY_NAME[name], instance)
    return parse_answer(text, instance.family)


def test_always_enough():
    assert parsed("siempre_alcanza", AVAILABILITY) == {"can_fulfill": True, "missing_units": 0}


def test_never_enough_declares_whole_order_missing():
    assert parsed("nunca_alcanza", AVAILABILITY) == {"can_fulfill": False, "missing_units": 8}


def test_first_location_is_blind():
    assert parsed("primera_sucursal", SELECTION) == {
        "location_id": "S1", "covered_units": 10, "pending_units": 0,
    }


def test_first_location_counted_uses_real_coverage():
    assert parsed("primera_sucursal_contada", SELECTION) == {
        "location_id": "S1", "covered_units": 5, "pending_units": 5,
    }


def test_random_location_is_reproducible_and_depends_on_instance():
    picks = {
        parsed("sucursal_azar", replace(SELECTION, id=f"caso{i}"))["location_id"] for i in range(30)
    }
    assert picks == {"S1", "S2", "S3"}
    assert answer_text(BY_NAME["sucursal_azar"], SELECTION) == answer_text(
        BY_NAME["sucursal_azar"], SELECTION
    )


def test_random_location_seed_changes_result(dataset):
    selection = [i for i in dataset if i.family == "selection"]
    a = [answer_text(BY_NAME["sucursal_azar"], i, seed=1) for i in selection]
    b = [answer_text(BY_NAME["sucursal_azar"], i, seed=2) for i in selection]
    assert a != b


def test_everything_served():
    assert parsed("todo_atendido", COMPOSITION) == {
        "orders": {
            "O1": {"covered_units": 7, "pending_units": 0},
            "O2": {"covered_units": 6, "pending_units": 0},
        },
        "total_pending": 0,
    }


def test_ignore_reserves_uses_physical_stock():
    assert parsed("ignorar_reservas", AVAILABILITY) == {"can_fulfill": True, "missing_units": 0}
    assert parsed("ignorar_reservas", SELECTION)["location_id"] == "S3"  # fisico 10, disponible 1
    assert parsed("ignorar_reservas", COMPOSITION)["total_pending"] == 1  # 12 fisico vs 13 pedido


def test_no_discount_gives_each_order_the_initial_stock():
    # Disponible 10: ambos pedidos caben por separado. La respuesta correcta deja 3 pendientes.
    answer = parsed("no_descontar_stock", COMPOSITION)
    assert answer["total_pending"] == 0
    assert answer["orders"]["O2"] == {"covered_units": 6, "pending_units": 0}
    assert COMPOSITION.expected["total_pending"] == 3


def test_rules_only_apply_to_their_family():
    assert answer_text(BY_NAME["siempre_alcanza"], SELECTION) is None
    assert answer_text(BY_NAME["primera_sucursal"], COMPOSITION) is None
    assert answer_text(BY_NAME["todo_atendido"], AVAILABILITY) is None
    assert answer_text(BY_NAME["no_descontar_stock"], SELECTION) is None


@pytest.mark.parametrize("instance", ALL, ids=lambda i: i.family)
def test_format_answer_is_accepted_by_the_verifier(instance):
    text = format_answer(instance.family, instance.expected)
    assert verify_final_text(text, instance).reward == 1.0


def test_only_the_control_reads_expected(dataset):
    """Con `expected` falso, toda regla no control debe producir el mismo texto."""
    scrambled = {"can_fulfill": None, "location_id": "S99", "orders": {}, "total_pending": -1}
    for instance in dataset:
        fake = replace(instance, expected=scrambled)
        for baseline in BASELINES:
            if not baseline.uses_expected:
                assert answer_text(baseline, instance) == answer_text(baseline, fake), baseline.name


def test_expected_flag_marks_exactly_the_control():
    assert [b.name for b in BASELINES if b.uses_expected] == ["control_expected"]
    assert all(b.kind == "control" for b in BASELINES if b.uses_expected)


def test_reasonable_errors_are_described_as_such():
    for name in ("ignorar_reservas", "no_descontar_stock"):
        assert BY_NAME[name].kind == "error_razonable"
        assert BY_NAME[name].uses_inventory


def test_control_scores_perfect_in_every_cell(dataset):
    rows = [r for r in evaluate_baselines(dataset) if r["baseline"] == "control_expected"]
    assert len(rows) == len(FAMILIES) * len(DIFFICULTIES)
    assert all(r["aciertos"] == r["n"] == 20 for r in rows)


def test_results_cover_family_by_difficulty(dataset):
    rows = evaluate_baselines(dataset)
    assert {(r["family"], r["difficulty"]) for r in rows} == {
        (f, d) for f in FAMILIES for d in DIFFICULTIES
    }
    selection = [r for r in rows if r["baseline"] == "sucursal_azar"]
    assert {r["family"] for r in selection} == {"selection"}
    assert all(0 <= r["tasa"] <= 1 for r in rows)


def test_results_do_not_depend_on_order(dataset):
    shuffled = list(dataset)
    random.Random(0).shuffle(shuffled)
    assert evaluate_baselines(dataset) == evaluate_baselines(shuffled)


def test_best_by_cell_excludes_control_and_inventory_rules(dataset):
    rows = evaluate_baselines(dataset)
    for row in best_by_cell(rows).values():
        assert row["baseline"] != "control_expected"
        assert not row["usa_inventario"]
    with_errors = best_by_cell(rows, include_reasonable_errors=True).values()
    assert all(row["baseline"] != "control_expected" for row in with_errors)
