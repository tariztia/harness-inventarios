# Propuesta preliminar para el Desafío de Investigación IIC-3694

**Tema:** razonamiento composicional sobre inventarios mediante herramientas y recompensas verificables  
**Fecha:** 3 de noviembre de 2026  
**Estado:** propuesta para validación grupal; **no se ha implementado ni evaluado**.

## 0. Resumen ejecutivo

**Propuesta.** Construir un entorno reproducible que genere consultas en lenguaje natural sobre inventarios sintéticos. Un LLM pequeño (aproximadamente 1–2 mil millones de parámetros) recibe la solicitud, consulta una o varias herramientas ejecutables y responde. Un verificador independiente calcula si el resultado final es correcto. El interés no es enseñar llamadas de función arbitrarias, sino medir y eventualmente mejorar la **composición de operaciones sobre datos estructurados**.

**Versión inicial (MVP):** inventario general, una herramienta `get_inventory`, cuatro tipos de tareas y máximo una o dos interacciones del modelo con herramientas, según el contrato que se defina. No incorporar todavía preguntas de aclaración al usuario ni extender el caso a dominios específicos. Las herramientas no deben entregar directamente la decisión solicitada: deben proporcionar datos que el modelo necesite combinar y razonar.

**Decisión pendiente:** no asumir que el tema es suficientemente difícil para un modelo de 1–2B; hay que ejecutar un piloto y medir `pass@1`, `pass@5`, acierto con/sin herramientas y errores por tipo de problema.

**Importante:** el desafío actual solicita construir harness, dataset, trazas para SFT, pares para DPO y línea base; el entrenamiento del modelo y comparación de estrategias corresponden al proyecto posterior, conforme a *DesafioInvestigacion-2026.pdf*, pp. 1–3.

## 1. Motivación e hipótesis

### Motivación
Los agentes empresariales deben recuperar registros, filtrar, comparar, agregar y combinar información para contestar preguntas operativas. Una llamada sintácticamente válida a una herramienta no garantiza que se elija el dato correcto ni que se produzca una respuesta correcta.

### Pregunta de investigación provisional
> ¿Pueden tareas sintéticas, procedurales y verificables de inventario calibrarse para detectar una brecha aprendible en modelos de 1–2B, y servir luego para mejorar su capacidad de resolver consultas composicionales usando herramientas?

**Hipótesis (no resultado):** las tareas simples de disponibilidad podrían resultar fáciles; los problemas con varias entidades, filtros y agregaciones pueden producir una caída gradual de rendimiento y, potencialmente, una zona aprovechable para post-training. Se requiere evidencia experimental antes de aceptar la hipótesis.

**Qué NO se pretende demostrar ahora:** que ya se encontró una debilidad, que las herramientas por sí mismas incrementan el razonamiento, o que el aprendizaje transferirá a entornos reales.

## 2. Alcance y exclusiones

### Dentro del alcance inicial
- Datos de inventarios **sintéticos** con stock físico, reservas, productos, sucursales y pedidos.
- Preguntas generadas con familias de operaciones parametrizadas.
- Herramientas **reales, ejecutables** en Python, que consultan el estado sintético de cada instancia.
- Verificador separado del modelo y de las respuestas de la herramienta.
- Particiones `train/eval/test`, niveles de dificultad, líneas base y revisión de robustez.

### Fuera de alcance inicial
- Aclaraciones interactivas al usuario cuando falta información.
- Acciones irreversibles sobre sistemas reales.
- Extensión a un dominio sanitario u otro dominio aplicado: se retira de esta propuesta.
- Agentes de muchos turnos, búsquedas web y arquitectura empresarial completa.
- Comprometerse con TRL, verl o cualquier framework de RL antes de revisar las reglas del curso.

## 3. Diseño del entorno (harness)

**Componentes:**

