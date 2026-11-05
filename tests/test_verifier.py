from __future__ import annotations

import json
import random
import re
import sys
import time
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from adversarial_cases import AV_NO, B_AV_NO, B_COMP, B_SEL, CASES, COMP, KNOWN_LIMITATIONS, SEL  # noqa: E402

from inventory_harness.schema import Instance  # noqa: E402
from inventory_harness.verifier import AnswerParseError, parse_answer, verify_final_text  # noqa: E402


def make_instance(family: str, expected: dict[str, Any]) -> Instance:
    return Instance(
        id="caso",
        seed=0,
        family=family,
        difficulty="easy",
        split="test",
        template_id="t",
        inventory=(),
        orders=(),
        product_ids=(),
        location_ids=(),
        request="",
        expected=expected,
        required_records=(),
    )


AV = make_instance("availability", AV_NO)
SE = make_instance("selection", SEL)
CO = make_instance("composition", COMP)
VALID = [(AV, B_AV_NO), (SE, B_SEL), (CO, B_COMP)]


# ------------------------------------------------------------------- casos adversariales

_LIMITED = {entry["case_id"] for entry in KNOWN_LIMITATIONS if entry.get("case_id")}


def _params():
    params = []
    for case in CASES:
        marks = ()
        if case["id"] in _LIMITED:
            marks = (pytest.mark.xfail(strict=True, reason="limitacion conocida"),)
        params.append(pytest.param(case, id=case["id"], marks=marks))
    return params


@pytest.mark.parametrize("case", _params())
def test_adversarial_case(case):
    verdict = verify_final_text(case["text"], make_instance(case["family"], case["expected"]))
    assert (verdict.reward == 1.0) == case["should_pass"], verdict
    if case["should_pass"]:
        assert verdict.error_type == "ok"
    elif case["expected_error_type"] is not None:
        assert verdict.error_type == case["expected_error_type"], verdict


def test_adversarial_suite_shape():
    ids = [case["id"] for case in CASES]
    assert len(ids) == len(set(ids))
    assert len(CASES) >= 80
    assert {"availability", "selection", "composition"} <= {case["family"] for case in CASES}
    assert _LIMITED <= set(ids)
    assert {
        "equivalencias_validas", "parafrasis_correctas", "respuestas_parciales",
        "multiples_respuestas", "inyeccion_formato", "numeros_fuera_de_contexto", "homoglifos",
        "overflow_numerico", "copia_herramienta", "prompt_injection", "contradicciones",
        "falsos_positivos_contradiccion",
    } == {case["category"] for case in CASES}


# ------------------------------------------------------------------------- parse_answer


def test_parse_answer_canonical_shapes():
    assert parse_answer(B_AV_NO, "availability") == AV_NO
    assert parse_answer(B_SEL, "selection") == SEL
    assert parse_answer(B_COMP, "composition") == COMP


def test_parse_answer_detects_orders_from_keys():
    text = (
        "<answer>\no12_atendidas: 1\no12_pendientes: 2\nO3_atendidas: 3\nO3_pendientes: 4\n"
        "total_pendientes: 6\n</answer>"
    )
    parsed = parse_answer(text, "composition")
    assert list(parsed["orders"]) == ["O3", "O12"]
    assert parsed["orders"]["O12"] == {"covered_units": 1, "pending_units": 2}


def test_parse_answer_discards_think():
    with pytest.raises(AnswerParseError) as err:
        parse_answer(f"<think>{B_AV_NO}</think>", "availability")
    assert err.value.error_type == "no_answer_block"


@pytest.mark.parametrize(
    ("text", "family", "error_type"),
    [
        ("", "availability", "no_answer_block"),
        ("<answer>\nalcanza: no\n</answer>", "availability", "missing_field"),
        ("<answer>\nalcanza: no\nfaltan: 3\nx: 1\n</answer>", "availability", "unknown_field"),
        ("<answer>\nO0_atendidas: 1\nO0_pendientes: 1\ntotal_pendientes: 1\n</answer>", "composition", "unknown_field"),
        ("<answer>\nO01_atendidas: 1\nO01_pendientes: 1\ntotal_pendientes: 1\n</answer>", "composition", "unknown_field"),
        ("<answer>\nO1_atendidas: 1\nO01_atendidas: 1\n</answer>", "composition", "unknown_field"),
        ("<answer>\nalcanza: no\nfaltan: 3 o 4\n</answer>", "availability", "ambiguous_value"),
    ],
)
def test_parse_answer_error_types(text, family, error_type):
    with pytest.raises(AnswerParseError) as err:
        parse_answer(text, family)
    assert err.value.error_type == error_type


