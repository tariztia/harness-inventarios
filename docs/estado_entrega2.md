# Estado del proyecto para la Entrega 2

Corte: sábado 21 de noviembre de 2026. Entrega 2: miércoles 25 de noviembre. Entrega final (paper y poster): miércoles 9 de diciembre.

La Entrega 2 pide una implementación inicial del trabajo propuesto, la línea base del modelo antes de entrenar y las curvas de recompensa de los primeros entrenamientos.

## Ya hecho

**Del Desafío** (en `main`, informe en `docs/informe.md`):
- Entorno, generador de tareas, verificador y casos adversariales.
- Línea base de cinco modelos sobre `eval`. El modelo objetivo, Qwen3-1.7B con thinking, tiene pass@1 de 64 % con datos visibles y 41 % con herramientas.
- Datos derivados: 170 trazas SFT y 106 pares DPO, todos con respuestas correctas del Qwen3-8B.

**Del Proyecto, esta rama:**
- `docs/propuesta_proyecto.md`: base de la Entrega 1. Cinco caminos de entrenamiento, preguntas de investigación, diseño experimental, reward hacking previsto y 10 referencias verificadas contra arXiv y la ACL Anthology. Está también en `main`.
- Scripts de entrenamiento con LoRA, probados de punta a punta **en CPU con Qwen3-0.6B**:
  - `train_sft.py`, `train_dpo.py` y `train_grpo.py` (con la recompensa del harness, solo en `visible`).
  - `make_train_prompts.py`: 360 instancias nuevas de `train`, sin repetir `eval` ni `test`.
  - `run_pilot.py --stage eval_final --adapter ...`: mide un modelo entrenado sobre las mismas 90 instancias de `eval` que la línea base (un test compara la huella del dataset).
  - `plot_training.py` (curvas) y `audit_sample.py` (hoja CSV para la auditoría manual).
- `docs/guia_entrenamiento.md`: comandos, argumentos, límites y orden para el lunes. `requirements-train.txt`: versiones probadas.
- 25 tests nuevos en `tests/test_training_prep.py`.

## Falta antes del lunes (repartible entre tres)

1. **Más datos del Qwen3-8B.** Las 170 trazas son pocas. Se pueden generar más sobre las instancias de `data/train_extra.jsonl`, repartidas entre las cuentas de Kaggle (2 T4 cada una; el 8B tardó entre 40 y 100 s por respuesta). **Falta la herramienta:** hay que hacer que `run_pilot.py` lea instancias desde un archivo y que `build_training_data.py` las reconozca, y armar el notebook.
2. **Auditoría manual de trazas exitosas**, que pide el enunciado. Ya se puede empezar con las respuestas existentes:
   ```bash
   python scripts/audit_sample.py results/kaggle_qwen17b/linea_base_qwen17b --n 50 --out auditoria_1_7b.csv
   python scripts/audit_sample.py results/kaggle_qwen8b/trazas_qwen8b --n 50 --out auditoria_8b.csv
   ```
   Cada fila indica archivo y línea; se completan las columnas `datos_ok`, `razon_ok`, `genuino` y `comentario`.
3. **Dejar listo el acceso a Peteroa:** clonar el repo, `pip install -r requirements-train.txt`, correr `pytest tests/test_training_prep.py` y generar `data/train_extra.jsonl`.
4. **Entrega 1:** escribirle al profesor o al ayudante para saber si todavía se acepta (la fecha original era el 11 de noviembre; se pierde 1 punto por día). Leer los trabajos citados en la propuesta y confirmar sus referencias.

## Lunes 23 (con Peteroa)

Seguir la sección 7 de `docs/guia_entrenamiento.md`:
1. Una corrida de tres pasos de cada script, para medir segundos por paso y memoria. **Todavía no se sabe cuánto tarda nada en una GPU.**
2. SFT completo y medirlo en `eval` (primero `--n-samples 1`).
3. GRPO corto desde el modelo base, en `visible`, para tener las primeras curvas de recompensa.
4. Con esos tiempos, fijar el presupuesto comparable y lanzar el resto.

## Martes 24 y miércoles 25

- Más corridas: DPO, GRPO desde el SFT (camino 3) y evaluación de cada una.
- Anotar lo que se observe: falta de señal (`frac_reward_zero_std` cercano a 1), explotación del verificador, respuestas cortadas por el tope de tokens.
- Escribir el informe de avance con línea base, implementación y curvas, y entregarlo.

## Del 26 de noviembre al 4 de diciembre

- Los cinco caminos con presupuesto comparable, medidos en `eval` y en `test`.
- Entrenar sin hard (`--difficulties easy medium`) y medir hard como nivel no visto.
- Ablación opcional: filtrar los grupos sin señal (DAPO).
- Ciclo de iteración: revisar las respuestas con recompensa alta, corregir el verificador si se explota, volver a entrenar y **reportar todo con la versión final del verificador** (`scripts/reevaluate.py`).
- Auditoría manual de las trazas exitosas de cada camino.
- Más de una semilla, si alcanza el cómputo.

## Del 5 al 9 de diciembre

Paper de 7 páginas (doble columna, sin contar referencias), poster y video. Secciones pedidas: introducción, revisión bibliográfica, descripción del proyecto con diagrama de bloques, resultados, ciclo de iteración y conclusiones.

## Decisiones abiertas

- **Presupuesto comparable:** en horas de GPU o en número de respuestas generadas. Se fija el lunes, con los tiempos medidos.
- **RL en `tools`:** el GRPO de TRL genera un mensaje por prompt, así que se entrena en `visible`. Extenderlo a varias rondas exige un ciclo de generación propio.
- **Entorno congelado:** no se cambia el prompt ni el verificador hasta tener las primeras corridas. Un prompt nuevo invalida las trazas y la línea base.
- **Composición hard:** casi no da señal. Se excluye del RL inicial o se usa solo al final.

## Riesgos conocidos

- Nada del código de entrenamiento se ha corrido en una GPU. Las versiones de TRL, transformers y PEFT del cluster pueden diferir de las probadas y pedir ajustes pequeños.
- GRPO genera con `transformers`, sin vLLM, y será lo más lento.
- DPO con herramientas entrena también sobre el mensaje con los resultados de la herramienta. Con `--condition visible` no pasa, pero quedan 41 de 106 pares.
- Con 170 trazas de SFT, lo esperable es que mejore sobre todo el formato y no tanto el razonamiento.
- El `pytest` completo en Windows da unos 47 errores por nombres de prueba larguísimos (`test_verifier.py`, `test_reward.py`). No son de lo nuevo y en Linux no aparecen.
