#!/usr/bin/env bash
#SBATCH --job-name=sft-visible-em
#SBATCH --comment="Curso Inteligencia Artificial Generativa (IIC3694), profesor Alvaro Soto: SFT con LoRA de Qwen3-1.7B sobre trazas del Qwen3-8B y evaluacion pass@1/pass@5"
#SBATCH --qos=regular
#SBATCH --partition=peteroa-default
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=1-00:00:00
#SBATCH --output=/workspace1/grupo5-iagenerativa/harness/logs/%x-%j.log
# SFT (visible, easy+medium, datos combinados) y evaluacion pass@1/pass@5 en eval.
set -euo pipefail
W=/workspace1/grupo5-iagenerativa
cd $W/harness
source $W/venv/bin/activate
export HF_HOME=$W/hf_cache TMPDIR=$W/tmp PIP_CACHE_DIR=$W/pip_cache PYTHONIOENCODING=utf-8 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
echo "GPU asignada por SLURM: ${CUDA_VISIBLE_DEVICES:-?}"
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv
SFT="--data results/datos_combinados/sft.jsonl --condition visible --difficulties easy medium --max-length 8192 --batch-size 2 --grad-accum 8 --gradient-checkpointing"
EVAL="--stage eval_final --models Qwen/Qwen3-1.7B --thinking on --conditions visible --max-new-tokens 4096 --batch-size 16 --n-samples 5"
paso() { echo; echo "=== $(date '+%F %T') $1 ==="; }

paso "1/4 Prueba de humo del SFT (3 pasos)"
python scripts/train_sft.py $SFT --max-steps 3 --out runs/humo_sft

paso "2/4 SFT completo"
python scripts/train_sft.py $SFT --out runs/sft_visible_em
python scripts/plot_training.py runs/sft_visible_em --metric loss --out runs/sft_visible_em/curva_perdida.png

paso "3/4 Evaluacion del SFT (5 muestras: pass@1 y pass@5)"
python scripts/run_pilot.py $EVAL --adapter runs/sft_visible_em/adapter --adapter-name sft_visible_em --out results/eval_peteroa/sft_visible_em
python scripts/analyze_results.py results/eval_peteroa/sft_visible_em

paso "4/4 Evaluacion del modelo base (mismo protocolo)"
python scripts/run_pilot.py $EVAL --out results/eval_peteroa/base
python scripts/analyze_results.py results/eval_peteroa/base

paso "LISTO"
