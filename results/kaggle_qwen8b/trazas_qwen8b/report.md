# Informe del piloto

- Etapa: `trazas`; split `train`; semilla base 2026; 10 por celda; 2 muestras.
- Entorno: GPU Tesla T4; torch 2.11.0+cu130; transformers 5.20.2.
- Código: `d4ea15d25f41ff8f`; fecha 2026-11-12T20:43:33+00:00.
- Archivos leídos: 1. Rollouts válidos: 142.
- Problemas de carga: ninguno.

## Estado por modelo

| Modelo | Estado | Rollouts | s/rollout (reloj) | Error |
|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | completo | 142/142 | 101.718 | — |

## Resultados por modelo, condición, familia y dificultad

pass@1 usa la muestra 0 de cada instancia. pass@2 cuenta las instancias con al menos un acierto entre las primeras 2 muestras. El IC95 es de Wilson sobre instancias. La tasa por muestra se da sin IC porque las muestras están correlacionadas.

**Esta corrida tiene 2 muestras por instancia, así que aquí no existe pass@5.** pass@2 no es comparable con pass@5.

### `Qwen/Qwen3-8B+think`

| Condición | Familia | Nivel | n inst. | pass@1 | pass@2 | Tasa por muestra | Incompletas k=2 |
|---|---|---|---|---|---|---|---|
| tools | availability | easy | 3 | 100.0 % (3/3; IC95 44–100) | 100.0 % (3/3; IC95 44–100) | 100.0 % | 0 |
| tools | availability | medium | 4 | 100.0 % (4/4; IC95 51–100) | 100.0 % (4/4; IC95 51–100) | 100.0 % | 0 |
| tools | availability | hard | 1 | 100.0 % (1/1; IC95 21–100) | 100.0 % (1/1; IC95 21–100) | 100.0 % | 0 |
| tools | selection | easy | 1 | 100.0 % (1/1; IC95 21–100) | 100.0 % (1/1; IC95 21–100) | 100.0 % | 0 |
| tools | selection | medium | 1 | 100.0 % (1/1; IC95 21–100) | 100.0 % (1/1; IC95 21–100) | 100.0 % | 0 |
| tools | selection | hard | 5 | 100.0 % (5/5; IC95 57–100) | 100.0 % (5/5; IC95 57–100) | 100.0 % | 0 |
| tools | composition | easy | 10 | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) | 100.0 % | 0 |
| tools | composition | medium | 9 | 88.9 % (8/9; IC95 57–98) | 100.0 % (9/9; IC95 70–100) | 88.9 % | 0 |
| tools | composition | hard | 10 | 40.0 % (4/10; IC95 17–69) | 40.0 % (4/10; IC95 17–69) | 25.0 % | 0 |
| visible | availability | easy | 1 | 100.0 % (1/1; IC95 21–100) | 100.0 % (1/1; IC95 21–100) | 100.0 % | 0 |
| visible | availability | medium | 2 | 100.0 % (2/2; IC95 34–100) | 100.0 % (2/2; IC95 34–100) | 100.0 % | 0 |
| visible | availability | hard | 2 | 100.0 % (2/2; IC95 34–100) | 100.0 % (2/2; IC95 34–100) | 100.0 % | 0 |
| visible | selection | easy | 1 | 100.0 % (1/1; IC95 21–100) | 100.0 % (1/1; IC95 21–100) | 100.0 % | 0 |
| visible | selection | hard | 2 | 100.0 % (2/2; IC95 34–100) | 100.0 % (2/2; IC95 34–100) | 100.0 % | 0 |
| visible | composition | easy | 2 | 100.0 % (2/2; IC95 34–100) | 100.0 % (2/2; IC95 34–100) | 100.0 % | 0 |
| visible | composition | medium | 7 | 85.7 % (6/7; IC95 49–97) | 100.0 % (7/7; IC95 65–100) | 92.9 % | 0 |
| visible | composition | hard | 10 | 30.0 % (3/10; IC95 11–60) | 60.0 % (6/10; IC95 31–83) | 40.0 % | 0 |

## Comparación con y sin herramientas

