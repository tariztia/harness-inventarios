# Informe del piloto

- Etapa: `piloto`; split `eval`; semilla base 2026; 10 por celda; 5 muestras.
- Entorno: GPU Tesla T4; torch 2.11.0+cu130; transformers 5.20.2.
- Código: `27f29db9ca698f3e`; fecha 2026-11-13T09:51:36+00:00.
- Archivos leídos: 1. Rollouts válidos: 700.
- Problemas de carga: ninguno.

## Estado por modelo

| Modelo | Estado | Rollouts | s/rollout (reloj) | Error |
|---|---|---|---|---|
| `Qwen/Qwen3-0.6B+think` | corriendo | 700/900 | 55.912 | — |

## Resultados por modelo, condición, familia y dificultad

pass@1 usa la muestra 0 de cada instancia. pass@5 cuenta las instancias con al menos un acierto entre las primeras 5 muestras. El IC95 es de Wilson sobre instancias. La tasa por muestra se da sin IC porque las muestras están correlacionadas.

### `Qwen/Qwen3-0.6B+think`

| Condición | Familia | Nivel | n inst. | pass@1 | pass@5 | Tasa por muestra | Incompletas k=5 |
|---|---|---|---|---|---|---|---|
| tools | availability | easy | 8 | 0.0 % (0/8; IC95 0–32) | 37.5 % (3/8; IC95 14–69) | 10.0 % | 0 |
| tools | availability | medium | 8 | 37.5 % (3/8; IC95 14–69) | 50.0 % (4/8; IC95 22–78) | 10.0 % | 0 |
| tools | availability | hard | 8 | 12.5 % (1/8; IC95 2–47) | 12.5 % (1/8; IC95 2–47) | 2.5 % | 0 |
| tools | selection | easy | 8 | 50.0 % (4/8; IC95 22–78) | 100.0 % (8/8; IC95 68–100) | 45.0 % | 0 |
| tools | selection | medium | 8 | 12.5 % (1/8; IC95 2–47) | 12.5 % (1/8; IC95 2–47) | 5.0 % | 0 |
| tools | selection | hard | 8 | 0.0 % (0/8; IC95 0–32) | 0.0 % (0/8; IC95 0–32) | 0.0 % | 0 |
| tools | composition | easy | 8 | 0.0 % (0/8; IC95 0–32) | 12.5 % (1/8; IC95 2–47) | 2.5 % | 0 |
| tools | composition | medium | 7 | 0.0 % (0/7; IC95 0–35) | 0.0 % (0/7; IC95 0–35) | 0.0 % | 0 |
| tools | composition | hard | 7 | 0.0 % (0/7; IC95 0–35) | 0.0 % (0/7; IC95 0–35) | 0.0 % | 0 |
| visible | availability | easy | 8 | 0.0 % (0/8; IC95 0–32) | 12.5 % (1/8; IC95 2–47) | 2.5 % | 0 |
| visible | availability | medium | 8 | 0.0 % (0/8; IC95 0–32) | 0.0 % (0/8; IC95 0–32) | 0.0 % | 0 |
| visible | availability | hard | 8 | 0.0 % (0/8; IC95 0–32) | 12.5 % (1/8; IC95 2–47) | 2.5 % | 0 |
| visible | selection | easy | 8 | 37.5 % (3/8; IC95 14–69) | 100.0 % (8/8; IC95 68–100) | 37.5 % | 0 |
| visible | selection | medium | 8 | 12.5 % (1/8; IC95 2–47) | 37.5 % (3/8; IC95 14–69) | 7.5 % | 0 |
| visible | selection | hard | 8 | 0.0 % (0/8; IC95 0–32) | 12.5 % (1/8; IC95 2–47) | 2.5 % | 0 |
| visible | composition | easy | 8 | 0.0 % (0/8; IC95 0–32) | 25.0 % (2/8; IC95 7–59) | 5.0 % | 0 |
| visible | composition | medium | 7 | 0.0 % (0/7; IC95 0–35) | 14.3 % (1/7; IC95 3–51) | 2.9 % | 0 |
| visible | composition | hard | 7 | 14.3 % (1/7; IC95 3–51) | 14.3 % (1/7; IC95 3–51) | 5.7 % | 0 |

