from __future__ import annotations

import re
from dataclasses import replace

import pytest

from inventory_harness.generator import generate_dataset, generate_instance
from inventory_harness.prompts import render_prompt, render_tool_reply
from inventory_harness.schema import DIFFICULTIES, FAMILIES
from inventory_harness.tools import execute_tool_call, parse_tool_calls
from inventory_harness.verifier import verify_final_text

CELLS = [(f, d) for f in FAMILIES for d in DIFFICULTIES]
CONDITIONS = ("tools", "visible")


def format_text(instance, condition):
    """Donde el modelo ve el formato: en tools llega con los resultados."""
    if condition == "tools":
        return render_tool_reply(instance, [], 2)
    return render_prompt(instance, condition)


def cell_instances():
    return [generate_instance(f, d, "train", seed) for f, d in CELLS for seed in (6, 7)]


@pytest.mark.parametrize("instance", cell_instances(), ids=lambda i: i.id)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_contains_required_sections(instance, condition):
    prompt = render_prompt(instance, condition)
    assert prompt.startswith(f"Caso: {instance.id}\n")
    assert instance.request in prompt
    for identifier in instance.product_ids + instance.location_ids:
        assert identifier in prompt
    assert "Disponible = stock físico − stock reservado" in prompt


@pytest.mark.parametrize("instance", cell_instances(), ids=lambda i: i.id)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_protected_fields_do_not_change_prompt(instance, condition):
    prompt = render_prompt(instance, condition)
    altered = replace(
        instance,
        seed=instance.seed + 1,
        expected={"x": 1},
        solution_program="otro",
        complexity={"n_records": 999},
        template_id="otra",
        required_records=(),
    )
    assert render_prompt(altered, condition) == prompt


@pytest.mark.parametrize("instance", cell_instances(), ids=lambda i: i.id)
def test_tools_prompt_has_no_stock(instance):
    prompt = render_prompt(instance, "tools")
    emptied = replace(
        instance,
        inventory=tuple(replace(r, physical_stock=59, reserved_stock=58) for r in instance.inventory),
    )
    assert render_prompt(emptied, "tools") == prompt
    assert "Inventario:" not in prompt


def test_protected_values_are_not_literally_present():
    instance = replace(generate_instance("availability", "easy", "train", 4), seed=918273645)
    for condition in CONDITIONS:
        prompt = render_prompt(instance, condition)
        assert "918273645" not in prompt
        assert instance.template_id not in prompt
        assert instance.solution_program not in prompt
        assert "complexity" not in prompt and "expected" not in prompt


@pytest.mark.parametrize("instance", cell_instances(), ids=lambda i: i.id)
def test_visible_shows_every_record_but_not_available(instance):
    prompt = render_prompt(instance, "visible")
    for r in instance.inventory:
        assert f"{r.product_id} | {r.location_id} | {r.physical_stock} | {r.reserved_stock}" in prompt
    assert "<tool_call>" not in prompt
    assert "get_inventory" not in prompt


@pytest.mark.parametrize("instance", cell_instances(), ids=lambda i: i.id)
def test_rules_and_format_are_shared_between_conditions(instance):
    tools, visible = (render_prompt(instance, c) for c in CONDITIONS)

    def section(prompt, start, end):
        return prompt[prompt.index(start) : prompt.index(end)]

    assert section(tools, "Reglas de negocio:", "Catálogo:") == section(
        visible, "Reglas de negocio:", "Catálogo:"
    )
    assert instance.request in tools and instance.request in visible
    final_format = visible[visible.index("Formato de respuesta:") :]
    assert render_tool_reply(instance, [], 2).endswith(final_format)


def answer_block(prompt):
    return prompt[prompt.index("<answer>") : prompt.index("</answer>") + len("</answer>")]


@pytest.mark.parametrize("instance", cell_instances(), ids=lambda i: i.id)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_copying_format_example_scores_zero(instance, condition):
    verdict = verify_final_text(answer_block(format_text(instance, condition)), instance)
    assert verdict.reward == 0.0
    assert verdict.parser_error


