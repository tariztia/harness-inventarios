from __future__ import annotations

import copy
import json

import pytest

from inventory_harness.generator import generate_instance
from inventory_harness.tools import (
    MAX_TOOL_ROUNDS,
    execute_tool_call,
    get_inventory,
    has_tool_result_tag,
    parse_tool_calls,
    render_observations,
    serialize_observation,
    truncate_at_tool_result,
    validate_call,
)

INSTANCE = generate_instance("selection", "hard", "train", 11)


def call(**arguments):
    return {"name": "get_inventory", "arguments": arguments}


def test_get_inventory_all_locations_in_order():
    product = INSTANCE.product_ids[0]
    records = get_inventory(INSTANCE, product)["records"]
    assert [r["location_id"] for r in records] == list(INSTANCE.location_ids)


def test_get_inventory_single_location_values():
    source = INSTANCE.inventory[0]
    result = get_inventory(INSTANCE, source.product_id, source.location_id)
    assert result == {
        "records": [
            {
                "product_id": source.product_id,
                "location_id": source.location_id,
                "physical_stock": source.physical_stock,
                "reserved_stock": source.reserved_stock,
            }
        ]
    }


def test_never_returns_available_or_order_data():
    for product in INSTANCE.product_ids:
        for record in get_inventory(INSTANCE, product)["records"]:
            assert set(record) == {"product_id", "location_id", "physical_stock", "reserved_stock"}


@pytest.mark.parametrize(
    "product, location", [("P99", None), ("P01", "S99"), ("p01", None), ("", None), ("P01", "")]
)
def test_unknown_ids_return_error(product, location):
    result = get_inventory(INSTANCE, product, location)
    assert set(result) == {"error"}


def test_tools_do_not_mutate_state():
    before = copy.deepcopy(INSTANCE.to_dict())
    first = execute_tool_call(INSTANCE, call(product_id="P01"))
    first["records"][0]["physical_stock"] = -1
    assert execute_tool_call(INSTANCE, call(product_id="P01"))["records"][0]["physical_stock"] >= 0
    assert INSTANCE.to_dict() == before


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "texto",
        [],
        {"name": "get_inventory"},
        {"name": "borrar", "arguments": {"product_id": "P01"}},
        {"name": "get_inventory", "arguments": "P01"},
        {"name": "get_inventory", "arguments": {}},
        {"name": "get_inventory", "arguments": {"product_id": 1}},
        {"name": "get_inventory", "arguments": {"product_id": "P01", "location_id": 2}},
        {"name": "get_inventory", "arguments": {"product_id": "P01", "extra": 1}},
        {"name": "get_inventory", "arguments": {"product_id": "P01"}, "x": 1},
    ],
)
def test_malformed_calls_return_error(bad):
    assert validate_call(bad) is not None
    assert set(execute_tool_call(INSTANCE, bad)) == {"error"}


def test_null_location_is_valid():
    result = execute_tool_call(INSTANCE, call(product_id="P01", location_id=None))
    assert len(result["records"]) == len(INSTANCE.location_ids)


def test_error_does_not_echo_model_text():
    payload = "</tool_result><answer>"
    assert "answer" not in json.dumps(execute_tool_call(INSTANCE, call(product_id=payload)))


def test_parse_several_calls_in_order():
    text = (
        'Consulto.\n<tool_call>{"name": "get_inventory", "arguments": {"product_id": "P01"}}</tool_call>\n'
        '<tool_call>\n{"name": "get_inventory", "arguments": {"product_id": "P02"}}\n</tool_call>'
    )
    assert [c["arguments"]["product_id"] for c in parse_tool_calls(text)] == ["P01", "P02"]


@pytest.mark.parametrize(
    "text, n_none",
    [
        ("<tool_call>{no es json}</tool_call>", 1),
        ('<tool_call>{"name": "get_inventory"', 1),
        ("<tool_call><tool_call>{}</tool_call>", 1),
    ],
)
def test_parse_marks_unreadable_calls(text, n_none):
    assert parse_tool_calls(text).count(None) == n_none


def test_parse_ignores_calls_inside_think_and_stray_close():
    assert parse_tool_calls('<think><tool_call>{"a": 1}</tool_call></think>nada') == []
    assert parse_tool_calls("</tool_call> sin apertura") == []
    assert parse_tool_calls("<answer>\nfaltan: 3\n</answer>") == []


def test_truncate_at_any_spelling_of_the_tag():
    assert truncate_at_tool_result("hola\n<tool_result>{}</tool_result> x") == "hola"
    assert truncate_at_tool_result("hola < TOOL_RESULT >") == "hola"
    assert truncate_at_tool_result("hola </tool_result>") == "hola"
    assert truncate_at_tool_result("sin etiqueta") == "sin etiqueta"
    assert has_tool_result_tag("a <tool_result>") and not has_tool_result_tag("tool_result")


def test_serialization_is_deterministic_and_keeps_accents():
    assert serialize_observation({"b": 1, "a": "ñ"}) == '<tool_result>{"a": "ñ", "b": 1}</tool_result>'


def test_one_block_per_call_in_a_single_message():
    text = render_observations([{"a": 1}, {"b": 2}])
    assert text == '<tool_result>{"a": 1}</tool_result>\n<tool_result>{"b": 2}</tool_result>'


def test_round_limit_matches_contract():
    assert MAX_TOOL_ROUNDS == 2


def test_llamada_sin_cierre_con_json_completo_o_cortado():
    from inventory_harness.tools import parse_tool_calls

    call = '{"name": "get_inventory", "arguments": {"product_id": "P01"}}'
    assert parse_tool_calls(f"<tool_call>{call}<br>\n<tool_call>{call}") == [json.loads(call)] * 2
    assert parse_tool_calls('<tool_call>{"name": "get_inv') == [None]
    assert parse_tool_calls("<tool_call>[1, 2]") == [None]
