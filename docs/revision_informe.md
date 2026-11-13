# Revisión del informe (documento de trabajo)

Notas para corregir `docs/informe.md` antes de entregarlo. No es parte de la entrega. Se completa a medida que encontramos cosas; recién al final se aplica al informe. El detalle técnico y las fuentes están en `docs/analisis_verificador.md`.

Estados: **pendiente**, **por decidir** (falta una decisión del equipo), **listo**.

## A. Bloqueantes para entregar hoy (13 de noviembre, Canvas)

| # | Qué | Estado |
|---|---|---|
| A1 | `Integrantes: _(completar)_` en la línea 5 | No urgente: el archivo final se arma aparte |
| A2 | El repo `tariztia/harness-inventarios` está **privado**. El enunciado dice que el entorno "será compartido con el resto del curso" (política de apertura) y el informe cita el repo como fuente. Hacerlo público, o al menos dar acceso al equipo docente | Decidido (E): se publica un repo limpio |
| A3 | Formato para Canvas: el informe está en Markdown. Exportarlo a PDF y adjuntar el link al repo (y, si se quiere, `dist/inventory_harness_colab.zip`) | pendiente |
| A4 | La carpeta vieja `results/kaggle_qwen17b/datos_derivados_qwen17b/` tiene otro `sft.jsonl` y otro `dpo.jsonl`. Los oficiales son los de `kaggle_qwen8b`. Borrarla o aclararla en el README | Decidido (E): queda fuera del repo limpio |
| A5 | **El informe no cita ningún trabajo**, ni siquiera las cuatro referencias del enunciado. Agregar una sección corta de trabajo relacionado y referencias, citando cada paper donde justifica una decisión (lista en `analisis_verificador.md` §2 y §6) | pendiente |

## B. Cambios al informe

| # | Sección | Problema | Propuesta | Estado |
|---|---|---|---|---|
| B1 | §3.2 | Muestra la tabla de controles sin explicar la lógica | Explicar qué es un atajo (responder siempre "alcanza", ignorar reservas, elegir la primera sucursal) y que cada fila mide **cuántas veces ese atajo falla**: se resuelve una versión trampa de la instancia y se compara con la respuesta real | pendiente |
| B2 | §4 | No explica qué hace el verificador ni cómo. Falta la idea central: **no juzga el razonamiento, compara valores contra `expected`**, que `solver.py` calculó al generar la instancia | Abrir §4 con un diagrama del flujo (búsqueda por sha256 → defensas de trayectoria → `<think>` → bloque → pares → valores tipados → comparación → contradicciones) y un ejemplo recorrido de punta a punta | pendiente |
| B3 | §4.1 | Lista equivalencias sin decir cómo se reconocen | Explicar que es una **gramática por tipo de valor** (entero, booleano, sucursal) escrita a mano, sin LLM ni `eval()`, y su principio: si hay más de una lectura posible, se rechaza. Ver C1 | pendiente |
| B4 | §4.4 | La tabla de categorías no dice qué es cada una ni qué significa "Como se esperaba" | Una fila de ejemplo por categoría. Aclarar que un acierto es "aceptó lo que debía aceptar y rechazó lo que debía rechazar", y que ninguno de los 8 fallos premia un valor incorrecto | pendiente |
| B5 | §4.5 | Se lee como datos sueltos | Contarla como un ciclo: casos inventados → revisión de respuestas reales → falso rechazo encontrado → corrección → reevaluación (27/90 → 37/90). Incluir por qué la corrección no abre ambigüedad (C2). Decir que la auditoría se hizo sobre las corridas exploratorias, no sobre la línea base final | pendiente |
| B6 | §5.1 | No define rollout, pass@k ni el intervalo de Wilson | Definir: rollout = un intento completo calificado con 0/1; pass@1 = acierta en la primera muestra; pass@5 = acierta en al menos una de 5; Wilson = IC 95 % para una proporción, robusto con n chico. Decir que **el IC solo se reporta para pass@1** | pendiente |
| B7 | §5.1 | No dice qué incluye el tope de tokens | Aclarar que es `max_new_tokens` **por generación, con el `<think>` incluido**, y que en `tools` cada turno tiene su propio tope (hasta 3 turnos) | pendiente |
| B8 | §5.1 y §6 | La mención de Qwen3-8B confunde ("81/90 en la primera muestra de cada condición") | Dejarlo solo en §7 como profesor, o en nota: corrió sobre `train` con 2 muestras, así que no es comparable con la tabla | pendiente |
| B9 | §5.4 | "9 / 10" significa pass@1 = 9 y pass@5 = 10, pero se lee como "9 de 10". "Composición hard 2 / 2" parece 100 % | Separar en columnas pass@1 y pass@5, con el total (/10) en el encabezado | pendiente |
| B10 | §5 en general | Muchas tablas, ningún gráfico y sin conclusión al inicio de cada subsección | Un gráfico de pass@1/pass@5 por dificultad y modelo; empezar cada subsección con una frase de lo que muestra; mover tablas de detalle a un anexo | pendiente |
| B11 | §2.3 o §4.2 | No queda claro qué formato de respuesta es obligatorio | Decir explícitamente: la respuesta final **exige** un bloque `<answer>`. Dentro del bloque se acepta `clave: valor` o un objeto JSON. Un JSON o pares sin etiquetas valen 0 (`no_answer_block`). Razón: sin etiqueta habría que buscar la respuesta en texto libre, donde aparecen cálculos intermedios (`faltan: 5` antes de `faltan: 3`). Reasoning Gym también exige `<answer>`. Ver C4 | listo (§2.3) |
| B12 | §2.3 y §5.6 | La aceptación de llamadas sin etiqueta aparece al pasar en §5.6 y no se justifica | Explicar la decisión y su alcance (C5): se aceptan `<tool_call>`, JSON suelto que nombre la herramienta y la forma Python, para que la línea base mida **qué datos pide el modelo y qué hace con ellos**, no la sintaxis. Solo 41 de 450 respuestas usan la etiqueta. Reconocer el riesgo: una mención en prosa (`llamaría get_inventory("P01")`) se ejecuta como llamada. Decir que en entrenamiento la recompensa debe exigir la etiqueta | listo (§2.3) |
| B13 | §8 | Faltan debilidades | Agregar: (1) la herramienta se describe en texto en el prompt y no con el mecanismo nativo (`tools=` en el chat template), que tienen **tanto Qwen3 como Llama 3.2** (C6, C7), lo que puede explicar el bajo uso de la etiqueta; (2) una sola herramienta, así que no se mide elegir entre varias; (3) la revisión de contradicciones solo entiende español y no se activó en las corridas reales (C3); (4) las etiquetas de una suma no se validan contra la instancia (C1) | pendiente |
| B14 | §1, §4 y §8 | El tono sobre la robustez promete más de lo medido | Cambiar "el verificador resiste las trampas" por "resiste las trampas previstas por el equipo (326 de 334 casos que escribimos nosotros)"; decir que en la línea base los modelos casi no usaron las equivalencias (0 de 1.918 aciertos usaron números en palabras, grupos o sumas) y que el reward hacking real se verá al entrenar con RL | pendiente |

