# Estado del proyecto para la Entrega 2

Corte: sábado 21 de noviembre de 2026. Entrega 2: miércoles 25 de noviembre. Entrega final (paper y poster): miércoles 9 de diciembre.

La Entrega 2 pide una implementación inicial del trabajo propuesto, la línea base del modelo antes de entrenar y las curvas de recompensa de los primeros entrenamientos.

**Actualización del 23 de noviembre.** El piloto de GRPO en Kaggle terminó con dos semillas (42 y 45 pasos). Ya están disponibles las curvas y los adaptadores LoRA. Queda medir ambos adaptadores en `eval` para estimar la mejora del modelo. [Resultados y cómo continuar](../results/grpo_kaggle/README.md)

**Actualización del 24 de noviembre.** Los adaptadores se midieron en `eval` (condición `visible`, 1 muestra, mismas 90 instancias): pass@1 de 53/90 en el base reevaluado a 69/90 (semilla 2026) y 67/90 (semilla 2027); hard, no entrenado, de 10/30 a 16/30. Falta pass@5. Resultados en `results/grpo_kaggle/eval_pass1`; borrador del informe en [informe_avance_E2.docx](informe_avance_E2.docx).

**Actualización del 25 de noviembre: SFT seguido de GRPO (camino 3).** Corrió en Peteroa (trabajo 11453): 45 pasos de GRPO desde el adaptador del SFT, con la configuración del piloto GRPO. En `eval`, con 5 muestras: pass@1 de 75/90 y pass@5 de 81/90, sin diferencia con el SFT (76/90 y 81/90; gana 3 y pierde 4). En el entrenamiento, la recompensa queda plana en torno a 0,96 y el 82 % de los grupos no tiene señal: el SFT ya resuelve casi todo easy y medium. Detalle en [results/sft_grpo_peteroa/README.md](../results/sft_grpo_peteroa/README.md).

**Actualización del 25 de noviembre: SFT (camino 2).** Corrió en Peteroa (trabajo SLURM 11447, una H100): 1.666 trazas `visible` easy y medium del conjunto combinado, 3 épocas, 13 minutos. En `eval`, con 5 muestras y el base medido en el mismo trabajo: pass@1 de 64/90 a 76/90 (McNemar p = 0,012) y pass@5 de 80/90 a 81/90; hard, no entrenado, de 13/30 a 17/30 en pass@1. Curva, adaptador y detalle en [results/sft_peteroa/README.md](../results/sft_peteroa/README.md), que también anota lo necesario para usar Peteroa (cuota del `/home`, `--comment` y `--qos=regular`). Siguiente: GRPO desde este adaptador (camino 3).

**Actualización del 25 de noviembre: DPO (camino 5).** Corrió en Kaggle con `notebooks/dpo_kaggle.ipynb` (rama `dpo-kaggle`, PR #4): dos semillas (2026 y 2027), una por T4, unos 80 minutos en total. Pendiente: medir los adaptadores en `eval`.
- **Datos:** pares `visible` del conjunto combinado (`results/datos_combinados/dpo.jsonl`, commit `7dd2db8`): 262 pares, de los que se descartaron 32 que superaban 4.096 tokens (`--drop-longer`, en vez de truncarlos). Quedaron 230. La elegida es del Qwen3-8B y la rechazada, casi siempre del Qwen3-1.7B.
- **Dificultades: se entrenó con los tres niveles, hard incluido.** De los 262 pares, 127 son hard, 95 medium y 40 easy. GRPO, en cambio, entrenó solo con easy y medium. Consecuencias: en DPO, hard **no** es un nivel no visto, y la comparación DPO contra GRPO en hard no mide generalización. Hay que declararlo en la sección de métodos.
- **Configuración:** 3 épocas, 16 pares por paso (`--batch-size 1 --grad-accum 16`), β = 0,1, tasa 2e-5, LoRA r = 16, `--gradient-checkpointing`, tope de 150 minutos (no se alcanzó). Unos 45 pasos por semilla, a unos 1,7 minutos por paso.
- **Curvas** (semilla 2027, primer tercio frente al último): pérdida de 0,339 a 0,022, exactitud de preferencia de 0,66 a 0,99 y margen de 4,3 a 9,4. Los registros y las curvas de las dos semillas están en `resultados_dpo.zip`, en el Output de la versión de Kaggle.
- **Cuidado al interpretar:** la exactitud pasó de 0,9 antes de completar la primera época. Como la elegida es del 8B y la rechazada del 1.7B, el modelo podría estar separando los pares por el estilo de cada modelo y no por la corrección. Además, 3 épocas sobre 230 pares invitan a memorizar, y solo se guardó el adaptador final. Lo que decide es el pass@1 en `eval`. Conviene revisar también `logps/chosen` en `log.jsonl`: si cae mucho, el modelo se alejó incluso de las respuestas correctas.
- **Evaluación:** `notebooks/evaluar_grpo_kaggle.ipynb` con `METODO = "dpo"`, `resultados_dpo.zip` y el zip del código como entrada, y `EVALUAR_BASE = False`. Se compara contra el base reevaluado con el mismo cuaderno (53/90). Con `MUESTRAS = 1` tarda unos 35 minutos (unos 17 s por respuesta, 90 respuestas por adaptador, un adaptador por GPU); con `MUESTRAS = 5`, unas 2,5 horas.
- **Si no mejora sobre el base, para la Entrega 3:** 1 época o β entre 0,3 y 0,5, guardar el adaptador por época (`--save-steps`) y entrenar sin hard (`--difficulties easy medium`, unos 135 pares) para comparar con GRPO bajo el mismo protocolo.

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
