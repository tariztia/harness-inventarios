<!-- Esqueleto de la version 2. Contenido del informe actual movido tal cual; las notas [Revisión] marcan lo que falta y se borran al terminar. -->

# Harness de razonamiento con herramientas sobre inventarios

**Desafío de Investigación, IIC-3694 Inteligencia Artificial Generativa (PUC Chile)**

Integrantes: _(completar)_

Código, datos y resultados: `github.com/tariztia/harness-inventarios`. Las rutas que cita este informe son relativas a ese repositorio.

> **[Revisión]** El link debe apuntar al repo limpio (decisión A2). Integrantes: se completan en el archivo final (A1).

> **[Revisión]** Las referencias cruzadas («sección 5.6», etc.) todavía usan la numeración antigua; se actualizan al reescribir cada sección.

## 1. Introducción

> **[Revisión]** Reescribir al final, con el tono corregido (B14): robustez frente a lo previsto. ~350 palabras. Absorbe las fortalezas de la antigua §8 (abajo).

Construimos un entorno para entrenar y evaluar modelos pequeños en solicitudes sobre inventarios de una cadena de sucursales. El modelo recibe una solicitud en español, consulta el stock con una herramienta y entrega una respuesta que un verificador califica con 0 o 1. Las tareas exigen restar reservas, comparar sucursales y repartir stock entre pedidos que compiten, de modo que la herramienta entrega datos y nunca la respuesta.

Los resultados principales son:

- **Las tareas caen en la zona aprendible del modelo objetivo.** Qwen3-1.7B con thinking acierta 41 % al primer intento usando herramientas y 69 % en alguno de 5 intentos. Con los datos a la vista acierta 64 % y 89 %.
- **La dificultad está graduada.** Con herramientas, el pass@1 del objetivo baja de 63 % en easy a 43 % en medium y 17 % en hard.
- **El entorno distingue capacidad.** Sobre las mismas instancias, Llama-3.2-1B acierta 0 %, Qwen3-1.7B sin thinking 24 %, y Qwen3-4B sin thinking 71 % (pass@1 con herramientas).
- **El verificador resiste las trampas previstas y se corrigió con respuestas reales.** Pasa 326 de 334 casos adversariales; los 8 restantes son limitaciones documentadas y ninguna premia un valor incorrecto. Una auditoría de las respuestas de los modelos encontró un falso rechazo frecuente, que se corrigió.
- **Los datos derivados están listos.** Hay 170 trazas SFT de Qwen3-8B y 106 pares DPO sobre 180 prompts de entrenamiento.

Las dos debilidades principales son que composición hard casi no da señal en ningún modelo medido, y que la línea base usa 10 instancias por celda, por lo que los intervalos por celda son anchos.

> **[Revisión]** Fortalezas de la antigua §8, para integrar aquí o en las conclusiones:
>
> **Fortalezas:**
> 
> - Respuestas verificables por construcción, con un solucionador independiente del generador.
> - Dataset de tamaño arbitrario y reproducible desde una semilla, con controles medidos contra instancias degeneradas.
> - Dos condiciones sobre las mismas instancias, que separan el razonamiento del uso de herramientas.
> - Un verificador que acepta equivalencias de valor, tiene 334 casos adversariales y se auditó con respuestas reales.
> - Defensas contra trayectorias falsificadas y respuestas adivinadas.
> - Dificultad graduada y confirmada por la línea base en cuatro modelos.

## 2. Entorno

> **[Revisión]** ~600 palabras. Falta la Figura 1: flujo instancia → modelo → herramienta → verificador.

### 2.1 Tareas

Cada instancia tiene un inventario sintético: un registro por cada par producto × sucursal, con stock físico y stock reservado. La regla central es que **disponible = stock físico − reservado**. Hay tres familias de tareas:

| Familia | Pregunta | Qué exige | Campos de la respuesta |
|---|---|---|---|
| Disponibilidad | ¿Alcanza el stock de una sucursal para un pedido? ¿Cuánto falta? | Restar reservas, comparar por línea y sumar faltantes | `alcanza`, `faltan` |
| Selección | ¿Qué sucursal cubre más unidades de un pedido? | Calcular la cobertura de cada sucursal, comparar y desempatar por ID | `sucursal`, `cubiertas`, `pendientes` |
| Composición | ¿Cómo se reparten varios pedidos que llegan en orden? | Descontar el stock ya asignado a pedidos anteriores | `Ok_atendidas` y `Ok_pendientes` por pedido, `total_pendientes` |

Las reglas completas están en `docs/reglas_negocio.md`. Todas van escritas en el prompt, así que el problema es de razonamiento y uso de herramientas, y no de memorización: los datos son sintéticos y cambian en cada instancia.

### 2.2 Dos condiciones

Cada instancia se evalúa en dos condiciones, para separar la dificultad de razonar de la de usar herramientas:

- **`visible`:** la tabla de inventario va en el prompt.
- **`tools`:** el modelo debe pedir los datos con `get_inventory(product_id, location_id=None)`, que devuelve stock físico y reservado. La herramienta nunca devuelve el disponible ni datos del pedido.

### 2.3 Protocolo de interacción

> **[Revisión]** Reducir el primer párrafo. «Qué cuenta como llamada» pasó al Anexo A, el contraste con Reasoning Gym al Anexo B y el párrafo de Llama al Anexo F. En el cuerpo queda una oración que mencione la flexibilidad con las llamadas y remita al anexo.

