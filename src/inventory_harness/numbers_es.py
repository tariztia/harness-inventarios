"""Interpretacion de valores de respuesta: enteros en espanol, aritmetica, grupos y sumas.

Solo stdlib. Nunca usa eval(). Ver docs/contrato.md, "Equivalencias de valores".

Principio de diseno: este modulo alimenta una recompensa de RL, asi que una forma no
reconocida se rechaza. Si el valor trae mas de una cantidad sin una regla que las
combine, es `ambiguous_value`; si no se entiende, `invalid_value`. Nunca se "extrae el
primer numero" de un texto.
"""
from __future__ import annotations

import re
import unicodedata

# Las cantidades reales del dominio son pequenas. El limite evita aceptar valores que
# solo coinciden por desborde (2**32 + 3) y acota el costo de la aritmetica.
MAX_VALUE = 10**9
MAX_DIGITS = 12
MAX_VALUE_CHARS = 200
MAX_EXPR_CHARS = 64
_MAX_NUMBER_WORDS = 10
_MAX_DEPTH = 3

_NEWLINE_LIKE = {"\r", "\x0b", "\x0c", "\x85", " ", " "}
_MINUS_LIKE = {"−"}


class ValueParseError(ValueError):
    """Valor no aceptable. `error_type` es `ambiguous_value` o `invalid_value`."""

    def __init__(self, error_type: str, message: str = "") -> None:
        super().__init__(message or error_type)
        self.error_type = error_type


def _invalid(message: str) -> ValueParseError:
    return ValueParseError("invalid_value", message)


def _ambiguous(message: str) -> ValueParseError:
    return ValueParseError("ambiguous_value", message)


# ---------------------------------------------------------------- normalizacion


def _map_char(ch: str) -> str:
    """Prepara un caracter no ASCII antes de NFKC."""
    if ch in _NEWLINE_LIKE:
        return "\n"
    if ch in _MINUS_LIKE:
        return "-"
    category = unicodedata.category(ch)
    if category in ("Cf", "Cs", "Cc"):
        return ""
    # NFKC convierte "10²" en "102", "S²" en "S2" y "½" en "1⁄2". Esos caracteres no
    # son digitos, asi que no deben fabricar uno: quedan marcados como invalidos.
    # Los digitos de ancho completo o matematicos son Nd y si se normalizan.
    if category != "Nd" and any(c.isdigit() for c in unicodedata.normalize("NFKC", ch)):
        return "�"
    return ch


def normalize_text(text: str) -> str:
    """NFKC, sin caracteres invisibles ni de control, y con saltos de linea uniformes."""
    text = text.replace("\r\n", "\n")
    parts: list[str] = []
    for ch in text:
        if ch in "\n\t" or " " <= ch <= "~":
            parts.append(ch)
        else:
            parts.append(_map_char(ch))
    return unicodedata.normalize("NFKC", "".join(parts))


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def _reject_foreign_chars(s: str) -> None:
    prev = ""
    for ch in unicodedata.normalize("NFD", s):
        if ch.isascii():
            prev = ch
            continue
        category = unicodedata.category(ch)
        if category.startswith("M"):
            # Una tilde sobre una letra es normal; sobre un digito es una trampa.
            if not prev.isalpha():
                raise _invalid("marca combinante fuera de una letra")
            continue
        if ch == "�" or category == "Nd":
            raise _invalid("digito no ASCII")
        if ch.isalpha() and not unicodedata.name(ch, "").startswith("LATIN"):
            raise _invalid("letra no latina")
        prev = ch


_WRAPPERS = (("**", "**"), ("`", "`"), ('"', '"'), ("'", "'"))
_UNIT_DOT_RE = re.compile(r"\b(u|ud|uds|und|unds)\.(?=\s|$)")


