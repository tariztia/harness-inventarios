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

Salida en --out: `adapter/`, `train_log.json` y `manifest.json`.
"""
from __future__ import annotations

import argparse
import sys
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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    from datasets import Dataset
    from transformers import set_seed
    from trl import DPOConfig, DPOTrainer

    set_seed(args.seed)
    rows = prep.load_jsonl(args.data)
    rows = prep.keep_conditions(prep.keep_difficulties(rows, args.difficulties), args.condition)
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("No quedaron pares. Revisa --data, --condition y --difficulties.")
    dataset = Dataset.from_list([prep.dpo_example(row) for row in rows])
    stats = {"pares": len(rows)}
    print(f"DPO: {stats}", flush=True)

    tokenizer = common.load_tokenizer(args.model)
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
    trainer = DPOTrainer(
        model=model,
        args=config,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=common.lora_config(args),
    )
    trainer.train()

    args.out.mkdir(parents=True, exist_ok=True)
    trainer.model.save_pretrained(str(args.out / "adapter"))
    tokenizer.save_pretrained(str(args.out / "adapter"))
    common.save_log_history(args.out, trainer.state.log_history)
    common.write_manifest(args.out, "dpo", args, {
        "datos": {"archivo": str(args.data), "sha256": common.file_sha256(args.data), **stats},
        "pasos": trainer.state.global_step,
    })
    print(f"Adaptador guardado en {args.out / 'adapter'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
