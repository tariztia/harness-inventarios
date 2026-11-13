# Harness de razonamiento con herramientas sobre inventarios

Entorno y dataset para el Desafío de Investigación de IIC-3694 (Inteligencia Artificial Generativa, PUC Chile). Evalúa si un modelo pequeño, de 1–2B de parámetros, puede resolver solicitudes sobre inventarios combinando datos, comparando alternativas y aplicando restricciones.

El modelo recibe una solicitud en español, consulta la herramienta `get_inventory` y responde. Un verificador independiente calcula la recompensa 0/1, que luego servirá para entrenamiento con SFT, DPO y RL.

**Modelo objetivo:** `Qwen/Qwen3-1.7B` con thinking.

## Estado

| Entregable | Estado |
|---|---|
| Harness y verificador | Listos |
| Generador de tareas | Listo |
| Línea base del modelo objetivo (pass@1 y pass@5) | Lista: 900 rollouts de Qwen3-1.7B sobre `eval` |
| Línea base de otros modelos | Lista para Llama-3.2-1B, Qwen3-1.7B sin thinking y Qwen3-4B; Qwen3-0.6B va en 70 de 90 instancias |
| Trazas SFT y pares DPO | Listos: 170 trazas, todas de Qwen3-8B, y 106 pares |
| Informe final | Borrador completo en [docs/informe.md](docs/informe.md) |

## Línea base de Qwen3-1.7B

Qwen3-1.7B con thinking sobre `eval`: 10 instancias por celda, 5 muestras, 90 instancias por condición (`results/kaggle_qwen17b/linea_base_qwen17b`). Con 10 instancias por celda, los intervalos por celda son anchos; el detalle está en su `report.md`.

| Condición | pass@1 | pass@5 |
|---|---|---|
| Datos visibles | 58/90 (64 %) | 80/90 (89 %) |
| Con herramientas | 37/90 (41 %) | 62/90 (69 %) |

Por dificultad (pass@1 y pass@5, sobre 30 instancias):

| Dificultad | Visible pass@1 | Visible pass@5 | Herramientas pass@1 | Herramientas pass@5 |
|---|---|---|---|---|
| Easy | 27 | 30 | 19 | 30 |
| Medium | 18 | 28 | 13 | 22 |
| Hard | 13 | 22 | 5 | 10 |

Lectura:

- Las tareas caen en la zona aprendible: el acierto baja con la dificultad y pass@5 supera con claridad a pass@1 en ambas condiciones.
- Usar herramientas cuesta unos 23 puntos de pass@1 frente a tener los datos a la vista.
- Composición hard con herramientas queda en 0/10 incluso con 5 intentos, y con datos visibles en 2/10: ahí casi no hay señal para RL.
- En selección con herramientas, 47 de 150 respuestas vienen sin claves (`S2|29|0`) y se rechazan; leídas por posición, 32 tendrían los valores correctos. Es un problema de formato tras recibir los resultados, no de razonamiento.

Estos números se **reevaluaron** con `scripts/reevaluate.py` después de la corrida. El verificador rechazaba las respuestas con varios pares en una línea (`O1_atendidas: 33O1_pendientes: 6...`), y 56 de esas respuestas eran correctas. Ahora se aceptan (ver [docs/contrato.md](docs/contrato.md)). Antes del cambio, herramientas daba 27/90 en pass@1. Cada fila corregida conserva su veredicto original en `verdict_anterior`.

## Línea base de otros modelos

Mismas instancias de `eval` y 5 muestras (`results/kaggle_otros_modelos`, corrida con `notebooks/linea_base_otros_kaggle.ipynb`). Sin thinking el tope es de 768 tokens; con thinking, de 4096.

