from __future__ import annotations

import time

import pytest

from inventory_harness.numbers_es import (
    MAX_VALUE,
    ValueParseError,
    normalize_text,
    parse_arithmetic,
    parse_bool_value,
    parse_int_value,
    parse_location_value,
    parse_spanish_int,
)


def _spell(n: int) -> str:
    """Deletrea n (1..9999) sin reutilizar las tablas del parser."""
    units = "un dos tres cuatro cinco seis siete ocho nueve".split()
    teens = (
        "diez once doce trece catorce quince dieciséis diecisiete dieciocho diecinueve "
        "veinte veintiún veintidós veintitrés veinticuatro veinticinco veintiséis "
        "veintisiete veintiocho veintinueve"
    ).split()
    tens = "treinta cuarenta cincuenta sesenta setenta ochenta noventa".split()
    hundreds = (
        "ciento doscientos trescientos cuatrocientos quinientos seiscientos setecientos "
        "ochocientos novecientos"
    ).split()
    parts: list[str] = []
    thousands, rest = divmod(n, 1000)
    if thousands == 1:
        parts.append("mil")
    elif thousands:
        parts += [_spell(thousands), "mil"]
    if rest == 100:
        return " ".join(parts + ["cien"])
    if rest >= 100:
        parts.append(hundreds[rest // 100 - 1])
        rest %= 100
    if 10 <= rest < 30:
        parts.append(teens[rest - 10])
    elif rest >= 30:
        parts.append(tens[rest // 10 - 3])
        if rest % 10:
            parts += ["y", units[rest % 10 - 1]]
    elif rest:
        parts.append(units[rest - 1])
    return " ".join(parts)


def test_spanish_int_covers_every_value_up_to_9999():
    for n in range(1, 10000):
        assert parse_spanish_int(_spell(n)) == n, _spell(n)


@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("cero", 0),
        ("uno", 1),
        ("una", 1),
        ("veintiún", 21),
        ("veintiun", 21),
        ("veintiuna", 21),
        ("veintitrés", 23),
        ("VEINTITRES", 23),
        ("treinta y dos", 32),
        ("cien", 100),
        ("ciento cinco", 105),
        ("doscientas tres", 203),
        ("quinientas", 500),
        ("mil", 1000),
        ("un mil", 1000),
        ("mil doscientos", 1200),
        ("dos mil trescientos cuarenta y cinco", 2345),
        ("nueve mil novecientos noventa y nueve", 9999),
        ("cien mil", 100000),
    ],
)
def test_spanish_int_forms(text, value):
    assert parse_spanish_int(text) == value


@pytest.mark.parametrize(
    "text",
    ["", "hola", "veinte y uno", "treinta y", "y dos", "ciento", "cien dos", "mil mil",
     "uno mil", "dos tres", "treinta dos", "cero cero", "noventa y diez", "cero mil"],
)
def test_spanish_int_rejects_bad_grammar(text):
    assert parse_spanish_int(text) is None


@pytest.mark.parametrize(
    ("expr", "value"),
    [
        ("20-17", 3),
        ("2+1", 3),
        ("4*10", 40),
        ("4 x 10", 40),
        ("4x10", 40),
        ("4×10", 40),
        ("(2+1)*4", 12),
        ("2+3*4", 14),
        ("20 - 5 - 5", 10),
        ("-(3)+5", 2),
        ("treinta y dos - 2", 30),
    ],
)
def test_arithmetic(expr, value):
    assert parse_arithmetic(expr) == value


@pytest.mark.parametrize("expr", ["2**3", "--3", "2(3)", "(3", "3)", "()", "3+", "*3", "abc", "1;2"])
def test_arithmetic_rejects_malformed(expr):
    assert parse_arithmetic(expr) is None


def test_arithmetic_never_executes_python():
    assert parse_arithmetic("__import__('os').system('true')") is None


def test_arithmetic_is_bounded():
    with pytest.raises(ValueParseError):
        parse_arithmetic("9" * 8 + "*" + "9" * 8)
    with pytest.raises(ValueParseError):
        parse_arithmetic("+".join(["1"] * 100))


@pytest.mark.parametrize(
    ("raw", "value"),
    [
        ("3", 3),
        ("03", 3),
        ("3 unidades", 3),
        ("3 u.", 3),
        ("3 u", 3),
        ("3 uds.", 3),
        ("una unidad", 1),
        ("cero unidades", 0),
        ("faltan 3", 3),
        ("faltan 3 unidades", 3),
        ("3 en total", 3),
        ("tres", 3),
        ("Veintitrés", 23),
        ("3.0", 3),
        ("3.00", 3),
        ("3.", 3),
        ("0.000", 0),
        ("1.200", 1200),
        ("1.200.000", 1200000),
        ("20-17", 3),
        ("20 menos 17", 3),
        ("4*10", 40),
        ("4 x 10", 40),
        ("2+1", 3),
        ("20-17 = 3", 3),
        ("3 (tres)", 3),
        ("cuatro filas de 10", 40),
        ("4 cajas de 10 unidades", 40),
        ("una fila de 10", 10),
        ("1 de P01 y 2 de P02", 3),
        ("1 de P01, 2 de P02 y 3 de P03", 6),
        ("1 unidad de P01 y 2 unidades de P02", 3),
        ("20 adelante y 20 atrás", 40),
        ("treinta y dos de P01 y cuarenta y tres de P02", 75),
        ("3 de P01", 3),
        ("**3**", 3),
        ("`3`", 3),
        ('"3"', 3),
        ("３", 3),
        ("ninguna", 0),
    ],
)
def test_int_value_accepts(raw, value):
    assert parse_int_value(raw) == value


@pytest.mark.parametrize(
    "raw",
    [
        "3 o 4", "3 u 8", "3 ó 4", "entre 3 y 4", "3/4", "3 / 4", "quizás 3", "quizá 3",
        "tal vez 3", "aproximadamente 3", "aprox. 3", "unos 3", "unas 3", "alrededor de 3",
        "cerca de 3", "casi 3", "3?", "al menos 3", "más de 3", "menos de 3", "~3", "3 y 5",
        "3, 5", "3 5", "3,5", "1,200", "3 de 5", "tres de cinco", "3 de 5 unidades",
        "3 de cada 5", "3, aunque podrían ser 5", "3 pero podrían ser 5", "3 unidades y 5 unidades",
        "3 de P01 y 3 de P01", "3 y 5 de P01", "veinte y uno", "3 (5)", "5 = 3", "3 – 5",
        "3 correcto y 5 incorrecto", "3 sucursales de 5",
    ],
)
def test_int_value_ambiguous(raw):
    with pytest.raises(ValueParseError) as err:
        parse_int_value(raw)
    assert err.value.error_type == "ambiguous_value"


@pytest.mark.parametrize(
    "raw",
    [
        "", "   ", "abc", "-3", "−3", "menos tres", "17-20", "3.5", "1.20", "1.2000", "01.200",
        "-4 filas de 10", "- 4 cajas de 10", "4 filas de -10", "3e0", "0x10", "P03", "S3", "O1", "<b>3</b>", "&#51;", "línea 3", "tres y medio",
        "3 gatos", "40 adelante", "4 filas", "٣", "३", "3̶", "10²", "½", "③", "Ⅲ", "trεs",
        "9" * 13, "9" * 300, str(MAX_VALUE + 1), "1.000.000.000.000",
    ],
)
def test_int_value_invalid(raw):
    with pytest.raises(ValueParseError) as err:
        parse_int_value(raw)
    assert err.value.error_type == "invalid_value"


@pytest.mark.parametrize("raw", ["[4] filas de 10", "4-filas de 10", "4 filas (de 10)", "4 filas de 10!!"])
def test_group_with_foreign_symbols_is_ambiguous(raw):
    # El tokenizador descarta estos simbolos: el grupo no debe valer 40 por omision.
    with pytest.raises(ValueParseError) as err:
        parse_int_value(raw)
    assert err.value.error_type == "ambiguous_value"


def test_superscript_does_not_become_a_digit():
    # NFKC puro daria "102".
    assert "102" not in normalize_text("10²")


@pytest.mark.parametrize(
    ("raw", "value"),
    [
        ("sí", True), ("si", True), ("SÍ", True), ("true", True), ("verdadero", True),
        ("alcanza", True), ("sí alcanza", True), ("sí, alcanza", True), ("no", False),
        ("No.", False), ("false", False), ("falso", False), ("no alcanza", False),
        ("**no**", False),
    ],
)
def test_bool_value(raw, value):
    assert parse_bool_value(raw) is value


@pytest.mark.parametrize(
    "raw",
    ["sí y no", "sí pero no", "si/no", "sí o no", "sí, no", "alcanza y no alcanza", "true y false",
     "verdadero o falso", "quizás sí", "tal vez", "depende", "parcialmente"],
)
def test_bool_value_ambiguous(raw):
    with pytest.raises(ValueParseError) as err:
        parse_bool_value(raw)
    assert err.value.error_type == "ambiguous_value"


@pytest.mark.parametrize("raw", ["", "1", "0", "tal", "nо", "ѕí", "<b>sí</b>"])
def test_bool_value_invalid(raw):
    with pytest.raises(ValueParseError) as err:
        parse_bool_value(raw)
    assert err.value.error_type == "invalid_value"


@pytest.mark.parametrize(
    ("raw", "value"),
    [("S2", "S2"), ("s2", "S2"), ("sucursal S2", "S2"), ("Sucursal s2", "S2"),
     ("la sucursal S2", "S2"), ("**S2**", "S2"), ("S2.", "S2"), ("S10", "S10"), ("Ｓ２", "S2")],
)
def test_location_value(raw, value):
    assert parse_location_value(raw) == value


@pytest.mark.parametrize("raw", ["S1, S2", "S1 y S2", "S1 o S2", "S1/S2", "quizás S2", "S2 S2"])
def test_location_value_ambiguous(raw):
    with pytest.raises(ValueParseError) as err:
        parse_location_value(raw)
    assert err.value.error_type == "ambiguous_value"


@pytest.mark.parametrize("raw", ["", "2", "S", "S0", "S02", "P02", "S²", "Ѕ2", "S٢", "sucursal"])
def test_location_value_invalid(raw):
    with pytest.raises(ValueParseError) as err:
        parse_location_value(raw)
    assert err.value.error_type == "invalid_value"


@pytest.mark.parametrize(
    "raw",
    ["(" * 50000, "1+" * 50000, "1 " * 50000, " " * 200000, "de " * 50000, "treinta y " * 20000],
)
def test_int_value_is_fast_on_huge_input(raw):
    start = time.perf_counter()
    with pytest.raises(ValueParseError):
        parse_int_value(raw)
    assert time.perf_counter() - start < 1.0
