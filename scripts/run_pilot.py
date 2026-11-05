"""Ejecuta una etapa del piloto y guarda rollouts, reanudando sin duplicar.

Humo sin GPU:
    uv run python scripts/run_pilot.py --stage exploracion --dry-run --limit 9 --out results/humo
Exploracion en Colab:
    python scripts/run_pilot.py --stage exploracion --thinking both --out "$DRIVE/results/exploracion"

Cada etapa usa su propia semilla base y su propia carpeta. Una carpeta queda atada a su
dataset y a su configuracion de generacion: reanudar con otros valores haria pasar rollouts
de instancias distintas por los mismos IDs, asi que se rechaza.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gc
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from inventory_harness.generator import generate_dataset  # noqa: E402
from inventory_harness.schema import CONDITIONS, SPLITS, Instance  # noqa: E402

TARGET_MODEL = "Qwen/Qwen3-1.7B"
# Copia sin aprobacion manual de meta-llama/Llama-3.2-1B-Instruct (1,24B de parametros).
LLAMA_MODEL = "unsloth/Llama-3.2-1B-Instruct"
GATED_MODELS = ("google/gemma-3-1b-it",)
# El piloto se limita a modelos de maximo 2B.
DEFAULT_MODELS = (TARGET_MODEL, LLAMA_MODEL)
# Gemma 3 puede dar NaN en float16 segun la documentacion de su comunidad; pesa 2 GiB en 16 bits.
FLOAT32_MODEL_PREFIXES = ("google/gemma-3",)
# Qwen3 es el unico de estos modelos con modo thinking en su plantilla de chat.
THINKING_MODEL_PREFIXES = ("qwen/qwen3",)

STAGES: dict[str, dict[str, Any]] = {
    # `train`, para que la calibracion no toque `eval`. `test` queda reservado.
    "exploracion": {"base_seed": 11, "split": "train", "n_per_cell": 5, "n_samples": 2},
    "piloto": {"base_seed": 2026, "split": "eval", "n_per_cell": 40, "n_samples": 5},
}
DEFAULT_BATCH_SIZE = {TARGET_MODEL: 16, LLAMA_MODEL: 16}
FALLBACK_BATCH_SIZE = 16
MAX_NEW_TOKENS_OFF = 768
MAX_NEW_TOKENS_THINKING = 2048
# Explicitos: de otro modo cada modelo hereda los de su generation_config.
SAMPLING = {"do_sample": True, "temperature": 0.7, "top_p": 0.95, "top_k": 50, "repetition_penalty": 1.0}
GENERATION_SEED = 2026
# Una muestra se cuenta como hecha aunque fallara; estas se reintentan una vez.
RETRY_PASSES = 1


# --- Dataset --------------------------------------------------------------


def build_dataset(split: str, n_per_cell: int, base_seed: int) -> list[Instance]:
    """Instancias del split, intercaladas por celda.

    Genera los tres splits, como scripts/generate_dataset.py, para obtener las mismas
    instancias: los duplicados se descartan entre splits. Intercalar hace que una corrida
    cortada deje todas las celdas parejas, y no solo la primera familia.
    """
    config = {"n_per_cell": {name: n_per_cell for name in SPLITS}, "base_seed": base_seed}
    by_cell: dict[tuple[str, str], list[Instance]] = defaultdict(list)
    for instance in generate_dataset(config):
        if instance.split == split:
            by_cell[(instance.family, instance.difficulty)].append(instance)
    return [members[i] for i in range(n_per_cell) for members in by_cell.values()]


def dataset_fingerprint(instances: list[Instance]) -> str:
    digest = hashlib.sha256()
    for instance in sorted(instances, key=lambda item: item.id):
        digest.update(json.dumps(instance.to_dict(), sort_keys=True).encode("utf-8"))
    return digest.hexdigest()


# --- Variantes ------------------------------------------------------------


def supports_thinking(model: str) -> bool:
    return model.lower().startswith(THINKING_MODEL_PREFIXES)


def expand_variants(models: list[str], thinking: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Una variante por modelo y modo. Cada una tiene su etiqueta, y por tanto sus claves."""
    variants: list[dict[str, Any]] = []
    notes: list[str] = []
    for model in models:
        modes = {"off": [False], "on": [True], "both": [False, True]}[thinking]
        if not supports_thinking(model) and True in modes:
            notes.append(f"{model}: sin modo thinking, se corre solo con thinking off")
            modes = [False]
        for enabled in modes:
            variants.append(
                {"model": model, "thinking": enabled, "label": f"{model}+think" if enabled else model}
            )
    return variants, notes