El prompt es un único mensaje de usuario, sin rol de sistema, y la herramienta se describe en ese mismo texto, con un ejemplo de llamada. Es una decisión de portabilidad: un mismo prompt en texto plano sirve a cualquier modelo, incluso a los que no admiten rol de sistema o no tienen un formato nativo de llamadas. Los modelos que usamos sí tienen ambas cosas. Las plantillas de chat de Qwen3 y de Llama 3.2 aceptan rol de sistema y una lista de herramientas (`tools=`), cada una con su propio formato: Llama 3.2, por ejemplo, admite una sola llamada por turno. No usar el mecanismo nativo tiene un costo, que discutimos en la sección 8; para el proyecto planeamos medirlo con los modelos que lo admiten.

En la condición `tools` la interacción tiene pocos turnos, como recomienda el enunciado:

1. El modelo emite una o más llamadas: `<tool_call>{"name": "get_inventory", "arguments": {"product_id": "P01"}}</tool_call>`.
2. El harness las ejecuta y responde con un mensaje de usuario que trae los resultados (`<tool_result>...</tool_result>`) y el formato de la respuesta final. El formato llega recién en este mensaje: cuando iba en el prompt inicial, los modelos respondían sin llamar a la herramienta.
3. El modelo responde, o pide una segunda ronda. Una tercera ronda no se ejecuta y vale 0.

**Respuesta final.** Es texto libre seguido de exactamente un bloque `<answer>`, que es obligatorio. Dentro del bloque se acepta un par `clave: valor` por campo o un objeto JSON plano:

```text
<answer>
sucursal: S2
cubiertas: 7
pendientes: 1
</answer>
```

Fuera del bloque no se busca la respuesta: un JSON o unos pares `clave: valor` sin las etiquetas valen 0. La razón es que el texto libre trae cálculos intermedios (por ejemplo, `faltan: 5` antes de corregirse a `faltan: 3`), y elegir uno de ellos como respuesta sería adivinar.

### 2.4 Interfaz del curso

El entorno expone `reward(prompt: str, completion: str) -> float`:

```python
from inventory_harness.reward import InstanceStore, make_reward

reward = make_reward(InstanceStore.from_jsonl("data/eval.jsonl"))
reward(prompt, completion)  # 0.0 o 1.0
```

- `prompt` es el texto que produce `render_prompt`. Su `sha256` es la clave con que el harness encuentra la instancia y la condición en un almacén protegido. El prompt no contiene la respuesta.
- `completion` es texto plano (un solo mensaje del modelo) o la trayectoria serializada en JSON (los mensajes posteriores al prompt, incluidas las observaciones).
- Un prompt desconocido devuelve `0.0`; la función nunca lanza una excepción.

El núcleo usa solo la biblioteca estándar de Python. El contrato completo está en `docs/contrato.md`.

## 3. Dataset

> **[Revisión]** ~450 palabras. B1: explicar en §3.2 qué es un atajo y que cada fila mide cuántas veces el atajo falla.

### 3.1 Generación

Las instancias se generan por código (`src/inventory_harness/generator.py`), sin intervención manual:

1. Se fijan objetivos para la instancia: por ejemplo, si el pedido alcanza, qué sucursal gana o si habrá escasez.
2. Se propone un inventario al azar que apunte a esos objetivos.
3. Un solucionador independiente (`solver.py`) calcula la respuesta esperada. No comparte código con el generador.
4. Si la propuesta no cumple los objetivos, se reintenta.

Todo es determinista: la semilla de cada instancia se deriva con SHA-256 de la familia, la dificultad, la partición y un número. La misma configuración produce siempre el mismo dataset, así que basta versionar el código. Además, el generador produce una traza de la solución que los tests comparan con el solucionador, lo que funciona como segunda implementación.

La solicitud se redacta con una de 5 plantillas por familia (lista, relato, planilla, etc.), que no contienen valores de stock.

### 3.2 Controles contra instancias degeneradas

Una instancia es degenerada si se resuelve con un atajo, por ejemplo ignorando las reservas. El generador fija tasas objetivo y las mide comparando la solución real con la de variantes del caso. Sobre el dataset de 1.080 instancias:

| Familia | Control | Valor medido |
|---|---|---|
| Disponibilidad | El pedido alcanza | 50 % |
| Disponibilidad | Ignorar las reservas cambia la respuesta | 50 % (cambia `alcanza` en 28–38 %) |
| Selección | Hay empate entre sucursales | 13–19 % |
| Selección | Elegir por stock físico da otra sucursal | 73–83 % |
| Selección | Posición de la sucursal ganadora | Repartida entre todas las posiciones |
| Composición | Hay escasez | 81–88 % |
| Composición | Ignorar el orden de llegada cambia el resultado | 81–93 % |
| Composición hard | Se usa la cascada entre sucursales | 100 % |

Como segundo control, la línea base compara cada modelo con reglas triviales sobre las mismas instancias (sección 5.5).

### 3.3 Particiones

Hay tres particiones, `train`, `eval` y `test`, con semillas espaciadas para que no se solapen. Además, el generador calcula una huella de cada instancia y descarta duplicados entre particiones.

`test` incluye una plantilla de redacción reservada por familia, que no aparece en `train` ni en `eval` y cubre la mitad de sus instancias. Sirve para medir generalización a redacciones no vistas. `test` no se usó en ninguna medición de este informe.

