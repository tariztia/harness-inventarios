# Harness de razonamiento con herramientas sobre inventarios

Entorno, dataset y entrenamiento para IIC-3694 Inteligencia Artificial Generativa (PUC Chile). El repositorio cubre las dos partes del curso:

- **Desafío de Investigación** (terminado): un harness donde un modelo pequeño, de 1–2B de parámetros, resuelve solicitudes sobre inventarios combinando datos, comparando alternativas y aplicando restricciones. Incluye generador de tareas, verificador, línea base y datos para SFT y DPO.
- **Proyecto** (en curso): entrenar al modelo objetivo sobre ese entorno y comparar cinco caminos: modelo base, solo SFT, SFT seguido de GRPO, solo GRPO y DPO.

El modelo recibe una solicitud en español, consulta la herramienta `get_inventory` (o recibe los datos en el prompt) y responde. Un verificador independiente calcula la recompensa 0/1, que sirve a la vez para evaluar, filtrar trazas de SFT, armar pares de DPO y como recompensa de GRPO.

**Modelo objetivo:** `Qwen/Qwen3-1.7B` con thinking. **Profesor** para las trazas: `Qwen/Qwen3-8B` con thinking.

Integrantes: Tomás Ariztía, Arturo Herreros, Rodrigo Meza, Matías Retamales.

## Estado

### Desafío

| Entregable | Estado |
|---|---|
| Harness, generador de tareas y verificador | Listos. 334 casos adversariales, pasan 326 |
| Línea base del modelo objetivo | Lista: 900 rollouts de Qwen3-1.7B sobre `eval` (pass@1 y pass@5) |
| Línea base de otros modelos | Llama-3.2-1B, Qwen3-1.7B sin thinking y Qwen3-4B completas; Qwen3-0.6B en 70 de 90 instancias |
| Trazas SFT y pares DPO | 170 trazas y 106 pares (primera versión); 4.330 trazas y 148 pares (corrida grande con vLLM) |
| Informe | [docs/informe.md](docs/informe.md); versión revisada con figuras en [docs/informe_v2.md](docs/informe_v2.md) |

### Proyecto

| Hito | Fecha | Estado |
|---|---|---|
| Entrega 1: propuesta | 11 nov | [docs/propuesta_proyecto.md](docs/propuesta_proyecto.md) |
| Entrega 2: avance con línea base y primeras curvas | 25 nov | Piloto GRPO con dos semillas, curvas y evaluación en `eval`. Borrador del informe en [docs/informe_avance_E2.docx](docs/informe_avance_E2.docx); estado en [docs/estado_entrega2.md](docs/estado_entrega2.md) |
| Entrega 3: paper, poster y video | 9 dic | Pendiente |

| Camino | Estado |
|---|---|
| 1. Modelo base | Medido (línea base) |
| 2. Solo SFT | Script listo; sin correr en GPU |
| 3. SFT seguido de GRPO | Script listo; sin correr |
| 4. Solo GRPO | Piloto con dos semillas medido en `eval`: pass@1 de 53/90 (base) a 69/90 y 67/90 ([resultados](results/grpo_kaggle/README.md)); falta pass@5 |
| 5. DPO | Script listo; sin correr en GPU |

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

Qwen3-8B con thinking, el profesor, se midió solo sobre `train` (ver la sección siguiente), así que no es comparable punto a punto con esta tabla.

## Datos derivados

Los dos conjuntos se arman con `scripts/build_training_data.py`, que vuelve a verificar cada respuesta, descarta cualquier instancia igual a una de `eval` o `test` y deja el procedimiento y los conteos en `manifest.json`.

| Conjunto | Prompts de `train` | Trazas SFT | Pares DPO | Rechazada del par |
|---|---|---|---|---|
| `results/kaggle_qwen8b/datos_derivados_qwen8b` | 180 (90 instancias × 2 condiciones) | 170 | 106 | Qwen3-1.7B (105 pares) |
| `results/kaggle_qwen8b/datos_derivados_vllm` | 2.338 (1.170 instancias × 2 condiciones, 130 por celda) | 4.330 | 148 | Qwen3-8B |

En los dos, la traza correcta es siempre de Qwen3-8B.