def test_parse_answer_rejects_unknown_family():
    with pytest.raises(ValueError):
        parse_answer(B_AV_NO, "otra")


# -------------------------------------------------------------------------------- Verdict


def test_verdict_for_correct_answer():
    verdict = verify_final_text(B_AV_NO, AV)
    assert verdict.reward == 1.0
    assert verdict.correct_final_answer
    assert not verdict.parser_error
    assert not verdict.contradictory_answer
    assert verdict.error_type == "ok"
    for name in ("valid_tool_call", "correct_tool_arguments", "retrieved_required_data",
                 "forged_observation", "tool_limit_exceeded"):
        assert getattr(verdict, name) is None


def test_verdict_reports_failed_fields_without_leaking_expected():
    text = "<answer>\nsucursal: S2\ncubiertas: 6\npendientes: 2\n</answer>"
    verdict = verify_final_text(text, SE)
    assert verdict.reward == 0.0
    assert verdict.error_type == "wrong_value"
    assert not verdict.parser_error
    assert not verdict.correct_final_answer
    assert verdict.details["field"] == "covered_units"
    assert verdict.details["failed_fields"] == ["covered_units", "pending_units"]
    assert "7" not in json.dumps(verdict.details)


def test_verdict_for_parse_error_names_the_field():
    verdict = verify_final_text("<answer>\nalcanza: no\nfaltan: 3 o 4\n</answer>", AV)
    assert verdict.parser_error
    assert verdict.error_type == "ambiguous_value"
    assert verdict.details["field"] == "faltan"


def test_verdict_for_contradiction():
    verdict = verify_final_text("Sí alcanza.\n\n" + B_AV_NO, AV)
    assert verdict.reward == 0.0
    assert verdict.contradictory_answer
    assert verdict.error_type == "contradiction"
    assert not verdict.correct_final_answer
    assert not verdict.parser_error
    assert verdict.details["block_matches_expected"] is True


def test_composition_requires_same_order_set():
    expected = {
        "orders": {"O1": {"covered_units": 5, "pending_units": 0},
                   "O3": {"covered_units": 0, "pending_units": 0}},
        "total_pending": 0,
    }
    text = (
        "<answer>\nO1_atendidas: 5\nO1_pendientes: 0\nO2_atendidas: 0\nO2_pendientes: 0\n"
        "total_pendientes: 0\n</answer>"
    )
    verdict = verify_final_text(text, make_instance("composition", expected))
    assert verdict.reward == 0.0
    assert verdict.error_type == "missing_field"
    assert verdict.details["field"] == "O3"


def test_bad_instance_does_not_raise():
    assert verify_final_text(B_AV_NO, make_instance("otra", {})).reward == 0.0
    assert verify_final_text(B_COMP, make_instance("composition", {})).reward == 0.0
    assert verify_final_text(B_AV_NO, None).reward == 0.0  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [None, 3, b"x", [], {}])
def test_non_string_text_does_not_raise(value):
    assert verify_final_text(value, AV).reward == 0.0


@pytest.mark.parametrize(
    "text",
    [
        "",
        " ",
        "\x00",
        "\ud800",
        "﻿",
        "<",
        "<answer",
        "</answer>",
        "<answer></answer></answer>",
        "<think>",
        "</think>",
        "a" * 1_000_000,
        "<answer>" * 30_000,
        "<think>" * 30_000,
        "</think>" * 30_000,
        "<" + " " * 150_000 + "x",
        "\n" * 150_000 + "<answer>",
        "[" * 100_000,
        "<answer>" + "{" * 100_000 + "</answer>",
        '<answer>{"a":' * 10_000,
        "<answer>" + '{"a":' * 30_000 + "</answer>",
        "<answer>\n" + "x: 1\n" * 30_000 + "</answer>",
        "<answer>\n" + "alcanza: " + "no " * 30_000 + "\n</answer>",
        "ﷺ" * 50_000,
        "́" * 100_000,
        "😀" * 50_000,
    ],
)
def test_arbitrary_text_is_safe_and_fast(text):
    start = time.perf_counter()
    verdict = verify_final_text(text, AV)
    assert time.perf_counter() - start < 3.0
    assert verdict.reward == 0.0
    assert verdict.error_type != "internal_error"
    json.dumps(verdict.to_dict())