## Comparación con y sin herramientas

| Modelo | Familia | Nivel | Visible pass@1 | Herramientas pass@1 | Dif. (h − v) | Visible pass@5 | Herramientas pass@5 |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-0.6B+think` | availability | easy | 0.0 % (0/8; IC95 0–32) | 0.0 % (0/8; IC95 0–32) | +0.0 pts | 12.5 % (1/8; IC95 2–47) | 37.5 % (3/8; IC95 14–69) |
| `Qwen/Qwen3-0.6B+think` | availability | hard | 0.0 % (0/8; IC95 0–32) | 12.5 % (1/8; IC95 2–47) | +12.5 pts | 12.5 % (1/8; IC95 2–47) | 12.5 % (1/8; IC95 2–47) |
| `Qwen/Qwen3-0.6B+think` | availability | medium | 0.0 % (0/8; IC95 0–32) | 37.5 % (3/8; IC95 14–69) | +37.5 pts | 0.0 % (0/8; IC95 0–32) | 50.0 % (4/8; IC95 22–78) |
| `Qwen/Qwen3-0.6B+think` | composition | easy | 0.0 % (0/8; IC95 0–32) | 0.0 % (0/8; IC95 0–32) | +0.0 pts | 25.0 % (2/8; IC95 7–59) | 12.5 % (1/8; IC95 2–47) |
| `Qwen/Qwen3-0.6B+think` | composition | hard | 14.3 % (1/7; IC95 3–51) | 0.0 % (0/7; IC95 0–35) | -14.3 pts | 14.3 % (1/7; IC95 3–51) | 0.0 % (0/7; IC95 0–35) |
| `Qwen/Qwen3-0.6B+think` | composition | medium | 0.0 % (0/7; IC95 0–35) | 0.0 % (0/7; IC95 0–35) | +0.0 pts | 14.3 % (1/7; IC95 3–51) | 0.0 % (0/7; IC95 0–35) |
| `Qwen/Qwen3-0.6B+think` | selection | easy | 37.5 % (3/8; IC95 14–69) | 50.0 % (4/8; IC95 22–78) | +12.5 pts | 100.0 % (8/8; IC95 68–100) | 100.0 % (8/8; IC95 68–100) |
| `Qwen/Qwen3-0.6B+think` | selection | hard | 0.0 % (0/8; IC95 0–32) | 0.0 % (0/8; IC95 0–32) | +0.0 pts | 12.5 % (1/8; IC95 2–47) | 0.0 % (0/8; IC95 0–32) |
| `Qwen/Qwen3-0.6B+think` | selection | medium | 12.5 % (1/8; IC95 2–47) | 12.5 % (1/8; IC95 2–47) | +0.0 pts | 37.5 % (3/8; IC95 14–69) | 12.5 % (1/8; IC95 2–47) |

### Diagnóstico de herramientas (por muestra)

| Modelo | Familia | Nivel | Llamadas válidas | Argumentos correctos | Datos requeridos | Límite excedido | Correcta sin recompensa |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-0.6B+think` | availability | easy | 85.0 % (34/40) | 85.0 % (34/40) | 100.0 % (40/40) | 0.0 % (0/40) | 0.0 % (0/40) |
| `Qwen/Qwen3-0.6B+think` | availability | medium | 100.0 % (40/40) | 100.0 % (40/40) | 100.0 % (40/40) | 0.0 % (0/40) | 0.0 % (0/40) |
| `Qwen/Qwen3-0.6B+think` | availability | hard | 100.0 % (40/40) | 100.0 % (40/40) | 85.0 % (34/40) | 0.0 % (0/40) | 0.0 % (0/40) |
| `Qwen/Qwen3-0.6B+think` | selection | easy | 95.0 % (38/40) | 92.5 % (37/40) | 90.0 % (36/40) | 0.0 % (0/40) | 0.0 % (0/40) |
| `Qwen/Qwen3-0.6B+think` | selection | medium | 87.5 % (35/40) | 87.5 % (35/40) | 35.0 % (14/40) | 0.0 % (0/40) | 0.0 % (0/40) |
| `Qwen/Qwen3-0.6B+think` | selection | hard | 95.0 % (38/40) | 95.0 % (38/40) | 27.5 % (11/40) | 0.0 % (0/40) | 0.0 % (0/40) |
| `Qwen/Qwen3-0.6B+think` | composition | easy | 87.5 % (35/40) | 87.5 % (35/40) | 90.0 % (36/40) | 0.0 % (0/40) | 0.0 % (0/40) |
| `Qwen/Qwen3-0.6B+think` | composition | medium | 54.3 % (19/35) | 54.3 % (19/35) | 31.4 % (11/35) | 0.0 % (0/35) | 0.0 % (0/35) |
| `Qwen/Qwen3-0.6B+think` | composition | hard | 62.9 % (22/35) | 62.9 % (22/35) | 11.4 % (4/35) | 0.0 % (0/35) | 0.0 % (0/35) |

