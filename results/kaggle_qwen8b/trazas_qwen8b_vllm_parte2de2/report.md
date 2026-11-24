# Informe del piloto

- Etapa: `trazas`; split `train`; semilla base 2026; 130 por celda; 2 muestras.
- Entorno: GPU Tesla T4; torch 2.14.0+cu130; transformers 5.20.2.
- Código: `c0d1e2342820d4c2`; fecha 2026-11-24T05:55:49+00:00.
- Archivos leídos: 1. Rollouts válidos: 2340.
- Problemas de carga: ninguno.

## Estado por modelo

| Modelo | Estado | Rollouts | s/rollout (reloj) | Error |
|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | completo | 2340/2340 | 7.729 | — |

## Resultados por modelo, condición, familia y dificultad

pass@1 usa la muestra 0 de cada instancia. pass@2 cuenta las instancias con al menos un acierto entre las primeras 2 muestras. El IC95 es de Wilson sobre instancias. La tasa por muestra se da sin IC porque las muestras están correlacionadas.

**Esta corrida tiene 2 muestras por instancia, así que aquí no existe pass@5.** pass@2 no es comparable con pass@5.

### `Qwen/Qwen3-8B+think`

| Condición | Familia | Nivel | n inst. | pass@1 | pass@2 | Tasa por muestra | Incompletas k=2 |
|---|---|---|---|---|---|---|---|
| tools | availability | easy | 65 | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | 100.0 % | 0 |
| tools | availability | medium | 65 | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | 100.0 % | 0 |
| tools | availability | hard | 65 | 98.5 % (64/65; IC95 92–100) | 100.0 % (65/65; IC95 94–100) | 99.2 % | 0 |
| tools | selection | easy | 65 | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | 100.0 % | 0 |
| tools | selection | medium | 65 | 96.9 % (63/65; IC95 89–99) | 100.0 % (65/65; IC95 94–100) | 97.7 % | 0 |
| tools | selection | hard | 65 | 93.8 % (61/65; IC95 85–98) | 98.5 % (64/65; IC95 92–100) | 93.8 % | 0 |
| tools | composition | easy | 65 | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | 100.0 % | 0 |
| tools | composition | medium | 65 | 86.2 % (56/65; IC95 76–93) | 93.8 % (61/65; IC95 85–98) | 85.4 % | 0 |
| tools | composition | hard | 65 | 56.9 % (37/65; IC95 45–68) | 70.8 % (46/65; IC95 59–80) | 51.5 % | 0 |
| visible | availability | easy | 65 | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | 100.0 % | 0 |
| visible | availability | medium | 65 | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | 99.2 % | 0 |
| visible | availability | hard | 65 | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | 100.0 % | 0 |
| visible | selection | easy | 65 | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | 100.0 % | 0 |
| visible | selection | medium | 65 | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | 100.0 % | 0 |
| visible | selection | hard | 65 | 95.4 % (62/65; IC95 87–98) | 100.0 % (65/65; IC95 94–100) | 95.4 % | 0 |
| visible | composition | easy | 65 | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | 100.0 % | 0 |
| visible | composition | medium | 65 | 93.8 % (61/65; IC95 85–98) | 100.0 % (65/65; IC95 94–100) | 96.9 % | 0 |
| visible | composition | hard | 65 | 58.5 % (38/65; IC95 46–70) | 76.9 % (50/65; IC95 65–85) | 54.6 % | 0 |

## Comparación con y sin herramientas

| Modelo | Familia | Nivel | Visible pass@1 | Herramientas pass@1 | Dif. (h − v) | Visible pass@2 | Herramientas pass@2 |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | availability | easy | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | +0.0 pts | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) |
| `Qwen/Qwen3-8B+think` | availability | hard | 100.0 % (65/65; IC95 94–100) | 98.5 % (64/65; IC95 92–100) | -1.5 pts | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) |
| `Qwen/Qwen3-8B+think` | availability | medium | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | +0.0 pts | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) |
| `Qwen/Qwen3-8B+think` | composition | easy | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | +0.0 pts | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) |
| `Qwen/Qwen3-8B+think` | composition | hard | 58.5 % (38/65; IC95 46–70) | 56.9 % (37/65; IC95 45–68) | -1.5 pts | 76.9 % (50/65; IC95 65–85) | 70.8 % (46/65; IC95 59–80) |
| `Qwen/Qwen3-8B+think` | composition | medium | 93.8 % (61/65; IC95 85–98) | 86.2 % (56/65; IC95 76–93) | -7.7 pts | 100.0 % (65/65; IC95 94–100) | 93.8 % (61/65; IC95 85–98) |
| `Qwen/Qwen3-8B+think` | selection | easy | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) | +0.0 pts | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) |
| `Qwen/Qwen3-8B+think` | selection | hard | 95.4 % (62/65; IC95 87–98) | 93.8 % (61/65; IC95 85–98) | -1.5 pts | 100.0 % (65/65; IC95 94–100) | 98.5 % (64/65; IC95 92–100) |
| `Qwen/Qwen3-8B+think` | selection | medium | 100.0 % (65/65; IC95 94–100) | 96.9 % (63/65; IC95 89–99) | -3.1 pts | 100.0 % (65/65; IC95 94–100) | 100.0 % (65/65; IC95 94–100) |