## C. Análisis crítico del verificador

**C1. ¿El parser de valores es "hardcodeado"?** Sí, son reglas escritas a mano: `numbers_es.py` (~640 líneas) y `verifier.py` (~570). No es una lista de respuestas, sino una gramática por tipo de valor:

- **Entero:** dígitos, palabras hasta 999.999 (`veintitrés`), aritmética `+ - * x ( )` evaluada sin `eval()`, grupos (`4 filas de 10`), sumas etiquetadas (`20 adelante y 20 atrás`), glosas (`3 (tres)`) e igualdades (`20-17 = 3`).
- **Booleano:** un conjunto cerrado de formas (`sí`, `no`, `alcanza`, `no alcanza`, `true`...).
- **Sucursal:** `S<n>`, con o sin `sucursal`.
- **Principio rector:** si el valor admite más de una lectura, se rechaza. Hay una lista de palabras de duda (`o`, `entre`, `unos`, `aprox`...) y nunca se "extrae el primer número". Probado: `3 o 4` → `ambiguous_value`; `unos 3` → `ambiguous_value`; `3 (cuatro)` → `ambiguous_value`; `3.5` → `invalid_value`.

Por qué es viable sin un LLM juez: **el contrato fija las claves y los tipos**, así que el espacio de respuestas es chico y cerrado. El parser solo interpreta valores; no busca dónde está la respuesta en texto libre.

Argumentos a favor, que el informe debería explicitar:
- Es determinista y barato. En GRPO se califican miles de rollouts, y un juez agrega una pasada de modelo por cada uno.
- No se puede convencer con prosa. Un juez LLM es vulnerable a la inyección de instrucciones (Zhao et al., 2025), justo una de las categorías adversariales.
- El curso pide recompensa verificable, y es la práctica de Reasoning Gym, Tülu 3 y DeepSeek-R1.