1. **Generador procedural**: crea el estado del inventario, la consulta, el programa de referencia y los metadatos (familia, dificultad, semilla).
2. **Preparador de prompts**: explica reglas de negocio y herramientas disponibles, serializa la solicitud.
3. **Herramientas**: funciones Python sobre la instancia actual, con entradas y salidas estructuradas.
4. **Ejecutor / controlador de rollouts**: recibe la llamada del modelo, valida el nombre y argumentos, ejecuta la herramienta y devuelve la observación; impone límite de turnos.
5. **Parser**: extrae llamadas a herramientas y procesa la respuesta final. Su tratamiento de lenguaje natural libre versus un formato estructurado es una **decisión pendiente**, sujeta a validación con el equipo docente.
6. **Verificador independiente**: evalúa el estado original y los requisitos de la tarea, comprueba que la respuesta final satisface la solicitud completa y devuelve recompensa y diagnósticos. **Pendiente:** determinar cómo aceptar paráfrasis y detectar afirmaciones contradictorias en lenguaje natural.
7. **Adaptador del curso**: expone `reward(prompt, completion) -> float` según la interfaz común exigida. **Punto por confirmar:** si `completion` incluirá la trayectoria completa con llamadas/observaciones o solo la respuesta final; definir la forma de asociar el `prompt` con la instancia sin filtrar respuestas.

**Flujo:** instancia → prompt → modelo → llamada → ejecución de función → observación → respuesta final → verificador → recompensa. Durante SFT se guardan trazas correctas; durante RL futuro el algoritmo utilizaría las recompensas y tokens generados para actualizar el modelo. El harness **no es** el optimizador ni modifica pesos por sí solo.

### Herramientas: mantener ambas líneas de diseño abiertas

**Propuesta original (preferida como punto de partida): consultas de inventario y razonamiento del modelo.**

- Herramienta unificada `get_inventory(product_id, location_id=None)` → `physical_stock`, `reserved_stock` y otros datos básicos de un registro. Como alternativa de granularidad, separar `get_stock` y `get_reserved_units` o incorporar `get_pending_orders` y herramientas por sucursal.
- El modelo selecciona las consultas, interpreta las observaciones y **combina por sí mismo** los datos para resolver problemas de disponibilidad, selección y agregación. Las herramientas **no** devuelven `can_fulfill`, la sucursal óptima ni el déficit final si esas son precisamente las decisiones que se buscan evaluar.
- Puede hacer falta una variante por lotes (`list_inventory` o consulta filtrada) para que una tarea sobre múltiples registros sea factible en pocos turnos.

**Otra opción por evaluar: operaciones ejecutables propuestas por el modelo, análogas a generar SQL.**

- El modelo genera una consulta o procedimiento estructurado (por ejemplo, filtros, agrupaciones y comparaciones), y el harness lo ejecuta sobre el inventario sintético.
- Aquí se evalúa con mayor énfasis si el modelo **construye correctamente la operación** para resolver la solicitud, además de si comunica bien el resultado.
- No confundir este enfoque con proporcionar una función `resolve_order()` que entregue toda la solución: las operaciones deben ser suficientemente generales y la selección/composición corresponde al modelo.

**Decisión pendiente:** comparar ambas opciones en un piloto. La primera se conserva como propuesta inicial; la segunda queda explícitamente como alternativa, no sustitución. Más herramientas o más llamadas no implican automáticamente mayor complejidad de razonamiento.

Las funciones consultan una base sintética en memoria, SQLite o archivos y son **herramientas reales ejecutables**. Debe existir aislamiento de estado por instancia/rollout.

### Riesgo de trivialidad de las tareas

Preguntas como «¿cuál es el stock disponible de A?» pueden medir principalmente recuperación o copia de un resultado. Para estudiar razonamiento composicional, incluir tareas donde el modelo deba relacionar **varios pedidos, ubicaciones, reservas, filtros y reglas de asignación**. La complejidad real se decidirá según la línea base, no solo por intuición. Comparar además el rendimiento cuando los mismos datos están visibles directamente en el prompt frente a cuando deben recuperarse mediante herramientas.

## 4. Dataset y generador

### Esquema mínimo por instancia

```json
{
  "id": "inventory_0001",
  "seed": 17,
  "family": "availability",
  "difficulty": "easy",
  "inventory": [
    {"product_id": "A", "location_id": "S1", "physical_stock": 20, "reserved_stock": 11}
  ],
  "request": "¿Podemos preparar 12 unidades de A desde S1? Si no, ¿cuántas faltan?",
  "expected": {"can_fulfill": false, "missing_units": 3},
  "solution_program": "available=max(0,20-11); missing=max(0,12-available)"
}
```

**Nota:** `expected` e `inventory` son metadatos protegidos del evaluador: no se entregan íntegramente al modelo salvo los campos explícitamente visibles o devueltos por las herramientas.

### Familias iniciales

