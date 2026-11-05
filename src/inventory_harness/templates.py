"""Plantillas en espanol para `Instance.request`.

Cada plantilla recibe los pedidos y las sucursales y devuelve texto sin valores
de stock: las unicas cifras que aparecen (ademas de los IDs) son cantidades
pedidas. Las reglas de negocio y el formato de respuesta los agrega prompts.py.

Las plantillas con `reserved=True` se usan solo en el split `test`, para medir
generalizacion a redacciones no vistas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from .schema import Order, OrderLine


def join_es(items: Sequence[str], conjunction: str = "y") -> str:
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} {conjunction} {items[-1]}"


def _units(quantity: int) -> str:
    return "1 unidad" if quantity == 1 else f"{quantity} unidades"


def _lines_prose(lines: Sequence[OrderLine]) -> str:
    """'12 unidades de P01, 7 de P03 y 3 de P02'."""
    parts = [f"{_units(lines[0].quantity)} de {lines[0].product_id}"]
    parts += [f"{line.quantity} de {line.product_id}" for line in lines[1:]]
    return join_es(parts)


def _lines_compact(lines: Sequence[OrderLine], separator: str = "; ") -> str:
    """'P01 × 12; P03 × 7'."""
    return separator.join(f"{line.product_id} × {line.quantity}" for line in lines)


def _lines_bullets(lines: Sequence[OrderLine]) -> str:
    return "\n".join(f"- {line.product_id}: {_units(line.quantity)}" for line in lines)


def _route_prose(locations: Sequence[str]) -> str:
    """'desde S1 y, si no alcanza, desde S2 y luego desde S3'."""
    route = f"desde {locations[0]}"
    if len(locations) > 1:
        route += f" y, si no alcanza, desde {locations[1]}"
    for location in locations[2:]:
        route += f" y luego desde {location}"
    return route


def _route_short(locations: Sequence[str]) -> str:
    """'S1' o 'S1, si no alcanza S2, si no alcanza S3'."""
    return ", si no alcanza ".join(locations)


# --- Disponibilidad -------------------------------------------------------


def _avail_directa(orders: Sequence[Order], _: Sequence[str]) -> str:
    order = orders[0]
    return (
        f"¿Se puede preparar el pedido {order.order_id} desde la sucursal "
        f"{order.location_ids[0]}? Lleva {_lines_prose(order.lines)}. "
        "Si no alcanza, ¿cuántas unidades faltan en total?"
    )


def _avail_lista(orders: Sequence[Order], _: Sequence[str]) -> str:
    order = orders[0]
    return (
        f"Pedido {order.order_id}, a despachar desde {order.location_ids[0]}:\n"
        f"{_lines_bullets(order.lines)}\n"
        "Indica si alcanza para cubrirlo completo y cuántas unidades faltarían en total."
    )


def _avail_cliente(orders: Sequence[Order], _: Sequence[str]) -> str:
    order = orders[0]
    return (
        f"Un cliente pidió {_lines_prose(order.lines)}; es el pedido {order.order_id}. "
        f"Todo tiene que salir de {order.location_ids[0]}, sin recurrir a otras "
        "sucursales. Dime si alcanza y, de no ser así, cuántas unidades quedarían "
        "faltando."
    )


def _avail_faltante(orders: Sequence[Order], _: Sequence[str]) -> str:
    order = orders[0]
    return (
        f"Necesito saber cuántas unidades faltarían para completar el pedido "
        f"{order.order_id} si lo despachamos solo desde {order.location_ids[0]}, "
        f"y por lo tanto si alcanza o no. El pedido consiste en "
        f"{_lines_prose(order.lines)}."
    )


def _avail_ficha(orders: Sequence[Order], _: Sequence[str]) -> str:
    order = orders[0]
    return (
        "Solicitud de despacho\n"
        f"Pedido: {order.order_id}\n"
        f"Origen: {order.location_ids[0]}\n"
        f"Detalle: {_lines_compact(order.lines)}\n"
        "Consulta: ¿alcanza lo disponible en el origen? Si no, ¿cuántas unidades "
        "faltan en total?"
    )


# --- Seleccion ------------------------------------------------------------


def _sel_directa(orders: Sequence[Order], locations: Sequence[str]) -> str:
    order = orders[0]
    return (
        f"Hay que atender el pedido {order.order_id} ({_lines_prose(order.lines)}) "
        f"desde una sola sucursal. ¿Cuál conviene elegir entre {join_es(locations, 'o')} "
        "para cubrir la mayor cantidad de unidades? Indica también cuántas cubre y "
        "cuántas quedan pendientes."
    )


def _sel_lista(orders: Sequence[Order], locations: Sequence[str]) -> str:
    order = orders[0]
    return (
        f"Pedido {order.order_id}:\n{_lines_bullets(order.lines)}\n"
        f"Sucursales candidatas: {join_es(locations)}.\n"
        "Solo una de ellas puede despachar. Elige la que cubra más unidades e "
        "informa cuántas cubre y cuántas quedan pendientes."
    )


def _sel_comparar(orders: Sequence[Order], locations: Sequence[str]) -> str:
    order = orders[0]
    return (
        f"Compara {join_es(locations)} para el pedido {order.order_id}, que pide "
        f"{_lines_prose(order.lines)}. Todo saldría de una única sucursal: "
        "dime en cuál se cubren más unidades, cuántas son y cuántas quedarían "
        "pendientes."
    )


def _sel_envio(orders: Sequence[Order], locations: Sequence[str]) -> str:
    order = orders[0]
    return (
        f"Un cliente quiere recibir {_lines_prose(order.lines)} en un solo envío "
        f"(pedido {order.order_id}). Podemos mandarlo desde {join_es(locations, 'o')}. "
        "¿Desde dónde lo despachamos para que salga la mayor cantidad posible? "
        "Dime además cuántas unidades saldrían y cuántas quedarían pendientes."
    )


def _sel_ficha(orders: Sequence[Order], locations: Sequence[str]) -> str:
    order = orders[0]
    return (
        "Asignación de sucursal\n"
        f"Pedido: {order.order_id}\n"
        f"Detalle: {_lines_compact(order.lines)}\n"
        f"Candidatas: {', '.join(locations)}\n"
        "Consulta: ¿qué única sucursal cubre más unidades del pedido, cuántas "
        "cubre y cuántas quedan pendientes?"
    )


# --- Composicion ----------------------------------------------------------


def _order_ids(orders: Sequence[Order]) -> str:
    return join_es([order.order_id for order in orders])


_REPORT = (
    "para cada pedido, cuántas unidades se atienden y cuántas quedan pendientes, "
    "además del total pendiente"
)


def _comp_lista(orders: Sequence[Order], _: Sequence[str]) -> str:
    rows = "\n".join(
        f"- {o.order_id}: {_lines_prose(o.lines)}, {_route_prose(o.location_ids)}"
        for o in orders
    )
    return f"Llegaron estos pedidos, en este orden:\n{rows}\nCalcula, {_REPORT}."


def _comp_relato(orders: Sequence[Order], _: Sequence[str]) -> str:
    connectors = ["Después", "Luego", "Más tarde"]
    sentences = []
    for index, order in enumerate(orders):
        if index == 0:
            opening = "Primero"
        elif index == len(orders) - 1:
            opening = "Por último"
        else:
            opening = connectors[index - 1]
        sentences.append(
            f"{opening} llegó {order.order_id}, que pide {_lines_prose(order.lines)} "
            f"{_route_prose(order.location_ids)}."
        )
    return f"{' '.join(sentences)} ¿Cómo queda cada uno? Quiero saber, {_REPORT}."


def _comp_competencia(orders: Sequence[Order], _: Sequence[str]) -> str:
    details = "; ".join(
        f"{o.order_id} pide {_lines_prose(o.lines)} {_route_prose(o.location_ids)}"
        for o in orders
    )
    return (
        f"Los pedidos {_order_ids(orders)} compiten por el mismo stock y se atienden "
        f"por orden de llegada, en ese orden. {details}. Calcula, {_REPORT}."
    )


def _comp_total_primero(orders: Sequence[Order], _: Sequence[str]) -> str:
    rows = "\n".join(
        f"{o.order_id} → {_lines_compact(o.lines, ', ')} ({_route_short(o.location_ids)})"
        for o in orders
    )
    return (
        f"¿Cuántas unidades quedan pendientes en total si procesamos {_order_ids(orders)} "
        "en ese orden? Necesito también el detalle de unidades atendidas y pendientes "
        f"de cada pedido. Entre paréntesis va la sucursal de la que sale:\n{rows}"
    )


def _comp_planilla(orders: Sequence[Order], _: Sequence[str]) -> str:
    rows = "\n".join(
        f"{o.order_id} | {_route_short(o.location_ids)} | {_lines_compact(o.lines, ', ')}"
        for o in orders
    )
    return (
        "Planilla de despacho\n"
        f"Orden de atención: {_order_ids(orders)}\n"
        f"Pedido | Sucursal | Detalle\n{rows}\n"
        f"Consulta: indica, {_REPORT}."
    )


# --- Registro -------------------------------------------------------------


@dataclass(frozen=True)
class Template:
    template_id: str
    render: Callable[[Sequence[Order], Sequence[str]], str]
    reserved: bool = False


TEMPLATES: dict[str, tuple[Template, ...]] = {
    "availability": (
        Template("avail_directa", _avail_directa),
        Template("avail_lista", _avail_lista),
        Template("avail_cliente", _avail_cliente),
        Template("avail_faltante", _avail_faltante),
        Template("avail_ficha", _avail_ficha, reserved=True),
    ),
    "selection": (
        Template("sel_directa", _sel_directa),
        Template("sel_lista", _sel_lista),
        Template("sel_comparar", _sel_comparar),
        Template("sel_envio", _sel_envio),
        Template("sel_ficha", _sel_ficha, reserved=True),
    ),
    "composition": (
        Template("comp_lista", _comp_lista),
        Template("comp_relato", _comp_relato),
        Template("comp_competencia", _comp_competencia),
        Template("comp_total_primero", _comp_total_primero),
        Template("comp_planilla", _comp_planilla, reserved=True),
    ),
}
