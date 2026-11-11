# Informe del piloto

- Etapa: `trazas`; split `train`; semilla base 2026; 10 por celda; 2 muestras.
- Entorno: GPU Tesla T4; torch 2.11.0+cu130; transformers 5.20.2.
- Código: `0790fe94aa2873b8`; fecha 2026-11-11T17:54:04+00:00.
- Archivos leídos: 1. Rollouts válidos: 360.
- Problemas de carga: ninguno.

## Estado por modelo

| Modelo | Estado | Rollouts | s/rollout (reloj) | Error |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | completo | 360/360 | 43.607 | — |

## Resultados por modelo, condición, familia y dificultad

pass@1 usa la muestra 0 de cada instancia. pass@2 cuenta las instancias con al menos un acierto entre las primeras 2 muestras. El IC95 es de Wilson sobre instancias. La tasa por muestra se da sin IC porque las muestras están correlacionadas.

**Esta corrida tiene 2 muestras por instancia, así que aquí no existe pass@5.** pass@2 no es comparable con pass@5.

### `Qwen/Qwen3-1.7B+think`

| Condición | Familia | Nivel | n inst. | pass@1 | pass@2 | Tasa por muestra | Incompletas k=2 |
|---|---|---|---|---|---|---|---|
| tools | availability | easy | 10 | 20.0 % (2/10; IC95 6–51) | 70.0 % (7/10; IC95 40–89) | 35.0 % | 0 |
| tools | availability | medium | 10 | 30.0 % (3/10; IC95 11–60) | 60.0 % (6/10; IC95 31–83) | 35.0 % | 0 |
| tools | availability | hard | 10 | 40.0 % (4/10; IC95 17–69) | 90.0 % (9/10; IC95 60–98) | 50.0 % | 0 |
| tools | selection | easy | 10 | 70.0 % (7/10; IC95 40–89) | 90.0 % (9/10; IC95 60–98) | 60.0 % | 0 |
| tools | selection | medium | 10 | 40.0 % (4/10; IC95 17–69) | 90.0 % (9/10; IC95 60–98) | 55.0 % | 0 |
| tools | selection | hard | 10 | 40.0 % (4/10; IC95 17–69) | 50.0 % (5/10; IC95 24–76) | 25.0 % | 0 |
| tools | composition | easy | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| tools | composition | medium | 10 | 10.0 % (1/10; IC95 2–40) | 10.0 % (1/10; IC95 2–40) | 5.0 % | 0 |
| tools | composition | hard | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| visible | availability | easy | 10 | 70.0 % (7/10; IC95 40–89) | 90.0 % (9/10; IC95 60–98) | 75.0 % | 0 |
| visible | availability | medium | 10 | 70.0 % (7/10; IC95 40–89) | 80.0 % (8/10; IC95 49–94) | 60.0 % | 0 |
| visible | availability | hard | 10 | 80.0 % (8/10; IC95 49–94) | 80.0 % (8/10; IC95 49–94) | 65.0 % | 0 |
| visible | selection | easy | 10 | 90.0 % (9/10; IC95 60–98) | 90.0 % (9/10; IC95 60–98) | 85.0 % | 0 |
| visible | selection | medium | 10 | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) | 95.0 % | 0 |
| visible | selection | hard | 10 | 70.0 % (7/10; IC95 40–89) | 80.0 % (8/10; IC95 49–94) | 70.0 % | 0 |
| visible | composition | easy | 10 | 60.0 % (6/10; IC95 31–83) | 80.0 % (8/10; IC95 49–94) | 65.0 % | 0 |
| visible | composition | medium | 10 | 0.0 % (0/10; IC95 0–28) | 30.0 % (3/10; IC95 11–60) | 15.0 % | 0 |
| visible | composition | hard | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |

## Comparación con y sin herramientas

