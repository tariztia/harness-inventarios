# Robustez del verificador

Archivo generado por `scripts/robustness_report.py`; no editar a mano.

Casos: 246. Aciertos: 242 (98.4 %). Fallos: 4, de los cuales 4 son limitaciones conocidas y 0 son fallos no documentados.

Un acierto significa que el verificador acepta o rechaza como indica el caso. Estos casos fueron escritos por el equipo: miden las equivalencias y trampas previstas, no la variedad de respuestas de un modelo real. Esa parte se revisa con `muestra_errores.jsonl` del piloto.

## Aciertos por categoría

| Categoría | Casos | Deben pasar | Deben rechazarse | Aciertos | Tasa | Falsos positivos | Falsos negativos |
|---|---:|---:|---:|---:|---:|---:|---:|
| equivalencias_validas | 41 | 41 | 0 | 40 | 97.6 % | 0 | 1 |
| parafrasis_correctas | 8 | 8 | 0 | 8 | 100.0 % | 0 | 0 |
| respuestas_parciales | 12 | 0 | 12 | 12 | 100.0 % | 0 | 0 |
| multiples_respuestas | 29 | 0 | 29 | 29 | 100.0 % | 0 | 0 |
| inyeccion_formato | 33 | 1 | 32 | 33 | 100.0 % | 0 | 0 |
| numeros_fuera_de_contexto | 20 | 0 | 20 | 20 | 100.0 % | 0 | 0 |
| homoglifos | 20 | 4 | 16 | 20 | 100.0 % | 0 | 0 |
| overflow_numerico | 17 | 0 | 17 | 17 | 100.0 % | 0 | 0 |
| copia_herramienta | 7 | 1 | 6 | 7 | 100.0 % | 0 | 0 |
| prompt_injection | 11 | 1 | 10 | 11 | 100.0 % | 0 | 0 |
| contradicciones | 18 | 0 | 18 | 15 | 83.3 % | 3 | 0 |
| falsos_positivos_contradiccion | 30 | 30 | 0 | 30 | 100.0 % | 0 | 0 |

## Tipo de error

De 159 casos que declaran un `error_type`, 156 coinciden (98.1 %).

## Fallos

| Caso | Categoría | Debía pasar | Aceptado | error_type | Limitación conocida |
|---|---|---|---|---|---|
| `eq-grupo-mas-suelta` | equivalencias_validas | sí | no | `ambiguous_value` | sí |
| `con-parrafo-previo` | contradicciones | no | sí | `ok` | sí |
| `con-linea-con-id` | contradicciones | no | sí | `ok` | sí |
| `con-recomendacion-enumerada` | contradicciones | no | sí | `ok` | sí |

## Limitaciones conocidas

- **`eq-grupo-mas-suelta`.** Falso rechazo. Un grupo no puede ser sumando: '3 filas de 10 y 5 sueltas' es ambiguo. Admitirlo abre 'dos filas de 3 y 4 filas de 3' como dos respuestas.
- **`con-parrafo-previo`.** Falso negativo por contrato: solo se revisa el ultimo parrafo. Basta un parrafo neutro despues de la conclusion contraria para que no se detecte.
- **`con-linea-con-id`.** Falso negativo aceptado. Una oracion con un producto se trata como parcial, aunque 'P01 no alcanza' implique que el pedido entero no alcanza. Es el costo de no castigar pedidos de varias lineas. El bloque sigue teniendo que ser correcto.
- **`con-recomendacion-enumerada`.** Falso negativo aceptado. La sucursal recomendada solo se reconoce cerca del verbo y en la misma clausula; una aposicion tras una coma se ignora.
- **Sin caso asociado.** Mencionar la etiqueta literal <answer> en la prosa antes del bloque real se rechaza como multiple_answer_blocks. Es lo que pide el contrato, y puede castigar una respuesta correcta: conviene que el prompt no invite a nombrar la etiqueta.
- **Sin caso asociado.** Las etiquetas de una suma no se validan contra la instancia, porque el parser no la conoce: '20 gatos y 20 perros' vale 40. Es un riesgo acotado: la suma debe ser exacta, asi que no permite cubrir varias respuestas.
- **Sin caso asociado.** La respuesta correcta sin evidencia (adivinada o memorizada) pasa este modulo. La defensa es retrieved_required_data, en reward.py.

## Cobertura por familia

| Familia | Casos | Deben pasar | Deben rechazarse | Categorías cubiertas | Categorías sin casos |
|---|---:|---:|---:|---:|---|
| availability | 196 | 65 | 131 | 12 | — |
| selection | 37 | 16 | 21 | 9 | overflow_numerico, copia_herramienta, prompt_injection |
| composition | 13 | 5 | 8 | 6 | multiples_respuestas, inyeccion_formato, overflow_numerico, copia_herramienta, prompt_injection, contradicciones |

La familia con menos casos es `composition` (13). Una categoría sin casos en una familia no implica que el verificador falle ahí; implica que esa combinación no está medida.
