from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace

import pytest

from inventory_harness.backends import (
    DEFAULT_STOP_STRINGS,
    Backend,
    HFBackend,
    ScriptedBackend,
    batch_seed,
    cut_at_stop,
    decode_new_tokens,
    derive_seed,
    plan_batches,
    template_accepts_thinking,
)


def user(text):
    return [{"role": "user", "content": text}]


def test_module_does_not_import_torch():
    code = "import sys, inventory_harness.backends; print('torch' in sys.modules, 'transformers' in sys.modules)"
    output = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True,
        env={"PYTHONPATH": "src"},
    )
    assert output.stdout.strip() == "False False"


def test_scripted_list_by_turn():
    backend = ScriptedBackend(["uno", "dos"])
    conversation = user("hola")
    assert backend.generate([conversation], {}, 0) == ["uno"]
    conversation = conversation + [{"role": "assistant", "content": "uno"}, *user("x")]
    assert backend.generate([conversation], {}, 0) == ["dos"]
    assert isinstance(backend, Backend)


def test_scripted_function_keeps_input_order_with_batches():
    backend = ScriptedBackend(lambda messages, context: messages[0]["content"].upper())
    batch = [user("a"), user("ccc"), user("bb"), user("dddd"), user("e")]
    assert backend.generate(batch, {"batch_size": 2}, 0) == ["A", "CCC", "BB", "DDDD", "E"]
    assert len(backend.last_usage) == 5


def test_scripted_applies_stops_and_keeps_them():
    backend = ScriptedBackend(["<answer>x</answer> resto"])
    assert backend.generate([user("a")], {}, 0) == ["<answer>x</answer>"]
    assert backend.last_usage[0]["stop_reason"] == "answer"


def test_scripted_exposes_lot_seed_and_row():
    seen = []

    def script(messages, context):
        seen.append((context.seed, context.row, context.batch_index))
        return ""

    ScriptedBackend(script).generate([user("a")] * 3, {"batch_size": 2}, 7)
    assert seen == [(batch_seed(7, 0), 0, 0), (batch_seed(7, 0), 1, 0), (batch_seed(7, 1), 0, 1)]


def test_seeds_are_stable_and_in_range():
    assert derive_seed("a", 1) == derive_seed("a", 1)
    assert derive_seed("a", 1) != derive_seed("a", 2)
    assert 0 <= derive_seed("a") < 2**63
    assert batch_seed(1, 0) != batch_seed(1, 1)


def test_derive_seed_value_is_fixed_across_runs():
    assert derive_seed("inventario") == derive_seed("inventario")
    code = "from inventory_harness.backends import derive_seed; print(derive_seed('inventario'))"
    output = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True,
        env={"PYTHONPATH": "src", "PYTHONHASHSEED": "123"},
    )
    assert int(output.stdout) == derive_seed("inventario")


@pytest.mark.parametrize(
    "text, expected, stop",
    [
        ("a</answer>", "a</answer>", "</answer>"),
        ("a</answer>\nresto", "a</answer>", "</answer>"),
        ("a<tool_result>b</answer>", "a<tool_result>", "<tool_result>"),
        ("sin parada", "sin parada", None),
    ],
)
def test_cut_at_stop(text, expected, stop):
    assert cut_at_stop(text, DEFAULT_STOP_STRINGS) == (expected, stop)


def test_plan_batches_sorted_and_complete():
    lots = plan_batches([1, 5, 3, 4, 2], 2)
    assert lots == [[1, 3], [2, 4], [0]]
    assert plan_batches([], 2) == []
    assert plan_batches([1, 1], 0) == [[0], [1]]


def test_template_detection():
    assert template_accepts_thinking("{% if enable_thinking is defined %}")
    assert not template_accepts_thinking("{{ messages }}")
    assert not template_accepts_thinking(None)


