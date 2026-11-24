# Análisis crítico del verificador (documento de trabajo)

Complementa `docs/revision_informe.md`. No es parte de la entrega: sirve para decidir qué afirmar en el informe y qué no.

## 1. Qué archivos forman el verificador

| Archivo | Líneas | Rol |
|---|---|---|
| `reward.py` | ~230 | `reward(prompt, completion)`: busca la instancia por sha256, re-ejecuta las llamadas, revisa evidencia y rondas |
| `tools.py` | ~230 | Herramienta `get_inventory` y lectura de llamadas (con y sin etiqueta) |
| `verifier.py` | ~570 | Texto final: `<think>`, bloque `<answer>`, pares clave-valor, comparación, contradicciones |
| `numbers_es.py` | ~640 | Interpreta **un valor**: enteros en español, aritmética, grupos, sumas, booleanos, sucursal |
| `solver.py` | ~95 | No verifica: calcula `expected` al generar la instancia |

Son unas 1.700 líneas en total. De ellas, la comparación propiamente tal son unas 30 (`_wrong_fields`). El resto es **interpretar** lo que escribió el modelo y **defenderse** de trampas.

## 2. Cómo lo hacen otros (mirado en código o en el paper)

| Trabajo | Cómo verifica | Comparación con lo nuestro |
|---|---|---|
| **Reasoning Gym** (Stojanovski et al., NeurIPS 2025). Repo `open-thought/reasoning-gym`, revisado en código | Cada tarea define `score_answer(answer, entry)` en Python, sin LLM. Por defecto es igualdad exacta de strings y da **crédito parcial** `len(oráculo)/len(respuesta)` si el oráculo aparece dentro de la respuesta. `extract_answer` toma el **último** `<answer>`, aunque haya varios. Hay una cascada opcional más permisiva (`score_answer_cascade`: string, float, `math-verify`) que solo puede subir el puntaje | Mismo enfoque: generación procedural y verificación en código. El nuestro es **más estricto**: 0/1 sin crédito parcial, exactamente un bloque y rechazo de lo ambiguo. También es **más permisivo** en formas de escribir los números (español, aritmética), porque el enunciado lo pide |
| **Tülu 3 / RLVR** (Lambert et al., 2024, arXiv 2411.15124) | Define RLVR: la recompensa solo se da si la respuesta se verifica como correcta, con chequeos en código (GSM8K, MATH, restricciones de IFEval) | Es el marco en que cae nuestro trabajo |
| **DeepSeek-R1** (DeepSeek-AI, 2025, arXiv 2501.12948) | Recompensas por reglas (exactitud y formato). Evitan explícitamente los reward models neuronales por riesgo de reward hacking | Respalda no usar un LLM juez |
| **Pitfalls of Rule- and Model-based Verifiers** (Huang et al., 2025, arXiv 2505.22203) | Los verificadores por reglas tienen **falsos negativos** (rechazan formas equivalentes), y eso perjudica más a medida que el modelo mejora. Los basados en modelos aciertan más en estático, pero **se hackean** durante RL e inflan la recompensa. Proponen híbridos | Es el trade-off exacto de nuestro diseño. Hay que citarlo |
| **One Token to Fool LLM-as-a-Judge** (Zhao et al., 2025, arXiv 2507.08794) | Respuestas triviales ("master keys", como un signo de puntuación o "Solution") logran hasta 80 % de falsos positivos en jueces como GPT-4o o Qwen2.5-72B | Argumento concreto contra un LLM juez como recompensa |
| **AgentGym** (Xi et al., 2025), citado en el enunciado | En entornos con herramientas, la recompensa sale del estado del entorno | Nuestra re-ejecución de llamadas y revisión de evidencia va en esa línea |

Conclusión: **verificar en código es la práctica estándar** para tareas con respuesta calculable, y un LLM juez se reserva para respuestas abiertas, donde además se sabe que es hackeable. Nuestra elección es defendible y citable. Lo que no es estándar es **cuánto** código tiene la interpretación de valores.

## 3. Hallazgo con datos: la mayoría de las equivalencias no se usan

Medido sobre las **1.918 respuestas correctas** de todas las corridas de Kaggle (todos los modelos, `visible` y `tools`):

| Forma | Respuestas |
|---|---|
| Valores con números en palabras (`tres`), grupos (`4 filas de 10`) o sumas etiquetadas | **0** |
| Valores con aritmética (`2+6`) | 1 |
| Valores con un punto final (`16.`) | 1 |
| Bloque completo en una sola línea (pares pegados o con comas) | 79 |

Lectura crítica:

- Casi todo `numbers_es.py` (español, grupos, sumas, glosas) responde al ejemplo de las sillas del enunciado, **no a algo que los modelos hayan hecho**. Los modelos escriben dígitos.
- Lo que sí importó en la práctica fue la **forma del bloque**: pares pegados, comas, una línea. Eso se descubrió con la auditoría, no se previó.
- Hay argumentos para mantener las equivalencias: el enunciado las pide explícitamente, y durante RL la política puede derivar hacia formas raras (Huang et al.: los falsos negativos pesan más a medida que el modelo mejora). Pero **cada regla permisiva es superficie de ataque**: `20 gatos y 20 perros` vale 40.
- En el informe no conviene vender las equivalencias como evidencia de robustez frente a modelos reales. Lo honesto es decir que se implementaron porque el enunciado las pide y para anticipar la deriva en RL, pero que en la línea base casi no se usaron.

## 4. Qué se puede afirmar y qué no

