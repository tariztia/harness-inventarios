# Auditoría del tool calling: ¿pasamos al formato nativo?

Documento para decidir en equipo antes de generar más trazas de `tools`. No cambia código. Las referencias de archivo y línea son de la rama `entrega-2` en el commit `2c473b6` (ahí están los scripts de entrenamiento). Los datos de TRL salen de su código fuente en el tag `v1.18.2`.

Convención: llamamos **variante A** al formato actual (herramienta descrita en texto), **variante B** a la que probó el equipo con 18 conversaciones (esquema en `tools=`, resultados con rol `tool` y un mensaje `user` con las instrucciones de formato después) y **variante C** al nativo puro (`assistant` con `tool_calls` estructurados, rol `tool`, sin `user` después).

## Resumen

- **Nada está mal hecho.** Evaluación, SFT y GRPO ven el mismo texto en `visible`, y el SFT por mensaje es coherente con cómo el formato actual borra el `<think>` en inferencia.
- **`visible` no cambia en ningún escenario.** Prompt, 86 trazas, 41 pares, línea base y GRPO siguen valiendo. La decisión solo afecta a la condición `tools`.
- **El objetivo del proyecto es razonar y calcular sobre los pedidos, no usar mejor la herramienta.** Por eso los fallos de sintaxis de la herramienta son ruido, y hay un sesgo concreto en la comparación entre caminos (sección 5).
- **Recomendación:** adoptar para `tools` la presentación nativa de la variante B, **sin RL sobre `tools` y sin `environment_factory`**, después de confirmarla con las 72 instancias que faltan. La E2 no depende de esto (sección 7).
- **El repo supone algo que ya no es cierto:** "el GRPOTrainer genera un solo mensaje por prompt". Con `trl==1.18.2` soporta herramientas multi-turno. Es posible, pero no lo necesitamos.

## 1. Cómo se arma hoy el prompt

El harness no usa herramientas nativas:

| Qué | Dónde |
|---|---|
| `apply_chat_template` solo recibe `add_generation_prompt` y `enable_thinking` | `backends.py:228-237` |
| No hay `tools=`, rol `tool` ni `tool_calls` en `src/` ni `scripts/` | búsqueda en todo el árbol |
| La herramienta se describe en texto, con un ejemplo de `<tool_call>` | `prompts.py:54-61` |
| Los resultados vuelven como mensaje `user` con `<tool_result>` | `tools.py:218-221`, `rollout.py:167-169` |
| Las instrucciones de formato llegan junto con los resultados | `prompts.py:116-122` |
| `enable_thinking=True` va explícito; el template solo actúa si vale `false`, así que equivale al default de Qwen3 | `backends.py:230-234` |

## 2. Qué cambia con el template nativo de Qwen3

Se comparó el chat template real de Qwen3-1.7B (viene dentro de `tokenizer_config.json`) renderizando las tres variantes con la misma instancia. El render se hizo con jinja2 imitando cómo transformers aplica el template; es una réplica, no la salida de transformers.

| | Variante A (actual) | Variantes B y C (nativas) |
|---|---|---|
| Bloque `system` | No hay | `# Tools … <tools>{esquema JSON}</tools>` e instrucciones de `<tool_call>` |
| Llamada | Una línea por llamada | `<tool_call>\n{...}\n</tool_call>` |
| Resultado | `<tool_result>…</tool_result>` dentro de un `user` | `<tool_response>\n…\n</tool_response>` dentro de un `user` (mensaje de rol `tool`) |
| `<think>` de la ronda 1 al responder | Se borra | Se borra en B; se conserva en C |

Sobre la última fila: el template borra el `<think>` de los mensajes anteriores a la última consulta del usuario. Un `user` con `<tool_result>` (A) o con las instrucciones de formato (B) cuenta como consulta nueva, así que el razonamiento de la ronda 1 se pierde. Solo en C se conserva.

## 3. Versiones y compatibilidad con TRL

Declaradas en `requirements-train.txt`: transformers 5.24.0, trl 1.18.2, peft 0.22.0, accelerate 1.16.0, datasets 5.2.0. vllm está comentado y unsloth no aparece. La línea base se midió con transformers 5.20.2 (está en los `manifest.json`), y `pyproject.toml` solo pide `transformers>=4.51` para Colab.

| | Qué hace TRL 1.18.2 | Qué hace el repo |
|---|---|---|
| SFTTrainer | Acepta la columna `tools` y mensajes con `tool_calls` y rol `tool` (`sft_trainer.py:1360-1381`). Con `assistant_only_loss` cambia el template de Qwen3 por `qwen3_training.jinja`, que siempre conserva el `<think>` | No lo usa. `Trainer` propio con un ejemplo por mensaje del asistente (`train_sft.py:10-13`, `training_prep.py:81-132`) |
| DPOTrainer | Acepta la columna `tools` (`dpo_trainer.py:1157-1176`) | No la pasa. Los pares `tools` incluyen el `user` con resultados en `chosen` y `rejected` (`training_prep.py:138-144`) |
| GRPOTrainer | Soporta herramientas multi-turno: `tools=[funciones]` y `environment_factory` (experimental), con transformers ≥ 5.0 y ≥ 5.2 (`grpo_trainer.py:687-699`) | Solo `visible`, sin `tools` ni `environment_factory` (`train_grpo.py:129-131`) |

