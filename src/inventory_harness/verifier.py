"""Verificador de la respuesta final. Es la recompensa de entrenamiento.

Solo stdlib. Contrato en docs/contrato.md, "Respuesta final del modelo".

`parse_answer` convierte el bloque <answer> a la forma canonica de `expected`.
`verify_final_text` agrega la revision de contradicciones y la comparacion, y nunca
lanza una excepcion: cualquier fallo interno es recompensa 0.
"""
from __future__ import annotations

import json
import re
from decimal import Decimal
from typing import Any

from inventory_harness.numbers_es import (
    MAX_VALUE,
    ValueParseError,
    normalize_text,
    parse_bool_value,
    parse_int_value,
    parse_location_value,
    parse_spanish_int,
    strip_accents,
)
from inventory_harness.schema import Instance, Verdict

MAX_TEXT_CHARS = 200_000
_MAX_PARAGRAPH_CHARS = 2_000


class AnswerParseError(ValueError):
    """Respuesta rechazada. `error_type` viene de la tabla de rechazos del contrato."""

    def __init__(self, error_type: str, message: str = "", field: str | None = None) -> None:
        super().__init__(message or error_type)
        self.error_type = error_type
        self.field = field


# ---------------------------------------------------------------- <think> y bloque

# Los cuantificadores acotados evitan el backtracking cuadratico de `\s*(/?)\s*`.
_THINK_TAG_RE = re.compile(r"<\s{0,8}(/?)\s{0,8}think\s{0,8}>", re.IGNORECASE)
_ANSWER_TAG_RE = re.compile(r"<\s{0,8}(/?)\s{0,8}answer(?![\w-])[^<>]{0,64}>", re.IGNORECASE)
_FENCE_LINE_RE = re.compile(r"^\s*(?:`{3,}|~{3,})[\w-]*\s*$")


def _strip_think(text: str) -> str:
    """Quita <think>...</think>, incluso anidado.

    Un <think> sin cerrar descarta el resto. Un </think> sin abrir descarta lo anterior,
    porque varias plantillas de chat abren el <think> antes de la completion.
    """
    kept: list[str] = []
    depth = 0
    pos = 0
    for match in _THINK_TAG_RE.finditer(text):
        closing = bool(match.group(1))
        if depth == 0:
            if closing:
                kept.clear()
            else:
                kept.append(text[pos : match.start()])
                depth = 1
            pos = match.end()
        elif closing:
            depth -= 1
            pos = match.end()
        else:
            depth += 1
    if depth == 0:
        kept.append(text[pos:])
    return "".join(kept)


def _clean_text(text: str) -> str:
    if not isinstance(text, str):
        raise AnswerParseError("no_answer_block", "la respuesta no es texto")
    if len(text) > MAX_TEXT_CHARS:
        raise AnswerParseError("invalid_value", "respuesta demasiado larga")
    return _strip_think(normalize_text(text))


def _is_blank_or_fence(text: str) -> bool:
    return all(not line.strip() or _FENCE_LINE_RE.match(line) for line in text.split("\n"))


def _locate_block(clean: str) -> tuple[str, str]:
    """Devuelve (texto previo, contenido). Exige exactamente un par de etiquetas."""
    tags = list(_ANSWER_TAG_RE.finditer(clean))
    if not tags:
        raise AnswerParseError("no_answer_block", "no hay bloque <answer>")
    if len(tags) != 2 or tags[0].group(1) or not tags[1].group(1):
        raise AnswerParseError("multiple_answer_blocks", "se esperaba un solo bloque cerrado")
    opening, closing = tags
    if not _is_blank_or_fence(clean[closing.end() :]):
        raise AnswerParseError("text_after_answer", "hay texto despues de </answer>")
    return clean[: opening.start()], clean[opening.end() : closing.start()]


# ----------------------------------------------------------- pares clave y valor


def _reject_json_constant(name: str) -> None:
    raise AnswerParseError("invalid_value", f"constante JSON no permitida: {name}")


class _JsonObject(list):
    """Pares de un objeto JSON, en orden y con repetidos (dict los ocultaria)."""


def _json_pairs(content: str) -> list[tuple[str, Any]]:
    try:
        data = json.loads(
            content,
            object_pairs_hook=_JsonObject,
            parse_float=Decimal,
            parse_constant=_reject_json_constant,
        )
    except AnswerParseError:
        raise
    except (ValueError, ArithmeticError, RecursionError):
        raise AnswerParseError("invalid_value", "JSON invalido") from None
    if not isinstance(data, _JsonObject):
        raise AnswerParseError("invalid_value", "se esperaba un objeto JSON plano")
    return data