| Familia | Ejemplo | Verificación |
|---|---|---|
| Disponibilidad | ¿Alcanzan las unidades disponibles para un pedido? | `available = stock - reserved`, comparación |
| Filtrado | ¿Qué productos tienen menos de N disponibles? | Filtrado y comparación de conjuntos |
| Selección | ¿Qué sucursal puede completar un pedido? | Evaluar sucursales y comparar resultados; regla de desempate explícita |
| Agregación/composición | ¿Cuántas unidades faltan para varios pedidos? | Simulación de asignación y déficit bajo reglas definidas |

### Generación por construcción

1. Crear IDs, ubicaciones, cantidades no negativas y reservas no mayores al stock.
2. Seleccionar una familia y sus parámetros de dificultad.
3. Calcular la respuesta exacta con un algoritmo independiente y determinista.
4. Generar el texto a partir de variantes de plantillas; validar que no sea ambiguo.
5. Guardar el estado, la respuesta de referencia y las semillas.
6. Hacer controles de duplicados y equivalencias entre train/eval/test.

**Reglas que deben especificarse antes de evaluar:** disponibilidad = stock físico menos reservas; pedidos parciales permitidos o prohibidos; prioridad de pedidos simultáneos; inventario por sucursal; desempates; tratamiento de resultados múltiples; unidades y redondeos, si existen.

### Dificultad propuesta (a calibrar)
- Fácil: un producto, una ubicación, una operación.
- Media: varios productos o ubicaciones, filtros y comparaciones.
- Difícil: varias restricciones, agregaciones y asignaciones de stock entre pedidos.

No asumir que estos niveles corresponden empíricamente a la dificultad del modelo. Registrar también cantidad de registros, número de operaciones, cantidad de entidades, profundidad de dependencia y número de llamadas necesarias.

## 5. Respuesta final, verificador y robustez

### Formato de respuesta final: por decidir

**No se establece por ahora un JSON obligatorio en la salida final del modelo.** La prioridad funcional es que el modelo responda correctamente **la solicitud en lenguaje natural**, no que copie un número ni que reproduzca literalmente la salida de una herramienta.

Se compararán, según lo permitido por el curso, al menos estas posibilidades:

1. **Lenguaje natural libre:** respuesta final redactada por el modelo; exige extraer y verificar afirmaciones relevantes, negaciones, cantidades y contradicciones. Puede necesitar un parser específico o un extractor auxiliar validado.
2. **Salida estructurada (por ejemplo, JSON) con o sin explicación natural:** puede simplificar la verificación determinista, pero corre el riesgo de medir cumplimiento de formato, ignorar contradicciones con la explicación o forzar esquemas diferentes para cada familia. No se adopta sin antes evaluar sus ventajas y límites.
3. **Alternativa híbrida:** representación interna estructurada para el verificador y respuesta final natural para el usuario; su implementación exacta queda pendiente.

**Lo que sí exige el enunciado:** aceptar distintas formas correctas equivalentes y resistir el *reward hacking*; ejemplifica equivalencias de respuestas, pero **no especifica expresamente** si debe permitirse lenguaje natural completamente irrestricto o si puede imponerse un formato de salida. Consultar en el foro antes de cerrar el diseño.

### Criterio semántico de corrección

La corrección depende de **responder completamente lo que pregunta cada instancia**, no solo de contener un cálculo válido. Si se pide decidir si un pedido de 12 unidades puede satisfacerse y justificar el déficit, «20 − 11 = 9» es insuficiente aunque el cálculo sea correcto; «no se puede completar y faltan tres unidades» sí lo responde. En cambio, si solo se pregunta por el déficit, «3» puede ser suficiente. Se deben rechazar respuestas contradictorias como «sí alcanza, pero faltan tres» y respuestas que enumeran varias opciones incompatibles.

- **Solución de referencia:** recalcular determinísticamente desde el estado protegido y las reglas del problema, no comparar una frase literal.
- **Respuesta final:** verificar que sus afirmaciones pertinentes corresponden a la solución y no se contradicen. La estrategia de interpretación es un riesgo técnico **por validar**, no la pregunta principal de investigación.
- **Herramientas:** evaluar por separado funciones seleccionadas, argumentos, observaciones y resultado final; no asumir que una llamada válida equivale a resolver la tarea.
- **Diagnósticos adicionales:** registrar `valid_tool_call`, `correct_tool_arguments`, `correct_final_answer`, `contradictory_answer`, `parser_error` y tipo de error, independientemente de la recompensa principal.
- **Recompensa:** mantener inicialmente una puntuación simple (por ejemplo, éxito final 0/1) y justificar posibles recompensas parciales antes de incorporarlas.
- **Robustez:** probar paráfrasis correctas, respuestas parciales, dos respuestas incompatibles, números correctos fuera de contexto, IDs inexistentes, llamadas erróneas, respuestas copiadas de la herramienta y formatos ambiguos.
- **Seguridad del evaluador:** impedir que el modelo vea `expected` o modifique el estado protegido.