def _clean_value(raw: str) -> str:
    s = normalize_text(raw).strip()
    if not s:
        raise _invalid("valor vacio")
    if len(s) > MAX_VALUE_CHARS:
        raise _invalid("valor demasiado largo")
    _reject_foreign_chars(s)
    if "<" in s or ">" in s or "&" in s:
        raise _invalid("marcado dentro del valor")
    s = strip_accents(s.lower())
    s = " ".join(s.split())
    s = _UNIT_DOT_RE.sub(r"\1", s)
    changed = True
    while changed:
        changed = False
        for left, right in _WRAPPERS:
            if len(s) > len(left) + len(right) and s.startswith(left) and s.endswith(right):
                s = s[len(left) : -len(right)].strip()
                changed = True
        stripped = s.rstrip(" .,")
        if stripped != s and stripped:
            s = stripped
            changed = True
    return s


# Alternativas, dudas y correcciones. Se revisan antes de interpretar el valor.
_DOUBT_RE = re.compile(
    r"\b(?:"
    r"o|ni|or|entre|quizas?|tal vez|acaso|aprox\w*|alrededor|cerca|casi|como|"
    r"mas o menos|unos|unas|posibles?|posiblemente|probables?|probablemente|"
    r"supongo|creo|diria|podrian?|puede ser|parece|estimo|estimad[oa]s?|depende|"
    r"aunque|pero|sino|mejor dicho|corrijo|perdon|maybe|perhaps|about|around|"
    r"al menos|por lo menos|como minimo|como maximo|a lo sumo|hasta|desde|"
    r"minimo|maximo|mas de|menos de|no se"
    r")\b"
    r"|[/\\|~?¿≈±⁄∕–—]"
)


def _check_doubt(s: str) -> None:
    if _DOUBT_RE.search(s):
        raise _ambiguous("el valor expresa alternativas o duda")


# ------------------------------------------------------------- enteros en espanol

_SMALL = {
    "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
    "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16, "diecisiete": 17,
    "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiun": 21, "veintiuno": 21,
    "veintiuna": 21, "veintidos": 22, "veintitres": 23, "veinticuatro": 24,
    "veinticinco": 25, "veintiseis": 26, "veintisiete": 27, "veintiocho": 28,
    "veintinueve": 29,
}
_UNITS = {w: v for w, v in _SMALL.items() if v <= 9}
_TENS = {
    "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70,
    "ochenta": 80, "noventa": 90,
}
_HUNDREDS = {
    "ciento": 100, "doscientos": 200, "doscientas": 200, "trescientos": 300,
    "trescientas": 300, "cuatrocientos": 400, "cuatrocientas": 400, "quinientos": 500,
    "quinientas": 500, "seiscientos": 600, "seiscientas": 600, "setecientos": 700,
    "setecientas": 700, "ochocientos": 800, "ochocientas": 800, "novecientos": 900,
    "novecientas": 900,
}
_ZERO_WORDS = {"ninguna", "ninguno", "nada"}


def _below_100(tokens: list[str]) -> int | None:
    if len(tokens) == 1:
        word = tokens[0]
        return _SMALL.get(word, _TENS.get(word))
    if len(tokens) == 3 and tokens[1] == "y" and tokens[0] in _TENS and tokens[2] in _UNITS:
        return _TENS[tokens[0]] + _UNITS[tokens[2]]
    return None


def _below_1000(tokens: list[str]) -> int | None:
    if not tokens:
        return None
    if tokens == ["cien"]:
        return 100
    if tokens[0] in _HUNDREDS:
        rest = tokens[1:]
        if not rest:
            # "ciento" a secas no es un numero; "doscientos" si.
            return None if tokens[0] == "ciento" else _HUNDREDS[tokens[0]]
        tail = _below_100(rest)
        return None if tail is None else _HUNDREDS[tokens[0]] + tail
    return _below_100(tokens)