El tamaño es un parámetro. La configuración estándar genera 40 instancias por celda (familia × dificultad × partición): 1.080 instancias, 360 por partición. Para la línea base y las trazas usamos 10 por celda (90 instancias por partición), por costo de cómputo.

### 3.4 Niveles de dificultad

| Familia | Easy | Medium | Hard |
|---|---|---|---|
| Disponibilidad | 1 línea | 2 líneas | 3–4 líneas |
| Selección | 1 línea, 2–3 sucursales | 2 líneas, 3 sucursales | 3–4 líneas, 4–5 sucursales |
| Composición | 2 pedidos, 1 producto, 1 sucursal | 3 pedidos, 2 productos, 1–2 sucursales | 4–5 pedidos, 3 productos, 2–3 sucursales, con cascada |

Cada instancia guarda además medidas de complejidad: registros necesarios, llamadas necesarias, operaciones aritméticas y profundidad de dependencias.

## 4. Verificador

> **[Revisión]** ~600 palabras. Abrir con el principio de diseño: no juzga el razonamiento, compara valores tipados contra `expected` y rechaza lo ambiguo (B2, B3). Una oración sobre por qué no un LLM juez, con cita (Huang et al., 2025; Zhao et al., 2025). Bajar el tono (B14).

### 4.1 Qué acepta

El verificador exige exactamente un bloque `<answer>` con todos los campos y compara cada uno con el valor esperado. La equivalencia se resuelve a nivel de valor, como pide el enunciado:

- Enteros: `3`, `3 unidades`, `tres`, `veintitrés`, `3.0`, `1.200`.
- Aritmética simple: `20-17`, `4*10`, `4 x 10`.
- Grupos y sumas etiquetadas: `cuatro filas de 10`, `20 adelante y 20 atrás`.
- Booleanos: `sí`, `no`, `true`, `verdadero`, `alcanza`, `no alcanza`.
- Sucursal: `S2`, `s2`, `sucursal S2`.
- Forma del bloque: un par por línea, varios pares en una línea o un objeto JSON plano. Las claves ignoran mayúsculas y tildes.

### 4.2 Qué rechaza

Recibe 0 toda respuesta sin bloque, con más de un bloque, con campos faltantes, desconocidos o repetidos, con valores ambiguos (`3 o 4`, `entre 3 y 4`, `S1, S2`), con texto después del bloque, o cuyo último párrafo contradice al bloque. El contenido de `<think>` se descarta antes de analizar. Cada rechazo lleva un `error_type`, que se usa para el diagnóstico y para elegir los pares DPO.

### 4.3 Defensas en la trayectoria

En la condición `tools`, `completion` podría venir falsificado, así que el verificador no confía en él:

1. **Repetición:** vuelve a ejecutar cada llamada contra el estado protegido. Si una observación registrada difiere de la real, la recompensa es 0.
2. **Evidencia:** las observaciones reales deben cubrir los registros necesarios para resolver la instancia. Una respuesta correcta sin haber pedido los datos vale 0, para no premiar la adivinación.
3. **Límite:** aplica el máximo de 2 rondas de herramientas.

### 4.4 Casos adversariales

> **[Revisión]** La tabla por categoría pasó al Anexo C. Dejar aquí una oración de resumen y aclarar que los casos los escribió el equipo (B4, B14).

`tests/adversarial_cases.py` tiene 334 casos escritos para engañar al verificador o para comprobar que acepta equivalencias (`docs/robustez_verificador.md`):

Los 8 fallos son limitaciones conocidas y documentadas. Una es un falso rechazo (`3 filas de 10 y 5 sueltas`). Las otras 7 son contradicciones en la prosa que no se detectan; en todas el bloque debe ser correcto en todos sus campos, así que ninguna premia un valor incorrecto. El repositorio tiene 1.269 tests en total.

### 4.5 Auditoría con respuestas reales

> **[Revisión]** Contarla como ciclo de corrección (B5). Decir que se hizo sobre las corridas exploratorias y que la corrección es una relajación posterior a ver resultados. El caso `33O1` contra `3301` va en el Anexo B.

Los casos anteriores los escribimos nosotros, así que no miden la variedad de respuestas de un modelo real. Por eso revisamos las respuestas de dos corridas de exploración (`docs/auditoria_verificador.md`):

- De 119 respuestas aceptadas, ninguna era un falso positivo.
- De 455 respuestas rechazadas, 9 eran falsos rechazos, por dos causas: valores entre `< >` y varios pares en una misma línea.

La segunda causa resultó mucho más frecuente en la línea base con herramientas: el modelo objetivo escribía `O1_atendidas: 33O1_pendientes: 6...`, y 56 de esas respuestas eran correctas. Corregimos el verificador para aceptar varios pares en una línea, agregamos 11 casos adversariales para ese formato y reevaluamos los rollouts guardados sin volver a correr el modelo (`scripts/reevaluate.py`). El pass@1 con herramientas del objetivo pasó de 27/90 a 37/90. Cada fila corregida conserva su veredicto original.

Este ciclo es el paso 6 que describe el enunciado: revisar trazas, corregir el verificador y volver a medir.

## 5. Línea base

> **[Revisión]** ~900 palabras; es la sección más larga y la primera a recortar. B6–B8: definir rollout, pass@k (citar Chen et al., 2021), Wilson y el tope de tokens; aclarar Qwen3-8B.

