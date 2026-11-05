"""Backends de generacion. Ver docs/contrato.md.

`torch` y `transformers` solo se importan dentro de `HFBackend.__init__`.

`generate(batch_of_messages, gen_config, seed)` devuelve un texto por conversacion, en
el orden recibido, y deja en `last_usage` una entrada paralela con `new_tokens`,
`seconds` y `stop_reason` ("answer", "tool_result", "eos", "length" u "oom").

Semillas: `seed` identifica la llamada. El lote interno `j` usa
`batch_seed(seed, j) = derive_seed(seed, j)`, y en HFBackend eso es `torch.manual_seed`.
Dentro de un lote cada fila consume ruido distinto, y entre lotes difiere la semilla.
`rollout.py` deriva `seed` de las claves de las muestras de la llamada, que incluyen el
numero de muestra: dos muestras de un caso no comparten ruido aunque cada una ocupe
sola su lote (ver `generation_seed` en rollout.py).

La cadena de parada se conserva en el texto: sin `</answer>` el bloque queda abierto y
el verificador da `multiple_answer_blocks`, recompensa 0 en todos los casos.
"""
from __future__ import annotations

import gc
import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from .tools import visible_start

Messages = list[dict[str, str]]

DEFAULT_STOP_STRINGS: tuple[str, ...] = ("</answer>", "<tool_result>")
_STOP_REASONS = {"</answer>": "answer", "<tool_result>": "tool_result"}


def derive_seed(*parts: Any) -> int:
    """Semilla de 63 bits, estable entre ejecuciones (`hash` no lo es)."""
    payload = "|".join(str(part) for part in parts).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") >> 1


def batch_seed(seed: int, batch_index: int) -> int:
    return derive_seed(seed, batch_index)


def cut_at_stop(text: str, stops: Sequence[str]) -> tuple[str, str | None]:
    """Recorta justo despues de la primera parada, conservandola. Devuelve (texto, parada).

    Las paradas dentro de <think> no cuentan.
    """
    best: tuple[int, str] | None = None
    start = visible_start(text)
    for stop in stops:
        position = text.find(stop, start)
        if position >= 0 and (best is None or position < best[0]):
            best = (position, stop)
    if best is None:
        return text, None
    return text[: best[0] + len(best[1])], best[1]


def plan_batches(lengths: Sequence[int], batch_size: int) -> list[list[int]]:
    """Agrupa indices por largo descendente, para que el peor lote falle primero."""
    order = sorted(range(len(lengths)), key=lambda index: (-lengths[index], index))
    size = max(1, batch_size)
    return [order[start : start + size] for start in range(0, len(order), size)]


class Backend(ABC):
    name: str = "backend"
    last_usage: list[dict[str, Any]] = []

    @abstractmethod
    def generate(
        self, batch_of_messages: list[Messages], gen_config: dict[str, Any], seed: int
    ) -> list[str]:
        raise NotImplementedError


# ------------------------------------------------------------------- modelo simulado


@dataclass(frozen=True)
class ScriptContext:
    """Lo que ve un guion: `seed` es la del lote y `row` la fila dentro de el."""

    seed: int
    row: int
    batch_index: int
    gen_config: dict[str, Any]