| Modelo | Familia | Nivel | Visible pass@1 | Herramientas pass@1 | Dif. (h − v) | Visible pass@2 | Herramientas pass@2 |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | availability | easy | 70.0 % (7/10; IC95 40–89) | 20.0 % (2/10; IC95 6–51) | -50.0 pts | 90.0 % (9/10; IC95 60–98) | 70.0 % (7/10; IC95 40–89) |
| `Qwen/Qwen3-1.7B+think` | availability | hard | 80.0 % (8/10; IC95 49–94) | 40.0 % (4/10; IC95 17–69) | -40.0 pts | 80.0 % (8/10; IC95 49–94) | 90.0 % (9/10; IC95 60–98) |
| `Qwen/Qwen3-1.7B+think` | availability | medium | 70.0 % (7/10; IC95 40–89) | 30.0 % (3/10; IC95 11–60) | -40.0 pts | 80.0 % (8/10; IC95 49–94) | 60.0 % (6/10; IC95 31–83) |
| `Qwen/Qwen3-1.7B+think` | composition | easy | 60.0 % (6/10; IC95 31–83) | 0.0 % (0/10; IC95 0–28) | -60.0 pts | 80.0 % (8/10; IC95 49–94) | 0.0 % (0/10; IC95 0–28) |
| `Qwen/Qwen3-1.7B+think` | composition | hard | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | +0.0 pts | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) |
| `Qwen/Qwen3-1.7B+think` | composition | medium | 0.0 % (0/10; IC95 0–28) | 10.0 % (1/10; IC95 2–40) | +10.0 pts | 30.0 % (3/10; IC95 11–60) | 10.0 % (1/10; IC95 2–40) |
| `Qwen/Qwen3-1.7B+think` | selection | easy | 90.0 % (9/10; IC95 60–98) | 70.0 % (7/10; IC95 40–89) | -20.0 pts | 90.0 % (9/10; IC95 60–98) | 90.0 % (9/10; IC95 60–98) |
| `Qwen/Qwen3-1.7B+think` | selection | hard | 70.0 % (7/10; IC95 40–89) | 40.0 % (4/10; IC95 17–69) | -30.0 pts | 80.0 % (8/10; IC95 49–94) | 50.0 % (5/10; IC95 24–76) |
| `Qwen/Qwen3-1.7B+think` | selection | medium | 100.0 % (10/10; IC95 72–100) | 40.0 % (4/10; IC95 17–69) | -60.0 pts | 100.0 % (10/10; IC95 72–100) | 90.0 % (9/10; IC95 60–98) |

### Diagnóstico de herramientas (por muestra)

| Modelo | Familia | Nivel | Llamadas válidas | Argumentos correctos | Datos requeridos | Límite excedido | Correcta sin recompensa |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | availability | easy | 100.0 % (20/20) | 100.0 % (20/20) | 100.0 % (20/20) | 0.0 % (0/20) | 0.0 % (0/20) |
| `Qwen/Qwen3-1.7B+think` | availability | medium | 95.0 % (19/20) | 95.0 % (19/20) | 85.0 % (17/20) | 0.0 % (0/20) | 0.0 % (0/20) |
| `Qwen/Qwen3-1.7B+think` | availability | hard | 100.0 % (20/20) | 100.0 % (20/20) | 85.0 % (17/20) | 10.0 % (2/20) | 0.0 % (0/20) |
| `Qwen/Qwen3-1.7B+think` | selection | easy | 100.0 % (20/20) | 95.0 % (19/20) | 90.0 % (18/20) | 5.0 % (1/20) | 0.0 % (0/20) |
| `Qwen/Qwen3-1.7B+think` | selection | medium | 100.0 % (20/20) | 100.0 % (20/20) | 95.0 % (19/20) | 0.0 % (0/20) | 0.0 % (0/20) |
| `Qwen/Qwen3-1.7B+think` | selection | hard | 100.0 % (20/20) | 95.0 % (19/20) | 70.0 % (14/20) | 15.0 % (3/20) | 0.0 % (0/20) |
| `Qwen/Qwen3-1.7B+think` | composition | easy | 100.0 % (20/20) | 100.0 % (20/20) | 100.0 % (20/20) | 0.0 % (0/20) | 0.0 % (0/20) |
| `Qwen/Qwen3-1.7B+think` | composition | medium | 90.0 % (18/20) | 90.0 % (18/20) | 75.0 % (15/20) | 5.0 % (1/20) | 0.0 % (0/20) |
| `Qwen/Qwen3-1.7B+think` | composition | hard | 65.0 % (13/20) | 65.0 % (13/20) | 10.0 % (2/20) | 0.0 % (0/20) | 0.0 % (0/20) |