| Afirmación | ¿Se sostiene? | Cómo decirlo |
|---|---|---|
| "El verificador es robusto" | Solo frente a trampas **previstas** | "Resiste 326 de 334 casos adversariales que escribimos nosotros". Lo escribió el mismo equipo que hizo el verificador, así que mide lo que imaginamos. El reward hacking real aparece bajo presión de optimización (Huang et al.), y eso solo se verá al entrenar con RL en el proyecto |
| "No hay falsos positivos" | En la auditoría: 0 de 119 aceptadas | Muestra chica, de dos corridas exploratorias. Para la línea base completa (1.918 aceptadas) no hubo una revisión manual equivalente |
| "Acepta respuestas equivalentes" | Sí en tests; casi no se ejerció con modelos reales | Ver sección 3 |
| "La revisión de contradicciones protege la recompensa" | No. Es un extra conservador, solo en español, y solo cubre disponibilidad y selección | Presentarla como opcional; 7 de 8 fallos adversariales están ahí |
| "El verificador se mejoró con evidencia" | Sí: auditoría → pares en una línea → corrección → reevaluación | Es el mejor ejemplo del ciclo del enunciado. Decir también que es una relajación hecha después de ver resultados |

## 5. Limitaciones que deberían ir en §8 y trabajo futuro

- Verificación binaria: composición hard da recompensa 0 casi siempre. Una **recompensa parcial por campo** (fracción de campos correctos) daría señal ahí. El PDF del proyecto la lista como mejora incremental posible ("recompensas parciales"), así que puede ser una línea del proyecto. Riesgo: premiar campos fáciles (`total_pendientes: 0`).
- Interpretación por reglas a mano: extender a un tipo nuevo (fechas, texto) exige escribir otro parser. Un híbrido, con reglas primero y un juez solo para los rechazos de formato, es la alternativa de la literatura, pero agrega costo y riesgo de hacking.
- Auditoría manual pequeña. El proyecto pide auditar una muestra de trazas "exitosas" al estilo SWE-Bench+; conviene hacerlo sobre la línea base completa.

## 5b. Código revisable de otros verificadores (revisado el 13 de noviembre)

| Proyecto | Dónde | Qué hace |
|---|---|---|
| Tülu 3 / OLMo (`allenai/open-instruct`) | `open_instruct/ground_truth_utils.py` | `GSM8KVerifier`: toma el **último número** del texto y lo compara con la etiqueta (0/1). Es mucho más laxo que el nuestro, que nunca "extrae un número" del texto. `MathVerifier` y `StrictMathVerifier` hacen equivalencia matemática. `IFEvalVerifier` revisa restricciones en código. **El mismo archivo también trae `LMJudgeVerifier`**, un juez LLM, para dominios sin respuesta calculable. En la práctica conviven: reglas donde se puede, juez donde no |
| Open-R1 (`huggingface/open-r1`), la reproducción abierta de DeepSeek-R1 | `src/open_r1/rewards.py` | `accuracy_reward`: usa `math-verify` (parser de LaTeX y equivalencia simbólica), recompensa binaria; si la respuesta de referencia no se puede parsear, devuelve `None` y el ejemplo se salta. `format_reward` aparte |
| DeepSeek-R1 | Solo el paper (arXiv 2501.12948) | No publicaron el código de entrenamiento. Describen dos recompensas por reglas: exactitud y formato |

## 5c. Decisiones para el proyecto (no para este informe)

- **Aritmética en el valor (`2+6`).** Hoy vale 1. El enunciado del desafío pide aceptar formas equivalentes ("cuatro filas de 10"), y `math-verify` también acepta expresiones equivalentes. Si queremos que el modelo entregue el número final, la práctica habitual es **separar** recompensas: exactitud (1 si el valor es correcto) más un término pequeño de formato (forma canónica). No conviene bajar la exactitud. En la línea base pasó 1 vez en 1.918 aciertos, así que no es urgente.
- **¿Reglas más estrictas?** Candidatas a eliminar, por ser superficie de ataque sin uso real: las sumas etiquetadas (`20 gatos y 20 perros`) y quizás los grupos. Choca con el ejemplo del enunciado, así que habría que justificarlo.
- **Recompensa parcial por campo** para composición hard (ver sección 5).

## 5d. Sobre `docs/auditoria_verificador.md`

Está bien hecha y es honesta:
- Valida `expected` con un solucionador escrito aparte.
- Clasifica cada rechazo (a, b, b\*, c) leyendo textos a mano.
- Prueba cada cambio propuesto contra los rollouts y contra los casos adversariales antes de recomendarlo.

Límites para decirlo en el informe:
- Se hizo sobre las **corridas exploratorias** (45 instancias de `train`, prompt original y corregido), no sobre la línea base final. En esas corridas la condición `tools` tenía el parser roto, así que casi todo el material es `visible`.
- Las 119 aceptadas son pocas.
- Ella misma anota que **la revisión de contradicciones no se activó en ninguno de los 1.080 rollouts**: con thinking es un no-op. Refuerza C3 de `revision_informe.md`.
- También anota aciertos por azar (`sí/0` en disponibilidad): conviene vigilarlos en RL.
- Es la base natural de la auditoría manual que pide el proyecto (estilo SWE-Bench+), extendida a la línea base completa.

## 6. Falta en el informe: referencias

`docs/informe.md` **no cita ningún trabajo**. Ni siquiera las cuatro referencias del enunciado (BIG-bench, MATH, Reasoning Gym y AgentGym). Para un "desafío de investigación" es la omisión más visible. Mínimo propuesto: una sección corta de trabajo relacionado y referencias con Reasoning Gym, AgentGym, Tülu 3 (RLVR), DeepSeek-R1, Huang et al. 2025 y Zhao et al. 2025, citados donde se justifica cada decisión.
