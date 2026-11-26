#!/usr/bin/env bash
#SBATCH --job-name=grpo-desde-sft
#SBATCH --comment="Curso Inteligencia Artificial Generativa (IIC3694), profesor Alvaro Soto: GRPO con LoRA de Qwen3-1.7B partiendo del adaptador SFT y evaluacion pass@1/pass@5"
#SBATCH --qos=regular
#SBATCH --partition=peteroa-default
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=1-00:00:00
#SBATCH --output=/workspace1/grupo5-iagenerativa/harness/logs/%x-%j.log
# Camino 3: GRPO desde el SFT, misma configuracion que el piloto GRPO de Kaggle (camino 4), 45 pasos.
set -euo pipefail
W=/workspace1/grupo5-iagenerativa
cd $W/harness
source $W/venv/bin/activate
export HF_HOME=$W/hf_cache TMPDIR=$W/tmp PIP_CACHE_DIR=$W/pip_cache PYTHONIOENCODING=utf-8 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
echo "GPU asignada por SLURM: ${CUDA_VISIBLE_DEVICES:-?}"
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv
GRPO="--init-adapter runs/sft_visible_em/adapter --train-file data/train_extra.jsonl --difficulties easy medium --seed 2026 --num-generations 8 --batch-size 4 --grad-accum 4 --max-completion-length 2048 --learning-rate 2e-5 --loss-type dapo --beta 0 --gradient-checkpointing --trace-every 4 --logging-steps 1"
EVAL="--stage eval_final --models Qwen/Qwen3-1.7B --thinking on --conditions visible --max-new-tokens 4096 --batch-size 16 --n-samples 5"
paso() { echo; echo "=== $(date '+%F %T') $1 ==="; }

paso "1/3 Prueba de humo del GRPO (2 pasos)"
python scripts/train_grpo.py $GRPO --max-steps 2 --out runs/humo_grpo_sft

paso "2/3 GRPO desde el SFT (45 pasos)"
python scripts/train_grpo.py $GRPO --max-steps 45 --max-minutes 600 --out runs/grpo_desde_sft
python scripts/plot_training.py runs/grpo_desde_sft --metric reward --smooth 3 --out runs/grpo_desde_sft/curva_recompensa.png
python scripts/plot_training.py runs/grpo_desde_sft --metric frac_reward_zero_std --smooth 3 --out runs/grpo_desde_sft/curva_senal.png

paso "3/3 Evaluacion de SFT -> GRPO (5 muestras: pass@1 y pass@5)"
python scripts/run_pilot.py $EVAL --adapter runs/grpo_desde_sft/adapter --adapter-name sft_grpo --out results/eval_peteroa/sft_grpo
python scripts/analyze_results.py results/eval_peteroa/sft_grpo

paso "LISTO"
