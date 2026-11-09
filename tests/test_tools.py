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


P01_S2 = call(product_id="P01", location_id="S2")
P02_S2 = call(product_id="P02", location_id="S2")
P01_JSON = json.dumps(P01_S2)
P02_JSON = json.dumps(P02_S2)


# Formas copiadas de results/exploracion_prompt_corregido.
@pytest.mark.parametrize(
    "text",
    [
        P01_JSON,
        f"```json\n{json.dumps(P01_S2, indent=2)}\n```",
        f"1. Llamada para P01 en S2:\n`{P01_JSON}`",
        f".tool_call={P01_JSON}",
        f"tool_call = {P01_JSON}",
        f"tool_call {P01_JSON}",
        f"<think>razono</think>\n\n{P01_JSON}",
        'get_inventory(product_id="P01", location_id="S2")',
        "`get_inventory(product_id='P01', location_id='S2')`",
        'GET_INVENTORY(product_id="P01", location_id="S2")',
        'get_inventory("P01", "S2")',
        "get_inventory(P01, S2)",
        'get_inventory(location_id="S2", product_id="P01")',
        f"{P01_JSON}</tool_call>",
    ],
)
def test_llamada_sin_etiqueta_se_reconoce(text):
    assert parse_tool_calls(text) == [P01_S2]


def test_varias_llamadas_sin_etiqueta_en_orden():
    text = f'{P01_JSON}\nget_inventory(product_id="P02", location_id="S2")'
    assert parse_tool_calls(text) == [P01_S2, P02_S2]


def test_forma_python_sin_sucursal_o_con_none():
    assert parse_tool_calls('get_inventory("P01")') == [call(product_id="P01")]
    assert parse_tool_calls('get_inventory("P01", location_id=None)') == [
        call(product_id="P01", location_id=None)
    ]


def test_llamada_envuelta_en_otro_objeto():
    assert parse_tool_calls(json.dumps({"tool_call": P01_S2})) == [P01_S2]


def test_resultados_inventados_no_son_llamadas_pero_no_las_borran():
    text = f'{P01_JSON}\nResultado: {{"physical_stock": 50, "reserved_stock": 0}}'
    assert parse_tool_calls(text) == [P01_S2]


def test_etiqueta_valida_tiene_prioridad_sobre_lo_demas():
    tagged = f"<tool_call>{P01_JSON}</tool_call>"
    assert parse_tool_calls(f'get_inventory("P02", "S2")\n{tagged}') == [P01_S2]


@pytest.mark.parametrize(
    "text",
    [
        "get_inventory",
        "uso get_inventory para consultar",
        "get_inventory()",
        "get_inventory(product_id, location_id)",
        "def get_inventory(product_id, location_id=None):",
        'get_inventory(location_id="S2")',
        'get_inventory("P01", "S2", "S3")',
        'get_inventory("P01", product_id="P02")',
        'get_inventory(sku="P01")',
        'get_inventory("P01"',
        'borrar_todo("P01")',
        'mi_get_inventory("P01")',
        '{"name": "get_inv',
        '{"name": "get_inventory"}',
        '{"name": "borrar", "arguments": {"product_id": "P01"}}',
        '{"name": "Pedido O1", "products": [{"product_id": "P01"}]}',
        '{"physical_stock": 50, "reserved_stock": 0}',
        f"<think>{P01_JSON}</think>nada",
        f"<think>{P01_JSON}",
    ],
)
def test_lo_que_no_es_llamada_completa_no_cuenta(text):
    assert parse_tool_calls(text) == []


@pytest.mark.parametrize("call_text", [P01_JSON, 'get_inventory("P01", "S2")', "tool_call=" + P01_JSON])
def test_mensaje_con_answer_es_respuesta_final(call_text):
    assert parse_tool_calls(f"{call_text}\n<answer>\nfaltan: 3\n</answer>") == []


def test_argumentos_con_id_inexistente_se_ejecutan_y_dan_error():
    calls = parse_tool_calls('get_inventory("P99", "S9")')
    assert validate_call(calls[0]) is None
    assert set(execute_tool_call(INSTANCE, calls[0])) == {"error"}


def test_json_sin_etiqueta_con_argumentos_invalidos_es_llamada_invalida():
    calls = parse_tool_calls('{"name": "get_inventory", "arguments": {"sku": 1}}')
    assert len(calls) == 1 and validate_call(calls[0]) is not None


def test_cadena_muy_anidada_no_lanza():
    assert parse_tool_calls('{"a":' * 50000) == []
