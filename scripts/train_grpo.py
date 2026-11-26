"""GRPO con LoRA, con la recompensa del harness (caminos 3 y 4 del proyecto).

Uso (humo, sin GPU):
    python scripts/train_grpo.py --out runs/grpo_humo --limit 4 --max-steps 1 \\
        --num-generations 2 --batch-size 2 --max-completion-length 32
Solo RL, desde el modelo base (camino 4):
    python scripts/train_grpo.py --out runs/grpo
SFT y luego RL (camino 3), partiendo del adaptador del SFT:
    python scripts/train_grpo.py --out runs/sft_grpo --init-adapter runs/sft/adapter
Entrenar sin hard, para medirlo como nivel no visto:
    python scripts/train_grpo.py --out runs/grpo_easy_medium --difficulties easy medium

Solo la condicion `visible`: el GRPOTrainer genera un mensaje por prompt, y `tools` pide
varias rondas con la herramienta ejecutandose entre ellas.

Los prompts salen de `scripts/make_train_prompts.py`: instancias nuevas de `train`, sin repetir
ninguna de eval ni de test. Si --train-file no existe, se generan al vuelo con la misma semilla.

Salida en --out: `adapter/`, `train_log.json` (recompensa, largo y perdida por paso),
`log.jsonl` (lo mismo, pero se escribe paso a paso: sirve si la corrida se corta),
`reward_errors.jsonl` (tipos de error acumulados), `completions.jsonl` (respuestas con su
recompensa, para auditar trazas exitosas y buscar reward hacking) y `manifest.json`.

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
from inventory_harness.reward import InstanceStore  # noqa: E402

DEFAULT_TRAIN_FILE = common.ROOT / "data" / "train_extra.jsonl"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common.add_common_args(parser, lr=1e-5, epochs=1)
    parser.set_defaults(batch_size=8, grad_accum=4)
    parser.add_argument("--train-file", type=Path, default=DEFAULT_TRAIN_FILE,
                        help="instancias de entrenamiento (make_train_prompts.py); se generan si no existe")
    parser.add_argument("--n-per-cell", type=int, default=40, help="solo al generar el archivo")
    parser.add_argument("--include-pilot-train", action="store_true",
                        help="agrega tambien las 90 instancias de train del piloto (las de las trazas SFT)")
    parser.add_argument("--init-adapter", type=Path, help="adaptador LoRA de partida, por ejemplo el del SFT")
    parser.add_argument("--num-generations", type=int, default=8, help="respuestas por prompt (tamano del grupo)")
    parser.add_argument("--max-completion-length", type=int, default=3072, help="tokens por respuesta, razonamiento incluido")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--beta", type=float, default=0.0, help="coeficiente de la penalizacion KL")
    parser.add_argument("--loss-type", default="dapo",
                        help="perdida de TRL (grpo, dapo, dr_grpo, bnpo...). Se fija explicito: el valor por omision "
                             "de TRL cambio entre versiones. 'dapo' es lo que uso el piloto de Kaggle")
    parser.add_argument("--use-vllm", action="store_true", help="generar con vLLM (debe estar instalado)")
    parser.add_argument("--trace-every", type=int, default=4, help="guarda 1 de cada N respuestas en completions.jsonl")
    parser.add_argument("--max-minutes", type=float,
                        help="detiene el entrenamiento tras N minutos de entrenar (sin contar la carga del modelo) y guarda lo hecho")
    return parser.parse_args(argv)


def load_instances(args: argparse.Namespace) -> list:
    if args.train_file.exists():
        instances = prep.read_instances(args.train_file)
    else:
        print(f"{args.train_file} no existe: se generan {args.n_per_cell} por celda.", flush=True)
        instances = prep.extra_train_instances(args.n_per_cell)
        prep.write_instances(args.train_file, instances)
    if args.include_pilot_train:
        import run_pilot

        instances = instances + run_pilot.build_dataset("train", 10, 2026)
    return instances


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sys.path.insert(0, str(common.ROOT / "scripts"))
    from datasets import Dataset
    from transformers import TrainerCallback, set_seed
    from trl import GRPOConfig, GRPOTrainer

    set_seed(args.seed)
    instances = load_instances(args)
    rows = prep.grpo_rows(instances, args.difficulties)
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("No quedaron prompts. Revisa --train-file y --difficulties.")
    store = InstanceStore(instances)
    reward = prep.make_grpo_reward(store, trace_path=args.out / "completions.jsonl", trace_every=args.trace_every)
    dataset = Dataset.from_list(rows)
    print(f"GRPO: {len(rows)} prompts, grupo de {args.num_generations}", flush=True)

    tokenizer = common.load_tokenizer(args.model, padding_side="left")
    model = common.load_model(args.model, init_adapter=args.init_adapter)

    config = GRPOConfig(
        output_dir=str(args.out / "trainer"),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        num_generations=args.num_generations,
        max_completion_length=args.max_completion_length,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        beta=args.beta,
        loss_type=args.loss_type,
        use_vllm=args.use_vllm,
        logging_steps=args.logging_steps,
        save_strategy="steps" if args.save_steps else "no",
        save_steps=args.save_steps or 500,
        gradient_checkpointing=args.gradient_checkpointing,
        seed=args.seed,
        report_to="none",
        **common.precision_flags(),
    )

    errors_path = args.out / "reward_errors.jsonl"
    log_path = args.out / "log.jsonl"
    errors_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    stopped_by_time: list[bool] = []

    class StepLog(TrainerCallback):
        """Despues de cada registro, deja las metricas del paso y los tipos de error acumulados."""

        def on_log(self, _args, state, _control, logs=None, **kwargs):
            row = {"paso": state.global_step, "minutos": round((time.time() - started) / 60, 2), **(logs or {})}
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, default=str) + chr(10))
            with errors_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"paso": state.global_step, **reward.summary()}, ensure_ascii=False) + chr(10))

    class TimeLimit(TrainerCallback):
        """Detiene el entrenamiento al cumplirse --max-minutes; el resto del script guarda como siempre."""

        def on_step_end(self, _args, state, control, **kwargs):
            if args.max_minutes and (time.time() - started) / 60 >= args.max_minutes and not stopped_by_time:
                stopped_by_time.append(True)
                control.should_training_stop = True
                print(f"Se cumplieron {args.max_minutes} minutos: se detiene en el paso {state.global_step}.", flush=True)

    trainer = GRPOTrainer(
        model=model,
        reward_funcs=[reward],
        args=config,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=None if args.init_adapter else common.lora_config(args),
        callbacks=[StepLog(), TimeLimit()],
    )
    started = time.time()  # el tiempo cuenta desde aqui, sin la carga del modelo
    trainer.train()

    trainer.model.save_pretrained(str(args.out / "adapter"))
    tokenizer.save_pretrained(str(args.out / "adapter"))
    common.save_log_history(args.out, trainer.state.log_history)
    common.write_manifest(args.out, "grpo", args, {
        "datos": {"prompts": len(rows), "archivo": str(args.train_file), "instancias": len(instances)},
        "recompensa": reward.summary(),
        "pasos": trainer.state.global_step,
        "detenido_por_tiempo": bool(stopped_by_time),
    })
    print(f"Adaptador guardado en {args.out / 'adapter'}", flush=True)
    print(f"Recompensa: {reward.summary()}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
