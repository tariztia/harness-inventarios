# Propuesta breve — Harness de razonamiento con herramientas sobre inventarios

**Idea.** Evaluar si modelos pequeños pueden resolver solicitudes sobre inventarios de una empresa usando herramientas que consultan una base de datos sintética. Buscamos tareas donde el modelo deba **combinar datos, comparar alternativas y aplicar restricciones**, no copiar la respuesta de una herramienta. Si encontramos dificultades aprendibles, reutilizaremos el entorno y los datos en el post-training del proyecto.

## ¿Qué construiríamos?

- **Base de datos sintética:** productos, sucursales, stock físico, unidades reservadas y pedidos pendientes.
- **Herramientas ejecutables:** inicialmente `get_inventory(product_id, branch_id)` y, según las tareas, consultas por sucursal o pedidos. Devuelven **datos**, no la solución final. **Alternativa por evaluar:** separar consultas elementales (`get_stock`, `get_reserved_units`, etc.) o pedir al modelo que genere operaciones/consultas ejecutables, como SQL.
- **Harness:** presenta el problema y las herramientas, ejecuta las llamadas del modelo, devuelve resultados y envía su respuesta al verificador.

## ¿Qué problemas generaríamos?

| Familia | Ejemplo | Qué exige al modelo |
|---|---|---|
| Disponibilidad | ¿Alcanza el inventario no reservado para un pedido? ¿Cuánto falta? | Consultar, calcular y decidir |
| Filtrado | ¿Qué productos tienen menos de 5 unidades disponibles? | Comparar varios registros |
| Selección | ¿Qué sucursal puede cubrir la mayor parte de un pedido? | Consultar sucursales y comparar alternativas |
| Composición | Con varios pedidos y reservas, ¿qué cantidades pueden atenderse y cuáles quedan pendientes? | Combinar operaciones y restricciones |

**Generador:** código Python crea inventarios aleatorios reproducibles; elige una familia, parámetros y una plantilla de pregunta en lenguaje natural; calcula la solución mediante código independiente. Genera conjuntos `train/eval/test` y niveles de dificultad según cantidad de entidades, operaciones y restricciones. No requiere redactar preguntas una por una.

**Ejemplo de prompt:** «Tenemos pedidos de A y B en dos sucursales. Considerando las unidades reservadas, ¿qué sucursal cubre más unidades y cuántas quedan pendientes?». El modelo recibe la descripción de las herramientas, **no** los valores ocultos ni la solución.

**Verificador:** consulta el estado original y comprueba por código la decisión, cantidades y restricciones, además de registrar errores de llamadas y cálculo. **Pendiente:** decidir cómo validar respuestas finales equivalentes en lenguaje natural sin aceptar explicaciones incompletas o contradictorias. Evaluar lenguaje libre versus JSON estructurado/híbrido; confirmar expectativas en el foro. Recompensa principal propuesta: `1` correcto, `0` incorrecto.

## Validación antes de comprometernos

1. Implementar un generador y harness mínimos con 2–3 familias; probar modelos recientes de ~1–2B y, opcionalmente, uno anterior.
2. Medir **pass@1 y pass@5** por dificultad, además de llamadas válidas y errores de respuesta.
3. Comparar tareas con datos entregados en el prompt frente a datos obtenidos por herramientas, para distinguir dificultades de razonamiento y de uso de herramientas.
4. **Decidir según resultados:** mantener el diseño si hay aciertos parciales y margen de mejora; aumentar composición/separar herramientas si resulta fácil; cambiar la tarea si es demasiado difícil o trivial.

## Alcance y pendientes

- **Ahora:** entorno, generador, verificador, dataset, trazas SFT/pares DPO y línea base. **Después:** entrenamiento y comparación de estrategias.
- **Fuera de alcance inicial:** preguntas aclaratorias al usuario y dominio sanitario.
- **Por definir:** herramientas exactas; formato y robustez del verificador de respuesta final; grado de dificultad real; modelo objetivo; uso permitido de frameworks como TRL/verl.

**Riesgo principal:** que las herramientas resuelvan el problema directamente o que las preguntas sean demasiado fáciles. Por eso deben devolver datos elementales y calibrarse con pruebas reales antes de escalar el dataset.
