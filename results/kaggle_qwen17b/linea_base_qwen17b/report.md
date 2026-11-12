# Informe del piloto

- Etapa: `piloto`; split `eval`; semilla base 2026; 10 por celda; 5 muestras.
- Entorno: GPU Tesla T4; torch 2.11.0+cu130; transformers 5.20.2.
- Código: `0790fe94aa2873b8`; fecha 2026-11-11T20:31:21+00:00.
- Archivos leídos: 1. Rollouts válidos: 900.
- Problemas de carga: ninguno.

## Estado por modelo

| Modelo | Estado | Rollouts | s/rollout (reloj) | Error |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | completo | 900/900 | 43.714 | — |

## Resultados por modelo, condición, familia y dificultad

pass@1 usa la muestra 0 de cada instancia. pass@5 cuenta las instancias con al menos un acierto entre las primeras 5 muestras. El IC95 es de Wilson sobre instancias. La tasa por muestra se da sin IC porque las muestras están correlacionadas.

### `Qwen/Qwen3-1.7B+think`

| Condición | Familia | Nivel | n inst. | pass@1 | pass@5 | Tasa por muestra | Incompletas k=5 |
|---|---|---|---|---|---|---|---|
| tools | availability | easy | 10 | 30.0 % (3/10; IC95 11–60) | 90.0 % (9/10; IC95 60–98) | 40.0 % | 0 |
| tools | availability | medium | 10 | 80.0 % (8/10; IC95 49–94) | 100.0 % (10/10; IC95 72–100) | 66.0 % | 0 |
| tools | availability | hard | 10 | 40.0 % (4/10; IC95 17–69) | 60.0 % (6/10; IC95 31–83) | 28.0 % | 0 |
| tools | selection | easy | 10 | 60.0 % (6/10; IC95 31–83) | 100.0 % (10/10; IC95 72–100) | 38.0 % | 0 |
| tools | selection | medium | 10 | 50.0 % (5/10; IC95 24–76) | 90.0 % (9/10; IC95 60–98) | 36.0 % | 0 |
| tools | selection | hard | 10 | 10.0 % (1/10; IC95 2–40) | 40.0 % (4/10; IC95 17–69) | 20.0 % | 0 |
| tools | composition | easy | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| tools | composition | medium | 10 | 0.0 % (0/10; IC95 0–28) | 10.0 % (1/10; IC95 2–40) | 2.0 % | 0 |
| tools | composition | hard | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| visible | availability | easy | 10 | 90.0 % (9/10; IC95 60–98) | 100.0 % (10/10; IC95 72–100) | 82.0 % | 0 |
| visible | availability | medium | 10 | 90.0 % (9/10; IC95 60–98) | 100.0 % (10/10; IC95 72–100) | 88.0 % | 0 |
| visible | availability | hard | 10 | 60.0 % (6/10; IC95 31–83) | 100.0 % (10/10; IC95 72–100) | 70.0 % | 0 |
| visible | selection | easy | 10 | 90.0 % (9/10; IC95 60–98) | 100.0 % (10/10; IC95 72–100) | 86.0 % | 0 |
| visible | selection | medium | 10 | 80.0 % (8/10; IC95 49–94) | 100.0 % (10/10; IC95 72–100) | 86.0 % | 0 |
| visible | selection | hard | 10 | 50.0 % (5/10; IC95 24–76) | 100.0 % (10/10; IC95 72–100) | 62.0 % | 0 |
| visible | composition | easy | 10 | 90.0 % (9/10; IC95 60–98) | 100.0 % (10/10; IC95 72–100) | 78.0 % | 0 |
| visible | composition | medium | 10 | 10.0 % (1/10; IC95 2–40) | 80.0 % (8/10; IC95 49–94) | 30.0 % | 0 |
| visible | composition | hard | 10 | 20.0 % (2/10; IC95 6–51) | 20.0 % (2/10; IC95 6–51) | 4.0 % | 0 |

## Comparación con y sin herramientas