_BULLET_RE = re.compile(r"^\s*(?:[-+•]|\*(?=\s))\s+")


def _line_pairs(content: str) -> list[tuple[str, Any]]:
    pairs: list[tuple[str, Any]] = []
    for raw_line in content.split("\n"):
        line = _BULLET_RE.sub("", raw_line).strip()
        if not line:
            continue
        if line.startswith("**") and line.endswith("**") and len(line) > 4:
            line = line[2:-2].strip()
        key, colon, value = line.partition(":")
        if not colon:
            raise AnswerParseError("unknown_field", "linea sin formato clave: valor")
        value = value.strip()
        # "**faltan:** 3": el cierre del resaltado queda al inicio del valor.
        if key.count("**") % 2 == 1 and value.startswith("**"):
            value = value[2:].strip()
        pairs.append((key, value))
    return pairs


def _block_pairs(content: str) -> list[tuple[str, Any]]:
    lines = content.split("\n")
    while lines and (not lines[0].strip() or _FENCE_LINE_RE.match(lines[0])):
        lines.pop(0)
    while lines and (not lines[-1].strip() or _FENCE_LINE_RE.match(lines[-1])):
        lines.pop()
    body = "\n".join(lines)
    if body.lstrip().startswith("{"):
        return _json_pairs(body)
    return _line_pairs(body)


def _normalize_key(key: str) -> str:
    cleaned = normalize_text(key).replace("*", "").replace("`", "").strip()
    return strip_accents(cleaned.lower())


# ------------------------------------------------------------------ valores tipados


def _value_error(error: ValueParseError, field: str) -> AnswerParseError:
    return AnswerParseError(error.error_type, str(error), field=field)


def _reject_container(value: Any, field: str) -> None:
    if isinstance(value, _JsonObject):
        raise AnswerParseError("invalid_value", "JSON anidado", field=field)
    if isinstance(value, list):
        raise AnswerParseError("ambiguous_value", "lista como valor", field=field)


def _to_int(value: Any, field: str) -> int:
    _reject_container(value, field)
    if isinstance(value, str):
        try:
            return parse_int_value(value)
        except ValueParseError as exc:
            raise _value_error(exc, field) from None
    # bool es subclase de int: `"faltan": true` no debe valer 1.
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise AnswerParseError("invalid_value", "tipo no numerico", field=field)
    if value < 0 or value > MAX_VALUE or value != int(value):
        raise AnswerParseError("invalid_value", "valor fuera de rango o no entero", field=field)
    return int(value)


def _to_bool(value: Any, field: str) -> bool:
    _reject_container(value, field)
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        raise AnswerParseError("invalid_value", "tipo no booleano", field=field)
    try:
        return parse_bool_value(value)
    except ValueParseError as exc:
        raise _value_error(exc, field) from None


def _to_location(value: Any, field: str) -> str:
    _reject_container(value, field)
    if not isinstance(value, str):
        raise AnswerParseError("invalid_value", "tipo no textual", field=field)
    try:
        return parse_location_value(value)
    except ValueParseError as exc:
        raise _value_error(exc, field) from None


# ----------------------------------------------------------------- forma canonica

_ORDER_KEY_RE = re.compile(r"o([1-9]\d{0,3})_(atendidas|pendientes)")
_SIMPLE_KEYS = {
    "availability": ("alcanza", "faltan"),
    "selection": ("sucursal", "cubiertas", "pendientes"),
}


def _key_allowed(key: str, family: str) -> bool:
    if family == "composition":
        return key == "total_pendientes" or _ORDER_KEY_RE.fullmatch(key) is not None
    return key in _SIMPLE_KEYS[family]


