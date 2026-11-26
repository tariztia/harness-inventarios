# Informe del piloto

- Etapa: `eval_final`; split `eval`; semilla base 2026; 10 por celda; 1 muestras.
- Entorno: GPU Tesla T4; torch 2.11.0+cu130; transformers 5.24.0.
- Código: `9b6422ea39f9397c`; fecha 2026-11-25T23:29:21+00:00.
- Archivos leídos: 1. Rollouts válidos: 90.
- Problemas de carga: ninguno.

## Estado por modelo

| Modelo | Estado | Rollouts | s/rollout (reloj) | Error |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | completo | 90/90 | 17.501 | — |

## Resultados por modelo, condición, familia y dificultad

pass@1 usa la muestra 0 de cada instancia. pass@1 cuenta las instancias con al menos un acierto entre las primeras 1 muestras. El IC95 es de Wilson sobre instancias. La tasa por muestra se da sin IC porque las muestras están correlacionadas.

**Esta corrida tiene 1 muestras por instancia, así que aquí no existe pass@5.** pass@1 no es comparable con pass@5.

### `Qwen/Qwen3-1.7B+think+lora:dpo_s2027`

| Condición | Familia | Nivel | n inst. | pass@1 | pass@1 | Tasa por muestra | Incompletas k=1 |
|---|---|---|---|---|---|---|---|
| visible | availability | easy | 10 | 60.0 % (6/10; IC95 31–83) | — | 60.0 % | 0 |
| visible | availability | medium | 10 | 90.0 % (9/10; IC95 60–98) | — | 90.0 % | 0 |
| visible | availability | hard | 10 | 60.0 % (6/10; IC95 31–83) | — | 60.0 % | 0 |
| visible | selection | easy | 10 | 100.0 % (10/10; IC95 72–100) | — | 100.0 % | 0 |
| visible | selection | medium | 10 | 90.0 % (9/10; IC95 60–98) | — | 90.0 % | 0 |
| visible | selection | hard | 10 | 50.0 % (5/10; IC95 24–76) | — | 50.0 % | 0 |
| visible | composition | easy | 10 | 70.0 % (7/10; IC95 40–89) | — | 70.0 % | 0 |
| visible | composition | medium | 10 | 40.0 % (4/10; IC95 17–69) | — | 40.0 % | 0 |
| visible | composition | hard | 10 | 0.0 % (0/10; IC95 0–28) | — | 0.0 % | 0 |

## Comparación con y sin herramientas

| Modelo | Familia | Nivel | Visible pass@1 | Herramientas pass@1 | Dif. (h − v) | Visible pass@1 | Herramientas pass@1 |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | availability | easy | 60.0 % (6/10; IC95 31–83) | ausente | n/d | — | — |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | availability | hard | 60.0 % (6/10; IC95 31–83) | ausente | n/d | — | — |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | availability | medium | 90.0 % (9/10; IC95 60–98) | ausente | n/d | — | — |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | composition | easy | 70.0 % (7/10; IC95 40–89) | ausente | n/d | — | — |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | composition | hard | 0.0 % (0/10; IC95 0–28) | ausente | n/d | — | — |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | composition | medium | 40.0 % (4/10; IC95 17–69) | ausente | n/d | — | — |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | selection | easy | 100.0 % (10/10; IC95 72–100) | ausente | n/d | — | — |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | selection | hard | 50.0 % (5/10; IC95 24–76) | ausente | n/d | — | — |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | selection | medium | 90.0 % (9/10; IC95 60–98) | ausente | n/d | — | — |

### Diagnóstico de herramientas (por muestra)

No hay rollouts en condición `tools`.

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

Cada fila se compara con la tasa de la regla sobre las mismas instancias de ese modelo y condición. `supera` significa que el límite inferior del IC de pass@1 queda sobre la tasa de la regla; `no_distinguible`, que la regla cae dentro del IC. Son muchas comparaciones con IC95 sin corrección por multiplicidad: algún `supera` puede ser casual.