| Modelo | Familia | Nivel | Visible pass@1 | Herramientas pass@1 | Dif. (h − v) | Visible pass@5 | Herramientas pass@5 |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | availability | easy | 90.0 % (9/10; IC95 60–98) | 30.0 % (3/10; IC95 11–60) | -60.0 pts | 100.0 % (10/10; IC95 72–100) | 90.0 % (9/10; IC95 60–98) |
| `Qwen/Qwen3-1.7B+think` | availability | hard | 60.0 % (6/10; IC95 31–83) | 40.0 % (4/10; IC95 17–69) | -20.0 pts | 100.0 % (10/10; IC95 72–100) | 60.0 % (6/10; IC95 31–83) |
| `Qwen/Qwen3-1.7B+think` | availability | medium | 90.0 % (9/10; IC95 60–98) | 80.0 % (8/10; IC95 49–94) | -10.0 pts | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) |
| `Qwen/Qwen3-1.7B+think` | composition | easy | 90.0 % (9/10; IC95 60–98) | 0.0 % (0/10; IC95 0–28) | -90.0 pts | 100.0 % (10/10; IC95 72–100) | 0.0 % (0/10; IC95 0–28) |
| `Qwen/Qwen3-1.7B+think` | composition | hard | 20.0 % (2/10; IC95 6–51) | 0.0 % (0/10; IC95 0–28) | -20.0 pts | 20.0 % (2/10; IC95 6–51) | 0.0 % (0/10; IC95 0–28) |
| `Qwen/Qwen3-1.7B+think` | composition | medium | 10.0 % (1/10; IC95 2–40) | 0.0 % (0/10; IC95 0–28) | -10.0 pts | 80.0 % (8/10; IC95 49–94) | 10.0 % (1/10; IC95 2–40) |
| `Qwen/Qwen3-1.7B+think` | selection | easy | 90.0 % (9/10; IC95 60–98) | 60.0 % (6/10; IC95 31–83) | -30.0 pts | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) |
| `Qwen/Qwen3-1.7B+think` | selection | hard | 50.0 % (5/10; IC95 24–76) | 10.0 % (1/10; IC95 2–40) | -40.0 pts | 100.0 % (10/10; IC95 72–100) | 40.0 % (4/10; IC95 17–69) |
| `Qwen/Qwen3-1.7B+think` | selection | medium | 80.0 % (8/10; IC95 49–94) | 50.0 % (5/10; IC95 24–76) | -30.0 pts | 100.0 % (10/10; IC95 72–100) | 90.0 % (9/10; IC95 60–98) |

### Diagnóstico de herramientas (por muestra)