| Modelo | Familia | Nivel | Visible pass@1 | Herramientas pass@1 | Dif. (h − v) | Visible pass@2 | Herramientas pass@2 |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | availability | easy | 100.0 % (1/1; IC95 21–100) | 100.0 % (3/3; IC95 44–100) | +0.0 pts | 100.0 % (1/1; IC95 21–100) | 100.0 % (3/3; IC95 44–100) |
| `Qwen/Qwen3-8B+think` | availability | hard | 100.0 % (2/2; IC95 34–100) | 100.0 % (1/1; IC95 21–100) | +0.0 pts | 100.0 % (2/2; IC95 34–100) | 100.0 % (1/1; IC95 21–100) |
| `Qwen/Qwen3-8B+think` | availability | medium | 100.0 % (2/2; IC95 34–100) | 100.0 % (4/4; IC95 51–100) | +0.0 pts | 100.0 % (2/2; IC95 34–100) | 100.0 % (4/4; IC95 51–100) |
| `Qwen/Qwen3-8B+think` | composition | easy | 100.0 % (2/2; IC95 34–100) | 100.0 % (10/10; IC95 72–100) | +0.0 pts | 100.0 % (2/2; IC95 34–100) | 100.0 % (10/10; IC95 72–100) |
| `Qwen/Qwen3-8B+think` | composition | hard | 30.0 % (3/10; IC95 11–60) | 40.0 % (4/10; IC95 17–69) | +10.0 pts | 60.0 % (6/10; IC95 31–83) | 40.0 % (4/10; IC95 17–69) |
| `Qwen/Qwen3-8B+think` | composition | medium | 85.7 % (6/7; IC95 49–97) | 88.9 % (8/9; IC95 57–98) | +3.2 pts | 100.0 % (7/7; IC95 65–100) | 100.0 % (9/9; IC95 70–100) |
| `Qwen/Qwen3-8B+think` | selection | easy | 100.0 % (1/1; IC95 21–100) | 100.0 % (1/1; IC95 21–100) | +0.0 pts | 100.0 % (1/1; IC95 21–100) | 100.0 % (1/1; IC95 21–100) |
| `Qwen/Qwen3-8B+think` | selection | hard | 100.0 % (2/2; IC95 34–100) | 100.0 % (5/5; IC95 57–100) | +0.0 pts | 100.0 % (2/2; IC95 34–100) | 100.0 % (5/5; IC95 57–100) |
| `Qwen/Qwen3-8B+think` | selection | medium | ausente | 100.0 % (1/1; IC95 21–100) | n/d | — | 100.0 % (1/1; IC95 21–100) |

### Diagnóstico de herramientas (por muestra)

