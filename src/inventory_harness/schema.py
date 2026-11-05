"""Tipos compartidos del harness. Contrato entre generador, verificador y rollouts.

Solo stdlib. Ver docs/contrato.md y docs/reglas_negocio.md.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Family = Literal["availability", "selection", "composition"]
Difficulty = Literal["easy", "medium", "hard"]
Split = Literal["train", "eval", "test"]
Condition = Literal["tools", "visible"]

FAMILIES: tuple[str, ...] = ("availability", "selection", "composition")
DIFFICULTIES: tuple[str, ...] = ("easy", "medium", "hard")
SPLITS: tuple[str, ...] = ("train", "eval", "test")
CONDITIONS: tuple[str, ...] = ("tools", "visible")


@dataclass(frozen=True)
class InventoryRecord:
    product_id: str
    location_id: str
    physical_stock: int
    reserved_stock: int

    @property
    def available(self) -> int:
        return max(0, self.physical_stock - self.reserved_stock)


@dataclass(frozen=True)
class OrderLine:
    product_id: str
    quantity: int


@dataclass(frozen=True)
class Order:
    order_id: str
    lines: tuple[OrderLine, ...]
    # availability: exactamente 1 sucursal.
    # selection: vacio (las candidatas son Instance.location_ids).
    # composition: 1 sucursal, o varias en orden de cascada.
    location_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Instance:
    id: str
    seed: int
    family: str
    difficulty: str
    split: str
    template_id: str
    # Protegido: nunca se entrega completo al modelo en la condicion "tools".
    inventory: tuple[InventoryRecord, ...]
    orders: tuple[Order, ...]
    # Catalogo visible para el modelo (solo IDs, sin valores).
    product_ids: tuple[str, ...]
    location_ids: tuple[str, ...]
    # Solicitud en lenguaje natural (sin valores de stock).
    request: str
    # Protegido. Forma por familia en docs/contrato.md.
    expected: dict[str, Any]
    # Pares (product_id, location_id) que hay que conocer para resolver.
    required_records: tuple[tuple[str, str], ...]
    # n_records, n_operations, n_entities, dependency_depth, n_required_calls
    complexity: dict[str, int] = field(default_factory=dict)
    solution_program: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Instance":
        return Instance(
            id=d["id"],
            seed=d["seed"],
            family=d["family"],
            difficulty=d["difficulty"],
            split=d["split"],
            template_id=d["template_id"],
            inventory=tuple(InventoryRecord(**r) for r in d["inventory"]),
            orders=tuple(
                Order(
                    order_id=o["order_id"],
                    lines=tuple(OrderLine(**l) for l in o["lines"]),
                    location_ids=tuple(o["location_ids"]),
                )
                for o in d["orders"]
            ),
            product_ids=tuple(d["product_ids"]),
            location_ids=tuple(d["location_ids"]),
            request=d["request"],
            expected=d["expected"],
            required_records=tuple(tuple(p) for p in d["required_records"]),
            complexity=d.get("complexity", {}),
            solution_program=d.get("solution_program", ""),
        )


@dataclass
class Verdict:
    """Resultado de evaluar una respuesta. `reward` es la recompensa 0/1."""

    reward: float = 0.0
    correct_final_answer: bool = False
    parser_error: bool = False
    contradictory_answer: bool = False
    # "ok", "no_answer_block", "multiple_answer_blocks", "missing_field",
    # "unknown_field", "duplicate_field", "ambiguous_value", "invalid_value",
    # "text_after_answer", "contradiction", "wrong_value", ...
    error_type: str = "ok"
    # Solo en condicion "tools"; None si no aplica.
    valid_tool_call: bool | None = None
    correct_tool_arguments: bool | None = None
    retrieved_required_data: bool | None = None
    forged_observation: bool | None = None
    tool_limit_exceeded: bool | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