`Correcta sin recompensa` cuenta respuestas finales correctas que no recibieron recompensa, por ejemplo sin haber obtenido los datos: una señal de adivinación.

## Comparación con líneas base

Cada regla se evalúa con `verify_final_text` sobre las mismas instancias que los rollouts. Las triviales y de azar no leen el inventario. Las marcadas como `error_razonable` o azar contado sí lo leen: son errores plausibles, no azar. El control usa `expected` y solo valida el formato; no se compara con los modelos. Las reglas miden solo el texto final; en `tools` el modelo necesita además evidencia.

| Regla | Clase | avail/easy | avail/medium | avail/hard | selec/easy | selec/medium | selec/hard | compo/easy | compo/medium | compo/hard |
|---|---|---|---|---|---|---|---|---|---|---|
| `control_expected` | control | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 7/7 | 7/7 |
| `ignorar_reservas` | error_razonable | 3/8 | 4/8 | 3/8 | 0/8 | 0/8 | 1/8 | 3/8 | 2/7 | 3/7 |
| `no_descontar_stock` | error_razonable | — | — | — | — | — | — | 3/8 | 2/7 | 3/7 |
| `nunca_alcanza` | trivial | 0/8 | 0/8 | 0/8 | — | — | — | — | — | — |
| `primera_sucursal` | trivial | — | — | — | 0/8 | 0/8 | 1/8 | — | — | — |
| `primera_sucursal_contada` | error_razonable | — | — | — | 3/8 | 2/8 | 2/8 | — | — | — |
| `siempre_alcanza` | trivial | 3/8 | 4/8 | 3/8 | — | — | — | — | — | — |
| `sucursal_azar` | azar | — | — | — | 0/8 | 0/8 | 0/8 | — | — | — |
| `sucursal_azar_contada` | azar | — | — | — | 1/8 | 2/8 | 2/8 | — | — | — |
| `todo_atendido` | trivial | — | — | — | — | — | — | 3/8 | 2/7 | 3/7 |

Cada fila se compara con la tasa de la regla sobre las mismas instancias de ese modelo y condición. `supera` significa que el límite inferior del IC de pass@1 queda sobre la tasa de la regla; `no_distinguible`, que la regla cae dentro del IC. Son muchas comparaciones con IC95 sin corrección por multiplicidad: algún `supera` puede ser casual.