### 5.1 Modelos y configuración

| Modelo | Parámetros | Thinking | Tope de tokens | Instancias por condición |
|---|---|---|---|---|
| Llama-3.2-1B-Instruct | 1,2B | No tiene | 768 | 90 |
| Qwen3-0.6B | 0,6B | Sí | 4.096 | 70 (corrida parcial) |
| Qwen3-1.7B | 1,7B | No | 768 | 90 |
| **Qwen3-1.7B (objetivo)** | 1,7B | Sí | 4.096 | 90 |
| Qwen3-4B | 4B | No | 768 | 90 |

Todas las corridas usan la partición `eval` con 10 instancias por celda y 5 muestras por instancia, con muestreo a temperatura 0,7, `top_p` 0,95, `top_k` 50 y semilla fija. Corrieron en GPU T4 de Kaggle. En total son 4.300 rollouts.

- **pass@1** usa la primera muestra de cada instancia.
- **pass@5** cuenta las instancias con al menos un acierto entre las 5 muestras.
- Los intervalos son de Wilson al 95 %, sobre instancias.

Tres salvedades:

- La corrida de Qwen3-0.6B se cortó por el límite de tiempo de Kaggle con 70 de 90 instancias por condición, repartidas de forma pareja entre las celdas y todas con sus 5 muestras.
- Los modelos sin thinking tienen un tope de 768 tokens y los modelos con thinking de 4.096, así que la comparación entre ambos grupos no es del todo pareja. El tope afecta sobre todo a Qwen3-4B en las tareas largas (sección 5.7).
- No medimos un modelo más grande con thinking sobre `eval`. Como referencia, Qwen3-8B con thinking acierta 81/90 en la primera muestra de cada condición, pero sobre `train` y con 2 muestras (sección 7).

### 5.2 Resultados globales

| Modelo | Visible pass@1 | Visible pass@5 | Herramientas pass@1 | Herramientas pass@5 |
|---|---|---|---|---|
| Llama-3.2-1B | 0/90 (0 %; IC 0–4) | 0/90 (0 %) | 0/90 (0 %; IC 0–4) | 0/90 (0 %) |
| Qwen3-0.6B con thinking | 5/70 (7 %; IC 3–16) | 18/70 (26 %) | 9/70 (13 %; IC 7–23) | 18/70 (26 %) |
| Qwen3-1.7B sin thinking | 27/90 (30 %; IC 22–40) | 51/90 (57 %) | 22/90 (24 %; IC 17–34) | 42/90 (47 %) |
| **Qwen3-1.7B con thinking** | 58/90 (64 %; IC 54–74) | 80/90 (89 %) | 37/90 (41 %; IC 32–51) | 62/90 (69 %) |
| Qwen3-4B sin thinking | 67/90 (74 %; IC 65–82) | 71/90 (79 %) | 64/90 (71 %; IC 61–79) | 73/90 (81 %) |

- El acierto sube con el tamaño del modelo en ambas condiciones.
- El thinking le da a Qwen3-1.7B unos 34 puntos de pass@1 con datos visibles y 17 con herramientas.
- Para el objetivo, usar herramientas cuesta 23 puntos de pass@1 frente a tener los datos a la vista.
- Qwen3-4B sin thinking supera al objetivo en pass@1, pero gana poco con más intentos: tiende a acertar o fallar una instancia en todas sus muestras.

### 5.3 Resultados por nivel de dificultad

> **[Revisión]** Reemplazar las dos tablas por la Figura 2 (pass@1 y pass@5 por dificultad y modelo). Las tablas pasan al Anexo E.

Cada celda muestra pass@1 / pass@5 sobre 30 instancias (23 o 24 para Qwen3-0.6B).

**Con herramientas:**

| Modelo | Easy | Medium | Hard |
|---|---|---|---|
| Llama-3.2-1B | 0 % / 0 % | 0 % / 0 % | 0 % / 0 % |
| Qwen3-0.6B con thinking | 17 % / 50 % | 17 % / 22 % | 4 % / 4 % |
| Qwen3-1.7B sin thinking | 40 % / 77 % | 23 % / 40 % | 10 % / 23 % |
| **Qwen3-1.7B con thinking** | 63 % / 100 % | 43 % / 73 % | 17 % / 33 % |
| Qwen3-4B sin thinking | 93 % / 100 % | 83 % / 97 % | 37 % / 47 % |

**Con datos visibles:**

| Modelo | Easy | Medium | Hard |
|---|---|---|---|
| Llama-3.2-1B | 0 % / 0 % | 0 % / 0 % | 0 % / 0 % |
| Qwen3-0.6B con thinking | 12 % / 46 % | 4 % / 17 % | 4 % / 13 % |
| Qwen3-1.7B sin thinking | 63 % / 93 % | 23 % / 57 % | 3 % / 20 % |
| **Qwen3-1.7B con thinking** | 90 % / 100 % | 60 % / 93 % | 43 % / 73 % |
| Qwen3-4B sin thinking | 100 % / 100 % | 87 % / 97 % | 37 % / 40 % |

En todos los modelos que aciertan algo, el acierto baja de easy a hard. Los niveles se definieron antes de medir, a partir de la estructura de la tarea, y la línea base confirma el orden.

### 5.4 Uso de herramientas y errores del objetivo

> **[Revisión]** Dejar la tabla de resultados o moverla al Anexo E; decidir según el espacio.