def parse_spanish_int(text: str) -> int | None:
    """Entero escrito en espanol, de 0 a 999.999. Devuelve None si no lo es.

    Gramatica estricta: "veinte y uno", "cien dos" o "mil mil" no son numeros.
    """
    tokens = strip_accents(text.lower()).split()
    if not tokens or len(tokens) > _MAX_NUMBER_WORDS:
        return None
    if tokens == ["cero"]:
        return 0
    if "mil" not in tokens:
        return _below_1000(tokens)
    if tokens.count("mil") > 1:
        return None
    index = tokens.index("mil")
    head, tail = tokens[:index], tokens[index + 1 :]
    thousands = 1
    if head:
        if head == ["uno"] or head == ["una"]:
            return None
        parsed = _below_1000(head)
        if parsed is None:
            return None
        thousands = parsed
    rest = 0
    if tail:
        parsed = _below_1000(tail)
        if parsed is None:
            return None
        rest = parsed
    return thousands * 1000 + rest


# ----------------------------------------------------------------------- literales

_THOUSANDS_RE = re.compile(r"[1-9]\d{0,2}(?:\.\d{3})+", re.ASCII)
_DECIMAL_RE = re.compile(r"(\d+)\.(\d+)", re.ASCII)
_COMMA_RE = re.compile(r"\d+,\d+", re.ASCII)


def _check_bound(value: int) -> int:
    if abs(value) > MAX_VALUE:
        raise _invalid("valor fuera de rango")
    return value


def _parse_literal(token: str) -> int | None:
    """Literal numerico. None si no tiene forma numerica; lanza si no es entero."""
    if token.isascii() and token.isdigit():
        if len(token) > MAX_DIGITS:
            raise _invalid("valor fuera de rango")
        return _check_bound(int(token))
    if _THOUSANDS_RE.fullmatch(token):
        digits = token.replace(".", "")
        if len(digits) > MAX_DIGITS:
            raise _invalid("valor fuera de rango")
        return _check_bound(int(digits))
    decimal = _DECIMAL_RE.fullmatch(token)
    if decimal:
        if len(decimal.group(1)) > MAX_DIGITS or set(decimal.group(2)) != {"0"}:
            raise _invalid("valor no entero")
        return _check_bound(int(decimal.group(1)))
    if _COMMA_RE.fullmatch(token):
        # "3,5" puede ser un decimal o una lista; "1,200" depende del pais.
        raise _ambiguous("coma entre digitos")
    return None


# ---------------------------------------------------------------------- aritmetica

_ARITH_TOKEN_RE = re.compile(r"\s*(\d+(?:\.\d+)*(?:,\d+)?|[a-z]+(?: [a-z]+)*|[-+*()])")
_WORD_OPS = ((re.compile(r"\bpor\b"), "*"), (re.compile(r"\bmas\b"), "+"), (re.compile(r"\bmenos\b"), "-"))
_TIMES_X_RE = re.compile(r"(?<![a-z0-9])x(?![a-z0-9])|(?<=[0-9)])\s*x\s*(?=[0-9(])")


def _arith_tokens(expr: str) -> list[str] | None:
    s = expr.replace("×", "*")
    s = _TIMES_X_RE.sub("*", s)
    for pattern, op in _WORD_OPS:
        s = pattern.sub(op, s)
    s = s.rstrip()
    tokens: list[str] = []
    pos = 0
    while pos < len(s):
        match = _ARITH_TOKEN_RE.match(s, pos)
        if match is None:
            return None
        tokens.append(match.group(1))
        pos = match.end()
    return tokens