@pytest.mark.parametrize("instance", cell_instances(), ids=lambda i: i.id)
def test_copying_tool_example_returns_error(instance):
    prompt = render_prompt(instance, "tools")
    line = next(l for l in prompt.split("\n") if l.startswith("<tool_call>"))
    calls = parse_tool_calls(line)
    assert len(calls) == 1
    assert set(execute_tool_call(instance, calls[0])) == {"error"}


@pytest.mark.parametrize("family, keys", [
    ("availability", ["alcanza", "faltan"]),
    ("selection", ["sucursal", "cubiertas", "pendientes"]),
])
def test_exact_keys_simple(family, keys):
    block = answer_block(format_text(generate_instance(family, "easy", "train", 1), "tools"))
    assert re.findall(r"^([\w]+):", block, re.M) == keys


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_composition_shows_keys_of_its_orders(difficulty):
    instance = generate_instance("composition", difficulty, "train", 2)
    block = answer_block(format_text(instance, "tools"))
    expected = []
    for order in instance.orders:
        expected += [f"{order.order_id}_atendidas", f"{order.order_id}_pendientes"]
    assert re.findall(r"^([\w]+):", block, re.M) == expected + ["total_pendientes"]


def test_format_block_appears_once_and_asks_for_single_tag():
    prompt = format_text(generate_instance("selection", "easy", "train", 1), "tools")
    assert prompt.count("<answer>") == 1 and prompt.count("</answer>") == 1
    assert "una sola vez" in prompt
    assert "No las nombres" in prompt


def test_tools_prompt_states_protocol():
    prompt = render_prompt(generate_instance("availability", "easy", "train", 1), "tools")
    assert "solo las llamadas" in prompt
    assert "Máximo 2 rondas" in prompt
    assert "no puedes suponerlo" in prompt


@pytest.mark.parametrize("family", FAMILIES)
def test_tools_prompt_no_trae_el_formato_final(family):
    instance = generate_instance(family, "easy", "train", 1)
    prompt = render_prompt(instance, "tools")
    assert "<answer>" not in prompt and "razona paso a paso" not in prompt
    assert "<answer>" in render_tool_reply(instance, [], 1)


def test_otra_ronda_solo_se_ofrece_si_queda():
    instance = generate_instance("availability", "easy", "train", 1)
    assert "otra ronda" in render_tool_reply(instance, [], 1)
    assert "otra ronda" not in render_tool_reply(instance, [], 2)


def test_el_formato_no_usa_angulos_en_los_valores():
    for family in FAMILIES:
        block = answer_block(format_text(generate_instance(family, "easy", "train", 1), "visible"))
        assert not re.search(r":\s*<", block)


def test_cascade_rule_only_when_needed():
    hard = generate_instance("composition", "hard", "train", 1)
    easy = generate_instance("composition", "easy", "train", 1)
    assert "toma primero de la primera sucursal" in render_prompt(hard, "tools")
    assert "toma primero de la primera sucursal" not in render_prompt(easy, "tools")


def test_family_rules_do_not_mix():
    selection = render_prompt(generate_instance("selection", "easy", "train", 1), "tools")
    availability = render_prompt(generate_instance("availability", "easy", "train", 1), "tools")
    assert "gana el ID menor" in selection and "gana el ID menor" not in availability
    assert "orden de llegada" not in selection


def test_prompts_are_unique_across_dataset():
    instances = generate_dataset({"n_per_cell": {"train": 3, "eval": 3, "test": 3}, "base_seed": 5})
    prompts = {render_prompt(i, c) for i in instances for c in CONDITIONS}
    assert len(prompts) == 2 * len(instances)


def test_unknown_condition_raises():
    with pytest.raises(ValueError):
        render_prompt(generate_instance("selection", "easy", "train", 1), "otra")