def file_label(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9._+-]", "_", label)


def rollouts_path(out: Path, label: str) -> Path:
    return out / f"rollouts_{file_label(label)}.jsonl"


# --- Archivos de rollouts --------------------------------------------------


def finished_keys(path: Path) -> tuple[set[str], int]:
    """(claves terminadas, muestras con internal_error). Esas ultimas no cuentan como hechas."""
    keys: set[str] = set()
    internal = 0
    if not path.exists():
        return keys, internal
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                record = json.loads(line)
                key, error = record["key"], record["verdict"]["error_type"]
            except (ValueError, KeyError, TypeError):
                continue  # rollout.py descarta la linea cortada al reanudar.
            if error == "internal_error":
                internal += 1
            else:
                keys.add(key)
    return keys, internal


# --- Entorno y manifest -----------------------------------------------------


def environment() -> dict[str, Any]:
    info: dict[str, Any] = {
        "python": platform.python_version(),
        "plataforma": platform.platform(),
        "torch": None,
        "transformers": None,
        "gpu": None,
    }
    try:
        import transformers

        info["transformers"] = transformers.__version__
    except ImportError:
        pass
    try:
        import torch

        info["torch"] = torch.__version__
        if torch.cuda.is_available():
            info["gpu"] = torch.cuda.get_device_name(0)
    except ImportError:
        pass
    return info


def code_hash() -> str:
    digest = hashlib.sha256()
    for folder in ("src", "scripts"):
        for path in sorted((ROOT / folder).rglob("*.py")):
            digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def git_commit() -> str | None:
    try:
        done = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def write_manifest(out: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = now()
    temporary = out / "manifest.json.tmp"
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, out / "manifest.json")


def load_manifest(out: Path) -> dict[str, Any] | None:
    path = out / "manifest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SystemExit(f"manifest.json ilegible en {out}: {exc}") from exc


def check_same_run(previous: dict[str, Any], manifest: dict[str, Any], out: Path) -> None:
    """Rechaza reutilizar una carpeta para otra corrida. Los IDs se repetirian entre datasets."""
    for name in ("stage", "dry_run", "dataset", "n_samples"):
        if previous.get(name) != manifest.get(name):
            raise SystemExit(
                f"{out} ya contiene otra corrida: `{name}` era {previous.get(name)!r} y ahora es "
                f"{manifest.get(name)!r}. Usa otra carpeta con --out."
            )


def build_gen_config(args: argparse.Namespace, variant: dict[str, Any], batch_size: int) -> dict[str, Any]:
    default = MAX_NEW_TOKENS_THINKING if variant["thinking"] else MAX_NEW_TOKENS_OFF
    return {
        "model": variant["label"],
        "model_id": variant["model"],
        "enable_thinking": variant["thinking"],
        "max_new_tokens": args.max_new_tokens or default,
        **SAMPLING,
        "seed": GENERATION_SEED,
        "batch_size": batch_size,
    }


def comparable_config(gen_config: dict[str, Any]) -> dict[str, Any]:
    """batch_size puede bajar tras quedarse sin memoria; no cambia que se esta midiendo."""
    return {key: value for key, value in gen_config.items() if key != "batch_size"}


# --- Backends -------------------------------------------------------------


def scripted_policy(instances: list[Instance]) -> Any:
    """Modelo falso para el dry-run: llama bien, y falla la respuesta en parte de los casos.

    La falla depende de la semilla de la fila, de modo que pass@k difiere de pass@1 y el
    pipeline completo se ejercita con datos que no son triviales.
    """
    import random

    from inventory_harness.baselines import format_answer
    from inventory_harness.reward import InstanceStore

    store = InstanceStore(instances)

    def policy(messages: list[dict[str, str]], context: Any) -> str:
        found = store.lookup(messages[0]["content"])
        if found is None:
            return "No encuentro el caso."
        instance, condition = found
        if condition == "tools" and len(messages) == 1:
            calls = [
                {"name": "get_inventory", "arguments": {"product_id": product, "location_id": location}}
                for product, location in instance.required_records
            ]
            return "\n".join(f"<tool_call>{json.dumps(call)}</tool_call>" for call in calls)
        if random.Random(f"{context.seed}|{context.row}").random() < 0.4:
            return "No tengo una respuesta."
        return "Calculo el resultado.\n\n" + format_answer(instance.family, instance.expected)

    return policy