class _Arithmetic:
    """expr := term (('+'|'-') term)*; term := factor ('*' factor)*;
    factor := ('+'|'-')? (entero | '(' expr ')')

    El signo unario no se encadena, asi que "2**3" y "--3" no son expresiones validas.
    """

    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def run(self) -> int | None:
        value = self._expr()
        return value if value is not None and self.pos == len(self.tokens) else None

    def _expr(self) -> int | None:
        value = self._term()
        while value is not None and self._peek() in ("+", "-"):
            op = self.tokens[self.pos]
            self.pos += 1
            right = self._term()
            if right is None:
                return None
            value = _check_bound(value + right if op == "+" else value - right)
        return value

    def _term(self) -> int | None:
        value = self._factor()
        while value is not None and self._peek() == "*":
            self.pos += 1
            right = self._factor()
            if right is None:
                return None
            value = _check_bound(value * right)
        return value

    def _factor(self) -> int | None:
        sign = 1
        if self._peek() in ("+", "-"):
            sign = -1 if self.tokens[self.pos] == "-" else 1
            self.pos += 1
        value = self._primary()
        return None if value is None else sign * value

    def _primary(self) -> int | None:
        token = self._peek()
        if token is None:
            return None
        self.pos += 1
        if token == "(":
            value = self._expr()
            if value is None or self._peek() != ")":
                return None
            self.pos += 1
            return value
        if token[0].isdigit():
            return _parse_literal(token)
        if token[0].isalpha():
            return parse_spanish_int(token)
        return None


def parse_arithmetic(expr: str) -> int | None:
    """Evalua + - * x × ( ) entre enteros. None si no es una expresion valida.

    Lanza `invalid_value` si la expresion valida excede los limites o no es entera.
    """
    tokens = _arith_tokens(expr.strip().lower())
    if not tokens:
        return None
    if len(expr) > MAX_EXPR_CHARS:
        raise _invalid("expresion demasiado larga")
    return _Arithmetic(tokens).run()


# ---------------------------------------------------- grupos y sumas etiquetadas

_PREFIX_RE = re.compile(
    r"^(?:(?:un total de|el total es|en total|se cubren|se atienden|faltan|falta|"
    r"faltarian|faltaria|quedan|queda|quedarian|pendientes?|cubiertas?|atendidas?|"
    r"cubren|cubre|atienden|atiende|son|es|serian|seria|total|solamente|solo|"
    r"exactamente|justo)\b[ :]*)+"
)
_SUFFIX_RE = re.compile(
    r"(?:\s+(?:unidades|unidad|uds|ud|unds|und|u|piezas?|items?|articulos?|en total|"
    r"pendientes?|faltantes?|cubiertas?|atendidas?|por atender|por cubrir|exactas?))+$"
)
_HEX_RE = re.compile(r"\b0x[0-9a-f]+\b")
_TOKEN_RE = re.compile(r"[a-z0-9_]+(?:[.,]\d+)*|[,+]")
_SUM_CHARS_RE = re.compile(r"[a-z0-9_.,+ ]+")
_ID_RE = re.compile(r"[pso]\d+")

_GROUP_NOUNS = {
    "fila", "filas", "hilera", "hileras", "columna", "columnas", "caja", "cajas",
    "grupo", "grupos", "lote", "lotes", "paquete", "paquetes", "pack", "packs",
    "bolsa", "bolsas", "bandeja", "bandejas", "pallet", "pallets", "tanda", "tandas",
}
_UNIT_WORDS = {
    "unidad", "unidades", "uds", "ud", "unds", "und", "u", "pieza", "piezas", "item",
    "items", "articulo", "articulos",
}
_LABEL_PREPOSITIONS = {"de", "del", "en", "para", "la", "el", "los", "las"}
_SEPARATORS = {"y", "e", ",", "+"}
# Una "etiqueta" no puede ser un veredicto: "3 correcto y 5 incorrecto" o "5 antes y
# 3 ahora" son dos respuestas disfrazadas de suma.
_FORBIDDEN_LABELS = {
    "si", "no", "correcto", "correcta", "incorrecto", "incorrecta", "verdadero",
    "falso", "antes", "ahora", "despues", "luego", "primero", "final", "finalmente",
    "real", "mal", "bien", "error", "erroneo", "seguro", "segura", "total", "pendiente",
    "pendientes", "faltante", "faltantes", "cubierta", "cubiertas", "atendida",
    "atendidas", "faltan", "falta", "quedan", "queda", "mas", "menos", "respuesta",
} | _UNIT_WORDS