class ToyTokenizer:
    """Cada token es un trozo de texto; 0 es relleno y 1 es EOS (especiales)."""

    vocabulary = {
        0: "<pad>", 1: "<eos>", 2: "<answer>\nfaltan: 3\n", 3: "</answer>", 4: "<tool_result>",
        5: "hola ", 6: "</answer>\nresto",
    }
    special = {0, 1, 3}

    def __init__(self, stop_is_special=False):
        self.stop_is_special = stop_is_special

    def decode(self, ids, skip_special_tokens=False):
        hidden = {0, 1} | ({3} if self.stop_is_special else set())
        if not skip_special_tokens:
            hidden = set()
        return "".join(self.vocabulary[token] for token in ids if token not in hidden)


def decode(ids, tokenizer=None, pad=0):
    return decode_new_tokens(tokenizer or ToyTokenizer(), ids, {1}, pad, DEFAULT_STOP_STRINGS)


def test_stop_string_survives_decoding_and_padding():
    text, tokens, reason = decode([2, 3, 0, 0, 0])
    assert text == "<answer>\nfaltan: 3\n</answer>"
    assert (tokens, reason) == (2, "answer")


def test_token_overrunning_the_stop_is_trimmed():
    text, _, reason = decode([2, 6])
    assert text == "<answer>\nfaltan: 3\n</answer>" and reason == "answer"


def test_tool_result_stop_is_reported():
    assert decode([5, 4, 0]) == ("hola <tool_result>", 2, "tool_result")


def test_eos_and_length_reasons():
    assert decode([5, 1, 0, 0]) == ("hola ", 1, "eos")
    assert decode([5, 5]) == ("hola hola ", 2, "length")


def test_pad_equal_to_eos():
    text, tokens, reason = decode([2, 3, 1, 1], pad=1)
    assert (text.endswith("</answer>"), tokens, reason) == (True, 2, "answer")


def test_special_stop_token_is_reported_for_restoration():
    text, _, reason = decode([2, 3], tokenizer=ToyTokenizer(stop_is_special=True))
    assert "</answer>" not in text and reason == "answer"


class FakeOOM(RuntimeError):
    pass


def fake_backend(capacity=None):
    """HFBackend sin torch: solo se reemplaza la llamada que toca el modelo."""
    backend = HFBackend.__new__(HFBackend)
    backend.name = "falso"
    backend.last_usage = []
    backend._batch_limit = None
    backend._torch = SimpleNamespace(
        cuda=SimpleNamespace(
            OutOfMemoryError=FakeOOM, is_available=lambda: False, empty_cache=lambda: None
        )
    )
    backend.lots = []
    backend.tokenizer = SimpleNamespace(
        chat_template="plantilla",
        pad_token_id=0,
        apply_chat_template=lambda messages, **options: messages[0]["content"],
        __call__=None,
    )

    class Tok(SimpleNamespace):
        def __call__(self, text, add_special_tokens=False):
            return {"input_ids": text.split()}

    backend.tokenizer = Tok(**vars(backend.tokenizer))

    def lot(texts, options, stops, seed):
        backend.lots.append((list(texts), seed))
        if capacity is not None and len(texts) > capacity:
            raise FakeOOM()
        return [(text.upper(), 1, "eos", 0.0) for text in texts]

    backend._generate_lot = lot
    return backend


def test_generate_sorts_by_length_and_restores_order():
    backend = fake_backend()
    batch = [user("a"), user("b b b"), user("c c")]
    assert backend.generate(batch, {"batch_size": 2}, 1) == ["A", "B B B", "C C"]
    assert [texts for texts, _ in backend.lots] == [["b b b", "c c"], ["a"]]


def test_lots_use_different_seeds():
    backend = fake_backend()
    backend.generate([user("a")] * 4, {"batch_size": 1}, 1)
    assert len({seed for _, seed in backend.lots}) == 4


def test_oom_halves_batch_and_keeps_every_result(capsys):
    backend = fake_backend(capacity=2)
    batch = [user(f"t{i}") for i in range(8)]
    result = backend.generate(batch, {"batch_size": 8}, 1)
    assert result == [f"T{i}" for i in range(8)]
    assert backend._batch_limit == 2
    assert all(u["stop_reason"] == "eos" for u in backend.last_usage)