De las 450 respuestas de Qwen3-1.7B con thinking en la condición `tools`:

| Resultado | Respuestas | Porcentaje |
|---|---|---|
| Correcta | 168 | 37 % |
| Valor incorrecto | 165 | 37 % |
| Campo desconocido (respuestas sin claves) | 47 | 10 % |
| Sin bloque de respuesta | 36 | 8 % |
| Valor no interpretable | 13 | 3 % |
| Pidió una tercera ronda | 12 | 3 % |
| Respondió sin los datos necesarios | 5 | 1 % |
| Otros | 4 | 1 % |

El modelo casi siempre sabe llamar: entre 84 % y 100 % de sus respuestas tienen llamadas válidas, según la celda. Eso sí, solo en 41 de 450 casos usa la etiqueta `<tool_call>`; en el resto escribe el objeto JSON sin etiqueta, que el harness también acepta. Las trazas SFT reescriben todas las llamadas en la forma con etiqueta (sección 7). Lo que falla en las tareas difíciles es pedir todos los datos necesarios. En composición hard solo 34 % de las respuestas reunió los registros requeridos, frente a 94 % en composición easy.

De los 282 fallos con herramientas, 122 son errores de cálculo con llamadas válidas y todos los datos reunidos, y 43 son respuestas sin claves con todo lo demás en regla. El resto combina datos incompletos, respuestas sin bloque y rondas de más.

Con datos visibles, 66 % de las respuestas son correctas, 27 % tienen un valor incorrecto y 4 % no traen bloque.

El costo medio del objetivo es de 2.086 tokens y 55 s por respuesta con herramientas, y 1.371 tokens y 32 s con datos visibles. Menos del 4 % de las respuestas llegó al tope de 4.096 tokens.

### 5.5 Ejemplos

> **[Revisión]** Elegir 1 o 2 ejemplos breves del Anexo F (propuesta: la debilidad de formato `S2|29|0` y la cascada ignorada).

## 6. Calibración para el modelo objetivo

El enunciado pide que las tareas no sean imposibles ni triviales para el objetivo. La evidencia es:

- **Acierto intermedio.** El pass@1 global es de 41 % con herramientas y 64 % con datos visibles.
- **Señal para RL.** pass@5 supera a pass@1 por 28 puntos con herramientas y 25 con datos visibles. El modelo ya produce respuestas correctas con cierta frecuencia, que es lo que el aprendizaje por refuerzo puede reforzar.
- **Gradiente de dificultad.** El acierto baja de easy a hard en ambas condiciones.
- **Margen de mejora.** Un modelo más grande de la misma familia llega más lejos: Qwen3-4B alcanza 71 % con herramientas sin thinking, y Qwen3-8B con thinking resuelve 170 de los 180 prompts de `train`.

Según pass@1 y pass@5, las 18 celdas del objetivo (familia × dificultad × condición) quedan así:

| Zona | Celdas | Comentario |
|---|---|---|
| Casi resueltas (pass@1 ≥ 9/10) | Los tres easy con datos visibles; disponibilidad medium visible; disponibilidad easy con herramientas | Sirven como arranque del currículo |
| Aprendibles | Las otras 11 celdas | pass@1 intermedio, o bajo con pass@5 claramente mayor |
| Sin señal | Composición hard, en ambas condiciones | 0/10 con herramientas y 2/10 con datos visibles, incluso con 5 intentos |

Dos advertencias sobre esta clasificación. Con 10 instancias por celda, los límites entre zonas son inciertos. Y una parte de los fallos con herramientas es de formato y no de razonamiento, como muestra el ejemplo de respuestas sin claves de la sección 5.7.

## 7. Datos derivados

Los datos están en `results/kaggle_qwen8b/datos_derivados_qwen8b` y se arman con `scripts/build_training_data.py`. Su `manifest.json` registra el procedimiento y los conteos.

**Modelos.** El profesor es Qwen/Qwen3-8B con thinking, un modelo abierto más grande que el objetivo. Las respuestas incorrectas provienen de Qwen/Qwen3-1.7B con thinking, que es el modelo cuyos errores se quiere corregir.

**Procedimiento:**

1. Cada modelo resuelve los 180 prompts de `train` (90 instancias en 2 condiciones) con 2 muestras, con el mismo muestreo de la línea base.
2. Cada respuesta se normaliza: las llamadas se reescriben en la forma canónica `<tool_call>{json}</tool_call>` y se descarta el texto que las acompaña. El razonamiento de `<think>` se conserva.
3. El verificador vuelve a evaluar cada respuesta normalizada contra la instancia protegida. Si la normalización cambia la recompensa, la respuesta se descarta.
4. Se excluye toda instancia de `train` con la misma huella que una de `eval` o `test`.
5. **SFT:** por prompt, una respuesta con recompensa 1 y llamadas válidas, con prioridad para el profesor.
6. **DPO:** por prompt, una respuesta correcta y una incorrecta. La incorrecta prioriza al modelo objetivo y los errores de valor, y nunca es una respuesta cortada por el tope de tokens.

**Resultado:**

| Archivo | Filas | Contenido |
|---|---|---|
| `sft.jsonl` | 170 | Trazas correctas, todas de Qwen3-8B. `messages` empieza con el prompt |
| `dpo.jsonl` | 106 | `prompt`, `chosen` y `rejected`. La elegida es siempre de Qwen3-8B; la rechazada es de Qwen3-1.7B en 105 pares |

