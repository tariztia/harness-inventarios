"""Herramienta del modelo y protocolo de llamadas. Ver docs/contrato.md, "Herramienta".

Funciones puras sobre la instancia: el estado nunca muta, asi que repetir una llamada
da el mismo resultado. Por eso `reward.py` puede volver a ejecutar la trayectoria y
comparar el texto exacto de cada observacion. Solo existe una serializacion
(`serialize_observation`), la usan el rollout y la recompensa.
"""
from __future__ import annotations

import json
import re
from typing import Any

from .numbers_es import normalize_text
from .schema import Instance
from .verifier import _ANSWER_TAG_RE, _strip_think

MAX_TOOL_ROUNDS = 2
TOOL_NAME = "get_inventory"

# Los mensajes de error no repiten lo que escribio el modelo: un ID inventado podria
# contener etiquetas y terminaria dentro de una observacion.
ERROR_MALFORMED = "llamada mal formada: se esperaba un JSON con name y arguments"
ERROR_UNKNOWN_TOOL = "herramienta desconocida: la unica disponible es get_inventory"
ERROR_BAD_ARGUMENTS = "argumentos invalidos: usa product_id y, opcionalmente, location_id"
ERROR_UNKNOWN_PRODUCT = "product_id inexistente en el catalogo"
ERROR_UNKNOWN_LOCATION = "location_id inexistente en el catalogo"

_CALL_TAG_RE = re.compile(r"<\s{0,8}(/?)\s{0,8}tool_call\s{0,8}>", re.IGNORECASE)
_RESULT_TAG_RE = re.compile(r"<\s{0,8}/?\s{0,8}tool_result\b", re.IGNORECASE)
_UNTAGGED_START_RE = re.compile(rf'\{{\s{{0,8}}"|\b{TOOL_NAME}\s{{0,8}}\(', re.IGNORECASE)
_PYTHON_CALL_RE = re.compile(rf"{TOOL_NAME}\s{{0,8}}\(([^()\n]{{0,200}})\)", re.IGNORECASE)
_PYTHON_ARGUMENT_RE = re.compile(
    r"""\s*(?:(product_id|location_id)\s*=\s*)?(?:"([^"]*)"|'([^']*)'|([A-Za-z]\d+)|(None|null))\s*"""
)
_PYTHON_POSITIONS = ("product_id", "location_id")


def get_inventory(
    instance: Instance, product_id: str, location_id: str | None = None
) -> dict[str, Any]:
    """Registros del producto. Nunca incluye el disponible ni datos del pedido."""
    if product_id not in instance.product_ids:
        return {"error": ERROR_UNKNOWN_PRODUCT}
    if location_id is not None and location_id not in instance.location_ids:
        return {"error": ERROR_UNKNOWN_LOCATION}
    return {
        "records": [
            {
                "product_id": record.product_id,
                "location_id": record.location_id,
                "physical_stock": record.physical_stock,
                "reserved_stock": record.reserved_stock,
            }
            for record in instance.inventory
            if record.product_id == product_id
            and (location_id is None or record.location_id == location_id)
        ]
    }


def validate_call(call: Any) -> str | None:
    """Devuelve el error de forma de una llamada, o None si esta bien formada."""
    if not isinstance(call, dict) or set(call) != {"name", "arguments"}:
        return ERROR_MALFORMED
    if call["name"] != TOOL_NAME:
        return ERROR_UNKNOWN_TOOL
    arguments = call["arguments"]
    if not isinstance(arguments, dict) or not set(arguments) <= {"product_id", "location_id"}:
        return ERROR_BAD_ARGUMENTS
    location = arguments.get("location_id")
    if not isinstance(arguments.get("product_id"), str):
        return ERROR_BAD_ARGUMENTS
    if location is not None and not isinstance(location, str):
        return ERROR_BAD_ARGUMENTS
    return None


def execute_tool_call(instance: Instance, call: Any) -> dict[str, Any]:
    """Ejecuta `{"name": ..., "arguments": {...}}`. Nunca lanza: un fallo es `{"error"}`."""
    error = validate_call(call)
    if error is not None:
        return {"error": error}
    arguments = call["arguments"]
    return get_inventory(instance, arguments["product_id"], arguments.get("location_id"))


# ------------------------------------------------------------- protocolo de mensajes