Límites reales, que el informe debería admitir:
- Una familia nueva con los mismos tipos solo necesita sus claves. Un **tipo nuevo** (fechas, texto libre) exige otro parser.
- Las equivalencias son las que alguien previó. Una forma no prevista se rechaza (falso rechazo, nunca falso positivo); por eso existe la auditoría §4.5.
- **Sumas etiquetadas** (`_parse_labelled`): suman "número + etiqueta" sin validar la etiqueta contra la instancia, así que `20 gatos y 20 perros` vale 40. **No es un vector de reward hacking:** la suma debe ser exactamente el valor correcto, así que no da nada que no dé escribir `40`, y el modelo no ve el valor esperado. El único riesgo es acertar por casualidad con un desglose sin sentido, que también pasa con un número suelto. Es complejidad sin uso (0 de 1.918 aciertos), no un agujero.

**C2. Pares pegados en una línea (`O1_atendidas: 33O1_pendientes: 6`). ¿Podría ser 3301?** No, pero la razón hay que explicarla en el informe. El corte no se hace en cualquier punto: solo donde aparece **una clave literal del contrato seguida de `:`** (`O<n>_atendidas:`, `O<n>_pendientes:`, `total_pendientes:`, etc.), y solo si la línea empieza con una clave. Probado:

| Entrada | Resultado |
|---|---|
| `O1_atendidas: 33O1_pendientes: 6total_pendientes: 6` (letra O) | Se separa: 33 / 6 / 6 |
| `O1_atendidas: 3301_pendientes: 6 ...` (dígito cero) | No se separa → `missing_field`, recompensa 0 |
| `O1_atendidas: 3301` en su propia línea | Se lee 3301 |
| Clave repetida en la línea | `duplicate_field` |
| Texto antes de la primera clave | `unknown_field` |

Que el 3301 lo escribió el modelo con la letra "O" es imposible de confundir: `3301` no contiene ninguna clave, y "O1_pendientes:" no es un número. Lo que se puede discutir es otra cosa, y conviene decirla en el informe:

- **Es un problema del modelo, y se relajó el verificador después de ver la línea base.** Eso mueve la meta. La justificación es que la respuesta tiene una sola lectura posible. El mismo criterio explica por qué **no** se acepta `S2|29|0` (sin claves): ahí el significado depende de la posición.
- La transparencia ya está: cada fila corregida guarda `verdict_anterior`, y el informe reporta el antes y el después (27 → 37). Hay que mantenerlo explícito.
- Para RL, aceptar el formato pegado significa que el entrenamiento **no** va a corregir esa costumbre. Si se quiere un formato limpio, eso le toca a SFT, no a la recompensa.

**C3. La revisión de contradicciones solo entiende español.** `_find_contradiction` usa patrones en español. Probado con un bloque `alcanza: sí`:

- Prosa "No alcanza el stock para el pedido." → se detecta la contradicción.
- Prosa "The stock is not enough, the order cannot be fulfilled." → no se detecta.

En la línea base del objetivo, 54 de 900 respuestas tienen prosa fuera de `<think>`, y 30 de ellas están en inglés. La auditoría del compañero agrega que **no se activó en ninguno de los 1.080 rollouts exploratorios**: con thinking, todo el razonamiento queda dentro de `<think>` y no hay prosa que revisar. El impacto es bajo, porque igual se exige un bloque correcto, pero es la parte más frágil y ad hoc del verificador (7 de los 8 fallos adversariales están ahí).

**C4. Bloque `<answer>` obligatorio; JSON solo dentro.** Probado:

| Respuesta final | Resultado |
|---|---|
| `<answer>` con `alcanza: no` / `faltan: 3` | Correcta |
| `<answer>{"alcanza": "no", "faltan": 3}</answer>` | Correcta |
| `{"alcanza": "no", "faltan": 3}` sin etiquetas | `no_answer_block`, vale 0 |
| `alcanza: no` / `faltan: 3` sin etiquetas | `no_answer_block`, vale 0 |

Es la razón principal del 0 de Llama: 699 de sus 900 respuestas no traen bloque.

**C5. Llamadas a la herramienta: flexibles a propósito.** `tools.py` reconoce como llamada:

| Lo que escribe el modelo | ¿Cuenta? |
|---|---|
| `<tool_call>{"name": "get_inventory", ...}</tool_call>` | Sí |
| `{"name": "get_inventory", "arguments": {...}}` suelto | Sí |
| `get_inventory("P01", location_id="S1")` | Sí |
| `{"product_id": "P01"}` (no nombra la herramienta) | No |
| Cualquier cosa en un mensaje con `<answer>` | No: es la respuesta final |
| Una `<tool_call>` sin cierre (Llama) | Sí, si el JSON está completo |