| Modelo | Visible pass@1 | Visible pass@5 | Herramientas pass@1 | Herramientas pass@5 |
|---|---|---|---|---|
| Llama-3.2-1B | 0/90 | 0/90 | 0/90 | 0/90 |
| Qwen3-0.6B con thinking (parcial) | 5/70 (7 %) | 18/70 (26 %) | 9/70 (13 %) | 18/70 (26 %) |
| Qwen3-1.7B sin thinking | 27/90 (30 %) | 51/90 (57 %) | 22/90 (24 %) | 42/90 (47 %) |
| **Qwen3-1.7B con thinking (objetivo)** | 58/90 (64 %) | 80/90 (89 %) | 37/90 (41 %) | 62/90 (69 %) |
| Qwen3-4B sin thinking | 67/90 (74 %) | 71/90 (79 %) | 64/90 (71 %) | 73/90 (81 %) |

Lectura:

- El acierto sube con el tamaño del modelo en ambas condiciones, así que las tareas distinguen capacidad.
- El thinking le da al 1.7B unos 34 puntos de pass@1 con datos visibles y 17 con herramientas.
- Qwen3-4B sin thinking supera al objetivo en pass@1, pero no en pass@5 con datos visibles: gana poco con más intentos. 142 de sus generaciones se cortaron en el tope de 768 tokens.
- Llama-3.2-1B no acierta ninguna de sus 900 respuestas: 699 no traen bloque `<answer>` y 430 generaciones llegan al tope de tokens.
- Composición hard sigue casi en cero para todos: Qwen3-4B logra 0/10 con datos visibles y 1/10 con herramientas.
- Qwen3-0.6B se cortó a las 11 horas con 70 de 90 instancias por condición, todas con sus 5 muestras. La corrida se puede continuar.

Como referencia de un modelo más grande, Qwen3-8B con thinking acierta 81/90 en la primera muestra de cada condición, pero sobre `train` y con 2 muestras (`results/kaggle_qwen8b/trazas_qwen8b`), así que no es comparable punto a punto con esta tabla.

## Datos derivados

`results/kaggle_qwen8b/datos_derivados_qwen8b` tiene los datos de entrenamiento, armados con `scripts/build_training_data.py` sobre los 180 prompts de `train` (90 instancias por 2 condiciones):

- `sft.jsonl`: 170 trazas correctas, todas de Qwen3-8B (el profesor).
- `dpo.jsonl`: 106 pares (correcta, incorrecta). La correcta es siempre de Qwen3-8B; la incorrecta es de Qwen3-1.7B en 105 pares. 83 de las incorrectas son errores de valor.

Qwen3-8B corrió los 180 prompts con 2 muestras y acertó 329 de 360 respuestas. Los 10 prompts sin respuesta correcta son todos de composición hard (6 con herramientas y 4 con datos visibles). `results/kaggle_qwen8b/pendientes.json` es la lista de 71 prompts que se corrió primero, antes de extender la corrida a todos.

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

Con herramientas, todos los modelos quedaron cerca de 0 porque el harness aún no reconocía las llamadas sin etiqueta (`<tool_call>`): Qwen acertó 1 de 90 rollouts con y sin thinking, y Llama 0 de 90. Eso se corrigió después; los resultados válidos con herramientas son los de la línea base de arriba.

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

Deberían pasar todos los tests, salvo 8 marcados como `xfail`, que son limitaciones conocidas del verificador. El núcleo solo usa la biblioteca estándar; `torch` y `transformers` hacen falta únicamente para correr modelos.

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

El verificador acepta formas equivalentes como `3`, `tres`, `20-17` o `1 de P01 y 2 de P02`. Rechaza respuestas múltiples, ambiguas o contradictorias. La suite adversarial tiene 334 casos y pasa 326; los resultados y las 8 limitaciones están en [docs/robustez_verificador.md](docs/robustez_verificador.md). Esos casos los escribió el equipo, así que no reemplazan revisar respuestas reales.

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

1. Terminar la línea base de Qwen3-0.6B: faltan 200 rollouts, unas 3 horas en Kaggle. Se continúa agregando la salida anterior como entrada del cuaderno.
2. Dejar claro el formato de respuesta en el mensaje que llega con los resultados de la herramienta, por las respuestas sin claves en selección. Obliga a repetir las corridas.
3. Decidir qué hacer con composición hard, que casi no da señal en ningún modelo.
4. Revisar [docs/informe.md](docs/informe.md), el informe final, y completar los integrantes.