Qwen3-8B acertó 329 de sus 360 respuestas. De las rechazadas en los pares DPO, 83 son errores de valor, 12 tienen campos desconocidos, 5 no traen bloque y 6 son de otros tipos. Por construcción, `reward(prompt, chosen)` da 1.0 y `reward(prompt, rejected)` da 0.0.

Los 10 prompts sin traza son todos de composición hard: ni el profesor los resolvió en 2 intentos. Hay menos pares DPO que trazas porque en 64 prompts ningún modelo dejó una respuesta incorrecta utilizable.

Un detalle para quien entrene con estas trazas: la plantilla de chat de Qwen3 borra el `<think>` de los mensajes anteriores del asistente. Las trazas lo conservan, y hay que aplicar la misma plantilla al entrenar para que el modelo vea el mismo contexto que al generar.

## 8. Limitaciones y trabajo futuro

> **[Revisión]** ~300 palabras. Agregar las debilidades de B13: herramienta sin `tools=`, una sola herramienta, contradicciones solo en español, sumas sin validar. Trabajo futuro: los pendientes de la sección F de la revisión que corresponda mencionar.

**Debilidades:**

- **Composición hard no da señal** al objetivo, y tampoco la resuelven Qwen3-4B (1/10 con herramientas) ni, en parte, Qwen3-8B. Puede servir como meta de largo plazo, pero no para iniciar RL.
- **Pocas instancias por celda en la línea base** (10), por costo de cómputo. Las cifras globales y por dificultad son más firmes que las de cada celda.
- **Respuestas sin claves en selección con herramientas.** En 47 de 150 respuestas el objetivo escribe `S2|29|0` en vez de los tres pares `clave: valor`, y recibe 0 aunque en 32 de ellas los valores sean correctos. Preferimos no relajar el verificador, porque aceptar valores sin clave abre la puerta a respuestas ambiguas. Es un comportamiento que SFT debería corregir.
- **Topes de tokens distintos** entre modelos con y sin thinking. Parte de los fallos de los modelos sin thinking son respuestas cortadas.
- **Un solo dominio y una sola herramienta.** La herramienta no tiene errores ni latencia, y las redacciones salen de 5 plantillas por familia.
- **La revisión de contradicciones entre prosa y bloque es conservadora**: cubre disponibilidad y selección, pero no composición.

## Referencias

> **[Revisión]** Solo las citadas en el cuerpo (protocolo, punto 3): Huang et al. (2025), Zhao et al. (2025), Chen et al. (2021) y, opcional, Reasoning Gym o AgentGym en la introducción.

## Anexos

### A. Prompt e instancia de ejemplo

> **[Revisión]** Agregar el prompt completo de una instancia en ambas condiciones.

Composición medium, condición `visible` (`eval_composition_medium_0000`, reglas abreviadas):

```text
Inventario:
Producto | Sucursal | Stock físico | Stock reservado
P01 | S1 | 44 | 5
P01 | S2 | 16 | 4
P02 | S1 | 32 | 8
P02 | S2 | 15 | 2

Solicitud:
Llegaron estos pedidos, en este orden:
- O1: 18 unidades de P01, desde S1
- O2: 19 unidades de P02 y 13 de P01, desde S1
- O3: 10 unidades de P02 y 5 de P01, desde S2
Calcula, para cada pedido, cuántas unidades se atienden y cuántas quedan pendientes, además del total pendiente.
```

La respuesta esperada es O1: 18 atendidas y 0 pendientes; O2: 32 y 0; O3: 15 y 0; total pendiente 0. Para llegar a ella hay que calcular cuatro disponibles y descontar de P01 en S1 lo que se llevó O1 antes de atender O2. La metadata de la instancia cuenta 20 operaciones.

**Qué cuenta como llamada.** Además de la forma con etiqueta, el harness acepta un objeto JSON suelto que nombre la herramienta (`{"name": "get_inventory", "arguments": {...}}`) y la forma de Python (`get_inventory("P01", location_id="S1")`). No cuenta un objeto que no nombre la herramienta, ni una llamada dentro de un mensaje que ya trae `<answer>`. Lo decidimos para que la línea base mida qué datos pide el modelo y qué hace con ellos, y no si recuerda una sintaxis: solo 41 de las 450 respuestas del objetivo con herramientas usan la etiqueta (sección 5.6).

Aceptar más formas no regala recompensa, porque los datos siguen saliendo del harness y el modelo igual tiene que calcular. Pero tiene dos costos:

- El harness interpreta intenciones: una mención en prosa, como «para esto llamaría get_inventory("P01")», se ejecuta como llamada y gasta una de las dos rondas.
- Si la recompensa es la misma con o sin etiqueta, el aprendizaje por refuerzo no empuja al modelo hacia el formato estándar. Para entrenar, la recompensa debería exigir la etiqueta.

### B. Interpretación de valores

> **[Revisión]** Escribir a partir de C1 y C2 de la revisión: gramática por tipo de valor, principio de rechazo de lo ambiguo, caso `33O1` contra `3301`. Agregar que en la línea base 0 de 1.918 aciertos usaron números en palabras, grupos o sumas.

Reasoning Gym también usa un bloque `<answer>` (Stojanovski et al., 2025), pero lo trata de otra forma. Toma el último bloque aunque haya varios, compara texto y puede dar crédito parcial. El nuestro exige exactamente un bloque, interpreta cada campo según su tipo (entero, sí/no, sucursal) y da 1 solo si todos coinciden con la respuesta calculada. La sección 4 lo explica en detalle.