- **Por qué no regala recompensa:** una llamada solo pide datos. El harness devuelve el stock real y el modelo igual debe calcular y responder bien.
- **Problema 1:** el harness interpreta la intención. Una mención en prosa (`para esto llamaría get_inventory("P01")`) se ejecuta y gasta una de las 2 rondas.
- **Problema 2:** si la recompensa es igual con o sin etiqueta, RL nunca empuja hacia el formato estándar, que es lo que permitiría reutilizar al modelo con otras herramientas.

**C6. La herramienta no se le pasa a Qwen por su mecanismo nativo.** El prompt describe `get_inventory` en texto, con un ejemplo de `<tool_call>`, y `backends.py` aplica el chat template **sin** el parámetro `tools=`. Qwen3 fue entrenado para llamar herramientas con su formato nativo, que se activa con `tools=`. No es un bug: fue una decisión para que el mismo prompt funcionara en todos los modelos (un solo mensaje de usuario, porque no todos tienen rol de sistema). Pero tiene un costo probable, **no verificado**: podría explicar por qué Qwen casi no escribe la etiqueta y por qué falla más con herramientas que con datos visibles. Va en debilidades (B13) y como corrida pendiente (F2).

**C7. "No todos los modelos tienen rol de sistema" es cierto en general, pero no para los modelos que usamos.** Revisado en las plantillas oficiales (`tokenizer_config.json` en Hugging Face, 13-11): Llama-3.2-1B-Instruct y Qwen3-1.7B aceptan rol `system` **y** `tools=`. La frase viene de `docs/contrato.md`. Fue una decisión de portabilidad, no una limitación de nuestros modelos. Detalle importante para F2: el formato nativo de Llama 3.2 es distinto al de Qwen. Usa `{"name": ..., "parameters": ...}` (no `arguments`) y su plantilla dice "This model only supports single tool-calls at once". Con un máximo de 2 rondas, en modo nativo Llama no podría reunir los datos de las tareas hard. Con nuestro formato en texto, Llama sí llama bien: 364 de 450 respuestas tienen llamadas válidas.

**C8. El problema de Llama es de cálculo, no solo de formato.** Medido con `scripts/lectura_indulgente.py`, que busca cada clave en cualquier parte del texto, sin exigir `<answer>`:

| | Llama-3.2-1B | Qwen3-1.7B sin thinking |
|---|---|---|
| Valores correctos, entre los campos escritos | 211 / 1.460 (14 %) | 1.500 / 3.033 (49 %) |
| `alcanza` correcto | 43 / 129 (33 %, bajo el azar) | 187 / 280 (67 %) |
| Respuestas completas correctas | 6 / 900 | 280 / 900 |

En la instancia más fácil (`eval_availability_easy_0000`: pide 27, físico 29, reservado 1) Llama **suma** las reservas (29 + 1 = 30), copia el marcador `N` del formato o mezcla sucursales. Los 6 aciertos completos no coinciden con los 4 de §5.7, que usa un criterio distinto (solo la última línea `clave: valor`). **No se cambia el 4**: en §2.3 se usa la cifra por campo.

## D. Preguntas abiertas

- ¿Vale la pena mantener la revisión de contradicciones, o declararla un extra conservador y no un pilar de la robustez?
- ¿Se agrega algún caso adversarial en inglés antes de entregar, o solo se documenta?
- ¿Da el tiempo para una corrida corta con `tools=` antes de entregar (F2), o queda para el proyecto?

## E. Decisiones tomadas