def test_oom_limit_applies_to_later_calls():
    backend = fake_backend(capacity=2)
    backend.generate([user(f"t{i}") for i in range(4)], {"batch_size": 4}, 1)
    backend.lots.clear()
    backend.generate([user(f"t{i}") for i in range(4)], {"batch_size": 4}, 2)
    assert [len(texts) for texts, _ in backend.lots] == [2, 2]


def test_oom_with_single_sample_does_not_raise():
    backend = fake_backend(capacity=0)
    assert backend.generate([user("a"), user("b")], {"batch_size": 2}, 1) == ["", ""]
    assert [u["stop_reason"] for u in backend.last_usage] == ["oom", "oom"]


def test_other_errors_propagate():
    backend = fake_backend()

    def explode(*args):
        raise ValueError("otro")

    backend._generate_lot = explode
    with pytest.raises(ValueError):
        backend.generate([user("a")], {"batch_size": 1}, 1)


def test_thinking_only_passed_when_template_accepts_it():
    backend = fake_backend()
    seen = {}

    def apply(messages, **options):
        seen.clear()
        seen.update(options)
        return "x"

    backend.tokenizer.apply_chat_template = apply
    backend.render_chat(user("a"), {"enable_thinking": True})
    assert "enable_thinking" not in seen and seen["add_generation_prompt"] is True
    backend.tokenizer.chat_template = "{% if enable_thinking %}"
    backend.render_chat(user("a"), {"enable_thinking": False})
    assert seen["enable_thinking"] is False
    backend.render_chat(user("a"), {"enable_thinking": True})
    assert seen["enable_thinking"] is True


def test_omitted_thinking_means_off_when_template_supports_it():
    backend = fake_backend()
    seen = {}
    backend.tokenizer.chat_template = "{% if enable_thinking %}"
    backend.tokenizer.apply_chat_template = lambda messages, **options: seen.update(options) or "x"
    backend.render_chat(user("a"), {})
    assert seen["enable_thinking"] is False


def test_generate_options():
    backend = fake_backend()
    options = backend._generate_options(
        {"max_new_tokens": 9, "temperature": 0.5, "top_p": 0.8, "do_sample": True}, DEFAULT_STOP_STRINGS
    )
    assert options["stop_strings"] == list(DEFAULT_STOP_STRINGS)
    assert options["tokenizer"] is backend.tokenizer
    assert options["temperature"] == 0.5 and options["max_new_tokens"] == 9
    greedy = backend._generate_options({"do_sample": False, "temperature": 0.5}, ())
    assert "temperature" not in greedy and "stop_strings" not in greedy


def test_parada_dentro_de_think_no_cuenta():
    from inventory_harness.backends import cut_at_stop

    stops = ("</answer>", "<tool_result>")
    final = "<answer>\nalcanza: no\nfaltan: 3\n</answer>"
    text = f"<think>uso </answer> y <tool_result> al final</think>\n{final}\nresto"
    assert cut_at_stop(text, stops) == (text[: text.index("\nresto")], "</answer>")
    abierto = "<think>todavia razono </answer> y sigo"
    assert cut_at_stop(abierto, stops) == (abierto, None)


class _RecordingModelOptions:
    """Captura lo que `generate` pasaria al modelo, sin cargar torch."""

    @staticmethod
    def options_for(gen_config):
        from inventory_harness.backends import DEFAULT_STOP_STRINGS, HFBackend

        backend = HFBackend.__new__(HFBackend)
        backend.tokenizer = SimpleNamespace(pad_token_id=0)
        seen = {}

        def capture(config, stops):
            seen["stops"] = stops
            raise RuntimeError("fin")

        backend._generate_options = capture
        with pytest.raises(RuntimeError):
            backend.generate([[{"role": "user", "content": "x"}]], gen_config, 1)
        return seen["stops"], DEFAULT_STOP_STRINGS


def test_thinking_no_usa_stop_strings_al_generar():
    stops, default = _RecordingModelOptions.options_for({"enable_thinking": True})
    assert stops == ()
    stops, default = _RecordingModelOptions.options_for({"enable_thinking": False})
    assert stops == default