class ScriptedBackend(Backend):
    """Modelo por guion, para tests.

    `script` es una lista de textos por turno (el turno es el numero de mensajes
    `assistant` previos) o una funcion `script(messages, context) -> str`. Agrupa y
    aplica las paradas igual que HFBackend. Un guion aleatorio debe sortear con
    `(context.seed, context.row)`, que es lo que recibe una fila real.
    """

    def __init__(
        self, script: Sequence[str] | Callable[[Messages, ScriptContext], str], name: str = "scripted"
    ) -> None:
        self.script = script
        self.name = name
        self.last_usage = []
        self.calls: list[dict[str, Any]] = []

    def _turn(self, messages: Messages, context: ScriptContext) -> str:
        if callable(self.script):
            return self.script(messages, context)
        return self.script[sum(m["role"] == "assistant" for m in messages)]

    def generate(
        self, batch_of_messages: list[Messages], gen_config: dict[str, Any], seed: int
    ) -> list[str]:
        self.calls.append({"seed": seed, "n": len(batch_of_messages)})
        stops = tuple(gen_config.get("stop_strings", DEFAULT_STOP_STRINGS))
        lengths = [sum(len(m["content"]) for m in messages) for messages in batch_of_messages]
        texts = [""] * len(batch_of_messages)
        usage: list[dict[str, Any]] = [{} for _ in batch_of_messages]
        lots = plan_batches(lengths, gen_config.get("batch_size", 1))
        for batch_index, lot in enumerate(lots):
            lot_seed = batch_seed(seed, batch_index)
            for row, index in enumerate(lot):
                context = ScriptContext(lot_seed, row, batch_index, gen_config)
                text, stop = cut_at_stop(self._turn(batch_of_messages[index], context), stops)
                texts[index] = text
                usage[index] = {
                    "new_tokens": len(text.split()),
                    "seconds": 0.0,
                    "stop_reason": _STOP_REASONS.get(stop, "eos"),
                }
        self.last_usage = usage
        return texts


# ---------------------------------------------------------------------- Hugging Face


def template_accepts_thinking(chat_template: Any) -> bool:
    """Qwen3 lee `enable_thinking`; Gemma y Llama no, y entonces no se pasa."""
    return "enable_thinking" in str(chat_template or "")


def decode_new_tokens(
    tokenizer: Any,
    new_ids: Sequence[int],
    eos_ids: Sequence[int],
    pad_id: int | None,
    stops: Sequence[str],
) -> tuple[str, int, str]:
    """Texto de una fila, sin relleno ni EOS. Devuelve (texto, tokens, stop_reason).

    Conserva la cadena de parada. `transformers` puede parar en un token que se pasa de
    la cadena, y lo que sobra se recorta para no provocar `text_after_answer`.
    """
    ids = [int(token) for token in new_ids]
    reason = "length"
    for position, token in enumerate(ids):
        if token in eos_ids:
            ids, reason = ids[:position], "eos"
            break
    while ids and ids[-1] == pad_id:
        ids.pop()
    text, stop = cut_at_stop(tokenizer.decode(ids, skip_special_tokens=True), stops)
    if stop is None:
        # Si la parada es un token especial, el decodificado la borra. El rollout la
        # repone al ver stop_reason="answer".
        stop = cut_at_stop(tokenizer.decode(ids, skip_special_tokens=False), stops)[1]
    return text, len(ids), _STOP_REASONS.get(stop, reason)