| Modelo | Condición | Familia | Nivel | Mejor sin inventario | pass@1 frente a ella | Mejor con inventario | pass@1 frente a ella |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-0.6B+think` | tools | availability | easy | siempre_alcanza 37.5 % | por_debajo | ignorar_reservas 37.5 % | por_debajo |
| `Qwen/Qwen3-0.6B+think` | tools | availability | medium | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-0.6B+think` | tools | availability | hard | siempre_alcanza 37.5 % | no_distinguible | ignorar_reservas 37.5 % | no_distinguible |
| `Qwen/Qwen3-0.6B+think` | tools | selection | easy | primera_sucursal 0.0 % | supera | primera_sucursal_contada 37.5 % | no_distinguible |
| `Qwen/Qwen3-0.6B+think` | tools | selection | medium | primera_sucursal 0.0 % | supera | primera_sucursal_contada 25.0 % | no_distinguible |
| `Qwen/Qwen3-0.6B+think` | tools | selection | hard | primera_sucursal 12.5 % | no_distinguible | primera_sucursal_contada 25.0 % | no_distinguible |
| `Qwen/Qwen3-0.6B+think` | tools | composition | easy | todo_atendido 37.5 % | por_debajo | ignorar_reservas 37.5 % | por_debajo |
| `Qwen/Qwen3-0.6B+think` | tools | composition | medium | todo_atendido 28.6 % | no_distinguible | ignorar_reservas 28.6 % | no_distinguible |
| `Qwen/Qwen3-0.6B+think` | tools | composition | hard | todo_atendido 42.9 % | por_debajo | ignorar_reservas 42.9 % | por_debajo |
| `Qwen/Qwen3-0.6B+think` | visible | availability | easy | siempre_alcanza 37.5 % | por_debajo | ignorar_reservas 37.5 % | por_debajo |
| `Qwen/Qwen3-0.6B+think` | visible | availability | medium | siempre_alcanza 50.0 % | por_debajo | ignorar_reservas 50.0 % | por_debajo |
| `Qwen/Qwen3-0.6B+think` | visible | availability | hard | siempre_alcanza 37.5 % | por_debajo | ignorar_reservas 37.5 % | por_debajo |
| `Qwen/Qwen3-0.6B+think` | visible | selection | easy | primera_sucursal 0.0 % | supera | primera_sucursal_contada 37.5 % | no_distinguible |
| `Qwen/Qwen3-0.6B+think` | visible | selection | medium | primera_sucursal 0.0 % | supera | primera_sucursal_contada 25.0 % | no_distinguible |
| `Qwen/Qwen3-0.6B+think` | visible | selection | hard | primera_sucursal 12.5 % | no_distinguible | primera_sucursal_contada 25.0 % | no_distinguible |
| `Qwen/Qwen3-0.6B+think` | visible | composition | easy | todo_atendido 37.5 % | por_debajo | ignorar_reservas 37.5 % | por_debajo |
| `Qwen/Qwen3-0.6B+think` | visible | composition | medium | todo_atendido 28.6 % | no_distinguible | ignorar_reservas 28.6 % | no_distinguible |
| `Qwen/Qwen3-0.6B+think` | visible | composition | hard | todo_atendido 42.9 % | no_distinguible | ignorar_reservas 42.9 % | no_distinguible |

## Distribución de errores

| Modelo | Condición | error_type | Muestras | Porcentaje |
|---|---|---|---|---|
| `Qwen/Qwen3-0.6B+think` | tools | `wrong_value` | 144 | 41.1 % |
| `Qwen/Qwen3-0.6B+think` | tools | `no_answer_block` | 97 | 27.7 % |
| `Qwen/Qwen3-0.6B+think` | tools | `invalid_value` | 61 | 17.4 % |
| `Qwen/Qwen3-0.6B+think` | tools | `ok` | 30 | 8.6 % |
| `Qwen/Qwen3-0.6B+think` | tools | `missing_field` | 8 | 2.3 % |
| `Qwen/Qwen3-0.6B+think` | tools | `unknown_field` | 7 | 2.0 % |
| `Qwen/Qwen3-0.6B+think` | tools | `contradiction` | 2 | 0.6 % |
| `Qwen/Qwen3-0.6B+think` | tools | `multiple_answer_blocks` | 1 | 0.3 % |
| `Qwen/Qwen3-0.6B+think` | visible | `wrong_value` | 204 | 58.3 % |
| `Qwen/Qwen3-0.6B+think` | visible | `no_answer_block` | 67 | 19.1 % |
| `Qwen/Qwen3-0.6B+think` | visible | `invalid_value` | 36 | 10.3 % |
| `Qwen/Qwen3-0.6B+think` | visible | `ok` | 26 | 7.4 % |
| `Qwen/Qwen3-0.6B+think` | visible | `unknown_field` | 11 | 3.1 % |
| `Qwen/Qwen3-0.6B+think` | visible | `multiple_answer_blocks` | 4 | 1.1 % |
| `Qwen/Qwen3-0.6B+think` | visible | `ambiguous_value` | 2 | 0.6 % |