### C. Casos adversariales

| Categoría | Casos | Como se esperaba |
|---|---|---|
| Equivalencias válidas y paráfrasis correctas | 49 | 48 |
| Respuestas parciales | 12 | 12 |
| Múltiples respuestas | 38 | 38 |
| Inyección de formato | 58 | 58 |
| Números fuera de contexto | 20 | 20 |
| Homoglifos | 20 | 20 |
| Desbordes numéricos | 32 | 32 |
| Copia de la salida de la herramienta | 21 | 21 |
| Inyección de instrucciones | 26 | 26 |
| Contradicciones entre prosa y bloque | 25 | 18 |
| Prosa que no debe contarse como contradicción | 33 | 33 |
| **Total** | **334** | **326** |

### D. Auditoría del verificador

> **[Revisión]** Resumen de `docs/auditoria_verificador.md`: método, clasificación de rechazos y límites.

### E. Tablas de detalle

**Modelo objetivo por familia.**

Aciertos de Qwen3-1.7B con thinking sobre 10 instancias por celda, como pass@1 / pass@5:

| Familia | Condición | Easy | Medium | Hard |
|---|---|---|---|---|
| Disponibilidad | Visible | 9 / 10 | 9 / 10 | 6 / 10 |
| Disponibilidad | Herramientas | 9 / 10 | 8 / 10 | 4 / 6 |
| Selección | Visible | 9 / 10 | 8 / 10 | 5 / 10 |
| Selección | Herramientas | 6 / 10 | 5 / 9 | 1 / 4 |
| Composición | Visible | 9 / 10 | 1 / 8 | 2 / 2 |
| Composición | Herramientas | 4 / 10 | 0 / 3 | 0 / 0 |

Composición es la familia más difícil. Con 10 instancias por celda, el intervalo de cada celda es ancho (por ejemplo, 6/10 corresponde a un IC de 31–83 %), así que estas cifras orientan y no permiten comparar celdas vecinas.

**Comparación con reglas triviales.**

Para comprobar que acertar exige leer el inventario y razonar, evaluamos reglas simples sobre las mismas instancias:

| Regla | Disponibilidad | Selección | Composición |
|---|---|---|---|
| Responder siempre que alcanza | 5/10 en cada nivel | — | — |
| Elegir la primera sucursal, sin calcular | — | 0/10, 0/10, 1/10 | — |
| Decir que todo se atiende | — | — | 3/10 en cada nivel |
| Ignorar las reservas | 5/10 en cada nivel | 0/10, 0/10, 1/10 | 3/10 en cada nivel |

El objetivo queda por sobre estas reglas en disponibilidad y selección easy y medium, aunque con 10 instancias por celda la diferencia no siempre es significativa. En composición medium y hard con herramientas queda por debajo de «todo se atiende», que acierta las instancias sin escasez.

### F. Ejemplos cualitativos

Todos los ejemplos son respuestas reales de la línea base, citadas de los `rollouts_*.jsonl`. El razonamiento dentro de `<think>` se abrevia con `[...]`.

**Fortaleza: una trayectoria correcta con herramientas.** Qwen3-1.7B con thinking, composición medium (`eval_composition_medium_0005`, muestra 3). Los pedidos son O1: 21 unidades de P01 desde S1; O2: 5 de P01 y 22 de P02 desde S2; O3: 23 de P02 desde S2. El modelo pide exactamente los tres registros que necesita:

```text
<tool_call>{"name": "get_inventory", "arguments": {"product_id": "P01", "location_id": "S1"}}</tool_call>
<tool_call>{"name": "get_inventory", "arguments": {"product_id": "P01", "location_id": "S2"}}</tool_call>
<tool_call>{"name": "get_inventory", "arguments": {"product_id": "P02", "location_id": "S2"}}</tool_call>
```

El harness responde con el stock físico y el reservado: 10 y 1 para P01 en S1, 6 y 4 para P01 en S2, 35 y 1 para P02 en S2. El modelo razona y responde:

```text
<think>
[...]
O1: 21 units of P01. Available is 9. Attended 9, pendientes 12.
O2: 5 P01 (available 2, attended 2, pendientes 3) and 22 P02 (available 34, attended 22, pendientes 0). So O2_pendientes is 3.
O3: 23 P02. Available is 34 - 22 = 12. Attended 12, pendientes 11.
Total pendientes: 12 + 3 + 11 = 26.
[...]
</think>

<answer>O1_atendidas: 9,O1_pendientes: 12,O2_atendidas: 24,O2_pendientes: 3,O3_atendidas: 12,O3_pendientes: 11,total_pendientes: 26</answer>
```

Resta las reservas, descuenta a O3 lo que ya consumió O2 y acierta los siete campos. El bloque viene en una sola línea, separado por comas, y el verificador lo acepta.

**Debilidad de razonamiento: ignora la cascada.** Qwen3-1.7B con thinking, composición hard con datos visibles (`eval_composition_hard_0007`, muestra 3). El último pedido dice: «O5, que pide 16 unidades de P03 desde S1 y, si no alcanza, desde S2». En S1 hay 10 disponibles, y en S2 queda 1 después de los pedidos anteriores. El modelo razona:

```text
Finally, O5: Requests 16 units of P03 from S1. S1's P03 stock is 20, reserved 10, available 10.
Order is 16, so available is 10, which is less than 16. So they take 10, pendientes 16 - 10 = 6.
```

Responde 10 atendidas y 6 pendientes para O5, cuando lo correcto es 11 y 5. Acierta los otros cuatro pedidos, pero trata un pedido en cascada como si usara una sola sucursal. Es el error típico de composición hard: una regla del prompt que se aplica mal en un paso de una cadena larga.

**Debilidad de formato: respuestas sin claves.** Qwen3-1.7B con thinking, selección easy con herramientas (`eval_selection_easy_0000`, muestra 2). La solicitud pide comparar S1 y S2 para un pedido de 29 unidades de P02, y la respuesta esperada es S2, 29 cubiertas y 0 pendientes:

```text
<think>
[...] For S1, the available is 20, so they can handle 20 units, leaving 9 pending. For S2, available
is 29, so they handle all 29, leaving 0 pending. Since S2 has a higher coverage, that's the one chosen.
</think>

<answer>S2|29|0</answer>
```

El razonamiento y los tres valores son correctos, pero el bloque no trae las claves y recibe 0 (`unknown_field`). Esto ocurre en 47 de las 150 respuestas del objetivo en selección con herramientas, y en ninguna otra familia. Leídas por posición, 32 de esas 47 tendrían los tres valores correctos.

**Equivalencia aceptada: aritmética en los valores.** Qwen3-8B con thinking, composición medium con herramientas (`train_composition_medium_0007`, muestra 0). Lo esperado para O3 es 8 atendidas y 18 pendientes, y el modelo deja las sumas por línea de pedido sin resolver:

```text
<answer>
O1_atendidas: 4
O1_pendientes: 0
O2_atendidas: 4
O2_pendientes: 5
O3_atendidas: 2+6
O3_pendientes: 1+17
total_pendientes: 23
</answer>
```

El verificador evalúa `2+6` como 8 y `1+17` como 18, y da la respuesta por correcta. Otra forma aceptada, del modelo objetivo: `<answer>alcanza: no, faltan: 2</answer>`. En la línea base, 57 de las 464 respuestas correctas del objetivo no están en la forma canónica de un par por línea.

**Llama-3.2-1B: no sigue el formato.** Composición easy con datos visibles (`eval_composition_easy_0007`, muestra 4). Hay 19 unidades disponibles de P01 (27 de stock físico y 8 reservadas), O1 pide 12 y O2 pide 6, así que ambos se atienden completos. La respuesta completa del modelo es:

```text
O1_atendidas: 8
O1_pendientes: 9
O2_atendidas: 8
O2_pendientes: 4
total_pendientes: 13
```

Escribe los pares sin las etiquetas `<answer>`, y además los valores son incorrectos: usa las 8 unidades reservadas como si fueran las atendidas. De sus 900 respuestas, 699 no traen bloque. El formato no es su único problema: en una lectura indulgente, que toma sus pares finales como si llevaran etiquetas, acertaría solo 4 de 900.

**Qwen3-4B sin thinking: se queda sin tokens en las tareas largas.** En selección hard con datos visibles (`eval_selection_hard_0000`, muestra 0) tabula la cobertura de 4 sucursales para 4 productos, llega al tope de 768 tokens en el encabezado «Comparación:» y nunca emite el bloque. Le pasa en 142 de sus 900 respuestas, todas en selección hard, composición hard y composición medium, y todas con recompensa 0. Eso explica 142 de sus 269 fallos, así que sus cifras en hard subestiman lo que el modelo haría con más tokens.

> **[Revisión]** Párrafo sobre Llama que estaba en la §2.3; integrarlo con el ejemplo de Llama de arriba:

Exigir el bloque es la causa de rechazo más frecuente de Llama-3.2-1B: 699 de sus 900 respuestas no lo traen. Pero el formato no explica su resultado. Si se buscan las claves en cualquier parte del texto, sin exigir el bloque, solo 211 de los 1.460 valores que escribe son correctos (14 %), frente a 1.500 de 3.033 (49 %) de Qwen3-1.7B sin thinking. El problema principal de Llama es el cálculo (sección 5.7).

### G. Reproducción

```bash
git clone https://github.com/tariztia/harness-inventarios.git
cd harness-inventarios
uv run --group dev pytest -q                                   # 1.269 tests
uv run python scripts/generate_dataset.py --n-per-cell 40 --base-seed 2026 --out data
uv run python scripts/robustness_report.py                     # regenera docs/robustez_verificador.md
uv run python scripts/analyze_results.py results/kaggle_qwen17b/linea_base_qwen17b
```

| Qué | Dónde |
|---|---|
| Línea base del objetivo | `results/kaggle_qwen17b/linea_base_qwen17b` |
| Línea base de los otros modelos | `results/kaggle_otros_modelos` |
| Respuestas del profesor | `results/kaggle_qwen8b/trazas_qwen8b` |
| Datos SFT y DPO | `results/kaggle_qwen8b/datos_derivados_qwen8b` |
| Cuadernos para correr en Kaggle | `notebooks/`, con la guía en `docs/guia_kaggle.md` |

Cada carpeta de resultados trae los rollouts completos (`rollouts_*.jsonl`), un `report.md` con el detalle por celda y un `manifest.json` con la configuración y la versión del código.

```bash
python scripts/generate_dataset.py --n-per-cell 40 --base-seed 2026 --out data
```