def choose_dtype(model: str) -> Any:
    """Precision de carga. La T4 no tiene bfloat16 nativo: lo emula, y muy lento."""
    import torch

    if not torch.cuda.is_available():
        return "auto"
    if model.lower().startswith(FLOAT32_MODEL_PREFIXES):
        return torch.float32
    try:
        native = torch.cuda.is_bf16_supported(including_emulation=False)
    except TypeError:  # torch antiguo, sin ese argumento.
        native = "T4" not in torch.cuda.get_device_name(0)
    return "auto" if native else torch.float16


def make_backend(variant: dict[str, Any], dry_run: bool, instances: list[Instance]) -> Any:
    from inventory_harness.backends import HFBackend, ScriptedBackend

    if dry_run:
        return ScriptedBackend(scripted_policy(instances), name=variant["label"])
    return HFBackend(variant["model"], name=variant["label"], torch_dtype=choose_dtype(variant["model"]))


def free_memory() -> None:
    """Libera la GPU. Quien llama debe haber soltado antes su referencia al backend."""
    gc.collect()
    torch = sys.modules.get("torch")
    if torch is not None and torch.cuda.is_available():
        torch.cuda.empty_cache()


# --- Ejecucion -------------------------------------------------------------


def chunks(items: list[Any], size: int) -> list[list[Any]]:
    return [items[start : start + size] for start in range(0, len(items), size)]


def format_minutes(seconds: float) -> str:
    return f"{seconds / 60:.0f} min" if seconds < 5400 else f"{seconds / 3600:.1f} h"


