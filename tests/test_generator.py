"""Generador: determinismo, invariantes, degeneracion, duplicados y texto."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

import pytest

import inventory_harness.generator as generator
from inventory_harness.generator import (
    dataset_stats,
    fingerprint,
    generate_dataset,
    generate_instance,
    templates_for_split,
)
from inventory_harness.schema import DIFFICULTIES, FAMILIES, SPLITS, Instance
from inventory_harness.solver import solve
from inventory_harness.templates import TEMPLATES

ROOT = Path(__file__).resolve().parents[1]
CELLS = [(f, d) for f in FAMILIES for d in DIFFICULTIES]
CONFIG = {"n_per_cell": {"train": 40, "eval": 40, "test": 40}, "base_seed": 2026}
ID_RE = re.compile(r"\b[POS]\d+\b")


@pytest.fixture(scope="module")
def dataset():
    return generate_dataset(CONFIG)


@pytest.fixture(scope="module")
def stats(dataset):
    return dataset_stats(dataset)


# --- Determinismo ---------------------------------------------------------


@pytest.mark.parametrize("family,difficulty", CELLS)
def test_same_arguments_same_instance(family, difficulty):
    assert generate_instance(family, difficulty, "train", 11) == generate_instance(
        family, difficulty, "train", 11
    )


def test_arguments_change_the_instance():
    base = generate_instance("composition", "hard", "train", 1)
    assert base.inventory != generate_instance("composition", "hard", "train", 2).inventory
    assert base.inventory != generate_instance("composition", "hard", "eval", 1).inventory


def test_dataset_is_deterministic_across_processes():
    code = (
        "import hashlib, json\n"
        "from inventory_harness.generator import generate_dataset\n"
        "rows = [i.to_dict() for i in generate_dataset("
        "{'n_per_cell': {'train': 3, 'eval': 3, 'test': 3}, 'base_seed': 5})]\n"
        "print(hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest())\n"
    )
    digests = set()
    for hash_seed in ("1", "2", "31337"):
        env = {**os.environ, "PYTHONHASHSEED": hash_seed, "PYTHONPATH": str(ROOT / "src")}
        result = subprocess.run(
            [sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True
        )
        digests.add(result.stdout.strip())
    local = [
        i.to_dict()
        for i in generate_dataset({"n_per_cell": {"train": 3, "eval": 3, "test": 3}, "base_seed": 5})
    ]
    digests.add(hashlib.sha256(json.dumps(local, sort_keys=True).encode()).hexdigest())
    assert len(digests) == 1


# --- Invariantes ----------------------------------------------------------


def test_counts_and_ids(dataset):
    assert len(dataset) == 9 * 3 * 40
    assert len({i.id for i in dataset}) == len(dataset)
    for instance in dataset:
        assert re.fullmatch(
            rf"{instance.split}_{instance.family}_{instance.difficulty}_\d{{4}}", instance.id
        )


def test_inventory_is_complete_and_valid(dataset):
    for instance in dataset:
        pairs = [(r.product_id, r.location_id) for r in instance.inventory]
        assert len(pairs) == len(set(pairs))
        assert set(pairs) == {(p, l) for p in instance.product_ids for l in instance.location_ids}
        for record in instance.inventory:
            assert 0 <= record.reserved_stock <= record.physical_stock <= generator.MAX_STOCK


def test_order_ids_and_quantities(dataset):
    for instance in dataset:
        assert [o.order_id for o in instance.orders] == [
            f"O{n + 1}" for n in range(len(instance.orders))
        ]
        for order in instance.orders:
            products = [line.product_id for line in order.lines]
            assert len(products) == len(set(products))
            assert all(1 <= line.quantity <= 60 for line in order.lines)
            assert set(products) <= set(instance.product_ids)
            assert set(order.location_ids) <= set(instance.location_ids)


def test_difficulty_table(dataset):
    for i in dataset:
        n_lines = len(i.orders[0].lines)
        k = len(i.location_ids)
        if i.family == "availability":
            assert len(i.orders) == 1 and len(i.orders[0].location_ids) == 1
            assert n_lines in {"easy": {1}, "medium": {2}, "hard": {3, 4}}[i.difficulty]
        elif i.family == "selection":
            assert len(i.orders) == 1 and i.orders[0].location_ids == ()
            assert n_lines in {"easy": {1}, "medium": {2}, "hard": {3, 4}}[i.difficulty]
            assert k in {"easy": {2, 3}, "medium": {3}, "hard": {4, 5}}[i.difficulty]
        else:
            products = {line.product_id for o in i.orders for line in o.lines}
            assert len(i.orders) in {"easy": {2}, "medium": {3}, "hard": {4, 5}}[i.difficulty]
            assert len(products) == {"easy": 1, "medium": 2, "hard": 3}[i.difficulty]
            assert k in {"easy": {1}, "medium": {1, 2}, "hard": {2, 3}}[i.difficulty]
            routes = [len(o.location_ids) for o in i.orders]
            if i.difficulty == "hard":
                assert max(routes) > 1
            else:
                assert max(routes) == 1


def test_expected_equals_solve(dataset):
    for instance in dataset:
        assert instance.expected == solve(instance), instance.id


def test_round_trip_through_json(dataset):
    for instance in dataset[::17]:
        assert Instance.from_dict(json.loads(json.dumps(instance.to_dict()))) == instance


def test_required_records_are_sufficient_and_minimal(dataset):
    for instance in dataset:
        required = set(instance.required_records)
        assert len(required) == len(instance.required_records)
        kept = tuple(
            r for r in instance.inventory if (r.product_id, r.location_id) in required
        )
        assert solve(replace(instance, inventory=kept)) == instance.expected
        for index in range(len(kept)):
            without_one = kept[:index] + kept[index + 1 :]
            with pytest.raises(KeyError):
                solve(replace(instance, inventory=without_one))


def test_complexity_fields(dataset):
    keys = {"n_records", "n_operations", "n_entities", "dependency_depth", "n_required_calls"}
    for instance in dataset:
        complexity = instance.complexity
        assert set(complexity) == keys
        assert all(isinstance(v, int) and v > 0 for v in complexity.values())
        assert complexity["n_records"] == len(instance.required_records)
        assert complexity["n_required_calls"] == len({p for p, _ in instance.required_records})


def test_complexity_on_small_cases():
    easy = generate_instance("availability", "easy", "train", 0)
    assert easy.complexity == {
        "n_records": 1, "n_operations": 3, "n_entities": 3,
        "dependency_depth": 3, "n_required_calls": 1,
    }
    composition = generate_instance("composition", "easy", "train", 0)
    # 1 resta, 2 pasos (min + descuento cada uno), 1 suma: disp -> O1 -> O2 -> total.
    assert composition.complexity["n_operations"] == 6
    assert composition.complexity["dependency_depth"] == 4


def _program_tail(instance):
    expected = instance.expected
    if instance.family == "availability":
        answer = "si" if expected["can_fulfill"] else "no"
        return f"=> alcanza={answer}, faltan={expected['missing_units']}"
    if instance.family == "selection":
        return f"=> sucursal={expected['location_id']}, cubiertas={expected['covered_units']}"
    rows = ", ".join(
        f"{o}={v['covered_units']}/{v['pending_units']}" for o, v in expected["orders"].items()
    )
    return f"=> {rows}, total_pendientes={expected['total_pending']}"


def test_solution_program_trace_agrees_with_solver(dataset):
    """La traza del generador es una implementacion aparte de las reglas."""
    for instance in dataset:
        last = instance.solution_program.splitlines()[-1]
        assert last.startswith(_program_tail(instance)), instance.id
        if instance.family == "selection":
            assert last.endswith(f"={instance.expected['pending_units']}")


# --- Splits y plantillas --------------------------------------------------


def test_splits_are_disjoint(dataset):
    by_split = defaultdict(set)
    seeds = defaultdict(set)
    for instance in dataset:
        by_split[instance.split].add(fingerprint(instance))
        seeds[instance.split].add(instance.seed)
    for a, b in (("train", "eval"), ("train", "test"), ("eval", "test")):
        assert not by_split[a] & by_split[b]
        assert not seeds[a] & seeds[b]


def test_no_duplicates_anywhere(dataset):
    assert len({fingerprint(i) for i in dataset}) == len(dataset)


def test_fingerprint_ignores_irrelevant_differences():
    instance = generate_instance("availability", "medium", "train", 3)
    required = set(instance.required_records)
    changed = tuple(
        r if (r.product_id, r.location_id) in required else replace(r, physical_stock=59, reserved_stock=1)
        for r in instance.inventory
    )
    reordered = replace(instance.orders[0], lines=instance.orders[0].lines[::-1])
    twin = replace(instance, inventory=changed, orders=(reordered,), template_id="otra", request="x")
    assert fingerprint(twin) == fingerprint(instance)
    more = replace(
        reordered, lines=(replace(reordered.lines[0], quantity=reordered.lines[0].quantity + 1),
                          *reordered.lines[1:])
    )
    assert fingerprint(replace(instance, orders=(more,))) != fingerprint(instance)


def test_fingerprint_renames_products_in_composition():
    instance = generate_instance("composition", "easy", "train", 3)
    rename = lambda p: "P09" if p == "P01" else p  # noqa: E731
    inventory = tuple(replace(r, product_id=rename(r.product_id)) for r in instance.inventory)
    orders = tuple(
        replace(o, lines=tuple(replace(l, product_id=rename(l.product_id)) for l in o.lines))
        for o in instance.orders
    )
    required = tuple((rename(p), l) for p, l in instance.required_records)
    twin = replace(instance, inventory=inventory, orders=orders, required_records=required)
    assert fingerprint(twin) == fingerprint(instance)


def test_id_does_not_reveal_the_answer(dataset):
    rows = [i for i in dataset if i.family == "availability"]
    even_ids = [i for i in rows if int(i.id[-4:]) % 2 == 0]
    rate = sum(i.expected["can_fulfill"] for i in even_ids) / len(even_ids)
    assert 0.4 <= rate <= 0.6
    assert all(str(i.seed) not in i.id for i in rows)


def test_duplicates_are_replaced_keeping_counts(monkeypatch):
    real = generator.generate_instance
    calls = defaultdict(int)

    def collapsing(family, difficulty, split, seed):
        # Las primeras llamadas de cada celda repiten la misma instancia.
        calls[(family, difficulty, split)] += 1
        forced = 0 if calls[(family, difficulty, split)] <= 4 else seed
        return replace(real(family, difficulty, "train", forced), split=split, seed=seed)

    monkeypatch.setattr(generator, "generate_instance", collapsing)
    rows = generator.generate_dataset({"n_per_cell": {"train": 3}, "base_seed": 1})
    assert len(rows) == 9 * 3
    assert len({fingerprint(i) for i in rows}) == len(rows)
    assert [i.id for i in rows[:3]] == [
        f"train_availability_easy_{n:04d}" for n in range(3)
    ]


def test_template_registry():
    for family in FAMILIES:
        templates = TEMPLATES[family]
        ids = [t.template_id for t in templates]
        assert len(templates) >= 4
        assert len(ids) == len(set(ids))
        assert sum(t.reserved for t in templates) >= 1
        assert sum(not t.reserved for t in templates) >= 3


def test_reserved_templates_only_in_test(dataset):
    reserved = {t.template_id for ts in TEMPLATES.values() for t in ts if t.reserved}
    used_in_test = set()
    for instance in dataset:
        if instance.template_id in reserved:
            assert instance.split == "test"
            used_in_test.add(instance.template_id)
    assert used_in_test == reserved
    for family in FAMILIES:
        assert not any(t.reserved for t in templates_for_split(family, "train"))
        assert any(t.reserved for t in templates_for_split(family, "test"))


def test_templates_are_structurally_distinct(dataset):
    sample = {}
    for instance in dataset:
        if instance.difficulty == "hard":
            sample.setdefault(instance.template_id, instance.request)
    assert len(sample) == sum(len(t) for t in TEMPLATES.values())
    skeletons = {ID_RE.sub("#", re.sub(r"\d+", "#", text)) for text in sample.values()}
    assert len(skeletons) == len(sample)
    first_words = {text.split()[0] for text in sample.values()}
    assert len(first_words) >= 8


# --- Texto del pedido -----------------------------------------------------


def test_request_names_all_ids_and_quantities(dataset):
    for instance in dataset:
        text = instance.request
        for order in instance.orders:
            assert re.search(rf"\b{order.order_id}\b", text), instance.id
            for line in order.lines:
                assert re.search(rf"\b{line.product_id}\b", text)
                assert re.search(rf"\b{line.quantity}\b", text)
            for location in order.location_ids:
                assert re.search(rf"\b{location}\b", text)
        if instance.family == "selection":
            for location in instance.location_ids:
                assert re.search(rf"\b{location}\b", text)


def test_request_numbers_are_only_order_quantities(dataset):
    """Quitando los IDs, toda cifra es una cantidad: ningun stock se filtra."""
    for instance in dataset:
        quantities = sorted(l.quantity for o in instance.orders for l in o.lines)
        numbers = sorted(int(n) for n in re.findall(r"\d+", ID_RE.sub("", instance.request)))
        assert numbers == quantities, instance.id


def test_request_with_stock_disjoint_from_quantities_does_not_leak(dataset):
    checked = 0
    for instance in dataset:
        quantities = {l.quantity for o in instance.orders for l in o.lines}
        values = {
            v for r in instance.inventory for v in (r.physical_stock, r.reserved_stock, r.available)
        } - quantities
        text = ID_RE.sub("", instance.request)
        for value in values:
            assert not re.search(rf"\b{value}\b", text), instance.id
        checked += bool(values)
        lowered = instance.request.lower()
        assert "reserv" not in lowered and "físico" not in lowered
    assert checked > 900


def test_selection_mentions_are_not_always_sorted(dataset):
    orders = [
        re.findall(r"\bS\d\b", i.request) for i in dataset if i.family == "selection"
    ]
    assert any(found != sorted(found) for found in orders)


# --- Degeneracion ---------------------------------------------------------


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_availability_rates(stats, difficulty):
    cell = stats["cells"][f"availability/{difficulty}"]
    assert 0.4 <= cell["can_fulfill_rate"] <= 0.6
    assert cell["ignore_reserves_changes_rate"] >= 0.35
    assert cell["ignore_reserves_flips_rate"] >= 0.2
    assert cell["deficit_equal_1_rate"] <= 0.25
    assert cell["deficit_mean"] >= 3


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_selection_rates(stats, difficulty):
    cell = stats["cells"][f"selection/{difficulty}"]
    assert 0.08 <= cell["tie_rate"] <= 0.25
    assert cell["physical_choice_differs_rate"] >= 0.5
    assert 0.4 <= cell["has_pending_rate"] <= 0.9
    shares = cell["winner_position_share"]
    assert max(shares.values()) <= 0.5
    assert shares["0"] <= 0.5 and len(shares) >= 2


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_composition_rates(stats, difficulty):
    cell = stats["cells"][f"composition/{difficulty}"]
    assert cell["shortage_rate"] >= 0.7
    assert cell["ignore_priority_changes_rate"] >= 0.7
    assert cell["no_discount_changes_rate"] >= 0.7
    assert cell["ignore_reserves_changes_rate"] >= 0.6
    if difficulty == "hard":
        assert cell["cascade_used_rate"] == 1.0


def test_cli_writes_expected_files(tmp_path):
    out = tmp_path / "ds"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_dataset.py"),
         "--n-per-cell", "2", "--base-seed", "9", "--out", str(out)],
        check=True, capture_output=True, text=True,
    )
    for split in SPLITS:
        lines = (out / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(lines) == 18
        assert Instance.from_dict(json.loads(lines[0])).split == split
    stats = json.loads((out / "stats.json").read_text(encoding="utf-8"))
    assert stats["total"] == 54
    assert "can_fulfill_rate" in stats["cells"]["availability/easy"]