### Diagnóstico de herramientas (por muestra)

| Modelo | Familia | Nivel | Llamadas válidas | Argumentos correctos | Datos requeridos | Límite excedido | Correcta sin recompensa |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | availability | easy | 100.0 % (130/130) | 100.0 % (130/130) | 100.0 % (130/130) | 0.0 % (0/130) | 0.0 % (0/130) |
| `Qwen/Qwen3-8B+think` | availability | medium | 100.0 % (130/130) | 100.0 % (130/130) | 100.0 % (130/130) | 0.0 % (0/130) | 0.0 % (0/130) |
| `Qwen/Qwen3-8B+think` | availability | hard | 100.0 % (130/130) | 100.0 % (130/130) | 100.0 % (130/130) | 0.0 % (0/130) | 0.0 % (0/130) |
| `Qwen/Qwen3-8B+think` | selection | easy | 100.0 % (130/130) | 100.0 % (130/130) | 100.0 % (130/130) | 0.0 % (0/130) | 0.0 % (0/130) |
| `Qwen/Qwen3-8B+think` | selection | medium | 100.0 % (130/130) | 100.0 % (130/130) | 100.0 % (130/130) | 0.0 % (0/130) | 0.0 % (0/130) |
| `Qwen/Qwen3-8B+think` | selection | hard | 100.0 % (130/130) | 100.0 % (130/130) | 100.0 % (130/130) | 0.0 % (0/130) | 0.0 % (0/130) |
| `Qwen/Qwen3-8B+think` | composition | easy | 100.0 % (130/130) | 100.0 % (130/130) | 100.0 % (130/130) | 0.0 % (0/130) | 0.0 % (0/130) |
| `Qwen/Qwen3-8B+think` | composition | medium | 98.5 % (128/130) | 98.5 % (128/130) | 97.7 % (127/130) | 0.0 % (0/130) | 0.0 % (0/130) |
| `Qwen/Qwen3-8B+think` | composition | hard | 94.6 % (123/130) | 94.6 % (123/130) | 90.8 % (118/130) | 0.0 % (0/130) | 0.0 % (0/130) |

`Correcta sin recompensa` cuenta respuestas finales correctas que no recibieron recompensa, por ejemplo sin haber obtenido los datos: una señal de adivinación.

## Comparación con líneas base

Cada regla se evalúa con `verify_final_text` sobre las mismas instancias que los rollouts. Las triviales y de azar no leen el inventario. Las marcadas como `error_razonable` o azar contado sí lo leen: son errores plausibles, no azar. El control usa `expected` y solo valida el formato; no se compara con los modelos. Las reglas miden solo el texto final; en `tools` el modelo necesita además evidencia.

| Regla | Clase | avail/easy | avail/medium | avail/hard | selec/easy | selec/medium | selec/hard | compo/easy | compo/medium | compo/hard |
|---|---|---|---|---|---|---|---|---|---|---|
| `control_expected` | control | 65/65 | 65/65 | 65/65 | 65/65 | 65/65 | 65/65 | 65/65 | 65/65 | 65/65 |
| `ignorar_reservas` | error_razonable | 28/65 | 29/65 | 30/65 | 7/65 | 5/65 | 2/65 | 10/65 | 8/65 | 10/65 |
| `no_descontar_stock` | error_razonable | — | — | — | — | — | — | 10/65 | 8/65 | 10/65 |
| `nunca_alcanza` | trivial | 2/65 | 0/65 | 0/65 | — | — | — | — | — | — |
| `primera_sucursal` | trivial | — | — | — | 7/65 | 4/65 | 2/65 | — | — | — |
| `primera_sucursal_contada` | error_razonable | — | — | — | 26/65 | 19/65 | 15/65 | — | — | — |
| `siempre_alcanza` | trivial | 28/65 | 29/65 | 30/65 | — | — | — | — | — | — |
| `sucursal_azar` | azar | — | — | — | 9/65 | 8/65 | 3/65 | — | — | — |
| `sucursal_azar_contada` | azar | — | — | — | 28/65 | 23/65 | 19/65 | — | — | — |
| `todo_atendido` | trivial | — | — | — | — | — | — | 10/65 | 8/65 | 10/65 |

