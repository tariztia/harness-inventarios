"""SFT con LoRA sobre las trazas correctas del profesor (camino 2 del proyecto).

Uso (humo, unos pasos):
    python scripts/train_sft.py --out runs/sft_humo --limit 8 --max-steps 3
SFT completo sobre las 170 trazas:
    python scripts/train_sft.py --out runs/sft
Solo con niveles faciles, para medir generalizacion a hard:
    python scripts/train_sft.py --out runs/sft_easy_medium --difficulties easy medium

Cada mensaje del asistente es un ejemplo aparte y la perdida cae solo en ese mensaje (ver
`training_prep.conversation_examples`). Usa `transformers.Trainer` con PEFT en vez del
SFTTrainer de TRL, porque este no sabe aprender solo el ultimo mensaje de una conversacion
con herramientas.

Salida en --out: `adapter/` (adaptador LoRA), `train_log.json` (perdida por paso) y
`manifest.json`. Para evaluar: ver docs/guia_entrenamiento.md.
"""
from __future__ import annotations

import argparse
import dataclasses
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import train_common as common  # noqa: E402
from inventory_harness import training_prep as prep  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common.add_common_args(parser, lr=2e-4, epochs=3)
    parser.add_argument("--data", type=Path, default=common.DEFAULT_SFT, help="sft.jsonl")
    parser.add_argument("--condition", choices=("all", "visible", "tools"), default="all")
    parser.add_argument("--max-length", type=int, default=4096, help="tokens; los ejemplos mas largos se descartan")
    return parser.parse_args(argv)


def build_examples(args: argparse.Namespace, tokenizer) -> tuple[list[dict], dict]:
    rows = prep.load_jsonl(args.data)
    rows = prep.keep_conditions(prep.keep_difficulties(rows, args.difficulties), args.condition)
    if args.limit:
        rows = rows[: args.limit]
    examples, dropped = [], 0
    for row in rows:
        for conversation in prep.conversation_examples(row["messages"]):
            example = prep.tokenize_example(tokenizer, conversation, args.max_length)
            if example is None:
                dropped += 1
            else:
                examples.append(example)
    if not examples:
        raise SystemExit("No quedaron ejemplos. Revisa --data, --condition y --difficulties.")
    stats = {
        "filas": len(rows),
        "ejemplos": len(examples),
        "descartados_por_largo": dropped,
        "tokens_totales": sum(len(e["input_ids"]) for e in examples),
        "tokens_aprendidos": sum(sum(1 for label in e["labels"] if label != -100) for e in examples),
    }
    return examples, stats


def make_collator(pad_id: int):
    import torch

    def collate(batch: list[dict]) -> dict:
        width = max(len(item["input_ids"]) for item in batch)
        ids = [item["input_ids"] + [pad_id] * (width - len(item["input_ids"])) for item in batch]
        mask = [item["attention_mask"] + [0] * (width - len(item["attention_mask"])) for item in batch]
        labels = [item["labels"] + [-100] * (width - len(item["labels"])) for item in batch]
        return {
            "input_ids": torch.tensor(ids),
            "attention_mask": torch.tensor(mask),
            "labels": torch.tensor(labels),
        }

    return collate


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    from peft import get_peft_model
    from transformers import Trainer, TrainingArguments, set_seed

    set_seed(args.seed)
    random.seed(args.seed)
    tokenizer = common.load_tokenizer(args.model)
    examples, stats = build_examples(args, tokenizer)
    print(f"SFT: {stats}", flush=True)

    model = common.load_model(args.model)
    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()
    model = get_peft_model(model, common.lora_config(args))
    model.print_trainable_parameters()

    # transformers 5 quito `warmup_ratio`: `warmup_steps` menor que 1 se lee como proporcion.
    fields = {field.name for field in dataclasses.fields(TrainingArguments)}
    warmup = {"warmup_ratio": 0.05} if "warmup_ratio" in fields else {"warmup_steps": 0.05}
    arguments = TrainingArguments(
        output_dir=str(args.out / "trainer"),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        lr_scheduler_type="cosine",
        **warmup,
        logging_steps=args.logging_steps,
        save_strategy="steps" if args.save_steps else "no",
        save_steps=args.save_steps or 500,
        seed=args.seed,
        report_to="none",
        remove_unused_columns=False,
        **common.precision_flags(),
    )
    trainer = Trainer(model=model, args=arguments, train_dataset=examples, data_collator=make_collator(tokenizer.pad_token_id))
    trainer.train()

    args.out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(args.out / "adapter"))
    tokenizer.save_pretrained(str(args.out / "adapter"))
    common.save_log_history(args.out, trainer.state.log_history)
    common.write_manifest(args.out, "sft", args, {
        "datos": {"archivo": str(args.data), "sha256": common.file_sha256(args.data), **stats},
        "pasos": trainer.state.global_step,
    })
    print(f"Adaptador guardado en {args.out / 'adapter'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
