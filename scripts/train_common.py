"""Piezas comunes de los scripts de entrenamiento (SFT, DPO y GRPO).

Todo lo que importa `torch` o `transformers` esta dentro de funciones, para que importar
este modulo sin GPU no falle (los tests solo ejercitan las funciones puras).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TARGET_MODEL = "Qwen/Qwen3-1.7B"
DEFAULT_SFT = ROOT / "results" / "kaggle_qwen8b" / "datos_derivados_qwen8b" / "sft.jsonl"
DEFAULT_DPO = ROOT / "results" / "kaggle_qwen8b" / "datos_derivados_qwen8b" / "dpo.jsonl"
DIFFICULTIES = ("easy", "medium", "hard")


def add_common_args(parser: argparse.ArgumentParser, *, lr: float, epochs: float) -> None:
    parser.add_argument("--model", default=TARGET_MODEL, help="modelo base")
    parser.add_argument("--out", type=Path, required=True, help="carpeta de salida (adaptador, registros y manifest)")
    parser.add_argument("--difficulties", nargs="+", choices=DIFFICULTIES,
                        help="entrenar solo con estos niveles (por ejemplo: easy medium, para medir hard sin verlo)")
    parser.add_argument("--epochs", type=float, default=epochs)
    parser.add_argument("--max-steps", type=int, default=-1, help="humo: corta tras N pasos")
    parser.add_argument("--limit", type=int, help="humo: usa solo las primeras N filas")
    parser.add_argument("--learning-rate", type=float, default=lr)
    parser.add_argument("--batch-size", type=int, default=4, help="por GPU")
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--gradient-checkpointing", action="store_true", help="menos memoria, mas lento (T4)")
    parser.add_argument("--logging-steps", type=int, default=1)
    parser.add_argument("--save-steps", type=int, default=0, help="guarda el adaptador cada N pasos (0 = solo al final)")
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)


def lora_config(args: argparse.Namespace) -> Any:
    from peft import LoraConfig

    return LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules="all-linear",
        task_type="CAUSAL_LM",
    )


def precision_flags() -> dict[str, bool]:
    """bf16 en GPU que lo soporta (H100, A100, L4); fp16 en T4; ninguno en CPU."""
    import torch

    if not torch.cuda.is_available():
        return {"bf16": False, "fp16": False}
    try:
        native = torch.cuda.is_bf16_supported(including_emulation=False)
    except TypeError:
        native = "T4" not in torch.cuda.get_device_name(0)
    return {"bf16": bool(native), "fp16": not native}


def model_dtype() -> Any:
    import torch

    flags = precision_flags()
    if flags["bf16"]:
        return torch.bfloat16
    if flags["fp16"]:
        return torch.float16
    return torch.float32


def load_tokenizer(model: str, padding_side: str = "right") -> Any:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model, padding_side=padding_side)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def load_model(model: str, init_adapter: Path | None = None, trainable: bool = True) -> Any:
    """Modelo base; con `init_adapter`, un adaptador LoRA ya entrenado (por ejemplo, el del SFT)."""
    from transformers import AutoModelForCausalLM

    try:
        loaded = AutoModelForCausalLM.from_pretrained(model, dtype=model_dtype())
    except TypeError:  # transformers antiguo: el argumento se llamaba torch_dtype
        loaded = AutoModelForCausalLM.from_pretrained(model, torch_dtype=model_dtype())
    if init_adapter is not None:
        from peft import PeftModel

        loaded = PeftModel.from_pretrained(loaded, str(init_adapter), is_trainable=trainable)
    return loaded


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return None


def library_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {"python": platform.python_version()}
    for name in ("torch", "transformers", "trl", "peft", "accelerate", "datasets"):
        try:
            module = __import__(name)
            versions[name] = getattr(module, "__version__", None)
        except Exception:
            versions[name] = None
    try:
        import torch

        versions["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception:
        versions["gpu"] = None
    return versions


def write_manifest(out: Path, kind: str, args: argparse.Namespace, extra: dict[str, Any]) -> None:
    """manifest.json con lo necesario para repetir y comparar la corrida."""
    out.mkdir(parents=True, exist_ok=True)
    arguments = {key: (str(value) if isinstance(value, Path) else value) for key, value in vars(args).items()}
    manifest = {
        "tipo": kind,
        "argumentos": arguments,
        "git_commit": git_commit(),
        "versiones": library_versions(),
        "creado": dt.datetime.now().isoformat(timespec="seconds"),
        **extra,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def save_log_history(out: Path, history: list[dict[str, Any]]) -> None:
    """Historial de metricas (perdida, recompensa, largo, ...) para las curvas."""
    (out / "train_log.json").write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
