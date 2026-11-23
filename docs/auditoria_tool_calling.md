# Auditoría del tool calling: ¿pasamos al formato nativo?

Documento para decidir en equipo antes de generar más trazas de `tools`. No cambia código. Las referencias de archivo y línea son de la rama `entrega-2` en el commit `2c473b6` (ahí están los scripts de entrenamiento). Los datos de TRL salen de su código fuente en el tag `v1.18.2`.

## Resumen

- **Nada está mal hecho.** Evaluación, SFT y GRPO ven el mismo texto en `visible`, y el SFT por mensaje es coherente con cómo el formato actual borra el `<think>` en inferencia.
- **El repo supone algo que ya no es cierto:** "el GRPOTrainer genera un solo mensaje por prompt". Con `trl==1.18.2` el GRPOTrainer soporta herramientas multi-turno. RL sobre `tools` es posible, pero solo con formato nativo puro.
- **La prueba de las 18 conversaciones no fue nativo puro.** Midió "la herramienta presentada en el bloque de sistema y con `tool_response`", con un mensaje `user` agregado después de los resultados y las llamadas como texto, no como `tool_calls` estructurados.
- **Propuesta:** no cambiar todo a nativo antes de la E2. Hacer un piloto del nativo puro con fecha límite y decidir con eso. Detalle en la sección 5.

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

Se comparó el chat template real de Qwen3-1.7B (viene dentro de `tokenizer_config.json`) renderizando tres variantes con la misma instancia. El render se hizo con jinja2 imitando cómo transformers aplica el template; es una réplica, no la salida de transformers.

| | Harness actual | Nativo (`tools=`) |
|---|---|---|
| Bloque `system` | No hay | `# Tools … <tools>{esquema JSON}</tools>` e instrucciones de `<tool_call>` |
| Llamada | Una línea por llamada | `<tool_call>\n{...}\n</tool_call>` |
| Resultado | `<tool_result>…</tool_result>` dentro de un `user` | `<tool_response>\n…\n</tool_response>` dentro de un `user` (mensaje de rol `tool`) |
| `<think>` de la ronda 1 al responder | Se borra | Se conserva, solo en el nativo puro |

Sobre la última fila: el template borra el `<think>` de los mensajes anteriores a la última consulta del usuario. Un `user` con `<tool_result>` cuenta como consulta nueva, así que el razonamiento de la ronda 1 se pierde. En el nativo puro (`assistant` con `tool_calls`, mensajes de rol `tool`, sin `user` después) se conserva. En la variante del cuaderno (con un `user` al final) también se pierde.

## 3. Versiones y compatibilidad con TRL

Declaradas en `requirements-train.txt`: transformers 5.24.0, trl 1.18.2, peft 0.22.0, accelerate 1.16.0, datasets 5.2.0. vllm está comentado y unsloth no aparece. La línea base se midió con transformers 5.20.2 (está en los `manifest.json`), y `pyproject.toml` solo pide `transformers>=4.51` para Colab.

| | Qué hace TRL 1.18.2 | Qué hace el repo |
|---|---|---|
| SFTTrainer | Acepta la columna `tools` y mensajes con `tool_calls` y rol `tool` (`sft_trainer.py:1360-1381`). Con `assistant_only_loss` cambia el template de Qwen3 por `qwen3_training.jinja`, que siempre conserva el `<think>` | No lo usa. `Trainer` propio con un ejemplo por mensaje del asistente (`train_sft.py:10-13`, `training_prep.py:81-132`) |
| DPOTrainer | Acepta la columna `tools` (`dpo_trainer.py:1157-1176`) | No la pasa. Los pares `tools` incluyen el `user` con resultados en `chosen` y `rejected` (`training_prep.py:138-144`) |
| GRPOTrainer | Soporta herramientas multi-turno: `tools=[funciones]` y `environment_factory` (experimental), con transformers ≥ 5.0 y ≥ 5.2 (`grpo_trainer.py:687-699`) | Solo `visible`, sin `tools` ni `environment_factory` (`train_grpo.py:129-131`) |

Observaciones:

- El template de Qwen3-1.7B es idéntico, byte a byte, al `qwen3.jinja` que TRL reconoce. TRL ya trae el parser de llamadas de Qwen3 y la versión de entrenamiento.
- El SFT propio se justifica con el formato de texto: la versión de entrenamiento de TRL conserva el `<think>` de todas las rondas, pero en inferencia con texto se borra. Con nativo puro coinciden.
- GRPO con herramientas exigiría: un entorno por rollout con `get_inventory` (porque la herramienta necesita el inventario de la instancia; `reset(**fila)` recibe las columnas del dataset, `grpo_trainer.py:2541-2545`), resultados como JSON ya serializado (TRL los vuelve `str(result)`, `:2147-2148`), `max_tool_calling_iterations=2` (por defecto no hay tope, `:843-845`), y un adaptador de recompensa, porque hoy `GrpoReward` solo junta el `content` del asistente (`training_prep.py:240-243`) y no vería `tool_calls` estructurados.
- `max_completion_length` parece ser acumulado entre turnos (`grpo_trainer.py:2088`); la línea base usó 4.096 por turno. No se verificó a fondo.
- **Ajuste independiente del formato:** `train_grpo.py` no fija `loss_type`, y el valor por defecto de TRL 1.18.2 es `"dapo"` (`grpo_config.py:237`, `:809-810`). El "GRPO base" de la propuesta sería en realidad normalización estilo DAPO. Para la ablación hay que fijarlo explícito.

## 4. Lo que midió la prueba de 18 conversaciones

Resultado reportado: 18 de 18 respuestas con `<tool_call>` (frente a 5 de 18 en la línea base), llamadas válidas 18 de 18, fallos de formato en cero, aciertos de 6/18 a 10/18 (5 ganadas, 1 perdida, p ≈ 0,22).

- La mejora de formato es clara aunque sean pocas conversaciones. La de aciertos no es concluyente.
- No es nativo puro (ver sección 2). El resultado no se puede atribuir a `tools=` en sí.
- Tiempo: 3.457 s para 18 conversaciones en una T4 (≈192 s por conversación), unas 3,5 veces más lento por conversación que la línea base (55 s, lote de 16). Causa no diagnosticada.

## 5. Opciones

**A. Mantener el formato de texto (núcleo del proyecto) y entrenar RL en `visible`.**
- No requiere cambios. Lo ya probado sigue valiendo.
- Limitación: no hay RL sobre `tools`. Se mide como transferencia, y el paper debe decirlo.
- El fallo de formato (47 de 150 sin claves en selección con herramientas) queda como material para mostrar el efecto del SFT.

**B. Pasar a nativo puro.**
- Habilita RL en `tools`, SFT/DPO con las herramientas estándar de TRL, y coherencia entre entrenamiento e inferencia.
- Cambios (no aplicados): variante nativa en `prompts.py` y decidir dónde van las instrucciones de formato; `render_chat` con `tools=` y mensajes `tool` en `backends.py` y `rollout.py`; adaptar recompensa y verificador a trayectorias nativas; convertir o regenerar las 84 trazas y 65 pares de `tools`; entorno y adaptador de recompensa en `train_grpo.py`; medir de nuevo la línea base de `tools` (450 rollouts).
- Riesgos: `environment_factory` es experimental; GRPO multi-turno con thinking es lo más caro del proyecto; dónde ubicar las instrucciones de formato no está resuelto (en el prompt inicial hay una observación, no cuantificada, de que los modelos tienden a responder sin llamar).

**Recomendación (criterio, no medición):** opción A para la E2 y el núcleo, más un piloto acotado del nativo puro:

1. E2 como está planeada: SFT con las 170 trazas y GRPO en `visible` (con `loss_type` explícito), evaluando en ambas condiciones.
2. Piloto del nativo puro con las instrucciones de formato dentro del resultado de la herramienta, con más de 18 instancias (idealmente las 90, una muestra).
3. No generar trazas de `tools` con el 8B hasta tener ese resultado. Las de `visible` sí.
4. Si el nativo gana, reportarlo como hallazgo del ciclo de iteración sin reentrenar todo.

Criterio para cambiar a B: el piloto puro muestra una mejora grande (por ejemplo ≥ 15 puntos de pass@1 en `tools`, o fallos de formato casi en cero) con muestra suficiente, se decide hacia el 27-28 de noviembre y alguien puede implementarlo sin consumir tiempo de Peteroa.

## 6. Preguntas para el equipo

1. ¿Queremos RL en `tools` en este proyecto, o basta medirlo como transferencia desde `visible`?
2. ¿Quién corre el piloto del nativo puro y dónde (Colab, Kaggle o Peteroa)?
3. Las conclusiones del informe prometen "probar el formato nativo" y "exigir la etiqueta en la recompensa". ¿Las incluimos como ablación o las declaramos fuera de alcance en la E2?
4. ¿Fijamos `loss_type` y documentamos las versiones (línea base con transformers 5.20.2, entrenamiento con 5.24.0)?

## 7. Qué no se verificó

- No se ejecutó nada de TRL, transformers ni los scripts de entrenamiento; solo se leyó código y se renderizó el template.
- No se probó que `environment_factory` funcione con este entorno.
- No se midió el esfuerzo del cambio a nativo ni el efecto del nativo puro.
- El render del template es una réplica con jinja2.