def run_variant(
    variant: dict[str, Any],
    instances: list[Instance],
    conditions: list[str],
    n_samples: int,
    gen_config: dict[str, Any],
    path: Path,
    backend: Any,
    state: dict[str, Any],
    save_state: Any,
) -> None:
    """Corre por tramos, alternando condicion, e informa una estimacion con tiempos reales.

    Cada tramo cierra el archivo, lo que ayuda a que Drive lo sincronice, y alternar deja
    ambas condiciones parejas si la sesion se corta.
    """
    from inventory_harness.rollout import run_rollouts, sample_key

    label = variant["label"]
    wanted = {
        sample_key(label, condition, instance.id, sample)
        for condition in conditions
        for instance in instances
        for sample in range(n_samples)
    }
    state["esperados"] = len(wanted)

    def done_count() -> int:
        return len(finished_keys(path)[0] & wanted)

    def run(piece: list[Instance]) -> None:
        for condition in conditions:
            run_rollouts(
                piece, condition, backend, gen_config, n_samples, path,
                run_label=label, base_seed=GENERATION_SEED,
            )

    started = time.monotonic()
    done_at_start = done_count()
    # Una cohorte de rollout.py por tramo: 4 lotes de muestras de cada condicion.
    span = math.ceil(4 * gen_config["batch_size"] / n_samples)
    for piece in chunks(instances, span):
        run(piece)
        done = done_count()
        new = done - done_at_start
        state["hechos"] = done
        if new > 0:
            per_rollout = (time.monotonic() - started) / new
            state["segundos_por_rollout"] = round(per_rollout, 3)
            remaining = (len(wanted) - done) * per_rollout
            print(
                f"[{label}] TOTAL {done}/{len(wanted)} rollouts; {per_rollout:.2f} s/rollout; "
                f"faltan ~{format_minutes(remaining)}",
                flush=True,
            )
            save_state()
    for _ in range(RETRY_PASSES):
        if done_count() < len(wanted):
            print(f"[{label}] reintentando {len(wanted) - done_count()} muestras", flush=True)
            run(instances)
    state["hechos"] = done_count()
    state["errores_internos"] = finished_keys(path)[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", choices=sorted(STAGES), required=True)
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    parser.add_argument("--conditions", nargs="+", choices=CONDITIONS, default=list(CONDITIONS))
    parser.add_argument("--n-per-cell", type=int, help="por omision, el valor de la etapa")
    parser.add_argument("--n-samples", type=int, help="por omision, el valor de la etapa")
    parser.add_argument("--out", type=Path, help="por omision, results/<etapa>")
    parser.add_argument("--max-new-tokens", type=int, help="por omision, 768 sin thinking y 2048 con thinking")
    parser.add_argument("--batch-size", type=int, help="por omision, segun el modelo")
    parser.add_argument("--thinking", choices=("off", "on", "both"), default="off")
    parser.add_argument("--limit", type=int, help="humo: solo las primeras N instancias, intercaladas por celda")
    parser.add_argument("--dry-run", action="store_true", help="usa ScriptedBackend, sin GPU")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    stage = STAGES[args.stage]
    n_per_cell = args.n_per_cell or stage["n_per_cell"]
    n_samples = args.n_samples or stage["n_samples"]
    out = args.out or ROOT / "results" / args.stage
    out.mkdir(parents=True, exist_ok=True)

    instances = build_dataset(stage["split"], n_per_cell, stage["base_seed"])
    dataset = {
        "split": stage["split"],
        "n_per_cell": n_per_cell,
        "base_seed": stage["base_seed"],
        "fingerprint": dataset_fingerprint(instances),
    }
    selected = instances[: args.limit] if args.limit else instances
    variants, notes = expand_variants(list(args.models), args.thinking)
    for note in notes:
        print(note, flush=True)

    manifest: dict[str, Any] = {
        "stage": args.stage,
        "dry_run": args.dry_run,
        "dataset": dataset,
        "n_samples": n_samples,
        "limit": args.limit,
        "conditions": list(args.conditions),
        "seeds": {"dataset": stage["base_seed"], "generation": GENERATION_SEED},
        "entorno": environment(),
        "code_hash": code_hash(),
        "git_commit": git_commit(),
        "created_at": now(),
        "gen_configs": {},
        "modelos": {},
        "notas": notes,
    }
    previous = load_manifest(out)
    if previous:
        check_same_run(previous, manifest, out)
        manifest["created_at"] = previous.get("created_at", manifest["created_at"])
        manifest["gen_configs"] = previous.get("gen_configs", {})
        manifest["modelos"] = previous.get("modelos", {})
        if previous.get("code_hash") != manifest["code_hash"]:
            print("AVISO: el codigo cambio desde la corrida anterior; se anota en el manifest.", flush=True)
            manifest["hashes_anteriores"] = [
                *previous.get("hashes_anteriores", []),
                previous.get("code_hash"),
            ]
    write_manifest(out, manifest)

    failures = 0
    for variant in variants:
        label = variant["label"]
        batch_size = args.batch_size or DEFAULT_BATCH_SIZE.get(variant["model"], FALLBACK_BATCH_SIZE)
        gen_config = build_gen_config(args, variant, batch_size)
        known = manifest["gen_configs"].get(label)
        if known and comparable_config(known) != comparable_config(gen_config):
            print(
                f"[{label}] OMITIDO: ya hay rollouts con otra configuracion de generacion. "
                "Usa otra carpeta.",
                flush=True,
            )
            manifest["modelos"].setdefault(label, {})["aviso"] = "configuracion distinta; no se reanudo"
            write_manifest(out, manifest)
            failures += 1
            continue
        manifest["gen_configs"][label] = gen_config
        state = manifest["modelos"].setdefault(label, {})
        state.update({"estado": "cargando", "error": None})
        write_manifest(out, manifest)

        path = rollouts_path(out, label)
        try:
            backend = make_backend(variant, args.dry_run, selected)
        except Exception as exc:  # Modelo restringido, sin red, version incompatible...
            state.update({"estado": "no_cargo", "error": f"{type(exc).__name__}: {str(exc)[:300]}"})
            print(f"[{label}] no cargo y se salta: {state['error']}", flush=True)
            write_manifest(out, manifest)
            failures += 1
            free_memory()
            continue
        state["estado"] = "corriendo"
        write_manifest(out, manifest)
        try:
            run_variant(
                variant, selected, list(args.conditions), n_samples, gen_config, path, backend,
                state, lambda: write_manifest(out, manifest),
            )
            state["estado"] = "completo" if state["hechos"] == state["esperados"] else "incompleto"
        except Exception as exc:
            state.update({"estado": "error", "error": f"{type(exc).__name__}: {str(exc)[:300]}"})
            print(f"[{label}] se detuvo: {state['error']}", flush=True)
            failures += 1
        write_manifest(out, manifest)
        backend = None
        free_memory()

    print(f"Salida en {out}", flush=True)
    return 1 if failures == len(variants) else 0


if __name__ == "__main__":
    sys.exit(main())