def test_long_reasoning_before_block_is_still_valid():
    assert verify_final_text("razono mucho. " * 5000 + "\n\n" + B_AV_NO, AV).reward == 1.0


def test_oversized_text_is_rejected_without_raising():
    verdict = verify_final_text("a" * 300_000 + "\n\n" + B_AV_NO, AV)
    assert verdict.reward == 0.0
    assert verdict.parser_error


# ------------------------------------------------------------------------- prueba difusa

_ALPHABET = list("<>/{}[]():,.-+*x= \n\t\"'0123456789") + list("answerthinkalcanzafaltan") + [
    "<answer>", "</answer>", "<think>", "</think>", "alcanza:", "faltan:", "sí", "no", "3",
    "​", "́", "а", "３", "٣", "²", "\ud800", "\U0001d7d1", "```",
]


def _random_text(rng: random.Random) -> str:
    return "".join(rng.choice(_ALPHABET) for _ in range(rng.randrange(0, 120)))


def test_fuzz_random_strings_never_raise():
    rng = random.Random(20261103)
    for _ in range(3000):
        text = _random_text(rng)
        for instance in (AV, SE, CO):
            verdict = verify_final_text(text, instance)
            assert verdict.error_type != "internal_error", repr(text)
            assert verdict.reward in (0.0, 1.0)


def test_fuzz_mutations_of_valid_answers_never_raise():
    rng = random.Random(7)
    for _ in range(3000):
        instance, text = rng.choice(VALID)
        chars = list(text)
        for _ in range(rng.randrange(1, 6)):
            position = rng.randrange(len(chars))
            operation = rng.randrange(3)
            if operation == 0:
                chars[position] = rng.choice(_ALPHABET)
            elif operation == 1:
                chars.insert(position, rng.choice(_ALPHABET))
            else:
                del chars[position]
        mutated = "".join(chars)
        assert verify_final_text(mutated, instance).error_type != "internal_error", repr(mutated)


def test_fuzz_changing_a_digit_in_the_block_never_rewards():
    rng = random.Random(11)
    for instance, text in VALID:
        positions = [i for i, ch in enumerate(text) if ch.isdigit()]
        for position in positions:
            for _ in range(5):
                digit = rng.choice([d for d in "0123456789" if d != text[position]])
                mutated = text[:position] + digit + text[position + 1 :]
                assert verify_final_text(mutated, instance).reward == 0.0, mutated


_WORDS = {0: "cero", 1: "uno", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis",
          7: "siete", 8: "ocho", 9: "nueve", 10: "diez", 12: "doce", 21: "veintiuno"}
_RENDERINGS = (
    lambda n, r: str(n),
    lambda n, r: f"{n} unidades",
    lambda n, r: f"{n}.0",
    lambda n, r: f"{n + 7}-7",
    lambda n, r: f"{n}+0",
    lambda n, r: f"1*{n}",
    lambda n, r: f"{n} = {n}",
    lambda n, r: f"una fila de {n}",
    lambda n, r: f"{n} de P01 y 0 de P02",
    lambda n, r: _WORDS.get(n, str(n)),
)


def test_rendering_a_wrong_number_never_rewards():
    rng = random.Random(13)
    for _ in range(1500):
        instance, text = rng.choice(VALID)
        matches = list(re.finditer(r"(?<=: )\d+$", text, re.MULTILINE))
        match = rng.choice(matches)
        original = int(match.group())
        wrong = rng.choice([n for n in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 21) if n != original])
        rendered = rng.choice(_RENDERINGS)(wrong, rng)
        mutated = text[: match.start()] + rendered + text[match.end() :]
        assert verify_final_text(mutated, instance).reward == 0.0, mutated


def test_rendering_the_right_number_keeps_the_reward():
    # Control de la prueba anterior: las mismas formas si se aceptan con el valor correcto.
    for render in _RENDERINGS:
        for instance, text in VALID:
            for match in re.finditer(r"(?<=: )\d+$", text, re.MULTILINE):
                rendered = render(int(match.group()), None)
                mutated = text[: match.start()] + rendered + text[match.end() :]
                assert verify_final_text(mutated, instance).reward == 1.0, mutated


def test_known_limitations_have_a_description():
    for entry in KNOWN_LIMITATIONS:
        assert entry["description"]
