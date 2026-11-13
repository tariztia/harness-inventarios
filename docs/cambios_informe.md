# Cambios al informe del desafío

Registro para el equipo: qué se cambió en `docs/informe.md`, por qué y con qué evidencia. Se actualiza a medida que se revisa cada sección. Los documentos de trabajo de la revisión son:

- `docs/revision_informe.md`: lista de pendientes, análisis crítico y decisiones tomadas.
- `docs/analisis_verificador.md`: comparación con otros trabajos, referencias y qué se puede afirmar.

Criterios de la revisión:

- **No se cambia ningún número de las corridas.** Cuando se agrega una cifra nueva, se indica de dónde sale y cómo reproducirla.
- **No se afirma nada que no esté medido.** Por ejemplo, la robustez del verificador es frente a las trampas que previó el equipo, no frente a un modelo entrenado con RL.
- **No se cambia código del verificador antes de la entrega**: cualquier cambio obligaría a reevaluar la línea base.

## §2.3 Protocolo de interacción

| Cambio | Por qué | Evidencia |
|---|---|---|
| "No todos los modelos tienen rol de sistema" pasa a ser una decisión de **portabilidad**. Se aclara que Qwen3 y Llama 3.2 sí tienen rol de sistema y herramientas nativas (`tools=`), y que para el proyecto se medirá el mecanismo nativo | La frase sugería una limitación que nuestros modelos no tienen | Plantillas de chat oficiales en Hugging Face (`tokenizer_config.json`), revisadas el 13-11. La de Llama 3.2 admite una sola llamada por turno y usa `parameters` en vez de `arguments` |
| Se explica que el formato del `<answer>` llega con los resultados de la herramienta, no en el prompt inicial | No estaba dicho, y explica el diseño | `src/inventory_harness/prompts.py`: con el formato a la vista, los modelos respondían sin llamar |
| Nuevo párrafo **"Qué cuenta como llamada"**: se aceptan `<tool_call>`, JSON suelto que nombre la herramienta y forma de Python; se dice por qué y sus dos costos | La flexibilidad aparecía solo de pasada en §5.6, sin justificación ni riesgos | Solo 41 de 450 respuestas del objetivo usan la etiqueta. Probado: «para esto llamaría get_inventory("P01")» se ejecuta como llamada |
| Se dice explícitamente que **`<answer>` es obligatorio** y que fuera del bloque no se busca la respuesta, con la razón | No quedaba claro qué formato era obligatorio | El texto libre trae cálculos intermedios |
| La mención de Reasoning Gym se escribe como **contraste**: ellos toman el último bloque, comparan texto y dan crédito parcial; nosotros exigimos un bloque, interpretamos valores por tipo y damos 0/1 | Decir "también lo hacemos" era impreciso | Código de `open-thought/reasoning-gym`, ver `docs/analisis_verificador.md` §2 |
| Sobre Llama: se reemplaza "con una lectura indulgente acertaría solo 4" por la cifra por campo: **14 % de sus valores son correctos**, frente a 49 % de Qwen3-1.7B sin thinking | Se quería saber si Llama razona bien y solo presenta mal. No: suma las reservas en vez de restarlas, copia el marcador `N` y mezcla sucursales | Nuevo `scripts/lectura_indulgente.py`. Llama: 211/1.460 valores correctos y `alcanza` 43/129 (bajo el azar). El "4 de 900" de §5.7 no se toca: usa otro criterio, y con este script salen 6 |

## Reestructuración: `docs/informe_v2.md`

| Cambio | Por qué |
|---|---|
| Nueva versión del informe en un archivo aparte, armada moviendo el contenido actual sin reescribirlo. `docs/informe.md` queda intacto como fuente hasta aprobar la nueva | El cambio es grande (de ~5.900 a ~4.000 palabras de cuerpo); en un archivo aparte se puede comparar lado a lado y comprobar que no se pierden cifras |
| Estructura tipo paper, a lo más 7 páginas a doble columna, como pide el proyecto: Introducción, Entorno, Dataset, Verificador, Línea base, Calibración, Datos derivados, Limitaciones y trabajo futuro, Referencias | El informe actual era difícil de leer (~15 páginas) |
| A anexos: ejemplo de instancia y detalle de las llamadas (A), interpretación de valores (B), tabla de casos adversariales (C), auditoría (D), tablas por familia y reglas triviales (E), ejemplos cualitativos (F) y reproducción (G) | El cuerpo cuenta qué se hizo y qué muestra; la evidencia detallada va en anexos |
| Las notas **[Revisión]** marcan lo pendiente de cada sección y se borran al terminar | Para que el equipo vea qué falta en cada parte |

## Versión 2 completa (`docs/informe_v2.md`)

Cuerpo de ~4.250 palabras (tablas incluidas) con 2 figuras, más anexos A–G. Todas las cifras se cruzaron con `docs/informe.md` y los documentos de la revisión; las únicas cifras nuevas son las de Llama por campo (`scripts/lectura_indulgente.py`), las 364 llamadas válidas de Llama y las 1.918 respuestas correctas sin equivalencias, verificadas sobre los rollouts.

