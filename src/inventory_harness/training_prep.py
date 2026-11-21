"""Datos y recompensa para entrenar con SFT, DPO y GRPO. Solo biblioteca estandar.

Lo que depende de `torch`, `transformers` o `trl` vive en los scripts de `scripts/train_*.py`;
aqui queda lo que se puede probar sin GPU.

SFT. Una traza `tools` tiene dos mensajes del asistente: las llamadas y la respuesta final.
La plantilla de chat de Qwen3 borra el `<think>` de todo mensaje del asistente anterior al
ultimo mensaje del usuario. Si se entrenara la conversacion entera de una vez, la primera
ronda se aprenderia sin su razonamiento, pero al generar el modelo si lo escribe. Por eso
cada mensaje del asistente es un ejemplo aparte: el contexto es lo que el modelo ve al
generar y la perdida cae solo en ese mensaje (`conversation_examples`).

GRPO. La recompensa es la del harness, sobre un solo mensaje del asistente (condicion
`visible`). `make_grpo_reward` ademas cuenta los tipos de error y puede guardar las
respuestas, que sirven para auditar trazas exitosas y para detectar reward hacking.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from .generator import fingerprint, generate_dataset
from .prompts import render_prompt
from .reward import InstanceStore, evaluate_trajectory
from .schema import DIFFICULTIES, FAMILIES, SPLITS, Instance

Messages = list[dict[str, str]]

# Formato ChatML de Qwen. El contenido va despues de "assistant\n" y llega hasta <|im_end|>.
_ASSISTANT_SPAN = re.compile(r"<\|im_start\|>assistant\n(.*?<\|im_end\|>)", re.S)

# Semilla de las instancias de entrenamiento extra. Distinta de la del piloto (2026).
EXTRA_BASE_SEED = 5151
# Configuraciones cuyas instancias no pueden repetirse en el entrenamiento: el piloto (10
# por celda) y la configuracion estandar (40 por celda), ambas con la semilla 2026.
PROTECTED_CONFIGS = ({"per_cell": 10, "base_seed": 2026}, {"per_cell": 40, "base_seed": 2026})


# --- Lectura -----------------------------------------------------------------


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except ValueError as exc:
                    raise ValueError(f"{path}:{number}: JSON invalido") from exc
    return rows


def keep_difficulties(rows: Iterable[dict[str, Any]], difficulties: Sequence[str] | None) -> list[dict[str, Any]]:
    """Filtra por dificultad, para entrenar solo con algunos niveles."""
    rows = list(rows)
    if not difficulties:
        return rows
    unknown = set(difficulties) - set(DIFFICULTIES)
    if unknown:
        raise ValueError(f"dificultades desconocidas: {sorted(unknown)}")
    return [row for row in rows if row["difficulty"] in difficulties]


def keep_conditions(rows: Iterable[dict[str, Any]], condition: str) -> list[dict[str, Any]]:
    rows = list(rows)
    if condition == "all":
        return rows
    if condition not in ("visible", "tools"):
        raise ValueError(f"condicion desconocida: {condition!r}")
    return [row for row in rows if row["condition"] == condition]


# --- SFT ---------------------------------------------------------------------


def conversation_examples(messages: Messages) -> list[Messages]:
    """Un ejemplo por mensaje del asistente: la conversacion hasta ese mensaje inclusive.

    El ultimo mensaje de cada ejemplo es el que se aprende.
    """
    if not messages or messages[0].get("role") != "user":
        raise ValueError("la conversacion debe empezar con un mensaje del usuario")
    examples = []
    for index, message in enumerate(messages):
        if message.get("role") == "assistant":
            examples.append([dict(m) for m in messages[: index + 1]])
        elif message.get("role") != "user":
            raise ValueError(f"rol desconocido: {message.get('role')!r}")
    if not examples:
        raise ValueError("la conversacion no tiene mensajes del asistente")
    return examples


def assistant_spans(rendered: str) -> list[tuple[int, int]]:
    """Tramos (inicio, fin) de caracteres de cada mensaje del asistente, con su <|im_end|>."""
    return [match.span(1) for match in _ASSISTANT_SPAN.finditer(rendered)]


def label_flags(offsets: Sequence[tuple[int, int]], span: tuple[int, int]) -> list[bool]:
    """True para los tokens que empiezan dentro del tramo. Los de largo cero (relleno) no."""
    start, end = span
    return [token_end > token_start and start <= token_start < end for token_start, token_end in offsets]


def tokenize_example(tokenizer: Any, messages: Messages, max_length: int) -> dict[str, Any] | None:
    """Ids y etiquetas de un ejemplo, o None si no cabe en `max_length`.

    Requiere un tokenizer rapido (usa `return_offsets_mapping`). Solo se aprende el ultimo
    mensaje del asistente, incluido su <|im_end|>. Un ejemplo demasiado largo se descarta
    en vez de cortarlo, porque cortarlo borraria la respuesta final.
    """
    rendered = tokenizer.apply_chat_template(messages, tokenize=False)
    spans = assistant_spans(rendered)
    if not spans:
        raise ValueError("la plantilla no produjo un mensaje del asistente")
    encoded = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)
    ids = list(encoded["input_ids"])
    if len(ids) > max_length:
        return None
    flags = label_flags(encoded["offset_mapping"], spans[-1])
    if not any(flags):
        raise ValueError("ningun token cae en el mensaje del asistente")
    return {
        "input_ids": ids,
        "attention_mask": [1] * len(ids),
        "labels": [token if flag else -100 for token, flag in zip(ids, flags)],
    }


# --- DPO ---------------------------------------------------------------------


def dpo_example(row: dict[str, Any]) -> dict[str, Any]:
    """Fila de dpo.jsonl en el formato conversacional de TRL."""
    return {
        "prompt": [{"role": "user", "content": row["prompt"]}],
        "chosen": [dict(m) for m in row["chosen"]],
        "rejected": [dict(m) for m in row["rejected"]],
    }


# --- Instancias de entrenamiento extra --------------------------------------


def protected_fingerprints() -> set[str]:
    """Huellas de todo lo que no debe entrar al entrenamiento extra: eval, test y train del piloto."""
    marks: set[str] = set()
    for config in PROTECTED_CONFIGS:
        instances = generate_dataset(
            {"n_per_cell": {split: config["per_cell"] for split in SPLITS}, "base_seed": config["base_seed"]}
        )
        marks.update(fingerprint(instance) for instance in instances)
    return marks


def extra_train_instances(
    n_per_cell: int, base_seed: int = EXTRA_BASE_SEED, margin: int = 20
) -> list[Instance]:
    """Instancias nuevas de `train`, sin repetir ninguna de eval, test ni del train del piloto.

    Se generan `margin` de mas por celda y se descartan las que coinciden por huella. Los IDs
    llevan el prefijo `train2_` para no chocar con los de `train`.
    """
    protected = protected_fingerprints()
    config = {"n_per_cell": {"train": n_per_cell + margin}, "base_seed": base_seed}
    by_cell: dict[tuple[str, str], list[Instance]] = {}
    for instance in generate_dataset(config):
        if instance.split != "train" or fingerprint(instance) in protected:
            continue
        by_cell.setdefault((instance.family, instance.difficulty), []).append(instance)
    chosen: list[Instance] = []
    for family in FAMILIES:
        for difficulty in DIFFICULTIES:
            members = by_cell.get((family, difficulty), [])
            if len(members) < n_per_cell:
                raise RuntimeError(f"{family}/{difficulty}: solo {len(members)} instancias; sube `margin`")
            chosen += [
                replace(instance, id=f"train2_{family}_{difficulty}_{index:04d}")
                for index, instance in enumerate(members[:n_per_cell])
            ]
    # Intercaladas por celda: un entrenamiento cortado deja todas las celdas parejas.
    per_cell = {key: [i for i in chosen if (i.family, i.difficulty) == key] for key in by_cell}
    ordered = []
    for position in range(n_per_cell):
        for members in per_cell.values():
            ordered.append(members[position])
    return ordered


def write_instances(path: str | Path, instances: Iterable[Instance]) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for instance in instances:
            handle.write(json.dumps(instance.to_dict(), ensure_ascii=False) + "\n")
            count += 1
    return count


def read_instances(path: str | Path) -> list[Instance]:
    return [Instance.from_dict(row) for row in load_jsonl(path)]


# --- GRPO --------------------------------------------------------------------


def grpo_rows(instances: Iterable[Instance], difficulties: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """Prompts de la condicion `visible`, en el formato conversacional de TRL.

    La condicion `tools` necesita varias rondas con ejecucion de la herramienta entre ellas, y
    el GRPOTrainer genera un solo mensaje por prompt. Queda fuera de esta primera etapa.
    """
    rows = []
    for instance in instances:
        if difficulties and instance.difficulty not in difficulties:
            continue
        rows.append(
            {
                "prompt": [{"role": "user", "content": render_prompt(instance, "visible")}],
                "instance_id": instance.id,
                "family": instance.family,
                "difficulty": instance.difficulty,
            }
        )
    return rows


def _prompt_text(prompt: Any) -> str:
    if isinstance(prompt, str):
        return prompt
    return next((m["content"] for m in reversed(prompt) if m.get("role") == "user"), "")


def _completion_text(completion: Any) -> str:
    if isinstance(completion, str):
        return completion
    return "".join(m.get("content", "") for m in completion if m.get("role") == "assistant")


class GrpoReward:
    """Funcion de recompensa para `GRPOTrainer`: `reward_funcs=[GrpoReward(store)]`.

    Califica con `evaluate_trajectory`, igual que `reward(prompt, completion)`, y deja un
    registro de lo ocurrido: `errors` cuenta los tipos de error y `reward_sum` y `calls` dan
    el promedio. Con `trace_path` guarda cada respuesta (una linea JSON) para la auditoria.
    """

    __name__ = "inventory_reward"

    def __init__(self, store: InstanceStore, trace_path: str | Path | None = None, trace_every: int = 1) -> None:
        self.store = store
        self.trace_path = Path(trace_path) if trace_path else None
        self.trace_every = max(1, trace_every)
        self.errors: Counter[str] = Counter()
        self.calls = 0
        self.reward_sum = 0.0
        self._seen = 0
        if self.trace_path:
            self.trace_path.parent.mkdir(parents=True, exist_ok=True)

    def score(self, prompt: Any, completion: Any) -> tuple[float, str, Any]:
        found = self.store.lookup(_prompt_text(prompt))
        if found is None:
            return 0.0, "prompt_desconocido", None
        instance, condition = found
        text = _completion_text(completion)
        verdict = evaluate_trajectory(instance, condition, [{"role": "assistant", "content": text}])
        return float(verdict.reward), verdict.error_type, instance

    def __call__(self, prompts: Sequence[Any], completions: Sequence[Any], **kwargs: Any) -> list[float]:
        rewards = []
        handle = self.trace_path.open("a", encoding="utf-8") if self.trace_path else None
        try:
            for prompt, completion in zip(prompts, completions):
                reward, error, instance = self.score(prompt, completion)
                self.errors[error] += 1
                self.calls += 1
                self.reward_sum += reward
                rewards.append(reward)
                self._seen += 1
                if handle and self._seen % self.trace_every == 0:
                    handle.write(
                        json.dumps(
                            {
                                "instance_id": instance.id if instance else None,
                                "family": instance.family if instance else None,
                                "difficulty": instance.difficulty if instance else None,
                                "reward": reward,
                                "error_type": error,
                                "completion": _completion_text(completion),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
        finally:
            if handle:
                handle.close()
        return rewards

    def summary(self) -> dict[str, Any]:
        mean = self.reward_sum / self.calls if self.calls else 0.0
        return {"respuestas": self.calls, "recompensa_media": round(mean, 4), "errores": dict(self.errors.most_common())}


def make_grpo_reward(
    store: InstanceStore, trace_path: str | Path | None = None, trace_every: int = 1
) -> Callable[..., list[float]]:
    return GrpoReward(store, trace_path, trace_every)
