# Harness de razonamiento con herramientas sobre inventarios

Entorno y dataset para el Desafío de Investigación de IIC-3694 (Inteligencia Artificial Generativa, PUC Chile). Evalúa si un modelo pequeño, de 1–2B de parámetros, puede resolver solicitudes sobre inventarios combinando datos, comparando alternativas y aplicando restricciones.

El modelo recibe una solicitud en español, consulta la herramienta `get_inventory` y responde. Un verificador independiente calcula la recompensa 0/1, que luego servirá para entrenamiento con SFT, DPO y RL.

**Modelo objetivo:** `Qwen/Qwen3-1.7B` con thinking.

## Estado

| Entregable | Estado |
|---|---|
| Harness y verificador | Listos |
| Generador de tareas | Listo |
| Exploración de línea base | Terminada |
| Piloto de línea base (más instancias y pass@5) | Pendiente |
| Trazas SFT y pares DPO | Script listo; faltan las corridas |
| Informe final | Pendiente |

### Llamadas sin etiqueta

Qwen suele escribir el JSON correcto sin `<tool_call>`. `parse_tool_calls` ahora acepta también JSON sin etiqueta, estilo Python (`get_inventory(...)`) y `tool_call={...}`. **Los resultados con herramientas de abajo son anteriores a ese cambio** y no miden la capacidad real del modelo: hay que repetir la exploración con herramientas.

## Resultados de la exploración

Son 45 instancias con 2 muestras cada una, por condición (`results/exploracion_prompt_corregido`). Los intervalos son anchos: sirven para orientar, no para concluir.

Con datos visibles:

| Modelo | pass@1 | pass@2 | Segundos por rollout |
|---|---|---|---|
| Qwen 1.7B con thinking | 25/45 (56 %) | 31/45 (69 %) | 14,9 |
| Qwen 1.7B sin thinking | 14/45 (31 %) | 20/45 (44 %) | 3,8 |
| Llama 3.2 1B | 0/45 | 0/45 | 3,4 |

Qwen con thinking, por dificultad:

| Dificultad | pass@1 | pass@2 |
|---|---|---|
| Easy | 13/15 | 14/15 |
| Medium | 9/15 | 12/15 |
| Hard | 3/15 | 5/15 |

Con herramientas, todos los modelos quedaron cerca de 0 porque el harness aún no reconocía las llamadas sin etiqueta: Qwen acertó 1 de 90 rollouts con y sin thinking, y Llama 0 de 90.

Conclusiones por ahora:

- Hay una posible zona aprendible con datos visibles: el acierto baja de easy a hard, y pass@2 supera a pass@1.
- Composición es la familia más difícil (4/15 en pass@1).
- Selección easy y medium podrían ser demasiado fáciles (20 de 20 aciertos por muestra).
- 13 de las 19 respuestas cortadas por el tope de 2.048 tokens fueron en hard, así que parte de esos fallos no mide razonamiento.
- Llama queda descartado como objetivo: tampoco acertó al ignorar el formato.

`results/exploracion_prompt_original` guarda la primera corrida, antes de corregir el prompt. Cada carpeta tiene `report.md` con el detalle.

## Instalación