`Correcta sin recompensa` cuenta respuestas finales correctas que no recibieron recompensa, por ejemplo sin haber obtenido los datos: una señal de adivinación.

## Comparación con líneas base

Cada regla se evalúa con `verify_final_text` sobre las mismas instancias que los rollouts. Las triviales y de azar no leen el inventario. Las marcadas como `error_razonable` o azar contado sí lo leen: son errores plausibles, no azar. El control usa `expected` y solo valida el formato; no se compara con los modelos. Las reglas miden solo el texto final; en `tools` el modelo necesita además evidencia.

| Regla | Clase | avail/easy | avail/medium | avail/hard | selec/easy | selec/medium | selec/hard | compo/easy | compo/medium | compo/hard |
|---|---|---|---|---|---|---|---|---|---|---|
| `control_expected` | control | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| `ignorar_reservas` | error_razonable | 5/10 | 5/10 | 5/10 | 0/10 | 1/10 | 0/10 | 3/10 | 0/10 | 0/10 |
| `no_descontar_stock` | error_razonable | — | — | — | — | — | — | 3/10 | 0/10 | 0/10 |
| `nunca_alcanza` | trivial | 1/10 | 0/10 | 0/10 | — | — | — | — | — | — |
| `primera_sucursal` | trivial | — | — | — | 0/10 | 0/10 | 0/10 | — | — | — |
| `primera_sucursal_contada` | error_razonable | — | — | — | 2/10 | 2/10 | 1/10 | — | — | — |
| `siempre_alcanza` | trivial | 5/10 | 5/10 | 5/10 | — | — | — | — | — | — |
| `sucursal_azar` | azar | — | — | — | 1/10 | 2/10 | 0/10 | — | — | — |
| `sucursal_azar_contada` | azar | — | — | — | 5/10 | 3/10 | 1/10 | — | — | — |
| `todo_atendido` | trivial | — | — | — | — | — | — | 3/10 | 0/10 | 0/10 |

`supera` significa que el límite inferior del IC de pass@1 queda sobre la tasa de la regla; `no_distinguible`, que la regla cae dentro del IC.

| Modelo | Condición | Familia | Nivel | Mejor sin inventario | pass@1 frente a ella | Mejor con inventario | pass@1 frente a ella |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | tools | availability | easy | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | availability | medium | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | availability | hard | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | selection | easy | sucursal_azar 10.0 % | supera | sucursal_azar_contada 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | selection | medium | sucursal_azar 20.0 % | no_distinguible | sucursal_azar_contada 30.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | selection | hard | primera_sucursal 0.0 % | supera | primera_sucursal_contada 10.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | tools | composition | easy | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `Qwen/Qwen3-1.7B+think` | tools | composition | medium | todo_atendido 0.0 % | supera | ignorar_reservas 0.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | tools | composition | hard | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | availability | easy | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | availability | medium | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | availability | hard | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | selection | easy | sucursal_azar 10.0 % | supera | sucursal_azar_contada 50.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | visible | selection | medium | sucursal_azar 20.0 % | supera | sucursal_azar_contada 30.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | visible | selection | hard | primera_sucursal 0.0 % | supera | primera_sucursal_contada 10.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | visible | composition | easy | todo_atendido 30.0 % | supera | ignorar_reservas 30.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | visible | composition | medium | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | composition | hard | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |

## Distribución de errores

