# Reglas de negocio

Fuente de verdad del dominio. El solucionador, las plantillas y el texto de los prompts deben coincidir con este documento.

## Datos

- Cada instancia tiene un inventario completo: existe un registro por cada par producto × sucursal.
- IDs: productos `P01`, `P02`, ...; sucursales `S1`, `S2`, ...; pedidos `O1`, `O2`, ...
- `physical_stock` y `reserved_stock` son enteros no negativos, y `reserved_stock <= physical_stock`.
- **Disponible = stock físico − unidades reservadas.** Las reservas nunca se pueden usar para un pedido.

## Asignación

- Se permiten pedidos parciales: si no alcanza, se asigna lo que haya y el resto queda pendiente.
- Para una línea de pedido: `atendidas = min(cantidad, disponible)` y `pendientes = cantidad − atendidas`.
- Las líneas de un pedido se procesan en el orden en que aparecen.
- Un pedido nunca repite un producto en dos líneas; el generador no lo produce.

## Disponibilidad

Un pedido de una o más líneas, desde una sola sucursal.

- `alcanza` es verdadero si y solo si todas las líneas se cubren por completo.
- `faltan` es la suma de las unidades pendientes de todas las líneas.

## Selección

Un pedido de una o más líneas. Se elige **una sola** sucursal, que atiende todo lo que pueda del pedido.

- Cobertura de una sucursal: suma de `min(cantidad, disponible)` sobre las líneas.
- Se elige la de mayor cobertura. **Empate:** gana el ID menor (`S1` antes que `S2`).
- `cubiertas` es la cobertura de la elegida y `pendientes` es el total pedido menos `cubiertas`.

## Composición

Varios pedidos que compiten por el mismo stock.

- **Prioridad:** los pedidos se atienden en orden de llegada, es decir, en el orden en que aparecen (`O1`, luego `O2`, ...).
- Cada unidad asignada descuenta el disponible para los pedidos siguientes.
- Si un pedido indica una sucursal, solo usa esa sucursal.
- Si indica varias (cascada, solo en `hard`), cada línea toma primero de la primera sucursal, y lo que falte de la siguiente, en el orden indicado.
- Por pedido se informa `atendidas` y `pendientes` (sumadas sobre sus líneas). `total_pendientes` es la suma sobre todos los pedidos.

## Niveles de dificultad (a calibrar)

| Familia | easy | medium | hard |
|---|---|---|---|
| Disponibilidad | 1 línea | 2 líneas | 3–4 líneas |
| Selección | 1 línea, 2–3 sucursales | 2 líneas, 3 sucursales | 3–4 líneas, 4–5 sucursales |
| Composición | 2 pedidos, 1 producto, 1 sucursal | 3 pedidos, 2 productos, 1–2 sucursales | 4–5 pedidos, 3 productos, 2–3 sucursales, con cascada |

Estos niveles son hipótesis. La dificultad real se mide en la línea base.