Observaciones:

- El template de Qwen3-1.7B es idéntico, byte a byte, al `qwen3.jinja` que TRL reconoce. TRL ya trae el parser de llamadas de Qwen3 y la versión de entrenamiento.
- El SFT propio se justifica con los formatos A y B: la versión de entrenamiento de TRL conserva el `<think>` de todas las rondas, pero en inferencia con A o B se borra. Con C coinciden.
- **Ajuste independiente del formato:** `train_grpo.py` no fija `loss_type`, y el valor por defecto de TRL 1.18.2 es `"dapo"` (`grpo_config.py:237`, `:809-810`). El "GRPO base" de la propuesta sería en realidad normalización estilo DAPO. Para la ablación hay que fijarlo explícito.

### Qué es `environment_factory` y por qué no lo necesitamos

Es la función de TRL para hacer RL con herramientas. TRL crea un "entorno" por cada intento del modelo (con la herramienta como método y un `reset(**fila)` que recibe las columnas del dataset, `grpo_trainer.py:2541-2545`), ejecuta las llamadas mientras el modelo genera y le devuelve los resultados. Nuestra herramienta lo exigiría porque necesita el inventario de cada instancia.

Además requeriría: resultados como JSON ya serializado (TRL los vuelve `str(result)`, `:2147-2148`), `max_tool_calling_iterations=2` (por defecto no hay tope, `:843-845`), un adaptador de recompensa (hoy `GrpoReward` solo junta el `content` del asistente, `training_prep.py:240-243`, y no vería `tool_calls` estructurados) y formato C. El presupuesto `max_completion_length` parece ser acumulado entre turnos (`:2088`), sin verificar a fondo.

Solo sirve para RL sobre `tools`. Como el objetivo no es entrenar el uso de la herramienta, no lo necesitamos. Además está marcado experimental y sería lo más caro del proyecto.

## 4. Lo que midió la prueba de 18 conversaciones

Resultado reportado: 18 de 18 respuestas con `<tool_call>` (frente a 5 de 18 en la línea base), llamadas válidas 18 de 18, fallos de formato en cero, aciertos de 6/18 a 10/18 (5 ganadas, 1 perdida, p ≈ 0,22).

- La mejora de formato es clara aunque sean pocas conversaciones. La de aciertos no es concluyente.
- Es la variante B, no la C (ver sección 2). El resultado no se puede atribuir a `tools=` en sí: cambian también el texto del prompt, el bloque de sistema y el rol `tool`.
- Tiempo: 3.457 s para 18 conversaciones en una T4 (≈192 s por conversación), unas 3,5 veces más lento por conversación que la línea base (55 s, lote de 16). Causa no diagnosticada.

## 5. Qué queremos medir y por qué importa el formato

El proyecto busca mejorar el razonamiento y el cálculo sobre los pedidos. Entrenar a usar mejor la herramienta no es el objetivo. Eso tiene dos consecuencias:

1. **Los fallos de formato de `tools` son ruido.** En la línea base del objetivo con herramientas, 47 respuestas vienen sin claves y 36 sin bloque, de 450: cerca del 18 % de las respuestas fallan por formato, no por razonar mal.
2. **Ese ruido sesga la comparación entre caminos.** El SFT incluye 84 trazas de `tools` y de paso aprende el formato; el RL en `visible` no. Si el SFT sale mejor en `tools`, no sabríamos si razona mejor o solo escribe mejor el formato. Con la herramienta presentada de forma nativa ese ruido casi desaparece en la prueba de 18 (cero fallos de formato), y la comparación mide razonamiento.

## 6. Razonamiento en el turno 2: lo que muestran los datos

Observación del equipo al leer las 18 conversaciones: en el `<think>` el modelo se enreda con sus propios cálculos, mezclando lo que va escribiendo, lo que obtuvo de la herramienta y la petición. No desconfía de la herramienta.

Se midió con las trazas del profesor (Qwen3-8B) y la línea base del objetivo (Qwen3-1.7B con thinking), en el turno 2 de `tools`, que es donde se razona con los resultados. "Frases de contradicción" cuenta razonamientos con expresiones como "that can't be right" o "doesn't make sense":

| Turno 2 de `tools` | Razonamiento (mediana) | Con frases de contradicción |
|---|---|---|
| Profesor Qwen3-8B (trazas correctas) | 1.471 caracteres | 0 de 84 |
| Objetivo 1.7B, respuestas correctas | 1.254 | 8 de 168 (4,8 %) |
| Objetivo 1.7B, respuestas incorrectas | 2.104 | 31 de 261 (11,9 %) |

En `visible` el objetivo muestra lo mismo: las respuestas incorrectas razonan el doble (4.540 contra 2.210 caracteres de mediana). En los pares DPO, la respuesta elegida no es sistemáticamente más corta que la rechazada (22 de 41 pares en `visible`, 36 de 65 en `tools`), así que DPO no empuja con claridad hacia respuestas más cortas.

