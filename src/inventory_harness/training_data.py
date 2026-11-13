"""Datos derivados: trazas SFT y pares DPO a partir de rollouts. Ver docs/contrato.md.

Cada rollout se vuelve a evaluar contra la instancia protegida: el veredicto guardado
puede venir de una version anterior del harness. Solo se aceptan instancias de `train`,
para que eval y test sigan midiendo lo que el modelo no vio.

Las llamadas se reescriben en la forma canonica `<tool_call>{json}</tool_call>`. El parser
acepta otras formas, pero entrenar con ellas ensenaria a omitir la etiqueta. El texto que
acompana una llamada (a veces resultados inventados) se descarta: los datos llegan en la
observacion. El razonamiento de <think> se conserva.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from .reward import InstanceStore, evaluate_trajectory, prompt_key
from .schema import Instance, Verdict
from .tools import parse_tool_calls
from .verifier import _THINK_TAG_RE

# Como respuesta rechazada sirven mas los errores de contenido que los de forma: el par
# ensena a razonar, no solo a cerrar el bloque.
REJECTED_PRIORITY = {"wrong_value": 0, "contradiction": 1}
# Sin informacion sobre el modelo, o propios de una trayectoria manipulada.
UNUSABLE_REJECTED = {"internal_error", "forged_observation", "invalid_trajectory"}


def thinking_part(text: str) -> str:
    """El razonamiento del mensaje, tal como se escribio: lo que `_strip_think` descarta.

    Usa la misma lectura de etiquetas que el verificador (mayusculas, espacios, varios
    bloques, un cierre sin apertura), para que nada de lo visible se cuele como razonamiento.
    """
    spans: list[str] = []
    depth = 0
    start = 0
    for match in _THINK_TAG_RE.finditer(text):
        closing = bool(match.group(1))
        if depth == 0:
            if closing:
                # Cierre sin apertura: la plantilla abrio el <think> antes de la completion.
                spans = [text[: match.end()]]
            else:
                start = match.start()
                depth = 1
        elif closing:
            depth -= 1
            if depth == 0:
                spans.append(text[start : match.end()])
        else:
            depth += 1
    if depth:
        spans.append(text[start:])
    return "\n".join(span.strip() for span in spans if span.strip())


def normalize_tool_message(text: str) -> str:
    """Mensaje de llamadas en forma canonica. Sin llamadas, o con una ilegible, queda igual."""
    calls = parse_tool_calls(text)
    if not calls or any(call is None for call in calls):
        return text
    thinking = thinking_part(text)
    body = "\n".join(
        f"<tool_call>{json.dumps(call, ensure_ascii=False)}</tool_call>" for call in calls
    )
    return f"{thinking}\n\n{body}" if thinking else body


def normalize_messages(condition: str, messages: list[dict[str, str]]) -> list[dict[str, str]]:
    if condition != "tools":
        return [dict(message) for message in messages]
    return [
        {"role": "assistant", "content": normalize_tool_message(m["content"])}
        if m["role"] == "assistant"
        else dict(m)
        for m in messages
    ]


@dataclass
class Candidate:
    """Un rollout ya normalizado y vuelto a evaluar."""

    model: str
    sample: int
    instance: Instance
    condition: str
    prompt: str
    messages: list[dict[str, str]]
    verdict: Verdict
    truncated: bool

    @property
    def correct(self) -> bool:
        # Una respuesta correcta con llamadas invalidas de por medio no es un buen ejemplo.
        return (
            self.verdict.reward == 1.0
            and self.verdict.valid_tool_call is not False
            and self.verdict.correct_tool_arguments is not False
        )

    @property
    def usable_rejected(self) -> bool:
        # Una respuesta cortada por el tope no muestra un error del modelo, sino del tope.
        return (
            self.verdict.reward == 0.0
            and not self.truncated
            and self.verdict.error_type not in UNUSABLE_REJECTED
        )


def collect(rows: Iterable[dict[str, Any]], store: InstanceStore, dropped: Counter) -> list[Candidate]:
    """Rollouts utilizables. Lanza ValueError si alguno no es de `train`."""
    candidates = []
    for row in rows:
        found = store.lookup(row.get("prompt", ""))
        if found is None:
            dropped["prompt_desconocido"] += 1
            continue
        instance, condition = found
        if instance.split != "train":
            raise ValueError(f"{instance.id} es de {instance.split}: solo se usa train")
        if row["verdict"]["error_type"] == "internal_error":
            dropped["error_interno"] += 1
            continue
        messages = normalize_messages(condition, row["messages"])
        verdict = evaluate_trajectory(instance, condition, messages)
        if verdict.reward != evaluate_trajectory(instance, condition, row["messages"]).reward:
            dropped["normalizar_cambia_recompensa"] += 1
            continue
        stops = row.get("usage", {}).get("stop_reasons", [])
        candidates.append(
            Candidate(row["model"], row["sample"], instance, condition, row["prompt"],
                      messages, verdict, "length" in stops)
        )
    return candidates


def _chosen_key(candidate: Candidate, teacher: str | None) -> tuple:
    return (candidate.model != teacher, candidate.model, candidate.sample)


def _rejected_key(candidate: Candidate, teacher: str | None) -> tuple:
    # Primero los errores de los modelos que no son el profesor: son los que se quieren corregir.
    return (
        candidate.model == teacher,
        REJECTED_PRIORITY.get(candidate.verdict.error_type, len(REJECTED_PRIORITY)),
        candidate.model,
        candidate.sample,
    )


def _meta(candidate: Candidate) -> dict[str, Any]:
    instance = candidate.instance
    return {
        "instance_id": instance.id,
        "family": instance.family,
        "difficulty": instance.difficulty,
        "condition": candidate.condition,
    }


def build(
    candidates: list[Candidate], teacher: str | None = None, max_sft_per_prompt: int = 1
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Trazas SFT, pares DPO y conteos. El profesor tiene prioridad como respuesta elegida."""
    # Por prompt, no por instance.id: corridas con otra semilla o con otro n_per_cell
    # reutilizan los mismos IDs para instancias distintas.
    groups: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        groups[prompt_key(candidate.prompt)].append(candidate)

    sft: list[dict[str, Any]] = []
    dpo: list[dict[str, Any]] = []
    cells: dict[str, Counter] = defaultdict(Counter)
    for key in sorted(groups, key=lambda k: (groups[k][0].instance.id, groups[k][0].condition, k)):
        group = groups[key]
        first = group[0]
        name = f"{first.instance.id}|{first.condition}|{key[:8]}"
        good = sorted((c for c in group if c.correct), key=lambda c: _chosen_key(c, teacher))
        bad = sorted((c for c in group if c.usable_rejected), key=lambda c: _rejected_key(c, teacher))
        cell = cells[f"{first.instance.family}|{first.instance.difficulty}|{first.condition}"]
        cell["prompts"] += 1
        cell["con_correcta"] += bool(good)
        cell["con_incorrecta"] += bool(bad)
        for candidate in good[:max_sft_per_prompt]:
            sft.append({
                "id": f"{name}|{candidate.model}|{candidate.sample}",
                **_meta(candidate),
                "source_model": candidate.model,
                "sample": candidate.sample,
                "messages": [{"role": "user", "content": candidate.prompt}, *candidate.messages],
            })
            cell["sft"] += 1
        if good and bad and good[0].messages != bad[0].messages:
            chosen, rejected = good[0], bad[0]
            dpo.append({
                "id": name,
                **_meta(chosen),
                "prompt": chosen.prompt,
                "chosen": chosen.messages,
                "rejected": rejected.messages,
                "chosen_model": chosen.model,
                "rejected_model": rejected.model,
                "rejected_error_type": rejected.verdict.error_type,
            })
            cell["dpo"] += 1

    stats = {
        "prompts": len(groups),
        "sft": len(sft),
        "dpo": len(dpo),
        "sft_por_modelo": dict(Counter(row["source_model"] for row in sft)),
        "dpo_rechazada_por_error": dict(Counter(row["rejected_error_type"] for row in dpo)),
        "por_celda": {name: dict(counts) for name, counts in sorted(cells.items())},
    }
    return sft, dpo, stats
