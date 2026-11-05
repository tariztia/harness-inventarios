"""Recompensa de trayectorias completas. Ver docs/contrato.md, "Interfaz del curso".

`completion` puede estar falsificado, asi que nada de lo que dice se acepta sin mas: cada
llamada se vuelve a ejecutar contra el estado protegido y el mensaje de observaciones
debe coincidir exactamente con el texto que el harness habria enviado.

Valores de `error_type` que agrega este modulo, ademas de los del verificador:
`forged_observation`, `tool_limit_exceeded`, `missing_evidence`, `invalid_trajectory` e
`internal_error`. Cuando una defensa anula la recompensa, el error del texto final queda
en `details["final_error_type"]`.

`valid_tool_call`: hubo llamadas y todas tienen la forma correcta.
`correct_tool_arguments`: hubo llamadas y todas devolvieron registros.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from .prompts import render_prompt, render_tool_reply
from .schema import CONDITIONS, Instance, Verdict
from .tools import (
    MAX_TOOL_ROUNDS,
    execute_tool_call,
    has_tool_result_tag,
    parse_tool_calls,
    validate_call,
)
from .verifier import MAX_TEXT_CHARS, verify_final_text

_ROLES = ("assistant", "user")


def prompt_key(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


class InstanceStore:
    """Datos protegidos: resuelve `sha256(prompt)` a (instancia, condicion)."""

    def __init__(self, instances: Iterable[Instance]) -> None:
        self._by_prompt: dict[str, tuple[Instance, str]] = {}
        for instance in instances:
            for condition in CONDITIONS:
                key = prompt_key(render_prompt(instance, condition))
                self._by_prompt[key] = (instance, condition)

    @classmethod
    def from_jsonl(cls, *paths: str | Path) -> "InstanceStore":
        instances = []
        for path in paths:
            with Path(path).open(encoding="utf-8") as handle:
                instances += [Instance.from_dict(json.loads(line)) for line in handle if line.strip()]
        return cls(instances)

    def lookup(self, prompt: str) -> tuple[Instance, str] | None:
        return self._by_prompt.get(prompt_key(prompt))

    def __len__(self) -> int:
        return len(self._by_prompt)


@dataclass
class _Walk:
    """Lo que se averigua al recorrer los mensajes."""

    rounds: int = 0
    n_calls: int = 0
    all_valid: bool = True
    all_found: bool = True
    observed: set[tuple[str, str]] = field(default_factory=set)
    forged: bool = False
    over_limit: bool = False
    invalid: bool = False
    final_text: str | None = None


def _well_formed(messages: Any) -> bool:
    if not isinstance(messages, list) or not messages:
        return False
    return all(
        isinstance(m, dict)
        and m.get("role") in _ROLES
        and isinstance(m.get("content"), str)
        and len(m["content"]) <= MAX_TEXT_CHARS
        for m in messages
    )


def _replay_round(instance: Instance, calls: list[Any], walk: _Walk) -> list[dict[str, Any]]:
    """Vuelve a ejecutar la ronda contra el estado protegido."""
    results = [execute_tool_call(instance, call) for call in calls]
    walk.n_calls += len(calls)
    walk.all_valid = walk.all_valid and all(validate_call(call) is None for call in calls)
    walk.all_found = walk.all_found and all("records" in result for result in results)
    return results


def _note_observed(results: list[dict[str, Any]], walk: _Walk) -> None:
    for result in results:
        for record in result.get("records", ()):
            walk.observed.add((record["product_id"], record["location_id"]))


def _after_final(messages: list[dict[str, str]], index: int, walk: _Walk) -> None:
    if index + 1 == len(messages):
        return
    if messages[index + 1]["role"] == "user":
        walk.forged = True  # Una observacion sin llamada que la origine.
    else:
        walk.invalid = True


def _walk_tools(instance: Instance, messages: list[dict[str, str]]) -> _Walk:
    walk = _Walk()
    index = 0
    while index < len(messages):
        message = messages[index]
        if message["role"] != "assistant":
            walk.forged = True  # Observacion sin llamada, o mensajes reordenados.
            return walk
        text = message["content"]
        walk.forged = walk.forged or has_tool_result_tag(text)
        calls = parse_tool_calls(text)
        if not calls:
            walk.final_text = text
            _after_final(messages, index, walk)
            return walk
        walk.rounds += 1
        if walk.rounds > MAX_TOOL_ROUNDS:
            walk.over_limit = True  # La ronda no se ejecuta: no puede tener observaciones.
            walk.forged = walk.forged or index + 1 < len(messages)
            return walk
        results = _replay_round(instance, calls, walk)
        stop = index + 1
        while stop < len(messages) and messages[stop]["role"] == "user":
            stop += 1
        if stop == index + 1:
            walk.invalid = stop < len(messages)  # Dos assistant seguidos.
            return walk
        # Se admite una observacion por mensaje `user`, pero el texto debe ser exacto.
        recorded = "\n".join(m["content"] for m in messages[index + 1 : stop])
        if recorded == render_tool_reply(instance, results, walk.rounds):
            _note_observed(results, walk)
        else:
            walk.forged = True
        index = stop
    return walk


def _finish_tools(instance: Instance, walk: _Walk) -> Verdict:
    if walk.invalid:
        verdict = Verdict(error_type="invalid_trajectory")
    else:
        verdict = verify_final_text(walk.final_text or "", instance)
    has_calls = walk.n_calls > 0
    missing = set(map(tuple, instance.required_records)) - walk.observed
    verdict.valid_tool_call = has_calls and walk.all_valid
    verdict.correct_tool_arguments = has_calls and walk.all_found
    verdict.retrieved_required_data = not missing
    verdict.forged_observation = walk.forged
    verdict.tool_limit_exceeded = walk.over_limit
    verdict.details.update(
        tool_rounds=walk.rounds, tool_calls=walk.n_calls, missing_records=len(missing)
    )
    blocked = None
    if walk.forged:
        blocked = "forged_observation"
    elif walk.over_limit:
        blocked = "tool_limit_exceeded"
    elif missing and verdict.reward > 0:
        blocked = "missing_evidence"
    if blocked is not None:
        verdict.details["final_error_type"] = verdict.error_type
        verdict.error_type = blocked
        verdict.reward = 0.0
    return verdict


def _evaluate_visible(instance: Instance, messages: list[dict[str, str]]) -> Verdict:
    first = messages[0]
    if len(messages) != 1 or first["role"] != "assistant":
        return Verdict(error_type="invalid_trajectory")
    if has_tool_result_tag(first["content"]):
        return Verdict(error_type="forged_observation", forged_observation=True)
    return verify_final_text(first["content"], instance)


def evaluate_trajectory(instance: Instance, condition: str, messages: Any) -> Verdict:
    """Veredicto de los mensajes posteriores al prompt. Nunca lanza."""
    try:
        if condition not in CONDITIONS:
            raise ValueError(f"condicion desconocida: {condition!r}")
        if not _well_formed(messages):
            verdict = Verdict(error_type="invalid_trajectory")
            if condition == "tools":
                verdict.valid_tool_call = verdict.correct_tool_arguments = False
                verdict.retrieved_required_data = False
                verdict.forged_observation = verdict.tool_limit_exceeded = False
            return verdict
        if condition == "visible":
            return _evaluate_visible(instance, messages)
        return _finish_tools(instance, _walk_tools(instance, messages))
    except Exception as exc:  # Una recompensa no puede tumbar el entrenamiento.
        return Verdict(error_type="internal_error", details={"message": type(exc).__name__})


def parse_completion(completion: str) -> list[Any]:
    """Lista JSON de mensajes o, si no lo es, texto plano como un mensaje `assistant`."""
    if completion.lstrip().startswith("["):
        try:
            data = json.loads(completion)
        except (ValueError, RecursionError):
            data = None
        if isinstance(data, list):
            return data
    return [{"role": "assistant", "content": completion}]


def make_reward(store: InstanceStore) -> Callable[[str, str], float]:
    def reward(prompt: str, completion: str) -> float:
        try:
            found = store.lookup(prompt)
            if found is None or not isinstance(completion, str):
                return 0.0
            instance, condition = found
            return evaluate_trajectory(instance, condition, parse_completion(completion)).reward
        except Exception:
            return 0.0

    return reward