Requiere Python 3.10 o superior y [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/tariztia/harness-inventarios.git
cd harness-inventarios
uv run --group dev pytest -q
```

Deberían pasar todos los tests, salvo 4 marcados como `xfail`, que son limitaciones conocidas del verificador. El núcleo solo usa la biblioteca estándar; `torch` y `transformers` hacen falta únicamente para correr modelos.

## Uso

### Generar un dataset

```bash
uv run python scripts/generate_dataset.py --n-per-cell 40 --base-seed 2026 --out data
```

Crea `train.jsonl`, `eval.jsonl`, `test.jsonl` y `stats.json`. La misma semilla produce el mismo dataset, por eso `data/` no se versiona.

### Usar la recompensa

La interfaz común del curso es `reward(prompt, completion) -> float`:

```python
from inventory_harness.generator import generate_instance
from inventory_harness.prompts import render_prompt
from inventory_harness.reward import InstanceStore, make_reward

instance = generate_instance("availability", "easy", "train", 7)
reward = make_reward(InstanceStore([instance]))

prompt = render_prompt(instance, "visible")
print(reward(prompt, "<answer>\nalcanza: sí\nfaltan: 999\n</answer>"))  # 0.0
```

Para un dataset guardado, usa `InstanceStore.from_jsonl("data/eval.jsonl")`.

En la condición con herramientas, `completion` es la trayectoria completa serializada como JSON. El harness repite cada llamada contra el estado protegido, así que una observación inventada o una respuesta adivinada recibe 0. El detalle está en [docs/contrato.md](docs/contrato.md).

### Línea base y datos del modelo objetivo

`notebooks/qwen_objetivo_colab.ipynb` corre Qwen3-1.7B con thinking en Colab: mide su línea base sobre `eval` (pass@1 y pass@5) y guarda sus respuestas sobre `train`. No entrena el modelo. Si Colab se queda sin cuota de GPU, `notebooks/qwen_objetivo_kaggle.ipynb` hace lo mismo en Kaggle y continúa la corrida anterior (ver `docs/guia_kaggle.md`).

Las respuestas sobre `train` se convierten en datos de entrenamiento con:

```bash
uv run python scripts/build_training_data.py results/trazas --out results/datos_derivados
```

El script vuelve a verificar cada respuesta y escribe `sft.jsonl` (trazas correctas), `dpo.jsonl` (una correcta y una incorrecta por prompt) y `manifest.json` (procedimiento y conteos). Acepta varias carpetas: con las de Qwen3-8B, sus respuestas tienen prioridad como correctas. Rechaza cualquier corrida que no sea de `train`.

### Correr modelos en Colab

No hace falta GPU local. Sigue [docs/guia_colab.md](docs/guia_colab.md). En resumen:

1. Genera el zip con `uv run python scripts/package_for_colab.py`.
2. Súbelo a `Mi unidad/inventory_harness/` en Drive.
3. Abre `notebooks/piloto_colab.ipynb` en Colab, con GPU T4.

Las corridas se guardan en Drive y se reanudan si Colab se desconecta. El piloto está protegido por `EJECUTAR_PILOTO = False`.

### Probar y analizar sin GPU

```bash
uv run python scripts/run_pilot.py --stage exploracion --dry-run --limit 9 --n-samples 1 --out /tmp/prueba
uv run python scripts/analyze_results.py /tmp/prueba
```

`--dry-run` usa un modelo simulado: sirve para probar el código, no para medir. `analyze_results.py` escribe `report.md`, `summary.json` y `muestra_errores.jsonl` en la carpeta indicada.

## El problema

Hay tres familias de tareas, con tres niveles cada una. Las reglas exactas están en [docs/reglas_negocio.md](docs/reglas_negocio.md).

| Familia | Pregunta | Qué exige |
|---|---|---|
| Disponibilidad | ¿Alcanza el stock para un pedido? ¿Cuánto falta? | Consultar, restar reservas y comparar |
| Selección | ¿Qué sucursal cubre más de un pedido? | Comparar sucursales y desempatar |
| Composición | ¿Cómo se reparten varios pedidos en orden de llegada? | Descontar stock entre pedidos |

Cada tarea se evalúa en dos condiciones, para separar la dificultad de razonar de la de usar herramientas:

- `tools`: el modelo debe obtener los datos con `get_inventory`.
- `visible`: los datos van en el prompt.

La respuesta final es texto libre seguido de un bloque:

```text
<answer>
alcanza: no
faltan: 3
</answer>
```

El verificador acepta formas equivalentes como `3`, `tres`, `20-17` o `1 de P01 y 2 de P02`. Rechaza respuestas múltiples, ambiguas o contradictorias. La suite adversarial tiene 246 casos y pasa 242; los resultados y las 4 limitaciones están en [docs/robustez_verificador.md](docs/robustez_verificador.md). Esos casos los escribió el equipo, así que no reemplazan revisar respuestas reales.

## Estructura

```text
src/inventory_harness/
  generator.py, templates.py   generan las tareas
  solver.py                    calcula la respuesta correcta
  verifier.py, numbers_es.py   analizan y verifican la respuesta final
  tools.py, prompts.py         herramienta y mensajes del modelo
  rollout.py, backends.py      ejecutan modelos, con lotes y reanudación
  reward.py                    interfaz reward(prompt, completion)
  metrics.py, baselines.py     pass@k, intervalos y reglas triviales
scripts/                       generar datos, correr, analizar y empaquetar
notebooks/piloto_colab.ipynb   ejecución en Colab
tests/                         tests y casos adversariales
results/                       corridas de exploración
docs/                          contrato, reglas, guía de Colab y robustez
docs/propuesta/                enunciado del desafío y propuestas
```

## Próximos pasos

1. Ajustar el prompt para que el mensaje de llamadas no incluya cálculos ni supuestos, y sugerir omitir `location_id` al comparar sucursales.
2. Repetir la exploración de Qwen con thinking y con herramientas.
3. Correr un piloto reducido, con 20 instancias por celda y 5 muestras (unos 1.800 rollouts).
4. Generar trazas SFT con un modelo abierto más grande, que el enunciado exige, y pares DPO.
5. Escribir el informe final de línea base.