class HFBackend(Backend):
    """Modelo de Hugging Face, con lotes reales y padding a la izquierda."""

    def __init__(
        self,
        model_id: str,
        *,
        name: str | None = None,
        trust_remote_code: bool = False,
        chat_template: str | None = None,
        torch_dtype: Any = "auto",
        device_map: Any = "auto",
        model_kwargs: dict[str, Any] | None = None,
    ) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._torch = torch
        self.model_id = model_id
        self.name = name or model_id
        self.last_usage = []
        self._batch_limit: int | None = None
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id, padding_side="left", trust_remote_code=trust_remote_code
        )
        self.tokenizer.padding_side = "left"
        if chat_template is not None:
            self.tokenizer.chat_template = chat_template
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token or self.tokenizer.unk_token
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            device_map=device_map,
            trust_remote_code=trust_remote_code,
            **(model_kwargs or {}),
        )
        self.model.eval()
        self._eos_ids = self._collect_eos_ids()

    def _collect_eos_ids(self) -> set[int]:
        found = self.model.generation_config.eos_token_id
        ids = set(found if isinstance(found, (list, tuple)) else [found])
        ids.add(self.tokenizer.eos_token_id)
        return {token for token in ids if token is not None}

    def render_chat(self, messages: Messages, gen_config: dict[str, Any]) -> str:
        options: dict[str, Any] = {}
        if template_accepts_thinking(self.tokenizer.chat_template):
            # La plantilla de Qwen3 razona si la variable falta: solo un `false` explicito
            # agrega el bloque <think> vacio. Omitirlo debe significar sin thinking, que
            # es lo que asume la clave del rollout.
            options["enable_thinking"] = bool(gen_config.get("enable_thinking", False))
        return self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, **options
        )

    def _generate_options(self, gen_config: dict[str, Any], stops: tuple[str, ...]) -> dict[str, Any]:
        do_sample = bool(gen_config.get("do_sample", True))
        options: dict[str, Any] = {
            "max_new_tokens": gen_config.get("max_new_tokens", 512),
            "do_sample": do_sample,
            "pad_token_id": self.tokenizer.pad_token_id,
        }
        if do_sample:
            for key in ("temperature", "top_p", "top_k"):
                if key in gen_config:
                    options[key] = gen_config[key]
        if "repetition_penalty" in gen_config:
            options["repetition_penalty"] = gen_config["repetition_penalty"]
        if stops:
            # transformers exige el tokenizer para evaluar stop_strings.
            options["stop_strings"] = list(stops)
            options["tokenizer"] = self.tokenizer
        return options

    def _generate_lot(
        self, texts: list[str], options: dict[str, Any], stops: tuple[str, ...], seed: int
    ) -> list[tuple[str, int, str, float]]:
        torch = self._torch
        started = time.perf_counter()
        torch.manual_seed(seed)
        encoded = self.tokenizer(
            texts, return_tensors="pt", padding=True, add_special_tokens=False
        ).to(self.model.device)
        output = self.model.generate(**encoded, **options)
        prompt_length = encoded["input_ids"].shape[1]
        rows = [
            decode_new_tokens(
                self.tokenizer, row[prompt_length:].tolist(), self._eos_ids,
                self.tokenizer.pad_token_id, stops,
            )
            for row in output
        ]
        seconds = (time.perf_counter() - started) / len(texts)
        return [(text, tokens, reason, seconds) for text, tokens, reason in rows]

    def _run_lot(
        self, texts: list[str], options: dict[str, Any], stops: tuple[str, ...], seed: int
    ) -> list[tuple[str, int, str, float]]:
        """Ante falta de memoria parte el lote; una sola fila que no cabe se marca "oom"."""
        torch = self._torch
        try:
            return self._generate_lot(texts, options, stops, seed)
        except torch.cuda.OutOfMemoryError:
            pass  # Se sale del except para soltar la traza, que retiene los tensores.
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        if len(texts) == 1:
            print(f"[{self.name}] sin memoria con una sola muestra", flush=True)
            return [("", 0, "oom", 0.0)]
        middle = len(texts) // 2
        self._batch_limit = middle
        print(f"[{self.name}] sin memoria: lote reducido a {middle}", flush=True)
        left = self._run_lot(texts[:middle], options, stops, batch_seed(seed, 0))
        return left + self._run_lot(texts[middle:], options, stops, batch_seed(seed, 1))

    def generate(
        self, batch_of_messages: list[Messages], gen_config: dict[str, Any], seed: int
    ) -> list[str]:
        stops = tuple(gen_config.get("stop_strings", DEFAULT_STOP_STRINGS))
        # `stop_strings` no distingue <think>: con thinking pararia al nombrar una etiqueta
        # mientras razona. Ahi se genera hasta EOS y `cut_at_stop` recorta despues.
        thinking = bool(gen_config.get("enable_thinking"))
        options = self._generate_options(gen_config, () if thinking else stops)
        rendered = [self.render_chat(messages, gen_config) for messages in batch_of_messages]
        lengths = [
            len(self.tokenizer(text, add_special_tokens=False)["input_ids"]) for text in rendered
        ]
        batch_size = gen_config.get("batch_size", 1)
        if self._batch_limit is not None:
            batch_size = min(batch_size, self._batch_limit)
        texts = [""] * len(rendered)
        usage: list[dict[str, Any]] = [{} for _ in rendered]
        for batch_index, lot in enumerate(plan_batches(lengths, batch_size)):
            results = self._run_lot(
                [rendered[index] for index in lot], options, stops, batch_seed(seed, batch_index)
            )
            for index, (text, tokens, reason, seconds) in zip(lot, results):
                texts[index] = text
                usage[index] = {"new_tokens": tokens, "seconds": seconds, "stop_reason": reason}
        self.last_usage = usage
        return texts