Cada fila se compara con la tasa de la regla sobre las mismas instancias de ese modelo y condición. `supera` significa que el límite inferior del IC de pass@1 queda sobre la tasa de la regla; `no_distinguible`, que la regla cae dentro del IC. Son muchas comparaciones con IC95 sin corrección por multiplicidad: algún `supera` puede ser casual.

| Modelo | Condición | Familia | Nivel | Mejor sin inventario | pass@1 frente a ella | Mejor con inventario | pass@1 frente a ella |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | tools | availability | easy | siempre_alcanza 43.1 % | supera | ignorar_reservas 43.1 % | supera |
| `Qwen/Qwen3-8B+think` | tools | availability | medium | siempre_alcanza 44.6 % | supera | ignorar_reservas 44.6 % | supera |
| `Qwen/Qwen3-8B+think` | tools | availability | hard | siempre_alcanza 46.2 % | supera | ignorar_reservas 46.2 % | supera |
| `Qwen/Qwen3-8B+think` | tools | selection | easy | sucursal_azar 13.8 % | supera | sucursal_azar_contada 43.1 % | supera |
| `Qwen/Qwen3-8B+think` | tools | selection | medium | sucursal_azar 12.3 % | supera | sucursal_azar_contada 35.4 % | supera |
| `Qwen/Qwen3-8B+think` | tools | selection | hard | sucursal_azar 4.6 % | supera | sucursal_azar_contada 29.2 % | supera |
| `Qwen/Qwen3-8B+think` | tools | composition | easy | todo_atendido 15.4 % | supera | ignorar_reservas 15.4 % | supera |
| `Qwen/Qwen3-8B+think` | tools | composition | medium | todo_atendido 12.3 % | supera | ignorar_reservas 12.3 % | supera |
| `Qwen/Qwen3-8B+think` | tools | composition | hard | todo_atendido 15.4 % | supera | ignorar_reservas 15.4 % | supera |
| `Qwen/Qwen3-8B+think` | visible | availability | easy | siempre_alcanza 43.1 % | supera | ignorar_reservas 43.1 % | supera |
| `Qwen/Qwen3-8B+think` | visible | availability | medium | siempre_alcanza 44.6 % | supera | ignorar_reservas 44.6 % | supera |
| `Qwen/Qwen3-8B+think` | visible | availability | hard | siempre_alcanza 46.2 % | supera | ignorar_reservas 46.2 % | supera |
| `Qwen/Qwen3-8B+think` | visible | selection | easy | sucursal_azar 13.8 % | supera | sucursal_azar_contada 43.1 % | supera |
| `Qwen/Qwen3-8B+think` | visible | selection | medium | sucursal_azar 12.3 % | supera | sucursal_azar_contada 35.4 % | supera |
| `Qwen/Qwen3-8B+think` | visible | selection | hard | sucursal_azar 4.6 % | supera | sucursal_azar_contada 29.2 % | supera |
| `Qwen/Qwen3-8B+think` | visible | composition | easy | todo_atendido 15.4 % | supera | ignorar_reservas 15.4 % | supera |
| `Qwen/Qwen3-8B+think` | visible | composition | medium | todo_atendido 12.3 % | supera | ignorar_reservas 12.3 % | supera |
| `Qwen/Qwen3-8B+think` | visible | composition | hard | todo_atendido 15.4 % | supera | ignorar_reservas 15.4 % | supera |

## Distribución de errores

| Modelo | Condición | error_type | Muestras | Porcentaje |
|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | tools | `ok` | 1076 | 92.0 % |
| `Qwen/Qwen3-8B+think` | tools | `wrong_value` | 83 | 7.1 % |
| `Qwen/Qwen3-8B+think` | tools | `no_answer_block` | 11 | 0.9 % |
| `Qwen/Qwen3-8B+think` | visible | `ok` | 1100 | 94.0 % |
| `Qwen/Qwen3-8B+think` | visible | `wrong_value` | 60 | 5.1 % |
| `Qwen/Qwen3-8B+think` | visible | `no_answer_block` | 9 | 0.8 % |
| `Qwen/Qwen3-8B+think` | visible | `multiple_answer_blocks` | 1 | 0.1 % |