| Fecha | Decisión | Razón |
|---|---|---|
| 13-11 | **No cambiar código del verificador antes de la entrega.** Solo se corrige el informe | Falta de tiempo; cualquier cambio obliga a reevaluar la línea base |
| 13-11 | No usar un LLM juez | La respuesta se puede calcular; costo por rollout; los jueces se hackean (Huang et al., 2025; Zhao et al., 2025). Se justifica en el informe con citas |
| 13-11 | La aritmética en el valor (`2+6`) sigue valiendo 1. **No se menciona en el informe** | El enunciado pide aceptar formas equivalentes; pasó 1 vez en 1.918 aciertos. Queda para el proyecto (F3) |
| 13-11 | Las sumas etiquetadas no son un riesgo de reward hacking. Solo se menciona como limitación | La suma debe ser exacta y el modelo no ve el valor esperado (C1) |
| 13-11 | La flexibilidad con las llamadas se mantiene **para la línea base** y se declara en el informe con su riesgo. **En entrenamiento, la recompensa debe exigir `<tool_call>`** | La línea base debe medir el uso de la herramienta y no la sintaxis; el entrenamiento debe enseñar el formato estándar para que el modelo sea reutilizable (C5) |
| 13-11 | La respuesta final sigue exigiendo `<answer>` | Sin etiqueta habría que buscar la respuesta en texto libre (C4) |
| 13-11 | Pasar la herramienta sin `tools=` se reporta como debilidad del diseño | Posible causa del bajo uso de la etiqueta, no verificada (C6) |
| 13-11 | `notebooks/tools_nativo_colab.ipynb` **no se menciona en el informe** hasta tener el resultado | Todavía no se corre |
| 13-11 | Se publica un **repo limpio**, solo con los archivos finales, en vez de hacer público `tariztia/harness-inventarios` (A2). El link del informe debe apuntar a ese repo | Este repo tiene corridas exploratorias, versiones provisorias y documentos de trabajo |
| 13-11 | `results/kaggle_qwen17b/datos_derivados_qwen17b` queda fuera del repo limpio (A4) | Es una versión provisoria (118 SFT, 53 DPO) armada solo con respuestas de Qwen3-1.7B, sin profesor; la reemplaza `kaggle_qwen8b` |
| 13-11 | Integrantes: no es urgente (A1) | El archivo final se arma aparte |
| 13-11 | El informe dice que el prompt sin rol de sistema y sin `tools=` es una decisión de **portabilidad**, y que los modelos usados sí tienen ambas cosas. Para el proyecto se mide el mecanismo nativo en los modelos que lo admiten (F2) | La frase anterior ("no todos los modelos tienen rol de sistema") sugería una limitación que nuestros modelos no tienen (C7) |
| 13-11 | La comparación con Reasoning Gym en §2.3 se escribe como contraste, no como "también lo hacemos" | Usan el último bloque, comparan texto y dan crédito parcial; nosotros exigimos un bloque, tipamos valores y damos 0/1 |

## F. Pendientes para el proyecto (no para este informe)

| # | Qué | Por qué |
|---|---|---|
| F1 | Recompensa estricta con `<tool_call>` después del SFT, o una recompensa de formato aparte, y comparar contra la flexible | Que RL no desaprenda el formato. Comparar flexible contra estricta responde "¿aparece reward hacking y bajo qué condiciones?" del enunciado del proyecto |
| F2 | Corrida de Qwen3-1.7B con la herramienta pasada por `tools=` en el chat template (esquema JSON), comparando la tasa de uso de `<tool_call>` y el pass@1 con herramientas contra la línea base | Medir el costo de C6. **No es solo agregar `tools=`:** el resultado vuelve como mensaje de rol `tool` (envuelto en `<tool_response>`), y `reward.py` hoy solo acepta roles `assistant`/`user` y exige que la observación sea idéntica a `render_tool_reply`, que además trae las instrucciones del `<answer>`. Hay que adaptar `reward.py`, `rollout.py`, `prompts.py`, las trazas SFT y los tests. **Prueba rápida lista:** `notebooks/tools_nativo_colab.ipynb` (18 instancias, 1 muestra) genera en formato nativo y califica traduciendo al formato del harness, sin tocar el harness. Comprobado el 13-11: `<tool_call>` no es token especial en Qwen3, así que el 41/450 de la línea base es real. Para Llama 3.2 el formato nativo es otro (`parameters`, una llamada por turno; C7) |
| F3 | Recompensa de exactitud más un término pequeño de formato (valor canónico, `8` en vez de `2+6`) | Separar "¿es correcto?" de "¿está bien escrito?", como Open-R1 separa `accuracy_reward` y `format_reward` |
| F4 | Recompensa parcial por campo para composición hard | Hoy da 0 casi siempre y no hay señal para RL. El enunciado del proyecto lista "recompensas parciales" como mejora posible |
| F5 | Varias herramientas en el prompt, incluida alguna irrelevante (distractora), descritas como lista con lo que devuelve cada una | Medir si el modelo elige la herramienta correcta, no solo si llama bien la única que hay. Es la extensión más barata hacia uso de herramientas en general; ver si cabe en el alcance |
| F6 | Auditoría manual de trazas "exitosas" de la línea base completa, al estilo SWE-Bench+ | La pide el enunciado del proyecto; extiende `docs/auditoria_verificador.md`, que cubrió solo las corridas exploratorias |