Lectura:

- Es justo la tarea que se entrena. **No hace falta RL sobre `tools` para atacarla**: el SFT supervisa el turno donde se razona con los resultados (84 trazas), DPO tiene como rechazadas las del propio 1.7B, y GRPO en `visible` premia los razonamientos que terminan bien, con la misma aritmética.
- Cautelas: la medida es tosca (búsqueda de frases en inglés), y que las incorrectas sean más largas es una correlación: puede que el enredo cause el error o que el error genere más texto.
- Hipótesis sin probar: en el turno 2 el modelo no ve su razonamiento del turno 1 (el template lo borra en A y en B) y tiene que reconstruir el plan. Solo la variante C lo conserva. No es motivo para cambiar ahora, pero la prueba de C la separaría.

Cómo comprobar la mejora después de la E2, en `tools` y entre base, SFT y GRPO: acierto, largo del razonamiento del turno 2, fracción con frases de contradicción y respuestas cortadas por el tope de tokens. Si no mejoran, ahí tendría sentido RL sobre `tools` para la E3.

## 7. Opciones y recomendación

**A. Mantener el formato de texto.**
- No requiere cambios; lo ya probado sigue valiendo.
- Mantiene el sesgo de la sección 5 y el ruido de formato en `tools`.

**B. Presentación nativa de la variante B para `tools`, sin RL sobre `tools`. (Recomendada.)**
- Reduce el ruido de formato y deja la comparación entre caminos más limpia.
- No necesita `environment_factory` ni la variante C. El SFT propio renderiza por mensaje con el mismo template, así que debería ser coherente con B (deducido leyendo el código y el render, no probado).
- Cambios, sin aplicar:
  - `prompts.py`: quitar la sección de la herramienta del prompt de `tools` y agregar el esquema.
  - `backends.py` y `rollout.py`: pasar `tools=` y agregar los resultados como mensajes de rol `tool`.
  - `training_prep.py`: pasar `tools=` en `tokenize_example` y convertir las 84 trazas de `tools` (mecánico).
  - Regenerar los 65 pares de `tools`: los rechazados vienen del 1.7B con el formato viejo.
  - Verificador y recompensa: aceptar trayectorias en el formato nuevo.
  - Medir de nuevo la línea base de `tools` (450 rollouts).
- Riesgos: el efecto real del nativo no está medido (la muestra es chica) y no se estimó el esfuerzo de reimplementar el rollout y el verificador.

**C. Nativo puro con RL sobre `tools`.** No recomendada ahora: exige `environment_factory` (experimental), un adaptador de recompensa y el RL más caro del proyecto, sin que el objetivo lo pida.

**Plan propuesto:**

1. E2 como está planeada: SFT con las 170 trazas y GRPO en `visible` (con `loss_type` explícito), medidos principalmente en `visible`. Lo de `tools` en la E2 es exploratorio.
2. Correr las 72 instancias que faltan de la prueba de B (1 muestra) y compararlas con la muestra 0 de la línea base. En una T4 son entre 1,1 y 3,8 horas según la velocidad (55 a 192 s por conversación), menos si se reparten entre cuentas de Kaggle.
3. No generar trazas de `tools` con el 8B hasta tener ese resultado. Las de `visible` sí.
4. Decidir hacia el 27-28 de noviembre. Se adopta B si los fallos de formato siguen casi en cero y el acierto no empeora. Si no, se mantiene A.
5. Si se adopta, convertir y regenerar los datos de `tools` y medir de nuevo su línea base después de la E2.

## 8. Preguntas para el equipo

1. ¿Adoptamos la presentación nativa (variante B) para `tools`, sujeto a confirmar con las 72 instancias?
2. ¿Quién corre las 72 instancias y dónde (Colab, Kaggle o Peteroa)?
3. ¿Aceptamos que el RL sea solo en `visible` y que `tools` se mida como transferencia? El paper debe decirlo explícito.
4. Las conclusiones del informe prometen "probar el formato nativo" y "exigir la etiqueta en la recompensa". ¿Las incluimos como ablación o las declaramos fuera de alcance en la E2?
5. ¿Fijamos `loss_type` y documentamos las versiones (línea base con transformers 5.20.2, entrenamiento con 5.24.0)?

## 9. Qué no se verificó

- No se ejecutó nada de TRL, transformers ni los scripts de entrenamiento; solo se leyó código y se renderizó el template con jinja2 (réplica).
- No se probó que `environment_factory` funcione con este entorno.
- La coherencia entre el SFT propio y la variante B se dedujo del código y del render, no se probó.
- No se midió el esfuerzo del cambio a B ni el efecto del nativo.
- No se vio el archivo de las 18 conversaciones: la observación sobre el enredo en los cálculos es del equipo. Las medidas de la sección 6 son sobre la línea base y las trazas del repo, con una búsqueda de frases en inglés; los scripts de esas medidas no están en el repo.