def parse_tool_calls(text: str) -> list[Any]:
    """Llamadas de un mensaje, en orden. Una llamada ilegible queda como `None`.

    Lo que esta dentro de <think> no cuenta, igual que en el verificador. Sin etiqueta de
    cierre, la llamada vale si tras la apertura hay un objeto JSON completo: Llama omite el
    cierre siempre. Si el JSON quedo cortado (sin tokens) es una llamada mal formada: el
    harness responde con un error y la ronda se cuenta. Si no hay ninguna etiqueta valida,
    se buscan llamadas sin etiqueta (`_untagged_calls`).
    """
    clean = _clean(text)
    tags = list(_CALL_TAG_RE.finditer(clean))
    calls: list[Any] = []
    index = 0
    while index < len(tags):
        tag = tags[index]
        if tag.group(1):
            index += 1
            continue
        following = tags[index + 1] if index + 1 < len(tags) else None
        if following is None or not following.group(1):
            end = following.start() if following is not None else len(clean)
            calls.append(_load_leading_object(clean[tag.end() : end]))
            index += 1
            continue
        calls.append(_load_call(clean[tag.end() : following.start()]))
        index += 2
    return calls or _untagged_calls(clean)


def _untagged_calls(clean: str) -> list[Any]:
    """Llamadas sin <tool_call>: JSON suelto (en bloque de codigo o tras `tool_call=`) o
    forma Python, `get_inventory("P01", location_id="S1")`.

    Qwen casi nunca escribe la etiqueta aunque la llamada sea correcta. Aceptarlas no regala
    recompensa: los datos siguen saliendo del harness, y lo que no sea una llamada completa
    no cuenta. Un mensaje con <answer> es respuesta final, aunque nombre la herramienta.
    """
    if _ANSWER_TAG_RE.search(clean):
        return []
    calls: list[Any] = []
    position = 0
    while (start := _UNTAGGED_START_RE.search(clean, position)) is not None:
        reader = _json_call_at if clean[start.start()] == "{" else _python_call_at
        call, end = reader(clean, start.start())
        if call is None:
            position = start.end()
        else:
            calls.append(call)
            position = end
    return calls


def _json_call_at(text: str, start: int) -> tuple[Any, int]:
    """Solo cuenta un objeto que nombre la herramienta: el resto es prosa o datos inventados."""
    try:
        value, end = json.JSONDecoder().raw_decode(text, start)
    except (ValueError, RecursionError):
        return None, start
    if isinstance(value, dict) and value.get("name") == TOOL_NAME and "arguments" in value:
        return value, end
    return None, start


def _python_call_at(text: str, start: int) -> tuple[Any, int]:
    """Exige valores literales: asi `def get_inventory(product_id, ...)` no es una llamada."""
    match = _PYTHON_CALL_RE.match(text, start)
    if match is None:
        return None, start
    arguments: dict[str, Any] = {}
    for position, piece in enumerate(match.group(1).split(",")):
        argument = _PYTHON_ARGUMENT_RE.fullmatch(piece)
        if argument is None or position >= len(_PYTHON_POSITIONS):
            return None, start
        key = argument.group(1) or _PYTHON_POSITIONS[position]
        if key in arguments:
            return None, start
        literal = next((group for group in argument.groups()[1:4] if group is not None), None)
        arguments[key] = literal
    if arguments.get("product_id") is None:
        return None, start
    return {"name": TOOL_NAME, "arguments": arguments}, match.end()


def _clean(text: str) -> str:
    return _strip_think(normalize_text(text))


def _load_leading_object(body: str) -> Any:
    """Objeto JSON completo al inicio de `body`, ignorando lo que venga despues."""
    try:
        value, _ = json.JSONDecoder().raw_decode(body.lstrip())
    except (ValueError, RecursionError):
        return None
    return value if isinstance(value, dict) else None


def _load_call(body: str) -> Any:
    try:
        return json.loads(body)
    except (ValueError, RecursionError):
        return None




def visible_start(text: str) -> int:
    """Donde empieza lo que cuenta como respuesta: despues del ultimo </think>.

    Con un <think> sin cerrar no hay nada visible todavia. Nombrar una etiqueta mientras
    se razona no es emitirla, igual que en el verificador.
    """
    closing = text.rfind("</think>")
    if closing >= 0:
        return closing + len("</think>")
    return len(text) if "<think>" in text else 0


def has_tool_result_tag(text: str) -> bool:
    return _RESULT_TAG_RE.search(text, visible_start(text)) is not None


def truncate_at_tool_result(text: str) -> str:
    """Corta antes del primer <tool_result> escrito por el modelo fuera de <think>."""
    match = _RESULT_TAG_RE.search(text, visible_start(text))
    return text if match is None else text[: match.start()].rstrip()


def serialize_observation(result: dict[str, Any]) -> str:
    """Unica serializacion de una observacion; debe ser determinista."""
    payload = json.dumps(result, sort_keys=True, ensure_ascii=False)
    return f"<tool_result>{payload}</tool_result>"


def render_observations(results: list[dict[str, Any]]) -> str:
    """Contenido del mensaje `user` de una ronda: un bloque por llamada, en orden."""
    return "\n".join(serialize_observation(result) for result in results)