El contrato externo del curso sigue siendo `reward(prompt, completion) -> float`. Queda por aclarar cómo se representa una trayectoria multitur con herramientas en `completion` o cómo se enlaza de forma segura con su estado.

## 6. Plan de evaluación piloto (ANTES de comprometerse)

### Preguntas que debe responder
1. ¿Resuelve el modelo el problema cuando los datos ya están incluidos en el prompt?
2. ¿Puede invocar las herramientas con el formato y argumentos correctos?
3. ¿Puede resolverlo cuando debe recuperar los datos mediante herramientas?
4. ¿En qué familia y nivel aparece una tasa intermedia de aciertos?
5. ¿Los aciertos son superiores a reglas triviales o azar informado?
6. ¿La herramienta solo entrega un dato o está resolviendo directamente la tarea?
7. ¿Puede verificarse con suficiente fiabilidad la respuesta natural final sin confundir equivalencias, omisiones o contradicciones?

### Protocolo sugerido
- Elegir 2 modelos objetivo de aproximadamente 1–2B, sujetos a licencia, disponibilidad y capacidad de ejecución. Candidatos para verificar: **Qwen3-1.7B**, **Gemma 3 1B IT** y/o **Llama 3.2 1B Instruct**. No asumir capacidades de herramientas equivalentes ni que una familia rendirá peor.
- Comparar al menos: **sin herramientas (datos visibles)** y **con herramientas (datos recuperables)**; mantener las reglas y respuestas equivalentes.
- Hacer una primera exploración de 10–15 ejemplos por familia y luego un piloto automático de, por ejemplo, 30–50 instancias por familia/nivel para los candidatos seleccionados. Cantidades **sugeridas**, no exigidas.
- Obtener cinco muestras por tarea con configuración de generación reproducible y suficientemente diversa; medir **pass@1** y **pass@5** junto con tasa de llamadas válidas, acierto de resultados e incidencias de parser.
- Conservar todos los rollouts y parámetros (modelo, versión, chat template, temperatura, semilla, límite de tokens, thinking mode si aplica).
- Validar el verificador con pruebas unitarias y revisar manualmente una muestra estratificada de errores.

### Criterios de decisión orientativos (NO umbrales del curso)

| Resultado del piloto | Interpretación provisional | Siguiente acción |
|---|---|---|
| Éxito cercano a 100% | Poco margen de mejora | Incrementar composición, variedad y/o dividir herramientas |
| Éxito cercano a 0% incluso con 5 intentos | Señal de RL escasa | Simplificar tareas, proveer SFT inicial o reconsiderar familia/modelo |
| Acierto intermedio y pass@5 apreciablemente mayor que pass@1 | Posible zona aprendible | Profundizar, comprobar estabilidad y ampliar dataset |
| Muy bien con datos visibles, mal con herramientas | Problema de interfaz/llamadas/integración | Priorizar harness y protocolo de herramientas |
| Mal en ambas condiciones | Problema de razonamiento/comprensión o formato | Aislar operaciones y ajustar niveles |

**Cuidado estadístico:** pass@5 depende del procedimiento de muestreo; estimar con suficientes instancias y acompañar los porcentajes con denominadores e intervalos de incertidumbre cuando sea posible. La diferencia entre pass@1 y pass@5 es una señal diagnóstica, no prueba de mejora garantizada por RL.

## 7. Arquitectura para el proyecto posterior

**Desafío actual:** harness reutilizable + dataset + trazas correctas SFT filtradas por verificador + pares correctos/incorrectos para DPO + línea base + pruebas de robustez/calibración.

**Proyecto posterior:** seleccionar estrategia(s) SFT, DPO y/o RLVR/GRPO/PPO según las instrucciones definitivas; evaluar mejora sobre test reservado y tareas composicionales no vistas.

La arquitectura debe ser **independiente del entrenador**. Considerar TRL/verl solo como **adaptadores posibles**, no como requisito ni como permiso establecido. La documentación de TRL describe herramientas y `environment_factory` para GRPO, pero esta integración es experimental y depende de versiones específicas. Antes de decidir, verificar con el equipo docente si se permite usar frameworks existentes, qué parte debe ser implementación propia y cuáles son los recursos de cómputo disponibles.