| Modelo | Condición | Muestras | parser_error | Contradicción |
|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | tools | 1170 | 0.9 % (11/1170) | 0.0 % (0/1170) |
| `Qwen/Qwen3-8B+think` | visible | 1170 | 0.9 % (10/1170) | 0.0 % (0/1170) |

## Clasificación según §6 de la propuesta (orientativa)

**Es una lectura orientativa, no una decisión ni un umbral del curso.** La propuesta define las categorías; los números son nuestros y están en `summary.json`. La certeza es `firme` solo si el IC completo cae en la categoría (y, si la categoría depende de la ganancia de pass@k sobre pass@1, también el IC de esa ganancia). Con un IC más ancho que 30 puntos se marca `IC muy ancho`: esa categoría es una lectura provisional y no debe usarse para decidir. `(solo pass@1)` indica que no hubo pass@k utilizable (sin muestras o con denominador distinto por instancias incompletas); el motivo está en `summary.json`.

| Modelo | Condición | Familia | Nivel | Lectura | Certeza | Frente a regla trivial | Acción sugerida |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | tools | availability | easy | Éxito cercano a 100 % | firme | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | availability | medium | Éxito cercano a 100 % | firme | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | availability | hard | Éxito cercano a 100 % | firme | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | selection | easy | Éxito cercano a 100 % | firme | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | selection | medium | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | selection | hard | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | composition | easy | Éxito cercano a 100 % | firme | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | tools | composition | medium | Acierto intermedio sin ganancia apreciable | tentativa | supera | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-8B+think` | tools | composition | hard | Acierto intermedio sin ganancia apreciable | tentativa | supera | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-8B+think` | visible | availability | easy | Éxito cercano a 100 % | firme | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | availability | medium | Éxito cercano a 100 % | firme | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | availability | hard | Éxito cercano a 100 % | firme | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | selection | easy | Éxito cercano a 100 % | firme | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | selection | medium | Éxito cercano a 100 % | firme | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | selection | hard | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | composition | easy | Éxito cercano a 100 % | firme | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | composition | medium | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-8B+think` | visible | composition | hard | Acierto intermedio y pass@k mayor que pass@1 | tentativa | supera | Posible zona aprendible: profundizar |

### Entre condiciones

| Modelo | Familia | Nivel | Lectura | Certeza | Acción sugerida |
|---|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | availability | easy | Ningún patrón de §6 entre condiciones | tentativa | — |
| `Qwen/Qwen3-8B+think` | availability | hard | Ningún patrón de §6 entre condiciones | tentativa | — |
| `Qwen/Qwen3-8B+think` | availability | medium | Ningún patrón de §6 entre condiciones | tentativa | — |
| `Qwen/Qwen3-8B+think` | composition | easy | Ningún patrón de §6 entre condiciones | tentativa | — |
| `Qwen/Qwen3-8B+think` | composition | hard | Ningún patrón de §6 entre condiciones | tentativa | — |
| `Qwen/Qwen3-8B+think` | composition | medium | Ningún patrón de §6 entre condiciones | tentativa | — |
| `Qwen/Qwen3-8B+think` | selection | easy | Ningún patrón de §6 entre condiciones | tentativa | — |
| `Qwen/Qwen3-8B+think` | selection | hard | Ningún patrón de §6 entre condiciones | tentativa | — |
| `Qwen/Qwen3-8B+think` | selection | medium | Ningún patrón de §6 entre condiciones | tentativa | — |

## Costo

| Modelo | Condición | Muestras | Tokens nuevos por muestra | s por muestra | Horas (suma de `usage.seconds`) | Llegó al tope de tokens |
|---|---|---|---|---|---|---|
| `Qwen/Qwen3-8B+think` | tools | 1170 | 1864 | 10.20 | 3.32 | 1.2 % (14/1170) |
| `Qwen/Qwen3-8B+think` | visible | 1170 | 1019 | 5.25 | 1.71 | 0.9 % (10/1170) |

`Llegó al tope de tokens` cuenta las muestras con alguna generación cortada por `max_new_tokens`, según `usage.stop_reasons`. En rollouts sin ese campo es una cota inferior. Un valor alto, sobre todo con thinking, indica respuestas cortadas.

## Instancias incompletas

Ninguna: todas las instancias vistas tienen 2 muestras.

## Revisión manual

`muestra_errores.jsonl` tiene 33 rollouts fallidos, estratificados por modelo, condición, familia, dificultad y error_type (hasta 3 por estrato). Sirve para verificar a mano si el verificador rechazó bien.
