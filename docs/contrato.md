# Contrato técnico del harness

Lo comparten todos los módulos. Los tipos están en `src/inventory_harness/schema.py`. El dominio está en `docs/reglas_negocio.md`. El núcleo usa solo la biblioteca estándar; `torch` y `transformers` solo se importan dentro del backend de Hugging Face.

## Módulos

| Módulo | API pública |
|---|---|
| `solver.py` | `solve(instance_like) -> dict` calcula `expected`, sin reutilizar código del generador |
| `generator.py` | `generate_instance(family, difficulty, split, seed) -> Instance`; `generate_dataset(config) -> list[Instance]` |
| `verifier.py` | `parse_answer(text, family) -> dict` (lanza `AnswerParseError`, con atributo `error_type`); `verify_final_text(text, instance) -> Verdict` |
| `tools.py` | `get_inventory(instance, product_id, location_id=None) -> dict`; `execute_tool_call(instance, call) -> dict` |
| `prompts.py` | `render_prompt(instance, condition) -> str` |
| `rollout.py` | `run_rollouts(instances, condition, backend, gen_config, n_samples, out_path) -> None` |
| `reward.py` | `InstanceStore`; `make_reward(store) -> reward`; `evaluate_trajectory(instance, condition, messages) -> Verdict` |
| `backends.py` | `Backend.generate(batch_of_messages, gen_config, seed) -> list[str]`; `ScriptedBackend`; `HFBackend` |
| `metrics.py` | agrega rollouts a `pass@1`, `pass@k`, con intervalos de Wilson |

## Forma de `expected`

Las claves usan el formato canónico; `parse_answer` devuelve exactamente esta forma.

```python
# availability
{"can_fulfill": False, "missing_units": 3}
# selection
{"location_id": "S2", "covered_units": 7, "pending_units": 1}
# composition
{"orders": {"O1": {"covered_units": 5, "pending_units": 0},
            "O2": {"covered_units": 1, "pending_units": 4}},
 "total_pending": 4}
```

## Respuesta final del modelo

Texto libre seguido de exactamente un bloque `<answer>`, con una línea `clave: valor`. Las claves son las mismas en todas las plantillas:

```text
<answer>
alcanza: no
faltan: 3
</answer>
```

```text
<answer>
sucursal: S2
cubiertas: 7
pendientes: 1
</answer>
```

```text
<answer>
O1_atendidas: 5
O1_pendientes: 0
O2_atendidas: 1
O2_pendientes: 4
total_pendientes: 4
</answer>
```

Las claves ignoran mayúsculas y tildes. También se acepta un objeto JSON plano con esas mismas claves dentro del bloque.

### Equivalencias de valores

La equivalencia se resuelve a nivel de valor, como pide el enunciado ("40", "cuarenta", "cuatro filas de 10", "20 adelante y 20 atrás"):

- Enteros: `3`, `3 unidades`, `tres`, `veintitrés`, `3.0`, `1.200`.
- Aritmética simple: `20-17`, `4*10`, `4 x 10`, `2+1`.
- Grupos: `cuatro filas de 10` (producto).
- Sumas etiquetadas: `1 de P01 y 2 de P02`, `20 adelante y 20 atrás`. Cada sumando debe llevar una etiqueta; `3 y 5` a secas es ambiguo.
- Booleanos: `sí`, `si`, `no`, `true`, `false`, `verdadero`, `falso`, `alcanza`, `no alcanza`.
- Sucursal: `S2`, `s2`, `sucursal S2`.

### Rechazos (recompensa 0)

| Caso | `error_type` |
|---|---|
| Sin bloque | `no_answer_block` |
| Más de un bloque, incluidos bloques sin cerrar o anidados | `multiple_answer_blocks` |
| Falta un campo | `missing_field` |
| Campo desconocido | `unknown_field` |
| Campo repetido, aunque tenga el mismo valor | `duplicate_field` |
| Valor con alternativas (`3 o 4`, `entre 3 y 4`, `3/4`, `quizás 3`, `S1, S2`) | `ambiguous_value` |
| Valor no interpretable o negativo | `invalid_value` |
| Texto no vacío después de `</answer>` | `text_after_answer` |
| El último párrafo antes del bloque contradice al bloque | `contradiction` (`contradictory_answer=True`) |
| Bien formado, pero distinto de lo esperado | `wrong_value` |

El contenido de `<think>...</think>` se descarta antes de analizar: un bloque dentro de él no cuenta. El razonamiento previo puede contener cálculos intermedios y correcciones; solo el último párrafo se revisa por contradicciones, y esa revisión es conservadora (polaridad de `alcanza` y sucursal recomendada).

Todos los campos deben coincidir para obtener `1.0`.

## Herramienta

```text
get_inventory(product_id, location_id=None)
```