**Primera versión.** Qwen3-8B corrió los 180 prompts con 2 muestras y acertó 329 de 360 respuestas. Los 10 prompts sin respuesta correcta son todos de composición hard. En DPO, la rechazada es del modelo objetivo, y 83 de las 106 son errores de valor.

**Corrida grande con vLLM.** 4.680 rollouts del 8B, repartidos en dos cuentas de Kaggle (`trazas_qwen8b_vllm_parte1de2` y `parte2de2`), a unos 7,5 s por rollout frente a 40–100 s con `transformers`. Se descartaron 4 instancias iguales a `eval` o `test`. El 8B acertó 4.337 de 4.680 respuestas, casi todas salvo en composición: en hard, pass@1 es 52 % con herramientas y 55 % con datos visibles (130 instancias cada una). Diferencias con la primera versión que conviene tener presentes:

- Las rechazadas de DPO son errores del propio 8B, no del 1.7B, y se concentran en composición (122 de 148 pares).
- Las trazas de `tools` usan el formato de herramienta en texto. Si se adopta el formato nativo ([docs/auditoria_tool_calling.md](docs/auditoria_tool_calling.md)), hay que convertirlas.
- `train_sft.py` y `train_dpo.py` siguen usando por defecto la primera versión. Para usar esta hay que pasar `--data results/kaggle_qwen8b/datos_derivados_vllm/sft.jsonl` (o `dpo.jsonl`).

## Entrenamiento

`scripts/train_sft.py`, `train_dpo.py` y `train_grpo.py` entrenan a Qwen3-1.7B con LoRA, y `run_pilot.py --stage eval_final --adapter ...` mide el resultado con el mismo protocolo y las mismas 90 instancias de `eval` que la línea base. Los pasos, los argumentos y los límites están en [docs/guia_entrenamiento.md](docs/guia_entrenamiento.md); las versiones probadas, en `requirements-train.txt`. GRPO entrena solo en la condición `visible`.

### Piloto GRPO (camino 4)

Qwen3-1.7B desde el modelo base, en `visible` con easy y medium, 2 problemas por paso y 8 respuestas por problema, 150 minutos por semilla en una T4 de Kaggle (`notebooks/grpo_curva_kaggle.ipynb`). Detalle, curvas y adaptadores en [results/grpo_kaggle/README.md](results/grpo_kaggle/README.md).

| Semilla | Pasos | Recompensa, primer → último tercio | Grupos sin señal | Respuestas cortadas |
|---|---|---|---|---|
| 2026 | 42 | 68 % → 83 % | 44 % | 10 % |
| 2027 | 45 | 81 % → 84 % | 58 % | 11 % |

![Curva de recompensa del piloto GRPO](results/grpo_kaggle/curva_recompensa.png)

Lectura:

- El entorno da señal: cerca de la mitad de los grupos mezclan aciertos y errores.
- La curva es ruidosa, porque cada paso usa solo 2 problemas, y son tasas sobre `train`; la mejora se mide aparte, en `eval` (abajo).
- La recompensa ya parte en 75–80 % en easy y medium, así que muchos grupos aciertan las 8 respuestas y no aportan gradiente.
- `train_grpo.py` no fija `loss_type`, así que TRL 1.18.2 usó `"dapo"`, y `beta=0` (sin KL). Hay que fijarlo explícitamente antes de las corridas comparables.

**Evaluación en `eval`** (`notebooks/evaluar_grpo_kaggle.ipynb`, resultados en `results/grpo_kaggle/eval_pass1`). Mismas 90 instancias `visible` de la línea base (misma huella), 1 muestra por instancia, 4.096 tokens. El base se volvió a correr en la misma sesión para comparar con el mismo protocolo.

| Modelo | Easy | Medium | Hard (no entrenado) | pass@1 |
|---|---|---|---|---|
| Base (reevaluado) | 24/30 | 19/30 | 10/30 | 53/90 (59 %; IC95 49–68) |
| GRPO semilla 2026 | 30/30 | 23/30 | 16/30 | 69/90 (77 %; IC95 67–84) |
| GRPO semilla 2027 | 30/30 | 21/30 | 16/30 | 67/90 (74 %; IC95 65–82) |

