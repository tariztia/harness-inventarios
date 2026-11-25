# Guía de entrenamiento: SFT, DPO y GRPO con LoRA

Los scripts de `scripts/train_*.py` entrenan a Qwen3-1.7B sobre el harness y `run_pilot.py --adapter` mide el resultado con el mismo protocolo de la línea base. Todo se probó de punta a punta **en CPU con Qwen3-0.6B** (unos pasos de cada uno, más una evaluación de un adaptador). **No se ha corrido todavía en una GPU**: los tiempos y la memoria con el modelo de 1.7B hay que medirlos el primer día (sección 3).

## 1. Qué hay y para qué sirve cada cosa

| Script | Camino del proyecto | Entrada | Salida |
|---|---|---|---|
| `make_train_prompts.py` | (prepara GRPO) | el generador del harness | `data/train_extra.jsonl`: 360 instancias nuevas de `train` |
| `train_sft.py` | 2 (solo SFT) y primera parte del 3 | `sft.jsonl`, 4.664 trazas (4.655 del Qwen3-8B) | adaptador LoRA |
| `train_dpo.py` | 5 (DPO) | `dpo.jsonl`, 635 pares (529 con rechazada del Qwen3-1.7B) | adaptador LoRA |
| `train_grpo.py` | 4 (solo RL) y segunda parte del 3 | prompts `visible` y `reward()` del harness | adaptador, curvas de recompensa y respuestas |
| `run_pilot.py --stage eval_final --adapter ...` | mide cualquiera de los anteriores | el modelo base más el adaptador | rollouts y pass@k en `eval` |
| `plot_training.py` | (curvas) | `train_log.json` | PNG y CSV |

**LoRA** congela el modelo y entrena matrices pequeñas encima (rango 16, sobre todas las capas lineales; unos 10 millones de parámetros en el 0.6B). El resultado es un adaptador de decenas de MB. El modelo base no cambia, así que "base" y "entrenado" se comparan desde el mismo punto.

## 2. Preparar el entorno

```bash
git clone https://github.com/tariztia/harness-inventarios.git && cd harness-inventarios
git switch entrenamiento            # o main, si la rama ya se fusionó
pip install -r requirements-train.txt
python -m pytest -q tests/test_training_prep.py     # 25 pruebas, sin GPU
python scripts/make_train_prompts.py --n-per-cell 40 --out data/train_extra.jsonl
```

El `pytest` completo, en Windows y con un pytest reciente, puede dar unos 47 errores de "environment variable is longer than 32767 characters". Vienen de nombres de prueba larguísimos en `test_verifier.py` y `test_reward.py`, no de los scripts de entrenamiento, y en Linux no aparecen.

El modelo (`Qwen/Qwen3-1.7B`, 3.4 GB) se descarga solo la primera vez. Los datos de SFT y DPO ya están en el repo: por omisión se usa el conjunto combinado (`results/datos_combinados/`). Los conjuntos anteriores siguen disponibles con `--data` (ver la sección "Datos derivados" del README).

## 3. Primera hora en el cluster: medir antes de lanzar

Cada script acepta `--max-steps` y `--limit` para probar en minutos. Antes de las corridas largas, haz una de tres pasos de cada una y anota segundos por paso y memoria (`nvidia-smi`):

```bash
python scripts/train_sft.py  --out runs/humo_sft  --max-steps 3
python scripts/train_dpo.py  --out runs/humo_dpo  --max-steps 3
python scripts/train_grpo.py --out runs/humo_grpo --max-steps 3
```

Con eso se fija el presupuesto comparable (horas de GPU o número de respuestas generadas) y se decide el tamaño del lote. Si falta memoria: baja `--batch-size` y sube `--grad-accum` (el producto es lo que importa), o agrega `--gradient-checkpointing`.

## 4. Los cinco caminos

```bash
# 1. Modelo base: ya medido (results/kaggle_qwen17b/linea_base_qwen17b).

# 2. Solo SFT
python scripts/train_sft.py --out runs/sft

# 3. SFT y luego RL: GRPO partiendo del adaptador del SFT
python scripts/train_grpo.py --out runs/sft_grpo --init-adapter runs/sft/adapter

# 4. Solo RL: GRPO desde el modelo base
python scripts/train_grpo.py --out runs/grpo

# 5. DPO
python scripts/train_dpo.py --out runs/dpo
```

