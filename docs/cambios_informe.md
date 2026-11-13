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