| Modelo | Familia | Nivel | Llamadas válidas | Argumentos correctos | Datos requeridos | Límite excedido | Correcta sin recompensa |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | availability | easy | 100.0 % (50/50) | 100.0 % (50/50) | 100.0 % (50/50) | 0.0 % (0/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-1.7B+think` | availability | medium | 98.0 % (49/50) | 98.0 % (49/50) | 84.0 % (42/50) | 0.0 % (0/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-1.7B+think` | availability | hard | 98.0 % (49/50) | 98.0 % (49/50) | 66.0 % (33/50) | 14.0 % (7/50) | 4.0 % (2/50) |
| `Qwen/Qwen3-1.7B+think` | selection | easy | 100.0 % (50/50) | 100.0 % (50/50) | 82.0 % (41/50) | 0.0 % (0/50) | 2.0 % (1/50) |
| `Qwen/Qwen3-1.7B+think` | selection | medium | 100.0 % (50/50) | 100.0 % (50/50) | 90.0 % (45/50) | 6.0 % (3/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-1.7B+think` | selection | hard | 96.0 % (48/50) | 96.0 % (48/50) | 80.0 % (40/50) | 4.0 % (2/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-1.7B+think` | composition | easy | 94.0 % (47/50) | 94.0 % (47/50) | 94.0 % (47/50) | 0.0 % (0/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-1.7B+think` | composition | medium | 88.0 % (44/50) | 88.0 % (44/50) | 72.0 % (36/50) | 0.0 % (0/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-1.7B+think` | composition | hard | 84.0 % (42/50) | 84.0 % (42/50) | 34.0 % (17/50) | 0.0 % (0/50) | 0.0 % (0/50) |

`Correcta sin recompensa` cuenta respuestas finales correctas que no recibieron recompensa, por ejemplo sin haber obtenido los datos: una señal de adivinación.

## Comparación con líneas base

Cada regla se evalúa con `verify_final_text` sobre las mismas instancias que los rollouts. Las triviales y de azar no leen el inventario. Las marcadas como `error_razonable` o azar contado sí lo leen: son errores plausibles, no azar. El control usa `expected` y solo valida el formato; no se compara con los modelos. Las reglas miden solo el texto final; en `tools` el modelo necesita además evidencia.

| Regla | Clase | avail/easy | avail/medium | avail/hard | selec/easy | selec/medium | selec/hard | compo/easy | compo/medium | compo/hard |
|---|---|---|---|---|---|---|---|---|---|---|
| `control_expected` | control | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| `ignorar_reservas` | error_razonable | 5/10 | 5/10 | 5/10 | 0/10 | 0/10 | 1/10 | 3/10 | 3/10 | 3/10 |
| `no_descontar_stock` | error_razonable | — | — | — | — | — | — | 3/10 | 3/10 | 3/10 |
| `nunca_alcanza` | trivial | 0/10 | 0/10 | 0/10 | — | — | — | — | — | — |
| `primera_sucursal` | trivial | — | — | — | 0/10 | 0/10 | 1/10 | — | — | — |
| `primera_sucursal_contada` | error_razonable | — | — | — | 3/10 | 2/10 | 2/10 | — | — | — |
| `siempre_alcanza` | trivial | 5/10 | 5/10 | 5/10 | — | — | — | — | — | — |
| `sucursal_azar` | azar | — | — | — | 0/10 | 0/10 | 0/10 | — | — | — |
| `sucursal_azar_contada` | azar | — | — | — | 2/10 | 2/10 | 3/10 | — | — | — |
| `todo_atendido` | trivial | — | — | — | — | — | — | 3/10 | 3/10 | 3/10 |

`supera` significa que el límite inferior del IC de pass@1 queda sobre la tasa de la regla; `no_distinguible`, que la regla cae dentro del IC.

| Modelo | Condición | Familia | Nivel | Mejor sin inventario | pass@1 frente a ella | Mejor con inventario | pass@1 frente a ella |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | tools | availability | easy | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | availability | medium | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | availability | hard | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | selection | easy | primera_sucursal 0.0 % | supera | primera_sucursal_contada 30.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | tools | selection | medium | primera_sucursal 0.0 % | supera | primera_sucursal_contada 20.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | tools | selection | hard | primera_sucursal 10.0 % | no_distinguible | sucursal_azar_contada 30.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | composition | easy | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `Qwen/Qwen3-1.7B+think` | tools | composition | medium | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `Qwen/Qwen3-1.7B+think` | tools | composition | hard | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `Qwen/Qwen3-1.7B+think` | visible | availability | easy | siempre_alcanza 50.0 % | supera | ignorar_reservas 50.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | visible | availability | medium | siempre_alcanza 50.0 % | supera | ignorar_reservas 50.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | visible | availability | hard | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | selection | easy | primera_sucursal 0.0 % | supera | primera_sucursal_contada 30.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | visible | selection | medium | primera_sucursal 0.0 % | supera | primera_sucursal_contada 20.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | visible | selection | hard | primera_sucursal 10.0 % | supera | sucursal_azar_contada 30.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | composition | easy | todo_atendido 30.0 % | supera | ignorar_reservas 30.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | visible | composition | medium | todo_atendido 30.0 % | no_distinguible | ignorar_reservas 30.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | composition | hard | todo_atendido 30.0 % | no_distinguible | ignorar_reservas 30.0 % | no_distinguible |

## Distribución de errores

| Modelo | Condición | error_type | Muestras | Porcentaje |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | tools | `wrong_value` | 124 | 27.6 % |
| `Qwen/Qwen3-1.7B+think` | tools | `ok` | 115 | 25.6 % |
| `Qwen/Qwen3-1.7B+think` | tools | `missing_field` | 108 | 24.0 % |
| `Qwen/Qwen3-1.7B+think` | tools | `unknown_field` | 47 | 10.4 % |
| `Qwen/Qwen3-1.7B+think` | tools | `no_answer_block` | 36 | 8.0 % |
| `Qwen/Qwen3-1.7B+think` | tools | `tool_limit_exceeded` | 12 | 2.7 % |
| `Qwen/Qwen3-1.7B+think` | tools | `invalid_value` | 3 | 0.7 % |
| `Qwen/Qwen3-1.7B+think` | tools | `missing_evidence` | 3 | 0.7 % |
| `Qwen/Qwen3-1.7B+think` | tools | `ambiguous_value` | 2 | 0.4 % |
| `Qwen/Qwen3-1.7B+think` | visible | `ok` | 293 | 65.1 % |
| `Qwen/Qwen3-1.7B+think` | visible | `wrong_value` | 123 | 27.3 % |
| `Qwen/Qwen3-1.7B+think` | visible | `no_answer_block` | 19 | 4.2 % |
| `Qwen/Qwen3-1.7B+think` | visible | `invalid_value` | 6 | 1.3 % |
| `Qwen/Qwen3-1.7B+think` | visible | `ambiguous_value` | 5 | 1.1 % |
| `Qwen/Qwen3-1.7B+think` | visible | `missing_field` | 3 | 0.7 % |
| `Qwen/Qwen3-1.7B+think` | visible | `unknown_field` | 1 | 0.2 % |

| Modelo | Condición | Muestras | parser_error | Contradicción |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | tools | 450 | 46.2 % (208/450) | 0.0 % (0/450) |
| `Qwen/Qwen3-1.7B+think` | visible | 450 | 7.6 % (34/450) | 0.0 % (0/450) |

## Clasificación según §6 de la propuesta (orientativa)

**Es una lectura orientativa, no una decisión ni un umbral del curso.** La propuesta define las categorías; los números son nuestros y están en `summary.json`. La certeza es `firme` solo si el IC completo cae en la categoría. Con un IC más ancho que 30 puntos se marca `IC muy ancho`: esa categoría es una lectura provisional y no debe usarse para decidir.

**16 de 18 celdas tienen un IC muy ancho.** Hacen falta más instancias antes de sacar conclusiones de ellas.

| Modelo | Condición | Familia | Nivel | Lectura | Certeza | Frente a regla trivial | Acción sugerida |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | tools | availability | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | tools | availability | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | tools | availability | hard | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | tools | selection | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | tools | selection | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | tools | selection | hard | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | tools | composition | easy | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | tools | composition | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | tools | composition | hard | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | visible | availability | easy | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-1.7B+think` | visible | availability | medium | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-1.7B+think` | visible | availability | hard | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | visible | selection | easy | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-1.7B+think` | visible | selection | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | visible | selection | hard | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | visible | composition | easy | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-1.7B+think` | visible | composition | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | visible | composition | hard | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |

### Entre condiciones

| Modelo | Familia | Nivel | Lectura | Certeza | Acción sugerida |
|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | availability | easy | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |
| `Qwen/Qwen3-1.7B+think` | availability | hard | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B+think` | availability | medium | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B+think` | composition | easy | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |
| `Qwen/Qwen3-1.7B+think` | composition | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B+think` | composition | medium | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B+think` | selection | easy | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |
| `Qwen/Qwen3-1.7B+think` | selection | hard | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B+think` | selection | medium | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |

## Costo

| Modelo | Condición | Muestras | Tokens nuevos por muestra | s por muestra | Horas (suma de `usage.seconds`) | Llegó al tope de tokens |
|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | tools | 450 | 2086 | 55.44 | 6.93 | 3.6 % (16/450) |
| `Qwen/Qwen3-1.7B+think` | visible | 450 | 1371 | 31.59 | 3.95 | 3.8 % (17/450) |

`Llegó al tope de tokens` cuenta las muestras con alguna generación cortada por `max_new_tokens`, según `usage.stop_reasons`. En rollouts sin ese campo es una cota inferior. Un valor alto, sobre todo con thinking, indica respuestas cortadas.

## Instancias incompletas

Ninguna: todas las instancias vistas tienen 5 muestras.

## Revisión manual

`muestra_errores.jsonl` tiene 138 rollouts fallidos, estratificados por modelo, condición, familia, dificultad y error_type (hasta 3 por estrato). Sirve para verificar a mano si el verificador rechazó bien.