- Pareado por instancia: la semilla 2026 resuelve 18 que el base fallaba y pierde 2 (McNemar exacto, p = 0,0004); la 2027, 18 y 4 (p = 0,004). 12 las resuelven ambas.
- Hard sube de 10 a 16 de 30 en ambas semillas sin haberlo entrenado (disponibilidad y selección). Composición hard sigue en 0/10 en los tres modelos.
- La semilla 2027 llega al tope de 4.096 tokens en 13 de 90 respuestas (el base en 2, la 2026 en 3), y 12 de ellas fallan solo por no cerrar el bloque de respuesta.
- El base reevaluado da 53/90 frente a 58/90 de la línea base: dentro del ruido de muestreo (los IC se solapan).
- Falta pass@5 (`MUESTRAS = 5` en el cuaderno) para saber si GRPO amplía lo que el modelo resuelve o solo lo hace más consistente. Tampoco se midió `tools`.

Los adaptadores están en `results/grpo_kaggle/resultados_grpo.zip`, con Git LFS: `git lfs install && git lfs pull`.

## Instalación

Requiere Python 3.10 o superior y [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/tariztia/harness-inventarios.git
cd harness-inventarios
uv run --group dev pytest -q
```

Deberían pasar todos los tests, salvo 8 marcados como `xfail`, que son limitaciones conocidas del verificador. La suite completa es lenta en Windows. El núcleo solo usa la biblioteca estándar; `torch` y `transformers` hacen falta para correr modelos, y `pip install -r requirements-train.txt` instala lo necesario para entrenar.

## Uso

### Generar un dataset

```bash
uv run python scripts/generate_dataset.py --n-per-cell 40 --base-seed 2026 --out data
```

Crea `train.jsonl`, `eval.jsonl`, `test.jsonl` y `stats.json`. La misma semilla produce el mismo dataset, por eso `data/` no se versiona. No cambies `--n-per-cell` para `eval`: cambia las instancias y deja de ser comparable con la línea base. Para más prompts de entrenamiento está `scripts/make_train_prompts.py`.

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

### Correr modelos (Colab y Kaggle)

No hace falta GPU local. Todos los cuadernos usan el zip de código que genera `uv run python scripts/package_for_colab.py`, y las corridas se reanudan si la sesión se corta.

| Cuaderno | Para qué |
|---|---|
| `notebooks/qwen_objetivo_colab.ipynb`, `qwen_objetivo_kaggle.ipynb` | Línea base del objetivo en `eval` y sus respuestas en `train` |
| `notebooks/qwen_profesor_kaggle.ipynb` | Trazas del 8B, con `transformers` o vLLM, repartibles entre cuentas (`SHARD`) |
| `notebooks/linea_base_otros_kaggle.ipynb` | Línea base de los otros modelos |
| `notebooks/grpo_curva_kaggle.ipynb`, `evaluar_grpo_kaggle.ipynb` | Piloto GRPO y evaluación de sus adaptadores |
| `notebooks/tools_nativo_colab.ipynb` | Prueba del formato nativo de herramientas |
| `notebooks/piloto_colab.ipynb` | Exploración inicial |

Guías: [docs/guia_colab.md](docs/guia_colab.md) y [docs/guia_kaggle.md](docs/guia_kaggle.md).

Las respuestas sobre `train` se convierten en datos de entrenamiento con:

```bash
uv run python scripts/build_training_data.py results/trazas --out results/datos_derivados
```

Acepta varias carpetas; las respuestas de Qwen3-8B tienen prioridad como correctas. Rechaza cualquier corrida que no sea de `train`. Si se corrige el verificador, `scripts/reevaluate.py` vuelve a evaluar los rollouts guardados.

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

- `tools`: el modelo debe obtener los datos con `get_inventory`, con un máximo de dos rondas.
- `visible`: los datos van en el prompt.

La respuesta final es texto libre seguido de un bloque:

```text
<answer>
alcanza: no
faltan: 3
</answer>
```

El verificador acepta formas equivalentes como `3`, `tres`, `20-17` o `1 de P01 y 2 de P02`. Rechaza respuestas múltiples, ambiguas o contradictorias. La suite adversarial tiene 334 casos y pasa 326; los resultados y las 8 limitaciones están en [docs/robustez_verificador.md](docs/robustez_verificador.md). Esos casos los escribió el equipo, así que no reemplazan revisar respuestas reales: la auditoría con respuestas reales está en [docs/auditoria_verificador.md](docs/auditoria_verificador.md).

## Estructura

```text
src/inventory_harness/
  generator.py, templates.py   generan las tareas
  solver.py                    calcula la respuesta correcta
  verifier.py, numbers_es.py   analizan y verifican la respuesta final
  tools.py, prompts.py         herramienta y mensajes del modelo
  rollout.py, backends.py      ejecutan modelos (transformers o vLLM), con lotes y reanudación
  reward.py                    interfaz reward(prompt, completion)
  training_data.py             trazas SFT y pares DPO a partir de rollouts
  training_prep.py             tokenización y recompensa para SFT, DPO y GRPO
  metrics.py, baselines.py     pass@k, intervalos y reglas triviales
scripts/
  generate_dataset.py, make_train_prompts.py   datasets
  run_pilot.py, analyze_results.py             correr modelos y resumir
  build_training_data.py, reevaluate.py        datos derivados y reevaluación
  train_sft.py, train_dpo.py, train_grpo.py    entrenamiento con LoRA
  plot_training.py, audit_sample.py            curvas y muestra para auditoría manual
notebooks/                     Colab y Kaggle (tabla de arriba)
tests/                         tests y casos adversariales
results/
  exploracion_*                corridas iniciales del Desafío
  kaggle_qwen17b/              línea base y trazas del objetivo
  kaggle_otros_modelos/        línea base de los otros modelos
  kaggle_qwen8b/               trazas del profesor y datos derivados
  grpo_kaggle/                 piloto GRPO: curvas, métricas, adaptadores y evaluación en eval
docs/                          ver la sección siguiente
docs/propuesta/                enunciados del Desafío y del Proyecto, y propuestas del Desafío
```

## Documentación

| Documento | Contenido |
|---|---|
| [docs/informe.md](docs/informe.md), [docs/informe_v2.md](docs/informe_v2.md) | Informe del Desafío y su revisión |
| [docs/propuesta_proyecto.md](docs/propuesta_proyecto.md) | Propuesta del Proyecto: caminos, diseño experimental y plan |
| [docs/informe_avance_E2.docx](docs/informe_avance_E2.docx) | Borrador del informe de avance (Entrega 2) |
| [docs/estado_entrega2.md](docs/estado_entrega2.md) | Estado y plan hasta la entrega final |
| [docs/guia_entrenamiento.md](docs/guia_entrenamiento.md) | Cómo entrenar y evaluar cada camino |
| [docs/auditoria_tool_calling.md](docs/auditoria_tool_calling.md) | Formato de herramientas en texto o nativo: análisis y recomendación |
| [docs/contrato.md](docs/contrato.md), [docs/reglas_negocio.md](docs/reglas_negocio.md) | Formato de interacción y reglas de las tareas |
| [docs/robustez_verificador.md](docs/robustez_verificador.md), [docs/auditoria_verificador.md](docs/auditoria_verificador.md), [docs/analisis_verificador.md](docs/analisis_verificador.md) | Robustez del verificador |
| [docs/guia_colab.md](docs/guia_colab.md), [docs/guia_kaggle.md](docs/guia_kaggle.md) | Cómo correr en Colab y Kaggle |

## Próximos pasos

El plan completo está en [docs/estado_entrega2.md](docs/estado_entrega2.md) y en la sección 5 de [docs/propuesta_proyecto.md](docs/propuesta_proyecto.md). Lo inmediato:

1. pass@5 de los adaptadores del piloto GRPO en `eval` (`MUESTRAS = 5` en `notebooks/evaluar_grpo_kaggle.ipynb`).
2. Fijar `loss_type` en `train_grpo.py` antes de las corridas comparables.
3. Correr SFT (con los datos de vLLM), DPO y SFT seguido de GRPO, y fijar el presupuesto de cómputo comparable entre caminos.
4. Decidir el formato de `tools` (texto o nativo), porque afecta a las 2.138 trazas de `tools`.
5. Auditoría manual de trazas exitosas con `scripts/audit_sample.py`.
