"""Generador procedural de instancias. Ver docs/reglas_negocio.md y docs/contrato.md.

Cada instancia se construye en cuatro pasos: se fijan objetivos (por ejemplo, si
alcanza, o que sucursal gana), se propone un inventario, `solve` calcula
`expected` y, si la propuesta no cumple los objetivos, se reintenta con el mismo
`random.Random`. Todo es determinista: la semilla se deriva con SHA-256.

Los controles de degeneracion comparan `solve` sobre el caso real con `solve`
sobre variantes del caso (sin reservas, orden invertido, etc.), asi que aqui no
hay reglas de asignacion. La unica excepcion es la traza que produce
`solution_program` y `required_records`; los tests comprueban que coincide con
el solucionador, de modo que funciona como segunda implementacion.

Definicion de `complexity`:
- n_records: largo de `required_records`.
- n_entities: productos + sucursales + pedidos que intervienen en esos registros.
- n_required_calls: productos distintos en `required_records`, porque una
  llamada a `get_inventory` sin `location_id` trae todas sus sucursales.
- n_operations: operaciones aritmeticas o comparaciones de la solucion.
    availability: R restas + L minimos + (L-1) sumas + 1 comparacion.
    selection: R restas + R minimos + k(L-1) sumas + (k-1) comparaciones + 1 resta.
    composition: R restas + 2 por paso de asignacion (minimo y descuento) +
    2(L_p-1) sumas por pedido p + (pedidos-1) sumas del total.
  R: registros, L: lineas, k: sucursales. Un paso es una sucursal visitada por
  una linea con unidades sin asignar.
- dependency_depth: largo de la cadena mas larga de resultados dependientes.
    availability: 3 (disponible, pendiente, decision).
    selection: 4 con una linea (disponible, minimo, comparacion, pendientes) y
    5 con varias (agrega la suma de cobertura).
    composition: pasos encadenados por stock compartido o por cascada, mas el
    disponible inicial y la suma final.
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from dataclasses import replace
from types import SimpleNamespace
from typing import Any

from .schema import DIFFICULTIES, FAMILIES, SPLITS, Instance, InventoryRecord, Order, OrderLine
from .solver import solve
from .templates import TEMPLATES, Template

MAX_STOCK = 60
MAX_ATTEMPTS = 4000
# Tasas objetivo por instancia.
SELECTION_TIE_RATE = 0.15
SELECTION_FULL_COVER_RATE = 0.30
SELECTION_PHYSICAL_TRAP_RATE = 0.75
COMPOSITION_SHORTAGE_RATE = 0.85
AVAILABILITY_FLIP_RATE = 0.70
TEST_RESERVED_TEMPLATE_RATE = 0.50
# Espaciado de semillas en generate_dataset: splits y celdas no se solapan.
SPLIT_SEED_STRIDE = 10**9
CELL_SEED_STRIDE = 10**7

Pair = tuple[str, str]


def _product_id(index: int) -> str:
    return f"P{index:02d}"


def _location_id(index: int) -> str:
    return f"S{index}"


def _catalog(n_products: int, n_locations: int) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return (
        tuple(_product_id(i + 1) for i in range(n_products)),
        tuple(_location_id(i + 1) for i in range(n_locations)),
    )


def _rng_for(family: str, difficulty: str, split: str, seed: int) -> random.Random:
    key = f"{family}|{difficulty}|{split}|{seed}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest()[:16], "big"))


def _noise_record(rng: random.Random, product: str, location: str) -> InventoryRecord:
    """Registro que el pedido no usa; solo completa producto × sucursal."""
    physical = rng.randint(0, MAX_STOCK)
    return InventoryRecord(product, location, physical, rng.randint(0, min(physical, 20)))


def _complete_inventory(
    rng: random.Random,
    products: tuple[str, ...],
    locations: tuple[str, ...],
    fixed: dict[Pair, tuple[int, int]],
) -> tuple[InventoryRecord, ...]:
    """`fixed` asigna (disponible, reservado); el resto se rellena con ruido."""
    records = []
    for product in products:
        for location in locations:
            if (product, location) in fixed:
                available, reserved = fixed[(product, location)]
                records.append(
                    InventoryRecord(product, location, available + reserved, reserved)
                )
            else:
                records.append(_noise_record(rng, product, location))
    return tuple(records)


def _view(
    family: str,
    inventory: tuple[InventoryRecord, ...],
    orders: tuple[Order, ...],
    location_ids: tuple[str, ...],
) -> SimpleNamespace:
    return SimpleNamespace(
        family=family, inventory=inventory, orders=orders, location_ids=location_ids
    )


def _without_reserves(instance: Any) -> SimpleNamespace:
    inventory = tuple(replace(r, reserved_stock=0) for r in instance.inventory)
    return _view(instance.family, inventory, instance.orders, instance.location_ids)


def _no_discount_result(instance: Any) -> dict[str, Any]:
    """Respuesta si cada pedido viera el stock inicial completo."""
    orders: dict[str, dict[str, int]] = {}
    for order in instance.orders:
        alone = _view(instance.family, instance.inventory, (order,), instance.location_ids)
        orders.update(solve(alone)["orders"])
    total = sum(result["pending_units"] for result in orders.values())
    return {"orders": orders, "total_pending": total}


def _reversed_priority_result(instance: Any) -> dict[str, Any]:
    view = _view(
        instance.family, instance.inventory, instance.orders[::-1], instance.location_ids
    )
    return solve(view)


def _first_location_only_result(instance: Any) -> dict[str, Any]:
    orders = tuple(replace(o, location_ids=o.location_ids[:1]) for o in instance.orders)
    return solve(_view(instance.family, instance.inventory, orders, instance.location_ids))


# --- Muestreo por familia -------------------------------------------------


def _draw_availability(
    rng: random.Random, difficulty: str, can_fulfill: bool
) -> tuple[tuple[InventoryRecord, ...], tuple[Order, ...], tuple[str, ...], tuple[str, ...]]:
    n_lines = {"easy": 1, "medium": 2, "hard": rng.randint(3, 4)}[difficulty]
    products, locations = _catalog(n_lines + rng.randint(1, 2), rng.randint(2, 3))
    location = rng.choice(locations)
    chosen = rng.sample(products, n_lines)
    short = set(rng.sample(chosen, rng.randint(1, n_lines))) if not can_fulfill else set()

    fixed: dict[Pair, tuple[int, int]] = {}
    lines = []
    for product in chosen:
        quantity = rng.randint(3, 35)
        if product in short:
            deficit = rng.randint(1, min(quantity, 15))
            available = quantity - deficit
            if deficit == 1 or rng.random() < AVAILABILITY_FLIP_RATE:
                # Contando el stock fisico, esta linea pareceria cubierta.
                reserved = deficit + rng.randint(0, 6)
            else:
                reserved = rng.randint(1, deficit - 1)
        else:
            available = quantity + rng.randint(0, 10)
            reserved = 0 if rng.random() < 0.1 else rng.randint(1, 15)
        lines.append(OrderLine(product, quantity))
        fixed[(product, location)] = (available, reserved)

    inventory = _complete_inventory(rng, products, locations, fixed)
    return inventory, (Order("O1", tuple(lines), (location,)),), products, locations


def _split_deficit(rng: random.Random, deficit: int, caps: list[int]) -> list[int]:
    """Reparte `deficit` entre lineas sin superar `caps`."""
    shares = [0] * len(caps)
    indices = list(range(len(caps)))
    rng.shuffle(indices)
    while deficit > 0:
        for i in indices:
            taken = rng.randint(0, min(caps[i] - shares[i], deficit))
            shares[i] += taken
            deficit -= taken
    return shares


def _selection_column(
    rng: random.Random, quantities: list[int], coverage: int
) -> list[int]:
    """Disponibles por linea cuya cobertura es exactamente `coverage`."""
    deficits = _split_deficit(rng, sum(quantities) - coverage, quantities)
    return [
        q - d if d else q + rng.randint(0, 8) for q, d in zip(quantities, deficits)
    ]


def _draw_selection(
    rng: random.Random, difficulty: str
) -> tuple[tuple[InventoryRecord, ...], tuple[Order, ...], tuple[str, ...], tuple[str, ...]]:
    n_lines, n_locations, quantity_range = {
        "easy": (1, rng.randint(2, 3), (5, 35)),
        "medium": (2, 3, (4, 25)),
        "hard": (rng.randint(3, 4), rng.randint(4, 5), (3, 20)),
    }[difficulty]
    products, locations = _catalog(n_lines + rng.randint(0, 1), n_locations)
    chosen = rng.sample(products, n_lines)
    quantities = [rng.randint(*quantity_range) for _ in chosen]
    lines = tuple(OrderLine(p, q) for p, q in zip(chosen, quantities))
    order = Order("O1", lines)
    total = sum(quantities)

    # Sin empate, la posicion ganadora es uniforme. El empate exige una rival
    # posterior, asi que la probabilidad se corrige para no sesgar la posicion.
    winner = rng.randrange(n_locations)
    tie_probability = SELECTION_TIE_RATE * n_locations / (n_locations - 1)
    wants_tie = winner < n_locations - 1 and rng.random() < tie_probability
    tied_with = rng.randrange(winner + 1, n_locations) if wants_tie else None
    full_cover = rng.random() < SELECTION_FULL_COVER_RATE
    # Con cobertura total, el fisico solo puede engañar desde un ID menor.
    wants_trap = rng.random() < SELECTION_PHYSICAL_TRAP_RATE and not (
        full_cover and winner == 0
    )

    for attempt in range(MAX_ATTEMPTS):
        if attempt == MAX_ATTEMPTS // 2:
            wants_trap = False
        best = total if full_cover else total - rng.randint(1, max(1, total * 6 // 10))
        fixed: dict[Pair, tuple[int, int]] = {}
        decoy = None
        if wants_trap:
            pool = range(winner) if full_cover else [
                i for i in range(n_locations) if i != winner
            ]
            decoy = rng.choice(list(pool))
        for index, location in enumerate(locations):
            if index == winner or index == tied_with:
                coverage = best
            else:
                coverage = best - rng.randint(1, min(best, max(3, total // 3)))
            column = _selection_column(rng, quantities, coverage)
            for product, quantity, available in zip(chosen, quantities, column):
                if index == decoy:
                    reserved = max(quantity - available, 0) + rng.randint(0, 6)
                elif index == winner and wants_trap:
                    reserved = rng.randint(0, 3)
                else:
                    reserved = rng.randint(1, 12)
                fixed[(product, location)] = (available, reserved)
        inventory = _complete_inventory(rng, products, locations, fixed)
        if max(r.physical_stock for r in inventory) > MAX_STOCK:
            continue
        view = _view("selection", inventory, (order,), locations)
        if solve(view)["location_id"] != locations[winner]:
            continue
        physical_choice = solve(_without_reserves(view))["location_id"]
        if wants_trap and physical_choice == locations[winner]:
            continue
        return inventory, (order,), products, locations
    raise RuntimeError("selection: no se encontro una instancia valida")


def _composition_structure(
    rng: random.Random, difficulty: str
) -> tuple[tuple[str, ...], tuple[str, ...], list[Order]]:
    """Propone pedidos sin cantidades definitivas; todo producto y sucursal se usa."""
    n_orders, n_products, n_locations, quantity_range = {
        "easy": (2, 1, 1, (5, 35)),
        "medium": (3, 2, rng.randint(1, 2), (3, 25)),
        "hard": (rng.randint(4, 5), 3, rng.randint(2, 3), (3, 20)),
    }[difficulty]
    products, locations = _catalog(n_products, n_locations)
    while True:
        orders = []
        for index in range(n_orders):
            n_lines = 1 if difficulty == "easy" else rng.randint(1, 2)
            lines = tuple(
                OrderLine(p, rng.randint(*quantity_range))
                for p in rng.sample(products, n_lines)
            )
            n_route = 1
            if difficulty == "hard" and rng.random() < 0.5:
                n_route = rng.randint(2, n_locations)
            orders.append(Order(f"O{index + 1}", lines, tuple(rng.sample(locations, n_route))))
        used_products = {line.product_id for o in orders for line in o.lines}
        used_locations = {location for o in orders for location in o.location_ids}
        has_cascade = any(len(o.location_ids) > 1 for o in orders)
        if (
            len(used_products) == n_products
            and len(used_locations) == n_locations
            and (has_cascade or difficulty != "hard")
        ):
            return products, locations, orders


def _draw_composition(
    rng: random.Random, difficulty: str
) -> tuple[tuple[InventoryRecord, ...], tuple[Order, ...], tuple[str, ...], tuple[str, ...]]:
    wants_shortage = rng.random() < COMPOSITION_SHORTAGE_RATE
    for _ in range(MAX_ATTEMPTS):
        products, locations, orders = _composition_structure(rng, difficulty)
        demand: Counter[Pair] = Counter()
        cascade_heads: set[Pair] = set()
        for order in orders:
            for line in order.lines:
                for location in order.location_ids:
                    demand[(line.product_id, location)] += line.quantity
                if len(order.location_ids) > 1:
                    cascade_heads.add((line.product_id, order.location_ids[0]))
        if len(demand) == sum(len(o.lines) * len(o.location_ids) for o in orders):
            continue  # Ningun registro es compartido: no hay competencia.

        fixed: dict[Pair, tuple[int, int]] = {}
        for pair in sorted(demand):
            units = demand[pair]
            if wants_shortage:
                available = int(units * rng.uniform(0.3, 0.95))
            elif pair in cascade_heads:
                available = int(units * rng.uniform(0.4, 0.9))
            else:
                available = units + rng.randint(0, 8)
            fixed[pair] = (available, rng.randint(1, 12))
        inventory = _complete_inventory(rng, products, locations, fixed)
        if max(r.physical_stock for r in inventory) > MAX_STOCK:
            continue

        view = _view("composition", inventory, tuple(orders), locations)
        expected = solve(view)
        short = expected["total_pending"] > 0
        if short != wants_shortage:
            continue
        if difficulty == "hard" and _first_location_only_result(view) == expected:
            continue
        if short and (
            _no_discount_result(view) == expected
            or _reversed_priority_result(view) == expected
            or solve(_without_reserves(view)) == expected
        ):
            continue
        return inventory, tuple(orders), products, locations
    raise RuntimeError("composition: no se encontro una instancia valida")


# --- Traza: solution_program, required_records y complejidad --------------


def _stock_text(record: InventoryRecord) -> str:
    return f"{record.physical_stock}-{record.reserved_stock}={record.available}"


def _trace_availability(
    inventory: dict[Pair, InventoryRecord], order: Order
) -> tuple[str, tuple[Pair, ...], dict[str, int]]:
    location = order.location_ids[0]
    rows, pendings, pairs = [], [], []
    for line in order.lines:
        record = inventory[(line.product_id, location)]
        covered = min(line.quantity, record.available)
        pending = line.quantity - covered
        rows.append(
            f"{line.product_id}@{location}: disp={_stock_text(record)}; "
            f"min({line.quantity},{record.available})={covered}; pendiente {pending}"
        )
        pendings.append(pending)
        pairs.append((line.product_id, location))
    missing = sum(pendings)
    rows.append(f"=> alcanza={'si' if missing == 0 else 'no'}, faltan={missing}")
    n_lines = len(order.lines)
    complexity = {
        "n_operations": len(pairs) + n_lines + (n_lines - 1) + 1,
        "n_entities": n_lines + 1 + 1,
        "dependency_depth": 3,
    }
    return "\n".join(rows), tuple(sorted(pairs)), complexity


def _trace_selection(
    inventory: dict[Pair, InventoryRecord], order: Order, locations: tuple[str, ...]
) -> tuple[str, tuple[Pair, ...], dict[str, int]]:
    rows, pairs, coverages = [], [], {}
    for location in locations:
        terms = []
        for line in order.lines:
            record = inventory[(line.product_id, location)]
            covered = min(line.quantity, record.available)
            terms.append((line.product_id, record, line.quantity, covered))
            pairs.append((line.product_id, location))
        coverages[location] = sum(term[3] for term in terms)
        detail = "; ".join(
            f"{p} disp={_stock_text(r)}, min({q},{r.available})={c}"
            for p, r, q, c in terms
        )
        rows.append(f"{location}: {detail}; cobertura={coverages[location]}")
    best = max(coverages.values())
    tied = [location for location in locations if coverages[location] == best]
    requested = sum(line.quantity for line in order.lines)
    if len(tied) > 1:
        rows.append(f"empate entre {', '.join(tied)}: gana el ID menor")
    rows.append(
        f"=> sucursal={tied[0]}, cubiertas={best}, pendientes={requested}-{best}={requested - best}"
    )
    n_lines, k = len(order.lines), len(locations)
    complexity = {
        "n_operations": 2 * len(pairs) + k * (n_lines - 1) + (k - 1) + 1,
        "n_entities": n_lines + k + 1,
        "dependency_depth": 4 if n_lines == 1 else 5,
    }
    return "\n".join(rows), tuple(sorted(pairs)), complexity


def _trace_composition(
    inventory: dict[Pair, InventoryRecord], orders: tuple[Order, ...]
) -> tuple[str, tuple[Pair, ...], dict[str, int]]:
    stock: dict[Pair, int] = {}
    depth_of: dict[Pair, int] = {}
    rows, totals = [], []
    steps = max_depth = 0
    for order in orders:
        parts, covered_total, pending_total = [], 0, 0
        for line in order.lines:
            unassigned = line.quantity
            hops, previous_depth = [], 0
            for location in order.location_ids:
                if unassigned == 0:
                    break
                pair = (line.product_id, location)
                if pair not in stock:
                    stock[pair] = inventory[pair].available
                    depth_of[pair] = 1
                    rows.append(f"disp {line.product_id}@{location}={_stock_text(inventory[pair])}")
                taken = min(unassigned, stock[pair])
                hops.append(f"{location} min({unassigned},{stock[pair]})={taken}")
                stock[pair] -= taken
                unassigned -= taken
                steps += 1
                previous_depth = 1 + max(depth_of[pair], previous_depth)
                depth_of[pair] = previous_depth
                max_depth = max(max_depth, previous_depth)
            covered_total += line.quantity - unassigned
            pending_total += unassigned
            parts.append(f"{line.product_id} x{line.quantity}: {', '.join(hops)}")
        rows.append(
            f"{order.order_id}: {'; '.join(parts)} -> "
            f"atendidas={covered_total}, pendientes={pending_total}"
        )
        totals.append((order.order_id, covered_total, pending_total))
    summary = ", ".join(f"{o}={c}/{p}" for o, c, p in totals)
    total = sum(p for _, _, p in totals)
    rows.append(f"=> {summary}, total_pendientes={total}")
    pairs = tuple(sorted(stock))
    entities = len({p for p, _ in pairs}) + len({l for _, l in pairs}) + len(orders)
    complexity = {
        "n_operations": len(pairs)
        + 2 * steps
        + sum(2 * (len(o.lines) - 1) for o in orders)
        + len(orders)
        - 1,
        "n_entities": entities,
        "dependency_depth": max_depth + 1,
    }
    return "\n".join(rows), pairs, complexity


def _trace(
    family: str,
    inventory: tuple[InventoryRecord, ...],
    orders: tuple[Order, ...],
    locations: tuple[str, ...],
) -> tuple[str, tuple[Pair, ...], dict[str, int]]:
    by_pair = {(r.product_id, r.location_id): r for r in inventory}
    if family == "availability":
        program, pairs, complexity = _trace_availability(by_pair, orders[0])
    elif family == "selection":
        program, pairs, complexity = _trace_selection(by_pair, orders[0], locations)
    else:
        program, pairs, complexity = _trace_composition(by_pair, orders)
    complexity = {
        **complexity,
        "n_records": len(pairs),
        "n_required_calls": len({product for product, _ in pairs}),
    }
    return program, pairs, complexity


# --- API publica ----------------------------------------------------------


def templates_for_split(family: str, split: str) -> tuple[Template, ...]:
    """Plantillas utilizables en un split; las reservadas solo aparecen en test."""
    templates = TEMPLATES[family]
    return templates if split == "test" else tuple(t for t in templates if not t.reserved)


def _choose_template(rng: random.Random, family: str, split: str) -> Template:
    shared = [t for t in TEMPLATES[family] if not t.reserved]
    reserved = [t for t in TEMPLATES[family] if t.reserved]
    # Sube la cuota de las reservadas en test para medir generalizacion con muestra util.
    if split == "test" and rng.random() < TEST_RESERVED_TEMPLATE_RATE:
        return rng.choice(reserved)
    return rng.choice(shared)


def generate_instance(family: str, difficulty: str, split: str, seed: int) -> Instance:
    if family not in FAMILIES or difficulty not in DIFFICULTIES or split not in SPLITS:
        raise ValueError(f"celda invalida: {family}/{difficulty}/{split}")
    rng = _rng_for(family, difficulty, split, seed)
    if family == "availability":
        # Con semillas consecutivas la tasa queda en 50 %. `Instance.seed` no debe
        # llegar al modelo, porque su paridad revela la respuesta.
        drawn = _draw_availability(rng, difficulty, can_fulfill=seed % 2 == 0)
    elif family == "selection":
        drawn = _draw_selection(rng, difficulty)
    else:
        drawn = _draw_composition(rng, difficulty)
    inventory, orders, products, locations = drawn

    template = _choose_template(rng, family, split)
    # Las sucursales se mencionan en desorden para no igualar orden de texto y desempate.
    mentioned = list(locations)
    if family == "selection":
        rng.shuffle(mentioned)
    expected = solve(_view(family, inventory, orders, locations))
    program, required, complexity = _trace(family, inventory, orders, locations)
    return Instance(
        # Sin la semilla: su paridad decide can_fulfill. generate_dataset lo reemplaza.
        id=f"{split}_{family}_{difficulty}_{rng.randrange(10000):04d}",
        seed=seed,
        family=family,
        difficulty=difficulty,
        split=split,
        template_id=template.template_id,
        inventory=inventory,
        orders=orders,
        product_ids=products,
        location_ids=locations,
        request=template.render(orders, mentioned),
        expected=expected,
        required_records=required,
        complexity=complexity,
        solution_program=program,
    )


def fingerprint(instance: Instance) -> str:
    """Huella canonica de (familia, inventario normalizado, pedidos).

    Dos instancias son equivalentes si plantean el mismo calculo con los mismos
    numeros. Se ignoran la plantilla, los registros que no intervienen y los
    nombres de producto; tambien las sucursales, salvo en seleccion, donde el ID
    decide los empates. En disponibilidad y seleccion las lineas son
    intercambiables; en composicion el orden importa y se conserva.
    """
    stock = {
        (r.product_id, r.location_id): (r.physical_stock, r.reserved_stock)
        for r in instance.inventory
    }
    if instance.family == "availability":
        order = instance.orders[0]
        location = order.location_ids[0]
        canonical: Any = sorted(
            (line.quantity, stock[(line.product_id, location)]) for line in order.lines
        )
    elif instance.family == "selection":
        canonical = sorted(
            (line.quantity, [stock[(line.product_id, l)] for l in instance.location_ids])
            for line in instance.orders[0].lines
        )
    else:
        products: dict[str, int] = {}
        locations: dict[str, int] = {}
        required = set(instance.required_records)
        rows = []
        for order in instance.orders:
            route = [locations.setdefault(l, len(locations)) for l in order.location_ids]
            lines = []
            for line in order.lines:
                product = products.setdefault(line.product_id, len(products))
                reachable = [
                    stock[(line.product_id, l)]
                    for l in order.location_ids
                    if (line.product_id, l) in required
                ]
                lines.append((product, line.quantity, reachable))
            rows.append((route, lines))
        canonical = rows
    payload = json.dumps([instance.family, canonical], separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def generate_dataset(config: dict[str, Any]) -> list[Instance]:
    """Genera todas las celdas (family, difficulty) de cada split, sin duplicados."""
    base_seed = config.get("base_seed", 0)
    n_per_cell = config["n_per_cell"]
    seen: set[str] = set()
    instances: list[Instance] = []
    cells = [(f, d) for f in FAMILIES for d in DIFFICULTIES]
    for split_index, split in enumerate(SPLITS):
        count = n_per_cell.get(split, 0)
        for cell_index, (family, difficulty) in enumerate(cells):
            first_seed = (
                base_seed + split_index * SPLIT_SEED_STRIDE + cell_index * CELL_SEED_STRIDE
            )
            # La paridad de la semilla decide can_fulfill y el indice del ID llega al
            # modelo ("Caso: <id>"): barajar evita que el ID filtre la respuesta.
            offsets = list(range(count))
            random.Random(f"{base_seed}|{split}|{family}|{difficulty}").shuffle(offsets)
            for index, offset in enumerate(offsets):
                # El salto es par y multiplo de 2*count: conserva la paridad de la
                # semilla y no pisa a otro indice.
                for retry in range(MAX_ATTEMPTS):
                    instance = generate_instance(
                        family, difficulty, split, first_seed + offset + retry * 2 * count
                    )
                    mark = fingerprint(instance)
                    if mark not in seen:
                        seen.add(mark)
                        break
                else:
                    raise RuntimeError(f"celda agotada: {family}/{difficulty}/{split}")
                instances.append(
                    replace(instance, id=f"{split}_{family}_{difficulty}_{index:04d}")
                )
    return instances


# --- Estadisticas de degeneracion -----------------------------------------


def degeneracy_metrics(instance: Instance) -> dict[str, Any]:
    """Indicadores por instancia, calculados con `solve` sobre variantes."""
    expected = solve(instance)
    without_reserves = solve(_without_reserves(instance))
    metrics: dict[str, Any] = {"ignore_reserves_changes": without_reserves != expected}
    if instance.family == "availability":
        metrics["can_fulfill"] = expected["can_fulfill"]
        metrics["ignore_reserves_flips"] = (
            without_reserves["can_fulfill"] != expected["can_fulfill"]
        )
        if not expected["can_fulfill"]:
            metrics["deficit"] = expected["missing_units"]
    elif instance.family == "selection":
        winner = expected["location_id"]
        rivals = tuple(l for l in instance.location_ids if l != winner)
        rival_best = solve(
            _view("selection", instance.inventory, instance.orders, rivals)
        )["covered_units"]
        metrics["winner_position"] = instance.location_ids.index(winner)
        metrics["physical_choice_differs"] = without_reserves["location_id"] != winner
        metrics["tie"] = rival_best == expected["covered_units"]
        metrics["has_pending"] = expected["pending_units"] > 0
    else:
        metrics["shortage"] = expected["total_pending"] > 0
        metrics["ignore_priority_changes"] = _reversed_priority_result(instance) != expected
        metrics["no_discount_changes"] = _no_discount_result(instance) != expected
        if instance.difficulty == "hard":
            metrics["cascade_used"] = _first_location_only_result(instance) != expected
    return metrics


def dataset_stats(instances: list[Instance]) -> dict[str, Any]:
    """Conteos y tasas por celda (family/difficulty), agregando los splits."""
    grouped: dict[str, list[Instance]] = {}
    for instance in instances:
        grouped.setdefault(f"{instance.family}/{instance.difficulty}", []).append(instance)
    cells: dict[str, dict[str, Any]] = {}
    for cell in sorted(grouped):
        group = grouped[cell]
        rows = [degeneracy_metrics(instance) for instance in group]
        summary: dict[str, Any] = {
            "n": len(group),
            "templates": dict(sorted(Counter(i.template_id for i in group).items())),
        }
        boolean_keys = sorted({k for row in rows for k, v in row.items() if isinstance(v, bool)})
        for key in boolean_keys:
            values = [row[key] for row in rows if key in row]
            summary[f"{key}_rate"] = round(sum(values) / len(values), 3)
        deficits = [row["deficit"] for row in rows if "deficit" in row]
        if deficits:
            summary["deficit_mean"] = round(sum(deficits) / len(deficits), 2)
            summary["deficit_equal_1_rate"] = round(deficits.count(1) / len(deficits), 3)
        positions = [row["winner_position"] for row in rows if "winner_position" in row]
        if positions:
            summary["winner_position_share"] = {
                str(p): round(c / len(positions), 3)
                for p, c in sorted(Counter(positions).items())
            }
        cells[cell] = summary
    counts: dict[str, int] = dict(sorted(Counter(i.split for i in instances).items()))
    return {"total": len(instances), "by_split": counts, "cells": cells}