def _strip_fillers(s: str) -> str:
    previous = None
    while s != previous:
        previous = s
        s = _PREFIX_RE.sub("", s).strip()
        s = _SUFFIX_RE.sub("", s).strip()
    return s


def _tokenize(s: str) -> list[str]:
    return _TOKEN_RE.findall(s)


def _atom_at(tokens: list[str], start: int) -> tuple[int, int] | None:
    """Numero mas largo que empieza en `start`, como (valor, indice siguiente)."""
    first = tokens[start]
    if first[0].isdigit():
        try:
            value = _parse_literal(first)
        except ValueParseError:
            return None
        return None if value is None else (value, start + 1)
    last = min(len(tokens), start + _MAX_NUMBER_WORDS)
    for end in range(last, start, -1):
        value = parse_spanish_int(" ".join(tokens[start:end]))
        if value is not None:
            return value, end
    return None


def _count_numbers(s: str) -> int:
    tokens = _tokenize(s)
    count = 0
    i = 0
    while i < len(tokens):
        atom = _atom_at(tokens, i)
        if atom is None:
            i += 1
        else:
            count += 1
            i = atom[1]
    return count


def _parse_group(s: str) -> int | None:
    """"cuatro filas de 10", "4 cajas de 10". Solo con sustantivos de agrupacion."""
    # _tokenize descarta lo que no reconoce: sin este filtro, "-4 filas de 10" valdria 40.
    if not _SUM_CHARS_RE.fullmatch(s):
        return None
    tokens = _tokenize(s)
    if not tokens:
        return None
    left = _atom_at(tokens, 0)
    if left is None:
        return None
    count, i = left
    if i + 2 >= len(tokens) or tokens[i] not in _GROUP_NOUNS or tokens[i + 1] != "de":
        return None
    right = _atom_at(tokens, i + 2)
    if right is None or right[1] != len(tokens):
        return None
    return _check_bound(count * right[0])


def _clean_label(words: list[str]) -> str | None:
    words = list(words)
    while words and words[0] in _LABEL_PREPOSITIONS:
        words.pop(0)
    if not words:
        return None
    for i, word in enumerate(words):
        if word in _FORBIDDEN_LABELS or word in _SEPARATORS:
            return None
        if _ID_RE.fullmatch(word):
            continue
        if not word.isalpha() or _atom_at(words, i) is not None:
            return None
    return " ".join(words)


def _parse_labelled(s: str) -> int | None:
    """"1 de P01 y 2 de P02", "20 adelante y 20 atras". Cada sumando lleva su etiqueta."""
    if not _SUM_CHARS_RE.fullmatch(s):
        return None
    tokens = _tokenize(s)
    addends: list[tuple[int, str]] = []
    i = 0
    while True:
        if i >= len(tokens):
            return None
        atom = _atom_at(tokens, i)
        if atom is None:
            return None
        value, i = atom
        while i < len(tokens) and tokens[i] in _UNIT_WORDS:
            i += 1
        words: list[str] = []
        while i < len(tokens):
            if tokens[i] in _SEPARATORS and i + 1 < len(tokens) and _atom_at(tokens, i + 1):
                break
            words.append(tokens[i])
            i += 1
        label = _clean_label(words)
        if label is None:
            return None
        addends.append((value, label))
        if i >= len(tokens):
            break
        i += 1
    labels = [label for _, label in addends]
    if len(set(labels)) != len(labels):
        return None
    if len(addends) == 1 and not _ID_RE.fullmatch(labels[0]):
        return None
    return _check_bound(sum(value for value, _ in addends))


_NEGATIVE_NUMBER_RE = re.compile(r"(?:^|[\s(,])-\s*(?:\d|[a-z])")
_GLOSS_RE = re.compile(r"(.+?)\s*\(([^()]+)\)")


def _parse_gloss(s: str, depth: int) -> int | None:
    """"3 (tres)": el parentesis repite el valor. Si difiere, es ambiguo."""
    match = _GLOSS_RE.fullmatch(s)
    if match is None:
        return None
    left = _eval_core(match.group(1), depth + 1)
    right = _eval_core(match.group(2), depth + 1)
    if left is None or right is None:
        return None
    if left != right:
        raise _ambiguous("el parentesis da otro valor")
    return left


