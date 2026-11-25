"""DPO con LoRA sobre los pares (correcta, incorrecta) del profesor (camino 5 del proyecto).

Uso (humo):
    python scripts/train_dpo.py --out runs/dpo_humo --limit 6 --max-steps 2
DPO completo sobre los 106 pares:
    python scripts/train_dpo.py --out runs/dpo
Solo con pares sin herramientas (una sola ronda por respuesta):
    python scripts/train_dpo.py --out runs/dpo_visible --condition visible

Usa el DPOTrainer de TRL. El modelo de referencia es el mismo modelo sin el adaptador, asi
que no hace falta cargar una segunda copia.

Limite conocido: en los pares con herramientas, `chosen` y `rejected` tienen tres mensajes
(llamadas, resultados, respuesta) y la perdida cubre todos los tokens que siguen al prompt,
incluido el mensaje con los resultados. Con `--condition visible` cada respuesta es un solo
mensaje y ese problema no existe, a costa de quedarse con 41 de los 106 pares.

Los pares que no caben en --max-length se descartan con --drop-longer en vez de truncarse:
truncar puede cortar justo el `<answer>` de ambas respuestas y dejar un par sin senal.

Salida en --out: `adapter/`, `train_log.json`, `log.jsonl` (lo mismo, pero se escribe paso a
paso: sirve si la corrida se corta) y `manifest.json`.

Con --max-minutes el entrenamiento se detiene solo al cumplirse el tiempo y guarda el adaptador
y los registros como si hubiera terminado: sirve para acotar una corrida en Kaggle.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import train_common as common  # noqa: E402
from inventory_harness import training_prep as prep  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common.add_common_args(parser, lr=2e-5, epochs=3)
    parser.add_argument("--data", type=Path, default=common.DEFAULT_DPO, help="dpo.jsonl")
    parser.add_argument("--condition", choices=("all", "visible", "tools"), default="all")
    parser.add_argument("--beta", type=float, default=0.1, help="fuerza de la restriccion al modelo de referencia")
    parser.add_argument("--max-length", type=int, default=4096, help="tokens de prompt mas respuesta")
    parser.add_argument("--drop-longer", action="store_true",
                        help="descarta los pares con algun lado mas largo que --max-length en vez de truncarlos")
    parser.add_argument("--max-minutes", type=float,
                        help="detiene el entrenamiento tras N minutos de entrenar (sin contar la carga del modelo) y guarda lo hecho")
    return parser.parse_args(argv)


def longest_side(tokenizer, example: dict) -> int:
    """Tokens de prompt mas respuesta del lado mas largo del par, con la plantilla de chat."""
    sizes = []
    for side in ("chosen", "rejected"):
        ids = tokenizer.apply_chat_template(example["prompt"] + example[side], tokenize=True)
        if isinstance(ids, dict) or hasattr(ids, "keys"):
            ids = ids["input_ids"]
        sizes.append(len(ids))
    return max(sizes)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    from datasets import Dataset
    from transformers import TrainerCallback, set_seed
    from trl import DPOConfig, DPOTrainer

    set_seed(args.seed)
    rows = prep.load_jsonl(args.data)
    rows = prep.keep_conditions(prep.keep_difficulties(rows, args.difficulties), args.condition)
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("No quedaron pares. Revisa --data, --condition y --difficulties.")
    examples = [prep.dpo_example(row) for row in rows]
    tokenizer = common.load_tokenizer(args.model)
    stats = {"pares": len(examples)}
    if args.drop_longer:
        kept = [ex for ex in examples if longest_side(tokenizer, ex) <= args.max_length]
        stats["descartados_por_largo"] = len(examples) - len(kept)
        examples = kept
        stats["pares"] = len(examples)
    if not examples:
        raise SystemExit("Todos los pares superan --max-length.")
    dataset = Dataset.from_list(examples)
    print(f"DPO: {stats}", flush=True)

    model = common.load_model(args.model)
    config = DPOConfig(
        output_dir=str(args.out / "trainer"),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        beta=args.beta,
        max_length=args.max_length,
        logging_steps=args.logging_steps,
        save_strategy="steps" if args.save_steps else "no",
        save_steps=args.save_steps or 500,
        gradient_checkpointing=args.gradient_checkpointing,
        seed=args.seed,
        report_to="none",
        **common.precision_flags(),
    )
    log_path = args.out / "log.jsonl"
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    stopped_by_time: list[bool] = []

    class StepLog(TrainerCallback):
        """Despues de cada registro, deja las metricas del paso (perdida, margenes, exactitud)."""

        def on_log(self, _args, state, _control, logs=None, **kwargs):
            row = {"paso": state.global_step, "minutos": round((time.time() - started) / 60, 2), **(logs or {})}
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, default=str) + chr(10))

    class TimeLimit(TrainerCallback):
        """Detiene el entrenamiento al cumplirse --max-minutes; el resto del script guarda como siempre."""

        def on_step_end(self, _args, state, control, **kwargs):
            if args.max_minutes and (time.time() - started) / 60 >= args.max_minutes and not stopped_by_time:
                stopped_by_time.append(True)
                control.should_training_stop = True
                print(f"Se cumplieron {args.max_minutes} minutos: se detiene en el paso {state.global_step}.", flush=True)

    trainer = DPOTrainer(
        model=model,
        args=config,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=common.lora_config(args),
        callbacks=[StepLog(), TimeLimit()],
    )
    started = time.time()  # el tiempo cuenta desde aqui, sin la carga del modelo ni la tokenizacion
    trainer.train()

    trainer.model.save_pretrained(str(args.out / "adapter"))
    tokenizer.save_pretrained(str(args.out / "adapter"))
    common.save_log_history(args.out, trainer.state.log_history)
    common.write_manifest(args.out, "dpo", args, {
        "datos": {"archivo": str(args.data), "sha256": common.file_sha256(args.data), **stats},
        "pasos": trainer.state.global_step,
        "detenido_por_tiempo": bool(stopped_by_time),
    })
    print(f"Adaptador guardado en {args.out / 'adapter'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
