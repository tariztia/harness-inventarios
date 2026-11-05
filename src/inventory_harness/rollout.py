"""Rollouts por lotes con escritura incremental. Ver docs/contrato.md.

Las muestras pendientes se reparten en cohortes y, dentro de una cohorte, todas las
trayectorias activas generan juntas en cada ronda. La cohorte acota lo que se pierde si
Colab se cae: una muestra se escribe en cuanto termina. El tamano por defecto es
`4 * batch_size`; el backend parte cada llamada en lotes de `batch_size`.

Semillas (`generation_seed`): cada llamada a `generate` recibe una semilla derivada de
`base_seed`, la condicion, la etiqueta, la ronda y las claves de las muestras de esa
llamada. La clave incluye el numero de muestra, asi que dos muestras de un caso nunca
repiten ruido, ni siquiera con lotes de tamano 1, y la misma llamada reproduce la misma
semilla. Una ejecucion reanudada forma otras cohortes y por eso muestrea otro ruido, lo
que no invalida `pass@k`.

Reanudacion: una linea truncada o duplicada se descarta, y las muestras con
`internal_error` se quitan del archivo para volver a intentarlas. Ese error suele ser
transitorio, y dejarlas marcadas como hechas convertiria un fallo pasajero en ceros.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .backends import Backend, derive_seed
from .prompts import render_prompt, render_tool_reply
from .reward import evaluate_trajectory
from .schema import CONDITIONS, Instance, Verdict
from .tools import (
    MAX_TOOL_ROUNDS,
    execute_tool_call,
    parse_tool_calls,
    truncate_at_tool_result,
)


@dataclass
class _Trajectory:
    instance: Instance
    sample: int
    key: str
    prompt: str = ""
    messages: list[dict[str, str]] = field(default_factory=list)
    tool_rounds: int = 0
    new_tokens: int = 0
    seconds: float = 0.0
    stop_reasons: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class _Output:
    text: str = ""
    usage: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


def run_label_for(backend: Backend, gen_config: dict[str, Any], run_label: str | None) -> str:
    """Nombre del modelo en la clave. Con thinking y sin etiqueta, se distingue solo:
    de otro modo la corrida se saltaria las muestras ya hechas sin thinking."""
    if run_label:
        return run_label
    return f"{backend.name}+think" if gen_config.get("enable_thinking") else backend.name


def sample_key(model: str, condition: str, instance_id: str, sample: int) -> str:
    return f"{model}|{condition}|{instance_id}|{sample}"


def generation_seed(base_seed: int, label: str, condition: str, round_index: int, keys: list[str]) -> int:
    return derive_seed(base_seed, label, condition, round_index, *sorted(keys))


def load_done_keys(path: Path) -> set[str]:
    """Claves terminadas. Reescribe el archivo si hay lineas que descartar."""
    if not path.exists():
        return set()
    raw = path.read_bytes()
    done: set[str] = set()
    kept: list[bytes] = []
    dirty = bool(raw) and not raw.endswith(b"\n")
    for line in raw.split(b"\n"):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            key = record["key"]
            failed = record["verdict"]["error_type"] == "internal_error"
        except (ValueError, KeyError, TypeError):
            dirty = True
            continue
        if failed or key in done:
            dirty = True
            continue
        done.add(key)
        kept.append(line)
    if dirty:
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_bytes(b"".join(line + b"\n" for line in kept))
        os.replace(temporary, path)
    return done


def restore_answer_close(text: str, stop_reason: str | None) -> str:
    """Repone `</answer>` solo si el backend paro en esa cadena y se perdio del texto.

    Un modelo que se quedo sin tokens tiene otro `stop_reason` y conserva su bloque
    abierto: inventarle el cierre seria regalarle una respuesta.
    """
    if stop_reason == "answer" and "<answer>" in text and "</answer>" not in text:
        return text + "</answer>"
    return text


def _generate(
    backend: Backend,
    active: list[_Trajectory],
    gen_config: dict[str, Any],
    seed_parts: tuple[int, str, str, int],
) -> list[_Output]:
    """Genera sin dejar escapar errores: un fallo se parte hasta aislar la trayectoria."""
    conversations = [
        [{"role": "user", "content": t.prompt}, *t.messages] for t in active
    ]
    seed = generation_seed(*seed_parts, [t.key for t in active])
    try:
        texts = backend.generate(conversations, gen_config, seed)
        if len(texts) != len(active):
            raise ValueError("el backend devolvio un numero distinto de textos")
    except Exception as exc:
        if len(active) == 1:
            return [_Output(error=f"{type(exc).__name__}: {exc}")]
        middle = len(active) // 2
        return _generate(backend, active[:middle], gen_config, seed_parts) + _generate(
            backend, active[middle:], gen_config, seed_parts
        )
    usage = list(getattr(backend, "last_usage", None) or [])
    if len(usage) != len(texts):
        usage = [{} for _ in texts]
    return [_Output(text, entry) for text, entry in zip(texts, usage)]


def _advance(trajectory: _Trajectory, output: _Output, condition: str) -> bool:
    """Aplica una generacion. Devuelve True si la trayectoria sigue a la proxima ronda."""
    if output.error is not None:
        trajectory.error = output.error
        return False
    stop_reason = output.usage.get("stop_reason")
    if stop_reason == "oom":
        trajectory.error = "OutOfMemoryError"
        return False
    trajectory.new_tokens += int(output.usage.get("new_tokens", 0))
    trajectory.seconds += float(output.usage.get("seconds", 0.0))
    if stop_reason is not None:
        trajectory.stop_reasons.append(stop_reason)
    text = truncate_at_tool_result(restore_answer_close(output.text, stop_reason))
    trajectory.messages.append({"role": "assistant", "content": text})
    if condition == "visible":
        return False
    calls = parse_tool_calls(text)
    if not calls or trajectory.tool_rounds >= MAX_TOOL_ROUNDS:
        return False  # Respuesta final, o una tercera ronda que no se ejecuta.
    trajectory.tool_rounds += 1
    results = [execute_tool_call(trajectory.instance, call) for call in calls]
    reply = render_tool_reply(trajectory.instance, results, trajectory.tool_rounds)
    trajectory.messages.append({"role": "user", "content": reply})
    return True


def _verdict_for(trajectory: _Trajectory, condition: str) -> Verdict:
    if trajectory.error is not None:
        return Verdict(error_type="internal_error", details={"message": trajectory.error})
    return evaluate_trajectory(trajectory.instance, condition, trajectory.messages)


class _Writer:
    def __init__(self, handle: Any, model: str, condition: str, gen_config: dict[str, Any],
                 total: int, progress_every: int) -> None:
        self.handle = handle
        self.model = model
        self.condition = condition
        self.gen_config = gen_config
        self.total = total
        self.progress_every = progress_every
        self.done = 0
        self.failed = 0
        self.started = time.perf_counter()

    def finish(self, trajectory: _Trajectory) -> None:
        verdict = _verdict_for(trajectory, self.condition)
        instance = trajectory.instance
        record = {
            "key": trajectory.key,
            "model": self.model,
            "condition": self.condition,
            "instance_id": instance.id,
            "family": instance.family,
            "difficulty": instance.difficulty,
            "split": instance.split,
            "sample": trajectory.sample,
            "prompt": trajectory.prompt,
            "messages": trajectory.messages,
            "verdict": verdict.to_dict(),
            "gen_config": self.gen_config,
            "usage": {
                "new_tokens": trajectory.new_tokens,
                "seconds": round(trajectory.seconds, 4),
                "stop_reasons": trajectory.stop_reasons,
            },
        }
        self.handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.handle.flush()
        self.failed += verdict.error_type == "internal_error"
        self.done += 1
        if self.done % self.progress_every == 0 or self.done == self.total:
            self._report()

    def _report(self) -> None:
        elapsed = max(time.perf_counter() - self.started, 1e-9)
        speed = self.done / elapsed
        eta = (self.total - self.done) / speed
        print(
            f"[{self.model}|{self.condition}] {self.done}/{self.total} muestras, "
            f"{speed:.2f} muestras/s, ETA {eta / 60:.1f} min, errores {self.failed}",
            flush=True,
        )


def _run_cohort(
    cohort: list[_Trajectory],
    condition: str,
    backend: Backend,
    gen_config: dict[str, Any],
    base_seed: int,
    label: str,
    writer: _Writer,
) -> None:
    active: list[_Trajectory] = []
    for trajectory in cohort:
        try:
            trajectory.prompt = render_prompt(trajectory.instance, condition)
            active.append(trajectory)
        except Exception as exc:
            trajectory.error = f"{type(exc).__name__}: {exc}"
            writer.finish(trajectory)
    for round_index in range(MAX_TOOL_ROUNDS + 1):
        if not active:
            return
        seed_parts = (base_seed, label, condition, round_index)
        outputs = _generate(backend, active, gen_config, seed_parts)
        following: list[_Trajectory] = []
        for trajectory, output in zip(active, outputs):
            try:
                proceeds = _advance(trajectory, output, condition)
            except Exception as exc:
                trajectory.error = f"{type(exc).__name__}: {exc}"
                proceeds = False
            if proceeds:
                following.append(trajectory)
            else:
                writer.finish(trajectory)
        active = following


def run_rollouts(
    instances: Iterable[Instance],
    condition: str,
    backend: Backend,
    gen_config: dict[str, Any],
    n_samples: int,
    out_path: str | Path,
    *,
    run_label: str | None = None,
    cohort_size: int | None = None,
    base_seed: int = 0,
    progress_every: int = 25,
) -> None:
    """Ejecuta las muestras que falten en `out_path` y las agrega al JSONL."""
    if condition not in CONDITIONS:
        raise ValueError(f"condicion desconocida: {condition!r}")
    if n_samples > 1 and not gen_config.get("do_sample", True):
        print("Aviso: do_sample=False repite la misma salida en todas las muestras.", flush=True)
    label = run_label_for(backend, gen_config, run_label)
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    done = load_done_keys(path)

    pending: list[_Trajectory] = []
    for instance in instances:
        for sample in range(n_samples):
            key = sample_key(label, condition, instance.id, sample)
            if key not in done:
                done.add(key)
                pending.append(_Trajectory(instance, sample, key))

    size = cohort_size or 4 * max(1, gen_config.get("batch_size", 1))
    with path.open("a", encoding="utf-8") as handle:
        writer = _Writer(handle, label, condition, dict(gen_config), len(pending), progress_every)
        for start in range(0, len(pending), size):
            _run_cohort(
                pending[start : start + size], condition, backend, gen_config, base_seed, label, writer
            )