def _parse_equality(s: str, depth: int) -> int | None:
    """"20-17 = 3": todos los lados deben valer lo mismo."""
    values = [_eval_core(part, depth + 1) for part in s.split("=")]
    if any(value is None for value in values):
        return None
    if len(set(values)) != 1:
        raise _ambiguous("igualdad con lados distintos")
    return values[0]


def _eval_core(s: str, depth: int = 0) -> int | None:
    if depth > _MAX_DEPTH:
        return None
    s = _strip_fillers(s.strip())
    if not s:
        return None
    if s in _ZERO_WORDS:
        return 0
    if _HEX_RE.search(s):
        raise _invalid("literal hexadecimal")
    if "=" in s:
        return _parse_equality(s, depth)
    if " " not in s:
        literal = _parse_literal(s)
        if literal is not None:
            return literal
    words = parse_spanish_int(s)
    if words is not None:
        return words
    for parser in (parse_arithmetic, _parse_group, _parse_labelled):
        value = parser(s)
        if value is not None:
            return value
    return _parse_gloss(s, depth)


# ----------------------------------------------------------------- API de valores


def parse_int_value(raw: str) -> int:
    """Interpreta un valor numerico como entero no negativo, o lanza `ValueParseError`."""
    s = _clean_value(raw)
    _check_doubt(s)
    if not s.isascii() and any(not c.isascii() and c != "×" for c in s):
        raise _invalid("simbolo no reconocido")
    value = _eval_core(s)
    if value is None:
        if _NEGATIVE_NUMBER_RE.search(s):
            raise _invalid("valor negativo")
        if _count_numbers(s) >= 2:
            raise _ambiguous("mas de una cantidad sin regla que las combine")
        raise _invalid("valor no interpretable")
    if value < 0:
        raise _invalid("valor negativo")
    return _check_bound(value)


_TRUE_FORMS = {"si", "true", "verdadero", "alcanza", "si alcanza", "si, alcanza"}
_FALSE_FORMS = {"no", "false", "falso", "no alcanza", "no, no alcanza"}
_PARTIAL_RE = re.compile(r"\b(?:parcial\w*|a medias|en parte|mas bien)\b")
_NEGATIVE_WORD_RE = re.compile(r"\b(?:no|false|falso)\b")
_POSITIVE_WORD_RE = re.compile(r"\b(?:si|true|verdadero|alcanza|yes)\b")


def parse_bool_value(raw: str) -> bool:
    """Booleanos del contrato. Un valor con ambas polaridades es ambiguo."""
    s = _clean_value(raw)
    if s in _TRUE_FORMS:
        return True
    if s in _FALSE_FORMS:
        return False
    _check_doubt(s)
    if _PARTIAL_RE.search(s):
        raise _ambiguous("respuesta parcial")
    without_no_alcanza = s.replace("no alcanza", "no")
    if _NEGATIVE_WORD_RE.search(without_no_alcanza) and _POSITIVE_WORD_RE.search(without_no_alcanza):
        raise _ambiguous("ambas polaridades")
    raise _invalid("booleano no reconocido")


_LOCATION_RE = re.compile(r"(?:(?:la|en) )?(?:sucursal )?s([1-9]\d{0,3})")
_LOCATION_ID_RE = re.compile(r"\bs\d+\b")


def parse_location_value(raw: str) -> str:
    """`S2`, `s2` o `sucursal S2`, en la forma canonica `S2`."""
    s = _clean_value(raw)
    _check_doubt(s)
    if len(_LOCATION_ID_RE.findall(s)) > 1:
        raise _ambiguous("mas de una sucursal")
    match = _LOCATION_RE.fullmatch(s)
    if match is None:
        raise _invalid("sucursal no reconocida")
    return f"S{match.group(1)}"