| Modelo | Condición | Familia | Nivel | Mejor sin inventario | pass@1 frente a ella | Mejor con inventario | pass@1 frente a ella |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | availability | easy | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | availability | medium | siempre_alcanza 50.0 % | supera | ignorar_reservas 50.0 % | supera |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | availability | hard | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | selection | easy | primera_sucursal 0.0 % | supera | primera_sucursal_contada 30.0 % | supera |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | selection | medium | primera_sucursal 0.0 % | supera | primera_sucursal_contada 20.0 % | supera |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | selection | hard | primera_sucursal 10.0 % | supera | sucursal_azar_contada 30.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | composition | easy | todo_atendido 30.0 % | supera | ignorar_reservas 30.0 % | supera |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | composition | medium | todo_atendido 30.0 % | no_distinguible | ignorar_reservas 30.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | composition | hard | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |

## Distribución de errores

| Modelo | Condición | error_type | Muestras | Porcentaje |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | `ok` | 56 | 62.2 % |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | `wrong_value` | 25 | 27.8 % |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | `no_answer_block` | 7 | 7.8 % |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | `ambiguous_value` | 1 | 1.1 % |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | `invalid_value` | 1 | 1.1 % |

| Modelo | Condición | Muestras | parser_error | Contradicción |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | 90 | 10.0 % (9/90) | 0.0 % (0/90) |

## Clasificación según §6 de la propuesta (orientativa)

**Es una lectura orientativa, no una decisión ni un umbral del curso.** La propuesta define las categorías; los números son nuestros y están en `summary.json`. La certeza es `firme` solo si el IC completo cae en la categoría (y, si la categoría depende de la ganancia de pass@k sobre pass@1, también el IC de esa ganancia). Con un IC más ancho que 30 puntos se marca `IC muy ancho`: esa categoría es una lectura provisional y no debe usarse para decidir. `(solo pass@1)` indica que no hubo pass@k utilizable (sin muestras o con denominador distinto por instancias incompletas); el motivo está en `summary.json`.

**7 de 9 celdas tienen un IC muy ancho.** Hacen falta más instancias antes de sacar conclusiones de ellas.

| Modelo | Condición | Familia | Nivel | Lectura | Certeza | Frente a regla trivial | Acción sugerida |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | availability | easy | Acierto intermedio sin ganancia apreciable (solo pass@1) | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | availability | medium | Éxito cercano a 100 % (solo pass@1) | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | availability | hard | Acierto intermedio sin ganancia apreciable (solo pass@1) | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | selection | easy | Éxito cercano a 100 % (solo pass@1) | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | selection | medium | Éxito cercano a 100 % (solo pass@1) | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | selection | hard | Acierto intermedio sin ganancia apreciable (solo pass@1) | IC muy ancho, no concluir | supera | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | composition | easy | Acierto intermedio sin ganancia apreciable (solo pass@1) | IC muy ancho, no concluir | supera | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | composition | medium | Acierto intermedio sin ganancia apreciable (solo pass@1) | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | composition | hard | Éxito cercano a 0 % (solo pass@1) | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |

### Entre condiciones

| Modelo | Familia | Nivel | Lectura | Certeza | Acción sugerida |
|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | availability | easy | Falta una condición | sin datos | No comparable |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | availability | hard | Falta una condición | sin datos | No comparable |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | availability | medium | Falta una condición | sin datos | No comparable |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | composition | easy | Falta una condición | sin datos | No comparable |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | composition | hard | Falta una condición | sin datos | No comparable |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | composition | medium | Falta una condición | sin datos | No comparable |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | selection | easy | Falta una condición | sin datos | No comparable |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | selection | hard | Falta una condición | sin datos | No comparable |
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | selection | medium | Falta una condición | sin datos | No comparable |

## Costo

| Modelo | Condición | Muestras | Tokens nuevos por muestra | s por muestra | Horas (suma de `usage.seconds`) | Llegó al tope de tokens |
|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B+think+lora:dpo_s2027` | visible | 90 | 1370 | 17.50 | 0.44 | 7.8 % (7/90) |

`Llegó al tope de tokens` cuenta las muestras con alguna generación cortada por `max_new_tokens`, según `usage.stop_reasons`. En rollouts sin ese campo es una cota inferior. Un valor alto, sobre todo con thinking, indica respuestas cortadas.

## Instancias incompletas

Ninguna: todas las instancias vistas tienen 1 muestras.

## Revisión manual

`muestra_errores.jsonl` tiene 24 rollouts fallidos, estratificados por modelo, condición, familia, dificultad y error_type (hasta 3 por estrato). Sirve para verificar a mano si el verificador rechazó bien.