Para comparar con **presupuesto comparable**, los dos GRPO (3 y 4) deben tener los mismos `--max-steps`, `--num-generations` y `--batch-size`.

**Niveles no vistos.** Para medir hard sin haberlo visto, entrena cada camino con `--difficulties easy medium` y evalúa en los tres niveles. Funciona igual en los tres scripts.

**Qué hace cada uno de los argumentos importantes**

| Argumento | Scripts | Efecto | Valor inicial |
|---|---|---|---|
| `--learning-rate` | todos | velocidad de aprendizaje | SFT 2e-4, DPO 2e-5, GRPO 1e-5 |
| `--epochs` | todos | vueltas sobre los datos | SFT y DPO 3, GRPO 1 |
| `--num-generations` | GRPO | respuestas por prompt (tamaño del grupo) | 8 |
| `--max-completion-length` | GRPO | tokens por respuesta; una respuesta cortada recibe 0 | 3072 |
| `--beta` | DPO y GRPO | fuerza de la restricción al modelo de referencia (KL) | DPO 0.1, GRPO 0.0 |
| `--condition` | SFT y DPO | `visible`, `tools` o `all` | all |
| `--lora-r` | todos | tamaño del adaptador | 16 |

Todos son valores de partida razonables, **no valores ajustados**. Se corrigen tras las primeras curvas. Son los candidatos para el estudio de sensibilidad (tamaño de grupo, KL, forma de la recompensa).

**Límites que conviene tener presentes**

- **GRPO solo en `visible`.** El trainer de TRL genera un mensaje por prompt y `tools` necesita varias rondas con la herramienta en medio. Por eso el RL se entrena en `visible` y se evalúa también en `tools`.
- **SFT por ronda.** Cada mensaje del asistente es un ejemplo aparte con la perdida solo en ese mensaje. Así el modelo aprende exactamente lo que verá al generar: la plantilla de Qwen3 borra el `<think>` de los mensajes anteriores, y entrenar la conversación entera enseñaría una primera ronda sin razonamiento.
- **DPO con herramientas.** En los pares `tools` la perdida cubre también el mensaje con los resultados de la herramienta. Con `--condition visible` el problema no existe, pero quedan 262 de los 635 pares del conjunto combinado.
- **Generación lenta.** GRPO genera con `transformers`, sin vLLM, a menos que se instale y se pase `--use-vllm` (no probado). Es lo que más va a pesar en el tiempo.

## 5. Medir un modelo entrenado

Con el mismo protocolo de la línea base: 90 instancias de `eval`, 5 muestras, mismas semillas y muestreo. El conjunto es idéntico al de la línea base (hay un test que compara su huella).

```bash
python scripts/run_pilot.py --stage eval_final --models Qwen/Qwen3-1.7B --thinking on \
    --adapter runs/sft/adapter --adapter-name sft --out results/entrenados/sft --batch-size 32
python scripts/analyze_results.py results/entrenados/sft
```

Para una medición rápida durante el entrenamiento, `--n-samples 1` (solo pass@1) cuesta una quinta parte. Los rollouts del adaptador quedan en un archivo con su propia etiqueta (`...+think+lora:sft`), así que varias corridas pueden convivir en una carpeta. Si el verificador cambia, `scripts/reevaluate.py` vuelve a calificar lo guardado sin correr los modelos otra vez.

## 6. Curvas y auditoría

```bash
python scripts/plot_training.py runs/grpo runs/sft_grpo --out runs/curvas_recompensa.png
python scripts/plot_training.py runs/sft runs/dpo --metric loss --out runs/curvas_perdida.png
```

`train_log.json` guarda por paso la recompensa media (`reward`), su desviación (`reward_std`), el largo medio de las respuestas (`completions/mean_length`), la fracción cortada por el tope (`completions/clipped_ratio`) y la fracción de grupos sin variación (`frac_reward_zero_std`). Esta última es la medida directa de "falta de señal": si es cercana a 1, el grupo no enseña nada.

**Reward hacking.** GRPO deja en cada carpeta:

- `reward_errors.jsonl`: tipos de error acumulados de la recompensa en cada paso. Un cambio brusco en la mezcla (por ejemplo, que `wrong_value` caiga y `ok` suba mientras el largo se desploma) merece una revisión.
- `completions.jsonl`: 1 de cada 4 respuestas, con su recompensa y su tipo de error. Es la fuente de la **auditoría manual de trazas exitosas**: se toman unas 50 con `reward: 1.0` y se revisa si los datos son los correctos y si el razonamiento es coherente.

Señales a vigilar (ver la sección 4.5 de la propuesta): respuestas casi idénticas entre prompts distintos, `visible` con acierto parejo cercano al 50 % en disponibilidad (el atajo "siempre alcanza"), largo de respuesta que se desploma, y razonamiento que contradice al bloque.

## 7. Orden sugerido para el lunes

1. Instalar y correr las pruebas, generar `data/train_extra.jsonl` (sección 2).
2. Una corrida de tres pasos de cada script y anotar tiempos y memoria (sección 3).
3. **GRPO primero**, desde el modelo base en `visible` y con `--max-minutes` para acotarlo: de ahí salen las curvas de recompensa, que es lo que pide la Entrega 2 (el SFT y el DPO solo dan curvas de pérdida).
4. SFT completo (el más barato) y medirlo en `eval` (`--n-samples 1` primero), en paralelo si hay otra GPU libre.
5. Con esos tiempos, fijar el presupuesto y lanzar el resto.

Los pasos 1 a 4 alcanzan para lo que pide la Entrega 2: implementación inicial, línea base y curvas de los primeros entrenamientos.

## 8. Sin Peteroa: la curva de recompensa en Kaggle

`notebooks/grpo_curva_kaggle.ipynb` entrena GRPO en las dos T4 de Kaggle, una semilla por GPU, y deja `curva_recompensa.png`, `curva_senal.png` y `resultados_grpo.zip`. Es un respaldo para tener curvas sin esperar al cluster.

1. **Zip del código.** Desde la carpeta del repo, en la rama `entrega-2`: `python scripts/package_for_colab.py --out codigo_grpo_kaggle.zip`. No hacen falta los datos: los prompts de entrenamiento se generan dentro del notebook.
2. **Dataset en Kaggle.** *Create > New Dataset*, sube ese zip y agrégalo como entrada del notebook.
3. **Notebook.** *Create > New Notebook > File > Import Notebook*: `notebooks/grpo_curva_kaggle.ipynb`. *Add Input*: el dataset. *Settings*: **GPU T4 x2** e **Internet On**.
4. *Save Version > Save & Run All (Commit)*, y cierra la página. Con `MINUTOS = 150` (el valor por omisión) la corrida dura unas 3 horas, que salen de la cuota semanal de 30.
5. En *Output* están `curva_recompensa.png`, `curva_senal.png` y `resultados_grpo.zip`.

**Cómo leer la curva.** `reward` es el promedio de las respuestas de cada paso. `frac_reward_zero_std` es la fracción de grupos en que todas las respuestas tienen la misma recompensa: si es cercana a 1, GRPO no tiene de dónde aprender. Con pocos pasos y pocos prompts por paso, la recompensa puede subir poco o con ruido; para la Entrega 2 importa si hay señal.

**Precauciones.** `LARGO = 2048` puede cortar respuestas con thinking. La línea base en `eval` usó 4.096 tokens, y las curvas miden recompensa durante `train`. La T4 no tiene bf16, por lo que entrena en fp16. Si falta memoria, baja `POR_GPU` a 1. Una prueba con `MODELO = "Qwen/Qwen3-0.6B"` permite comprobar si el problema es el tamaño del modelo.

## 9. Evaluar los adaptadores del piloto en Kaggle

El [informe de la corrida](../results/grpo_kaggle/README.md) enlaza el ZIP original de Kaggle con los dos adaptadores. En el [notebook de evaluación](../notebooks/evaluar_grpo_kaggle.ipynb), agrega ese ZIP y el del código como entradas. Con `MUESTRAS = 1` mide pass@1 sobre las 90 instancias visibles de la línea base. Con `MUESTRAS = 5` mide también pass@5. El notebook vuelve a evaluar el modelo base en el mismo entorno para comparar los tres resultados.