def _collect(pairs: list[tuple[str, Any]], family: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for raw_key, value in pairs:
        key = _normalize_key(raw_key)
        if not _key_allowed(key, family):
            raise AnswerParseError("unknown_field", "campo desconocido", field=key[:40])
        if key in fields:
            raise AnswerParseError("duplicate_field", "campo repetido", field=key)
        fields[key] = value
    return fields


def _require(fields: dict[str, Any], keys: list[str]) -> None:
    for key in keys:
        if key not in fields:
            raise AnswerParseError("missing_field", "falta un campo", field=key)


def _build_composition(fields: dict[str, Any]) -> dict[str, Any]:
    numbers = sorted({int(m.group(1)) for m in map(_ORDER_KEY_RE.fullmatch, fields) if m})
    keys = ["total_pendientes"]
    for n in numbers:
        keys += [f"o{n}_atendidas", f"o{n}_pendientes"]
    _require(fields, keys)
    if not numbers:
        raise AnswerParseError("missing_field", "no se informo ningun pedido", field="O<n>")
    orders = {
        f"O{n}": {
            "covered_units": _to_int(fields[f"o{n}_atendidas"], f"o{n}_atendidas"),
            "pending_units": _to_int(fields[f"o{n}_pendientes"], f"o{n}_pendientes"),
        }
        for n in numbers
    }
    return {"orders": orders, "total_pending": _to_int(fields["total_pendientes"], "total_pendientes")}


def _build(fields: dict[str, Any], family: str) -> dict[str, Any]:
    if family == "composition":
        return _build_composition(fields)
    _require(fields, list(_SIMPLE_KEYS[family]))
    if family == "availability":
        return {
            "can_fulfill": _to_bool(fields["alcanza"], "alcanza"),
            "missing_units": _to_int(fields["faltan"], "faltan"),
        }
    return {
        "location_id": _to_location(fields["sucursal"], "sucursal"),
        "covered_units": _to_int(fields["cubiertas"], "cubiertas"),
        "pending_units": _to_int(fields["pendientes"], "pendientes"),
    }


def _parse_clean(clean: str, family: str) -> tuple[dict[str, Any], str]:
    if family not in ("availability", "selection", "composition"):
        raise ValueError(f"familia desconocida: {family!r}")
    prefix, content = _locate_block(clean)
    return _build(_collect(_block_pairs(content), family), family), prefix


def parse_answer(text: str, family: str) -> dict[str, Any]:
    """Devuelve la forma canonica de `expected`, o lanza `AnswerParseError`."""
    return _parse_clean(_clean_text(text), family)[0]


# ------------------------------------------------------------------- contradicciones
#
# Es una revision conservadora: solo mira el ultimo parrafo y, ante la duda, no marca.
# No protege la recompensa de un valor incorrecto (eso lo hace la comparacion); solo
# castiga una explicacion que concluye lo contrario del bloque.


def _last_paragraph(prefix: str) -> str:
    collected: list[str] = []
    for line in reversed(prefix.split("\n")):
        if _FENCE_LINE_RE.match(line):
            continue
        if not line.strip():
            if collected:
                break
            continue
        collected.append(line)
    return "\n".join(reversed(collected))[-_MAX_PARAGRAPH_CHARS:]


def _prepare_paragraph(paragraph: str) -> str:
    # "si" sin tilde suele ser condicional; un marcador conserva la distincion con "sí".
    text = paragraph.lower()
    text = re.sub(r"\bsí\b", "afirmativo", text)
    text = strip_accents(text)
    # La forma del bloque repetida en prosa no debe leerse como un "alcanza" positivo.
    text = re.sub(r"\balcanza\s*:\s*(?:afirmativo|si)\b", "afirmativo alcanza", text)
    text = re.sub(r"\balcanza\s*:\s*no\b", "no alcanza", text)
    return text


_SENTENCE_RE = re.compile(r"([^.;!?\n]+)([.;!?\n]*)")
_CLAUSE_SPLIT_RE = re.compile(
    r"[,:]|\b(?:pero|aunque|sin embargo|mientras que|porque|ya que|asi que|por lo tanto|por eso)\b"
)
_LINE_SCOPE_RE = re.compile(r"\bp\d+\b|\blineas?\b|\bproductos?\b|\barticulos?\b")
_HYPOTHETICAL_RE = re.compile(
    r"\bsi\b|\bpense\b|\bcrei\b|\bsupuse\b|\binicialmente\b|\bal principio\b|\ben principio\b|"
    r"\bverific\w+|\brevis\w+|\bdetermin\w+|\bcomprob\w+|\bsaber\b|\bver si\b"
)
_BARE_YES_RE = re.compile(r"^\s*si,?\s+(?:el pedido\s+)?alcanza\s*$")

_FULFILL = r"(?:completar|cumplir|atender|satisfacer|surtir|cubrir)"
# "se puede cubrir 9 de 12" no dice que el pedido se complete.
_FULFILL_ALL = r"(?:(?:completar|cumplir|satisfacer)|(?:atender|surtir|cubrir)\s+(?:el\s+pedido|todo|por\s+completo))"
_NEG_STRONG_RE = re.compile(
    r"\bno\s+(?:\w+\s+)?alcanza(?:n|ra|ria)?\b"
    r"|\bno\s+(?:hay|es|son)\s+(?:\w+\s+)?suficientes?\b"
    r"|\bno\s+(?:se\s+)?puede\s+" + _FULFILL + r"\b"
    r"|\bno\s+es\s+posible\s+" + _FULFILL + r"\b"
    r"|\bno\s+se\s+cubre\b"
    r"|\binsuficientes?\b"
)
_POS_STRONG_RE = re.compile(
    r"\bafirmativo\s*,?\s+(?:\w+\s+)?(?:alcanza|se\s+puede|hay|es\s+suficiente)\b"
    r"|^\s*alcanza(?:\s+para\b.*)?\s*$"
    r"|\b(?:stock|inventario|disponible|mercaderia|existencias?|cantidad)\b[^,]{0,30}?(?<!no )\balcanza\b"
    r"|(?<!no )\bhay\s+(?:\w+\s+)?suficientes?\b"
    r"|(?<!no )\bes\s+suficiente\b"
    r"|(?<!no )(?<!no se )\b(?:se\s+)?puede\s+" + _FULFILL_ALL + r"\b"
    r"|\bno\s+falta(?:n)?\b"
)
_NEG_WEAK_RE = re.compile(r"(?<!no )\bfalta(?:n|rian|ria)?\s+(\w+)")
# Los pedidos parciales son validos: "alcanza solo para 9" no afirma que alcance.
_PARTIAL_CLAUSE_RE = re.compile(
    r"\b(?:solo|solamente|unicamente|apenas|parcial\w*|en\s+parte|una\s+parte|parte\s+del?|hasta)\b"
)
_WORD_RE = re.compile(r"\w+")


def _names_positive_amount(token: str) -> bool:
    if token.isdigit():
        return int(token[:12]) > 0
    value = parse_spanish_int(token)
    return value is not None and value > 0


def _claims_partial_amount(clause: str) -> bool:
    if _PARTIAL_CLAUSE_RE.search(clause):
        return True
    return any(_names_positive_amount(token) for token in _WORD_RE.findall(clause))


def _polarity_evidence(paragraph: str) -> tuple[bool, bool, bool]:
    """Devuelve (positiva fuerte, negativa fuerte, negativa debil) del parrafo."""
    pos_strong = neg_strong = neg_weak = False
    for match in _SENTENCE_RE.finditer(_prepare_paragraph(paragraph)):
        sentence, ending = match.group(1), match.group(2)
        if "?" in ending or sentence.lstrip().startswith("¿"):
            continue
        if _LINE_SCOPE_RE.search(sentence):
            continue
        if _BARE_YES_RE.match(sentence):
            pos_strong = True
            continue
        if _HYPOTHETICAL_RE.search(sentence):
            continue
        for clause in _CLAUSE_SPLIT_RE.split(sentence):
            if _NEG_STRONG_RE.search(clause):
                neg_strong = True
            elif _POS_STRONG_RE.search(clause) and not _claims_partial_amount(clause):
                pos_strong = True
            weak = _NEG_WEAK_RE.search(clause)
            if weak and _names_positive_amount(weak.group(1)):
                neg_weak = True
    return pos_strong, neg_strong, neg_weak


def _contradicts_can_fulfill(paragraph: str, can_fulfill: bool) -> bool:
    pos_strong, neg_strong, neg_weak = _polarity_evidence(paragraph)
    if pos_strong and neg_strong:
        return False  # El parrafo se corrige a si mismo: ante la duda, no se marca.
    return (neg_strong or neg_weak) if can_fulfill else pos_strong


_RECOMMEND_VERB = (
    r"(?:recomiendo|recomendamos|recomendaria|recomienda|sugiero|sugerimos|elijo|elegimos|"
    r"escojo|escogemos|selecciono|seleccionamos|se\s+elige|se\s+recomienda|se\s+selecciona|"
    r"se\s+escoge|debemos|se\s+debe|hay\s+que|opto\s+por|optamos\s+por|conviene|gana|"
    r"la\s+mejor(?:\s+opcion)?\s+es|sucursal(?:\s+(?:recomendada|elegida|seleccionada|ganadora))?\s+es)"
)
_RECOMMEND_BEFORE_RE = re.compile(
    r"\b" + _RECOMMEND_VERB + r"(?:\s+\w+){0,3}?\s+(?:la\s+)?(?:sucursal\s+)?s(\d+)\b"
)
_RECOMMEND_AFTER_RE = re.compile(
    r"(?<!\w)s(\d+)\s+(?:es|seria|sera)\s+(?:la\s+)?"
    r"(?:mejor|recomendada|elegida|seleccionada|ganadora|indicada)\b"
)
_LOCATION_ANSWER_RE = re.compile(
    r"\bsucursal(\s+(?:recomendada|elegida|seleccionada|ganadora))?\s*:\s*"
)
# Negacion o condicion justo antes del verbo: "no recomiendo S1", "si elegimos S1".
_NEGATED_BEFORE_RE = re.compile(r"\b(?:si|no|al)(?:\s+\w+)?\s*$")
# Dentro del tramo verbo-sucursal: "recomiendo no usar S1", "conviene evitar S1".
_NEGATED_SPAN_RE = re.compile(r"\bno\b|\bdescart\w+|\bexcluy\w+|\bevit\w+|\bsalvo\b|\bexcepto\b")
_NEGATED_AFTER_RE = re.compile(r"\bsi\b|\bno\b")


def _recommended_locations(paragraph: str) -> set[str]:
    text = _LOCATION_ANSWER_RE.sub(lambda m: f"sucursal{m.group(1) or ''} es ", strip_accents(paragraph.lower()))
    found: set[str] = set()
    for sentence in re.split(r"[.;!?\n]+", text):
        for clause in _CLAUSE_SPLIT_RE.split(sentence):
            for match in _RECOMMEND_BEFORE_RE.finditer(clause):
                if _NEGATED_BEFORE_RE.search(clause[: match.start()]):
                    continue
                if not _NEGATED_SPAN_RE.search(match.group(0)):
                    found.add(f"S{match.group(1)}")
            if not _NEGATED_AFTER_RE.search(clause):
                found.update(f"S{number}" for number in _RECOMMEND_AFTER_RE.findall(clause))
    return found


def _find_contradiction(prefix: str, parsed: dict[str, Any], family: str) -> str | None:
    paragraph = _last_paragraph(prefix)
    if not paragraph:
        return None
    if family == "availability" and _contradicts_can_fulfill(paragraph, parsed["can_fulfill"]):
        return "alcanza"
    if family == "selection":
        recommended = _recommended_locations(paragraph)
        if recommended and parsed["location_id"] not in recommended:
            return "sucursal"
    return None


# ------------------------------------------------------------------------ comparacion


def _order_set_mismatch(parsed: dict[str, Any], expected: dict[str, Any]) -> tuple[str, str] | None:
    got, want = set(parsed["orders"]), set(expected["orders"])
    if want - got:
        return "missing_field", sorted(want - got)[0]
    if got - want:
        return "unknown_field", sorted(got - want)[0]
    return None


def _wrong_fields(parsed: dict[str, Any], expected: dict[str, Any], family: str) -> list[str]:
    if family == "composition":
        wrong = [
            f"{order}.{name}"
            for order in sorted(expected["orders"])
            for name in ("covered_units", "pending_units")
            if parsed["orders"][order][name] != expected["orders"][order][name]
        ]
        if parsed["total_pending"] != expected["total_pending"]:
            wrong.append("total_pending")
        return wrong
    return [name for name in expected if parsed.get(name) != expected[name]]


def _reject(verdict: Verdict, error: AnswerParseError) -> Verdict:
    verdict.parser_error = True
    verdict.error_type = error.error_type
    verdict.details = {"message": str(error)}
    if error.field is not None:
        verdict.details["field"] = error.field
    return verdict


def _verify(text: str, instance: Instance, verdict: Verdict) -> Verdict:
    family = instance.family
    expected = instance.expected
    parsed, prefix = _parse_clean(_clean_text(text), family)
    # `details` llega a los rollouts: lleva lo que dijo el modelo, nunca `expected`.
    details: dict[str, Any] = {"parsed": parsed}

    if family == "composition":
        mismatch = _order_set_mismatch(parsed, expected)
        if mismatch is not None:
            raise AnswerParseError(mismatch[0], "conjunto de pedidos distinto", field=mismatch[1])

    wrong = _wrong_fields(parsed, expected, family)
    contradicted = _find_contradiction(prefix, parsed, family)
    verdict.details = details
    if contradicted is not None:
        verdict.contradictory_answer = True
        verdict.error_type = "contradiction"
        details["field"] = contradicted
        details["block_matches_expected"] = not wrong
        return verdict
    if wrong:
        verdict.error_type = "wrong_value"
        details["field"] = wrong[0]
        details["failed_fields"] = wrong
        return verdict
    verdict.correct_final_answer = True
    verdict.reward = 1.0
    return verdict


def verify_final_text(text: str, instance: Instance) -> Verdict:
    """Evalua la respuesta final. Nunca lanza; deja en None los campos de herramientas."""
    verdict = Verdict()
    try:
        return _verify(text, instance, verdict)
    except AnswerParseError as exc:
        return _reject(verdict, exc)
    except Exception as exc:  # Una recompensa no puede tumbar el entrenamiento.
        fallback = Verdict(parser_error=True, error_type="internal_error")
        fallback.details = {"message": type(exc).__name__}
        return fallback