| Sección | Cambio | Por qué |
|---|---|---|
| §1 Introducción | Reemplaza al resumen. Sitúa el trabajo (Reasoning Gym) y la robustez se presenta como "frente a las trampas que previmos" | Tono acorde a lo medido (B14) |
| §2 Entorno | Protocolo reducido; detalle de llamadas y formatos nativos al Anexo A. **Figura 1** con el flujo del entorno y del verificador | Largo tipo paper; faltaba explicar el flujo (B2) |
| §3 Dataset | §3.2 explica qué es un atajo y qué mide cada fila | B1 |
| §4 Verificador | Abre con el principio (compara valores, no juzga razonamiento), por qué reglas y no un LLM juez (Huang et al.; Zhao et al.), cómo interpreta valores, defensas, casos adversariales con su límite y la auditoría como ciclo, incluida la relajación posterior | B2–B5, B14 |
| §5 Línea base | Define rollout, pass@k (Chen et al.), Wilson y el tope de tokens; Qwen3-8B se remite a §7. **Figura 2** reemplaza las tablas por dificultad, que pasan al Anexo E. Ejemplos al Anexo F | B6–B10 |
| §6 Calibración | Incorpora la comparación con reglas triviales | Es evidencia de calibración |
| §8 Limitaciones | Agrega herramienta sin `tools=`, flexibilidad de llamadas, robustez solo frente a lo previsto, contradicciones débiles y sumas sin validar | B13, B14 |
| Referencias | 5 referencias, todas citadas en el cuerpo | A5 y protocolo |
| Anexo B | Interpretación de valores, caso `33O1` contra `3301`, contraste con Reasoning Gym | C1, C2 |
| Anexo C | Un ejemplo por categoría adversarial | B4 |
| Anexo E | Tabla por familia con pass@1 y pass@5 en columnas separadas | B9: "9 / 10" se leía como "9 de 10" |
| Figuras | `docs/figuras/`, generadas con `scripts/figuras_informe.py` | Reproducibles |

Pendiente: integrantes y link al repo limpio (A1, A2), y exportar a PDF (A3).

## Revisión final: afirmaciones demasiado fuertes

| Antes | Después | Por qué |
|---|---|---|
| "Las tareas caen en la zona aprendible" | "La evidencia apunta a que…, aunque eso solo se confirmará al entrenar" | Sin entrenar no se puede afirmar que el modelo aprenda |
| "El entorno distingue capacidad"; "el acierto sube con el tamaño" | "Separa a los modelos medidos"; sube dentro de Qwen3 con el mismo modo, no en general | Llama-3.2-1B es más grande que Qwen3-0.6B y acierta menos; el pass@5 de Qwen3-4B en visible es menor que el del objetivo |
| "El thinking le da 34 puntos" | Incluye también su tope de tokens mayor | Variables mezcladas: thinking va con 4.096 tokens y sin thinking con 768 |
| "Usar herramientas cuesta 23 puntos" | La condición `tools` cuesta 23 puntos, y la brecha mezcla herramienta, formato y turnos | No se aisló el efecto de la herramienta |
| "El acierto baja de easy a hard… lo que confirma el orden" | "Nunca sube… es consistente con el orden" | Qwen3-0.6B empata entre niveles; n = 30 por nivel |
| "Lo que falla en las tareas difíciles es pedir los datos" | "Una causa importante" | También hay 122 errores de cálculo con todos los datos |
| "Su problema principal es el cálculo" (Llama) | La lectura indulgente es aproximada, pero indica que también falla en el cálculo | La lectura por claves puede capturar valores intermedios |
| "Subestiman lo que haría con más tokens" (Qwen3-4B) | "Probablemente subestiman" | No se corrió con más tokens |
| "Margen de mejora" con Qwen3-4B y Qwen3-8B | "Las tareas son resolubles por modelos más grandes"; no prueba que el objetivo llegue ahí. Se aclara que Qwen3-8B usa 2 intentos | Un modelo más grande no demuestra margen para el pequeño |
| Celdas "Aprendibles" | "Candidatas a la zona aprendible" | Mismo motivo que la primera fila |
| "Lo mitigamos con la auditoría"; "ninguna aceptada era incorrecta" | "En parte"; "en esa muestra" | Auditoría chica y exploratoria |
| "Cuando el formato iba en el prompt, los modelos respondían sin llamar" | "En la exploración… tendían a" | Observación no cuantificada en el informe |

También se agregó:

- En §5.1 y §8, que pass@1 usa solo la primera de 5 muestras (confirmado en `metrics.py`) y hay una sola semilla.
- En §8, las variables mezcladas en las comparaciones.
- En §3.4, que los niveles son por familia.
- En la introducción, qué tiene de distintivo el entorno, porque la originalidad es un criterio de la rúbrica.
- Una sección 9 de conclusiones.

Para compensar el largo, se quitaron de §8 dos puntos que ya estaban en otras secciones.