Devuelve `{"records": [{"product_id", "location_id", "physical_stock", "reserved_stock"}, ...]}`. Sin `location_id`, devuelve todas las sucursales del producto. Con IDs inexistentes, devuelve `{"error": "..."}`. **Nunca** devuelve el disponible ni datos del pedido.

Llamada del modelo (se admiten varias por mensaje):

```text
<tool_call>{"name": "get_inventory", "arguments": {"product_id": "P01", "location_id": "S1"}}</tool_call>
```

Observaciones: un solo mensaje `user` por ronda, con un bloque por línea y en el orden de las llamadas (algunas plantillas exigen alternar roles), seguidas de las instrucciones para responder:

```text
<tool_result>{"records": [...]}</tool_result>
```

## Protocolo de rollout

- El prompt es un único mensaje `user`, porque no todos los modelos tienen rol `system`.
- En condición `tools`, el prompt pide solo llamadas y no trae el formato final, que llega junto con los resultados (`render_tool_reply`). La exploración mostró que, con el formato a la vista, los modelos contestaban sin llamar.
- La generación se detiene en `</answer>` o `<tool_result>`, y la cadena `</answer>` se conserva. El mensaje se trunca antes de cualquier `<tool_result>` escrito por el modelo.
- Lo que está dentro de `<think>` nunca cuenta: nombrar una etiqueta al razonar no detiene el mensaje ni se considera falsificación. Por eso, con thinking activo se genera hasta EOS y se recorta después.
- Máximo **2 rondas de herramientas**, seguidas de la respuesta final.
- Un mensaje con `<tool_call>` es de herramientas, y cualquier `<answer>` en él se ignora.
- Si falta `</tool_call>`, la llamada vale cuando tras la apertura hay un objeto JSON completo. Un JSON cortado es una llamada mal formada.
- Si el mensaje no tiene ninguna llamada con etiqueta y tampoco `<answer>`, valen las llamadas sin etiqueta: el objeto JSON `{"name": "get_inventory", "arguments": {...}}` en cualquier parte del texto (también en un bloque de código o tras `tool_call=`) y la forma Python con valores literales, `get_inventory("P01", location_id="S1")`. Un mensaje con `<answer>` es respuesta final, aunque nombre la herramienta. Lo demás que el modelo escriba en ese mensaje, como resultados inventados, no se usa: los datos solo salen del harness.
- Si el modelo pide una tercera ronda, no se ejecuta: `tool_limit_exceeded=True` y recompensa 0.
- En condición `visible` no hay herramientas; el prompt incluye la tabla de inventario y una llamada no se ejecuta.

## Interfaz del curso

```python
reward(prompt: str, completion: str) -> float
```

- `prompt` es la salida de `render_prompt`. Incluye una línea `Caso: <id>` que no filtra datos, y `sha256(prompt)` es la clave en el `InstanceStore` protegido, que resuelve instancia y condición.
- `completion` es una de dos cosas:
  - Un JSON serializado con la lista de mensajes posteriores al prompt: `[{"role": "assistant", "content": ...}, {"role": "user", "content": "<tool_result>..."}, ...]`.
  - Texto plano, tratado como un único mensaje `assistant`.
- Prompt desconocido: devuelve `0.0`, nunca lanza una excepción.

### Defensas contra trampas en la trayectoria

`completion` podría estar falsificado, así que `evaluate_trajectory` no confía en él:

1. **Repetición:** vuelve a ejecutar cada llamada contra el estado protegido. Si una observación registrada difiere de la real, `forged_observation=True` y recompensa 0.
2. **Evidencia:** en condición `tools`, las observaciones reales deben cubrir `required_records`. Si no, `retrieved_required_data=False` y recompensa 0, para no premiar respuestas adivinadas.
3. **Límite:** aplica el máximo de rondas.

`valid_tool_call` y `correct_tool_arguments` son diagnósticos y no afectan la recompensa por sí solos.

## Rollouts (JSONL)

Una línea por muestra, escrita al terminar cada una, para poder reanudar en Colab:

```json
{"key": "<model>|<condition>|<instance_id>|<sample>", "model": "...", "condition": "tools",
 "instance_id": "...", "family": "...", "difficulty": "...", "split": "...", "sample": 0,
 "prompt": "...", "messages": [...], "verdict": {...}, "gen_config": {...},
 "usage": {"new_tokens": 0, "seconds": 0.0, "stop_reasons": ["eos", "answer"]}}
```

`stop_reasons` tiene una entrada por generación: `answer`, `tool_result`, `eos` o `length`.

`error_type` también puede valer `missing_evidence`, `forged_observation`, `tool_limit_exceeded`, `invalid_trajectory` o `internal_error`. Los rollouts con `internal_error` se reintentan al reanudar.