## 9. Riesgos principales y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Tareas demasiado fáciles para un modelo reciente | Calibrar primero; aumentar composición y restricciones, no solo tamaños numéricos |
| Tareas imposibles para 1–2B | Incluir niveles sencillos y SFT de arranque; observar pass@k |
| Dataset basado en plantillas aprendidas de memoria | Variar lenguaje, estructuras y composiciones; reservar combinaciones fuera de distribución |
| Tareas que aceptan varias respuestas | Evaluar propiedades semánticas y definir desempates |
| Verificador vulnerable a reward hacking | Pruebas adversariales, parser estricto y estado protegido |
| Contaminación entre splits | Semillas y configuraciones separadas; deduplicar instancias equivalentes |
| Múltiples llamadas complican integración | Empezar con una sola herramienta y pocas interacciones |
| Restricciones del curso sobre herramientas/frameworks | Confirmarlas antes del proyecto; no acoplar harness a TRL |
| Interpretación de respuesta natural insuficiente | Pilotear paráfrasis correctas e incorrectas, negaciones y contradicciones; consultar formato permitido en el foro |
| Herramientas que resuelven toda la tarea | Exponer datos/operaciones elementales y exigir composición; validar con casos multietapa |

## 10. Preguntas concretas para validar con el grupo y el docente

1. ¿El desafío permite utilizar bibliotecas y frameworks existentes para el futuro post-training? ¿Qué debe implementarse desde cero?
2. ¿Qué contrato exacto tiene `reward(prompt, completion)` en tareas con herramientas? ¿Incluye la trayectoria completa?
3. ¿Cuántos turnos y llamadas son aceptables para una tarea?
4. ¿Qué recursos de inferencia y entrenamiento estarán disponibles y qué modelos/licencias son viables?
5. ¿Se valora más una sola familia de problemas bien calibrada o varias familias de menor profundidad?
6. ¿Se admite salida final estructurada como JSON, o se espera interpretación de lenguaje natural libre y paráfrasis? ¿Es aceptable un extractor auxiliar para apoyar la verificación?
7. ¿Los pares DPO deben ser generados por un modelo grande específico o es libre la metodología?

## 11. Decisión sugerida para la próxima revisión

**No aprobar aún el tema como definitivo.** Aprobar primero un **piloto de factibilidad**: un generador inicial con tareas simples y composicionales, `get_inventory` como diseño original, alternativas de consultas elementales u operaciones ejecutables documentadas, un verificador de resultados con estrategia de evaluación semántica todavía por validar, dos modelos pequeños y evaluación con/sin herramientas. Si aparece una zona aprendible, extender a selección y agregación; si no, ajustar o cambiar de tarea.

### Resultado mínimo esperado del piloto
Un informe de una página con tabla por familia/modelo (`pass@1`, `pass@5`, llamadas válidas), ejemplos de razonamiento composicional y errores de respuesta natural, costo/tiempo de inferencia, resultados de una prueba pequeña de robustez del parser y una decisión argumentada **seguir / ajustar / descartar**.

## 12. Fuentes y nivel de evidencia

**Fuente primaria del ramo**
- `DesafioInvestigacion-2026.pdf`, pp. 1–3: objetivo, contrato del harness, dataset, métricas, criterios y entregables.
- `Ciclo2-Asignacion-2026.pdf`, pp. 1–2: lecturas Reasoning Gym, AgentGym, SWE-agent y ReAct como contexto académico.

**Documentación externa consultada (no sustituye las reglas del curso)**
- Hugging Face TRL, GRPO Trainer: https://huggingface.co/docs/trl/grpo_trainer — describe herramientas y entornos de rollout; integración experimental y dependiente de versión.
- Hugging Face, integración OpenEnv: https://huggingface.co/docs/trl/openenv — explica interacción con herramientas en rollouts.
- Google, Gemma 3: https://gemma.ai/models/gemma-3/ — identifica variante instruction-tuned de 1B y benchmarks generales, que **no equivalen** al problema propuesto.

**Pendiente de verificación independiente:** versiones/licencias actuales de todos los candidatos, formato de tools y soporte real para entrenamiento, normas del docente y desempeño en el dataset propio. Ningún resultado de este documento es una medición empírica del harness propuesto.
