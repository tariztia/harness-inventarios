"""Prompt de cada condicion: un solo mensaje `user`, en espanol.

Lee solo `id`, `family`, `orders`, `product_ids`, `location_ids`, `request` y, en la
condicion visible, `inventory`. Nunca `seed` (su paridad revela la respuesta en
disponibilidad), `expected`, `solution_program`, `complexity` ni `template_id`.

Los ejemplos de formato usan marcadores (`N`, `ID`, `sí o no`) que no se pueden confundir
con una respuesta: copiarlos literalmente da recompensa 0. No van entre < >, porque en la
exploracion los modelos copiaban los angulos alrededor del valor. El verificador rechaza
mencionar la etiqueta de respuesta antes del bloque real, y por eso se pide no nombrarla.

En la condicion tools, el formato de respuesta no va en el prompt: llega con los resultados
(`render_tool_reply`). Con el formato a la vista, los modelos contestaban sin llamar.
"""
from __future__ import annotations

from typing import Any

from .schema import Instance
from .tools import MAX_TOOL_ROUNDS, render_observations

_COMMON_RULES = (
    "Disponible = stock físico − stock reservado. Las reservas nunca se usan para un pedido.",
    "Se permiten pedidos parciales. Por línea: atendidas = mín(cantidad, disponible) y "
    "pendientes = cantidad − atendidas.",
)
_AVAILABILITY_RULES = (
    "El pedido sale completo de la sucursal indicada.",
    "`alcanza` es sí solo si todas las líneas se cubren por completo.",
    "`faltan` es la suma de las unidades pendientes de todas las líneas.",
)
_SELECTION_RULES = (
    "Se elige una sola sucursal, que atiende todo lo que pueda del pedido.",
    "Cobertura de una sucursal: suma de mín(cantidad, disponible) sobre las líneas. Se elige "
    "la de mayor cobertura; si hay empate, gana el ID menor (S1 antes que S2).",
    "`cubiertas` es la cobertura de la elegida y `pendientes` es el total pedido menos "
    "`cubiertas`.",
)
_COMPOSITION_RULES = (
    "Los pedidos se atienden en orden de llegada, el orden en que aparecen (O1, luego O2, ...). "
    "Las líneas de un pedido se procesan en orden.",
    "Cada unidad asignada descuenta el disponible para los pedidos siguientes.",
    "Si un pedido indica una sucursal, solo usa esa sucursal.",
)
_CASCADE_RULE = (
    "Si indica varias, cada línea toma primero de la primera sucursal y lo que falte de la "
    "siguiente, en el orden indicado."
)
_COMPOSITION_REPORT_RULE = (
    "Por pedido se informan atendidas y pendientes, sumadas sobre sus líneas. "
    "`total_pendientes` es la suma de los pendientes de todos los pedidos."
)

_TOOL_SECTION = """\
Herramienta:
get_inventory(product_id, location_id=None) devuelve physical_stock y reserved_stock de un producto. Sin location_id entrega todas sus sucursales.

No conoces el stock y no puedes suponerlo: los valores solo se obtienen con la herramienta.

Ejemplo de llamada para el producto P99 en la sucursal S9, que no existen; usa IDs del catálogo:
<tool_call>{"name": "get_inventory", "arguments": {"product_id": "P99", "location_id": "S9"}}</tool_call>"""

_TOOL_STEPS = f"""\
Pasos:
1. Tu próximo mensaje contiene solo las llamadas que necesitas, una por línea. No calcules ni respondas todavía.
2. Recibirás los resultados y las instrucciones para responder. Máximo {MAX_TOOL_ROUNDS} rondas de llamadas."""

_ANOTHER_ROUND = "Si todavía te falta un dato, pide otra ronda de llamadas. Si no, responde."

_VISIBLE_NOTE = "No hay herramientas: usa estos datos y responde directamente."


def _rules(instance: Instance) -> tuple[str, ...]:
    if instance.family == "availability":
        return _COMMON_RULES + _AVAILABILITY_RULES
    if instance.family == "selection":
        return _COMMON_RULES + _SELECTION_RULES
    has_cascade = any(len(order.location_ids) > 1 for order in instance.orders)
    cascade = (_CASCADE_RULE,) if has_cascade else ()
    return _COMMON_RULES + _COMPOSITION_RULES + cascade + (_COMPOSITION_REPORT_RULE,)


def _answer_lines(instance: Instance) -> list[str]:
    if instance.family == "availability":
        return ["alcanza: sí o no", "faltan: N"]
    if instance.family == "selection":
        return ["sucursal: ID", "cubiertas: N", "pendientes: N"]
    lines: list[str] = []
    for order in instance.orders:
        lines += [f"{order.order_id}_atendidas: N", f"{order.order_id}_pendientes: N"]
    return lines + ["total_pendientes: N"]


def _answer_section(instance: Instance) -> str:
    block = "\n".join(["<answer>", *_answer_lines(instance), "</answer>"])
    return (
        "Formato de respuesta:\n"
        "Primero razona paso a paso: calcula cada valor aplicando las reglas. Después termina "
        "con este bloque, con las claves escritas exactamente así. Reemplaza N por un número, "
        "ID por el ID y `sí o no` por una de las dos:\n"
        f"{block}\n"
        "Abre y cierra el bloque con sus dos etiquetas. Escríbelas una sola vez, al final de tu "
        "respuesta. No las nombres en el razonamiento y no agregues nada después de cerrar."
    )


def _inventory_table(instance: Instance) -> str:
    rows = ["Producto | Sucursal | Stock físico | Stock reservado"]
    rows += [
        f"{r.product_id} | {r.location_id} | {r.physical_stock} | {r.reserved_stock}"
        for r in instance.inventory
    ]
    return "Inventario:\n" + "\n".join(rows) + "\n\n" + _VISIBLE_NOTE


def render_tool_reply(instance: Instance, results: list[dict[str, Any]], round_number: int) -> str:
    """Mensaje `user` tras una ronda: observaciones e instrucciones para responder."""
    parts = [render_observations(results)]
    if round_number < MAX_TOOL_ROUNDS:
        parts.append(_ANOTHER_ROUND)
    parts.append(_answer_section(instance))
    return "\n\n".join(parts)


def render_prompt(instance: Instance, condition: str) -> str:
    if condition not in ("tools", "visible"):
        raise ValueError(f"condicion desconocida: {condition!r}")
    tools = condition == "tools"
    rules = "\n".join(f"- {rule}" for rule in _rules(instance))
    return "\n\n".join(
        [
            f"Caso: {instance.id}",
            "Eres el asistente de inventario de una cadena de sucursales.",
            f"Reglas de negocio:\n{rules}",
            f"Catálogo:\nProductos: {', '.join(instance.product_ids)}\n"
            f"Sucursales: {', '.join(instance.location_ids)}",
            _TOOL_SECTION if tools else _inventory_table(instance),
            f"Solicitud:\n{instance.request}",
            _TOOL_STEPS if tools else _answer_section(instance),
        ]
    )