| Modelo | Condición | Muestras | parser_error | Contradicción |
|---|---|---|---|---|
| `Qwen/Qwen3-0.6B+think` | tools | 350 | 49.7 % (174/350) | 0.6 % (2/350) |
| `Qwen/Qwen3-0.6B+think` | visible | 350 | 34.3 % (120/350) | 0.0 % (0/350) |

## Clasificación según §6 de la propuesta (orientativa)

**Es una lectura orientativa, no una decisión ni un umbral del curso.** La propuesta define las categorías; los números son nuestros y están en `summary.json`. La certeza es `firme` solo si el IC completo cae en la categoría (y, si la categoría depende de la ganancia de pass@k sobre pass@1, también el IC de esa ganancia). Con un IC más ancho que 30 puntos se marca `IC muy ancho`: esa categoría es una lectura provisional y no debe usarse para decidir. `(solo pass@1)` indica que no hubo pass@k utilizable (sin muestras o con denominador distinto por instancias incompletas); el motivo está en `summary.json`.

**18 de 18 celdas tienen un IC muy ancho.** Hacen falta más instancias antes de sacar conclusiones de ellas.

| Modelo | Condición | Familia | Nivel | Lectura | Certeza | Frente a regla trivial | Acción sugerida |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-0.6B+think` | tools | availability | easy | pass@1 cercano a 0 %, pero pass@k mayor | IC muy ancho, no concluir | por_debajo | Señal escasa pero presente: candidata a SFT antes de RL |
| `Qwen/Qwen3-0.6B+think` | tools | availability | medium | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-0.6B+think` | tools | availability | hard | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-0.6B+think` | tools | selection | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-0.6B+think` | tools | selection | medium | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | supera | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-0.6B+think` | tools | selection | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-0.6B+think` | tools | composition | easy | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | por_debajo | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-0.6B+think` | tools | composition | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-0.6B+think` | tools | composition | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-0.6B+think` | visible | availability | easy | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | por_debajo | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-0.6B+think` | visible | availability | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-0.6B+think` | visible | availability | hard | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | por_debajo | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-0.6B+think` | visible | selection | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-0.6B+think` | visible | selection | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-0.6B+think` | visible | selection | hard | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-0.6B+think` | visible | composition | easy | pass@1 cercano a 0 %, pero pass@k mayor | IC muy ancho, no concluir | por_debajo | Señal escasa pero presente: candidata a SFT antes de RL |
| `Qwen/Qwen3-0.6B+think` | visible | composition | medium | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-0.6B+think` | visible | composition | hard | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |

### Entre condiciones

| Modelo | Familia | Nivel | Lectura | Certeza | Acción sugerida |
|---|---|---|---|---|---|
| `Qwen/Qwen3-0.6B+think` | availability | easy | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-0.6B+think` | availability | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-0.6B+think` | availability | medium | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-0.6B+think` | composition | easy | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-0.6B+think` | composition | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-0.6B+think` | composition | medium | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-0.6B+think` | selection | easy | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-0.6B+think` | selection | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-0.6B+think` | selection | medium | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |

## Costo

| Modelo | Condición | Muestras | Tokens nuevos por muestra | s por muestra | Horas (suma de `usage.seconds`) | Llegó al tope de tokens |
|---|---|---|---|---|---|---|
| `Qwen/Qwen3-0.6B+think` | tools | 350 | 2817 | 70.68 | 6.87 | 10.0 % (35/350) |
| `Qwen/Qwen3-0.6B+think` | visible | 350 | 1618 | 41.13 | 4.00 | 10.9 % (38/350) |

`Llegó al tope de tokens` cuenta las muestras con alguna generación cortada por `max_new_tokens`, según `usage.stop_reasons`. En rollouts sin ese campo es una cota inferior. Un valor alto, sobre todo con thinking, indica respuestas cortadas.

## Instancias incompletas

Ninguna: todas las instancias vistas tienen 5 muestras.

## Revisión manual

`muestra_errores.jsonl` tiene 168 rollouts fallidos, estratificados por modelo, condición, familia, dificultad y error_type (hasta 3 por estrato). Sirve para verificar a mano si el verificador rechazó bien.