| Modelo | Condición | error_type | Muestras | Porcentaje |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | tools | `ok` | 53 | 29.4 % |
| `Qwen/Qwen3-1.7B+think` | tools | `wrong_value` | 51 | 28.3 % |
| `Qwen/Qwen3-1.7B+think` | tools | `missing_field` | 40 | 22.2 % |
| `Qwen/Qwen3-1.7B+think` | tools | `no_answer_block` | 17 | 9.4 % |
| `Qwen/Qwen3-1.7B+think` | tools | `unknown_field` | 11 | 6.1 % |
| `Qwen/Qwen3-1.7B+think` | tools | `tool_limit_exceeded` | 7 | 3.9 % |
| `Qwen/Qwen3-1.7B+think` | tools | `ambiguous_value` | 1 | 0.6 % |
| `Qwen/Qwen3-1.7B+think` | visible | `ok` | 106 | 58.9 % |
| `Qwen/Qwen3-1.7B+think` | visible | `wrong_value` | 64 | 35.6 % |
| `Qwen/Qwen3-1.7B+think` | visible | `no_answer_block` | 5 | 2.8 % |
| `Qwen/Qwen3-1.7B+think` | visible | `ambiguous_value` | 2 | 1.1 % |
| `Qwen/Qwen3-1.7B+think` | visible | `missing_field` | 1 | 0.6 % |
| `Qwen/Qwen3-1.7B+think` | visible | `unknown_field` | 1 | 0.6 % |
| `Qwen/Qwen3-1.7B+think` | visible | `multiple_answer_blocks` | 1 | 0.6 % |

| Modelo | Condición | Muestras | parser_error | Contradicción |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | tools | 180 | 42.2 % (76/180) | 0.0 % (0/180) |
| `Qwen/Qwen3-1.7B+think` | visible | 180 | 5.6 % (10/180) | 0.0 % (0/180) |

## Clasificación según §6 de la propuesta (orientativa)

**Es una lectura orientativa, no una decisión ni un umbral del curso.** La propuesta define las categorías; los números son nuestros y están en `summary.json`. La certeza es `firme` solo si el IC completo cae en la categoría. Con un IC más ancho que 30 puntos se marca `IC muy ancho`: esa categoría es una lectura provisional y no debe usarse para decidir.

**14 de 18 celdas tienen un IC muy ancho.** Hacen falta más instancias antes de sacar conclusiones de ellas.

| Modelo | Condición | Familia | Nivel | Lectura | Certeza | Frente a regla trivial | Acción sugerida |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | tools | availability | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | tools | availability | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | tools | availability | hard | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | tools | selection | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | tools | selection | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | tools | selection | hard | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | supera | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-1.7B+think` | tools | composition | easy | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | tools | composition | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | supera | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | tools | composition | hard | Éxito cercano a 0 % incluso con k intentos | tentativa | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | visible | availability | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | visible | availability | medium | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-1.7B+think` | visible | availability | hard | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-1.7B+think` | visible | selection | easy | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-1.7B+think` | visible | selection | medium | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-1.7B+think` | visible | selection | hard | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | supera | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-1.7B+think` | visible | composition | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | visible | composition | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | visible | composition | hard | Éxito cercano a 0 % incluso con k intentos | tentativa | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |

### Entre condiciones

| Modelo | Familia | Nivel | Lectura | Certeza | Acción sugerida |
|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | availability | easy | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |
| `Qwen/Qwen3-1.7B+think` | availability | hard | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |
| `Qwen/Qwen3-1.7B+think` | availability | medium | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |
| `Qwen/Qwen3-1.7B+think` | composition | easy | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B+think` | composition | hard | Mal en ambas condiciones | firme | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B+think` | composition | medium | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B+think` | selection | easy | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B+think` | selection | hard | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B+think` | selection | medium | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |

## Costo

| Modelo | Condición | Muestras | Tokens nuevos por muestra | s por muestra | Horas (suma de `usage.seconds`) | Llegó al tope de tokens |
|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think` | tools | 180 | 2087 | 54.13 | 2.71 | 3.9 % (7/180) |
| `Qwen/Qwen3-1.7B+think` | visible | 180 | 1372 | 33.07 | 1.65 | 3.3 % (6/180) |

`Llegó al tope de tokens` cuenta las muestras con alguna generación cortada por `max_new_tokens`, según `usage.stop_reasons`. En rollouts sin ese campo es una cota inferior. Un valor alto, sobre todo con thinking, indica respuestas cortadas.

## Instancias incompletas

Ninguna: todas las instancias vistas tienen 2 muestras.

## Revisión manual

`muestra_errores.jsonl` tiene 89 rollouts fallidos, estratificados por modelo, condición, familia, dificultad y error_type (hasta 3 por estrato). Sirve para verificar a mano si el verificador rechazó bien.