| Modelo | Familia | Nivel | Llamadas válidas | Argumentos correctos | Datos requeridos | Límite excedido | Correcta sin recompensa |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | availability | easy | 100.0 % (6/6) | 100.0 % (6/6) | 100.0 % (6/6) | 0.0 % (0/6) | 0.0 % (0/6) |
| `Qwen/Qwen3-8B+think` | availability | medium | 100.0 % (8/8) | 100.0 % (8/8) | 100.0 % (8/8) | 0.0 % (0/8) | 0.0 % (0/8) |
| `Qwen/Qwen3-8B+think` | availability | hard | 100.0 % (2/2) | 100.0 % (2/2) | 100.0 % (2/2) | 0.0 % (0/2) | 0.0 % (0/2) |
| `Qwen/Qwen3-8B+think` | selection | easy | 100.0 % (2/2) | 100.0 % (2/2) | 100.0 % (2/2) | 0.0 % (0/2) | 0.0 % (0/2) |
| `Qwen/Qwen3-8B+think` | selection | medium | 100.0 % (2/2) | 100.0 % (2/2) | 100.0 % (2/2) | 0.0 % (0/2) | 0.0 % (0/2) |
| `Qwen/Qwen3-8B+think` | selection | hard | 100.0 % (10/10) | 100.0 % (10/10) | 100.0 % (10/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-8B+think` | composition | easy | 100.0 % (20/20) | 100.0 % (20/20) | 100.0 % (20/20) | 0.0 % (0/20) | 0.0 % (0/20) |
| `Qwen/Qwen3-8B+think` | composition | medium | 94.4 % (17/18) | 94.4 % (17/18) | 94.4 % (17/18) | 0.0 % (0/18) | 0.0 % (0/18) |
| `Qwen/Qwen3-8B+think` | composition | hard | 85.0 % (17/20) | 85.0 % (17/20) | 80.0 % (16/20) | 0.0 % (0/20) | 0.0 % (0/20) |

`Correcta sin recompensa` cuenta respuestas finales correctas que no recibieron recompensa, por ejemplo sin haber obtenido los datos: una señal de adivinación.

## Comparación con líneas base

Cada regla se evalúa con `verify_final_text` sobre las mismas instancias que los rollouts. Las triviales y de azar no leen el inventario. Las marcadas como `error_razonable` o azar contado sí lo leen: son errores plausibles, no azar. El control usa `expected` y solo valida el formato; no se compara con los modelos. Las reglas miden solo el texto final; en `tools` el modelo necesita además evidencia.

| Regla | Clase | avail/easy | avail/medium | avail/hard | selec/easy | selec/medium | selec/hard | compo/easy | compo/medium | compo/hard |
|---|---|---|---|---|---|---|---|---|---|---|
| `control_expected` | control | 3/3 | 5/5 | 3/3 | 2/2 | 1/1 | 6/6 | 10/10 | 10/10 | 10/10 |
| `ignorar_reservas` | error_razonable | 2/3 | 4/5 | 2/3 | 0/2 | 0/1 | 0/6 | 3/10 | 0/10 | 0/10 |
| `no_descontar_stock` | error_razonable | — | — | — | — | — | — | 3/10 | 0/10 | 0/10 |
| `nunca_alcanza` | trivial | 0/3 | 0/5 | 0/3 | — | — | — | — | — | — |
| `primera_sucursal` | trivial | — | — | — | 0/2 | 0/1 | 0/6 | — | — | — |
| `primera_sucursal_contada` | error_razonable | — | — | — | 1/2 | 0/1 | 1/6 | — | — | — |
| `siempre_alcanza` | trivial | 2/3 | 4/5 | 2/3 | — | — | — | — | — | — |
| `sucursal_azar` | azar | — | — | — | 0/2 | 0/1 | 0/6 | — | — | — |
| `sucursal_azar_contada` | azar | — | — | — | 2/2 | 0/1 | 0/6 | — | — | — |
| `todo_atendido` | trivial | — | — | — | — | — | — | 3/10 | 0/10 | 0/10 |

Cada fila se compara con la tasa de la regla sobre las mismas instancias de ese modelo y condición. `supera` significa que el límite inferior del IC de pass@1 queda sobre la tasa de la regla; `no_distinguible`, que la regla cae dentro del IC. Son muchas comparaciones con IC95 sin corrección por multiplicidad: algún `supera` puede ser casual.

| Modelo | Condición | Familia | Nivel | Mejor sin inventario | pass@1 frente a ella | Mejor con inventario | pass@1 frente a ella |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | tools | availability | easy | siempre_alcanza 66.7 % | no_distinguible | ignorar_reservas 66.7 % | no_distinguible |
| `Qwen/Qwen3-8B+think` | tools | availability | medium | siempre_alcanza 75.0 % | no_distinguible | ignorar_reservas 75.0 % | no_distinguible |
| `Qwen/Qwen3-8B+think` | tools | availability | hard | siempre_alcanza 100.0 % | no_distinguible | ignorar_reservas 100.0 % | no_distinguible |
| `Qwen/Qwen3-8B+think` | tools | selection | easy | primera_sucursal 0.0 % | supera | sucursal_azar_contada 100.0 % | no_distinguible |
| `Qwen/Qwen3-8B+think` | tools | selection | medium | primera_sucursal 0.0 % | supera | ignorar_reservas 0.0 % | supera |
| `Qwen/Qwen3-8B+think` | tools | selection | hard | primera_sucursal 0.0 % | supera | ignorar_reservas 0.0 % | supera |
| `Qwen/Qwen3-8B+think` | tools | composition | easy | todo_atendido 30.0 % | supera | ignorar_reservas 30.0 % | supera |
| `Qwen/Qwen3-8B+think` | tools | composition | medium | todo_atendido 0.0 % | supera | ignorar_reservas 0.0 % | supera |
| `Qwen/Qwen3-8B+think` | tools | composition | hard | todo_atendido 0.0 % | supera | ignorar_reservas 0.0 % | supera |
| `Qwen/Qwen3-8B+think` | visible | availability | easy | siempre_alcanza 100.0 % | no_distinguible | ignorar_reservas 100.0 % | no_distinguible |
| `Qwen/Qwen3-8B+think` | visible | availability | medium | siempre_alcanza 100.0 % | no_distinguible | ignorar_reservas 100.0 % | no_distinguible |
| `Qwen/Qwen3-8B+think` | visible | availability | hard | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-8B+think` | visible | selection | easy | primera_sucursal 0.0 % | supera | primera_sucursal_contada 100.0 % | no_distinguible |
| `Qwen/Qwen3-8B+think` | visible | selection | hard | primera_sucursal 0.0 % | supera | primera_sucursal_contada 50.0 % | no_distinguible |
| `Qwen/Qwen3-8B+think` | visible | composition | easy | todo_atendido 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-8B+think` | visible | composition | medium | todo_atendido 0.0 % | supera | ignorar_reservas 0.0 % | supera |
| `Qwen/Qwen3-8B+think` | visible | composition | hard | todo_atendido 0.0 % | supera | ignorar_reservas 0.0 % | supera |

## Distribución de errores

| Modelo | Condición | error_type | Muestras | Porcentaje |
|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | tools | `ok` | 71 | 80.7 % |
| `Qwen/Qwen3-8B+think` | tools | `wrong_value` | 12 | 13.6 % |
| `Qwen/Qwen3-8B+think` | tools | `no_answer_block` | 5 | 5.7 % |
| `Qwen/Qwen3-8B+think` | visible | `ok` | 41 | 75.9 % |
| `Qwen/Qwen3-8B+think` | visible | `wrong_value` | 12 | 22.2 % |
| `Qwen/Qwen3-8B+think` | visible | `no_answer_block` | 1 | 1.9 % |

| Modelo | Condición | Muestras | parser_error | Contradicción |
|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | tools | 88 | 5.7 % (5/88) | 0.0 % (0/88) |
| `Qwen/Qwen3-8B+think` | visible | 54 | 1.9 % (1/54) | 0.0 % (0/54) |

## Clasificación según §6 de la propuesta (orientativa)

**Es una lectura orientativa, no una decisión ni un umbral del curso.** La propuesta define las categorías; los números son nuestros y están en `summary.json`. La certeza es `firme` solo si el IC completo cae en la categoría (y, si la categoría depende de la ganancia de pass@k sobre pass@1, también el IC de esa ganancia). Con un IC más ancho que 30 puntos se marca `IC muy ancho`: esa categoría es una lectura provisional y no debe usarse para decidir. `(solo pass@1)` indica que no hubo pass@k utilizable (sin muestras o con denominador distinto por instancias incompletas); el motivo está en `summary.json`.

**16 de 17 celdas tienen un IC muy ancho.** Hacen falta más instancias antes de sacar conclusiones de ellas.

| Modelo | Condición | Familia | Nivel | Lectura | Certeza | Frente a regla trivial | Acción sugerida |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | tools | availability | easy | Éxito cercano a 100 % | IC muy ancho, no concluir | no_distinguible | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | availability | medium | Éxito cercano a 100 % | IC muy ancho, no concluir | no_distinguible | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | availability | hard | Éxito cercano a 100 % | IC muy ancho, no concluir | no_distinguible | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | selection | easy | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | selection | medium | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | selection | hard | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | composition | easy | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | composition | medium | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | supera | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-8B+think` | tools | composition | hard | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | supera | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-8B+think` | visible | availability | easy | Éxito cercano a 100 % | IC muy ancho, no concluir | no_distinguible | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | availability | medium | Éxito cercano a 100 % | IC muy ancho, no concluir | no_distinguible | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | availability | hard | Éxito cercano a 100 % | IC muy ancho, no concluir | no_distinguible | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | selection | easy | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | selection | hard | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | composition | easy | Éxito cercano a 100 % | IC muy ancho, no concluir | no_distinguible | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | composition | medium | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | supera | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-8B+think` | visible | composition | hard | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |

### Entre condiciones

| Modelo | Familia | Nivel | Lectura | Certeza | Acción sugerida |
|---|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | availability | easy | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-8B+think` | availability | hard | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-8B+think` | availability | medium | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-8B+think` | composition | easy | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-8B+think` | composition | hard | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-8B+think` | composition | medium | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-8B+think` | selection | easy | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-8B+think` | selection | hard | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-8B+think` | selection | medium | Falta una condición | sin datos | No comparable |

## Costo

| Modelo | Condición | Muestras | Tokens nuevos por muestra | s por muestra | Horas (suma de `usage.seconds`) | Llegó al tope de tokens |
|---|---|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | tools | 88 | 2298 | 120.65 | 2.95 | 5.7 % (5/88) |
| `Qwen/Qwen3-8B+think` | visible | 54 | 1665 | 93.52 | 1.40 | 1.9 % (1/54) |

`Llegó al tope de tokens` cuenta las muestras con alguna generación cortada por `max_new_tokens`, según `usage.stop_reasons`. En rollouts sin ese campo es una cota inferior. Un valor alto, sobre todo con thinking, indica respuestas cortadas.

## Instancias incompletas

Ninguna: todas las instancias vistas tienen 2 muestras.

## Revisión manual

`muestra_errores.jsonl` tiene 13 rollouts fallidos, estratificados por modelo, condición, familia, dificultad y error_type (hasta 3 por estrato). Sirve para verificar a mano si el verificador rechazó bien.
