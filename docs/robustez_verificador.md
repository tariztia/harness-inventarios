# Robustez del verificador

Archivo generado por `scripts/robustness_report.py`; no editar a mano.

Casos: 323. Aciertos: 315 (97.5 %). Fallos: 8, de los cuales 8 son limitaciones conocidas y 0 son fallos no documentados.

Un acierto significa que el verificador acepta o rechaza como indica el caso. Estos casos fueron escritos por el equipo: miden las equivalencias y trampas previstas, no la variedad de respuestas de un modelo real. Esa parte se revisa con `muestra_errores.jsonl` del piloto.

## Aciertos por categoría

| Categoría | Casos | Deben pasar | Deben rechazarse | Aciertos | Tasa | Falsos positivos | Falsos negativos |
|---|---:|---:|---:|---:|---:|---:|---:|
| equivalencias_validas | 41 | 41 | 0 | 40 | 97.6 % | 0 | 1 |
| parafrasis_correctas | 8 | 8 | 0 | 8 | 100.0 % | 0 | 0 |
| respuestas_parciales | 12 | 0 | 12 | 12 | 100.0 % | 0 | 0 |
| multiples_respuestas | 38 | 1 | 37 | 38 | 100.0 % | 0 | 0 |
| inyeccion_formato | 47 | 4 | 43 | 47 | 100.0 % | 0 | 0 |
| numeros_fuera_de_contexto | 20 | 0 | 20 | 20 | 100.0 % | 0 | 0 |
| homoglifos | 20 | 4 | 16 | 20 | 100.0 % | 0 | 0 |
| overflow_numerico | 32 | 2 | 30 | 32 | 100.0 % | 0 | 0 |
| copia_herramienta | 21 | 3 | 18 | 21 | 100.0 % | 0 | 0 |
| prompt_injection | 26 | 3 | 23 | 26 | 100.0 % | 0 | 0 |
| contradicciones | 25 | 0 | 25 | 18 | 72.0 % | 7 | 0 |
| falsos_positivos_contradiccion | 33 | 33 | 0 | 33 | 100.0 % | 0 | 0 |

## Tipo de error

De 223 casos que declaran un `error_type`, 216 coinciden (96.9 %).

## Fallos

| Caso | Categoría | Debía pasar | Aceptado | error_type | Limitación conocida |
|---|---|---|---|---|---|
| `eq-grupo-mas-suelta` | equivalencias_validas | sí | no | `ambiguous_value` | sí |
| `con-parrafo-previo` | contradicciones | no | sí | `ok` | sí |
| `con-linea-con-id` | contradicciones | no | sí | `ok` | sí |
| `con-recomendacion-enumerada` | contradicciones | no | sí | `ok` | sí |
| `con-comp-total-prosa` | contradicciones | no | sí | `ok` | sí |
| `con-comp-todo-alcanza` | contradicciones | no | sí | `ok` | sí |
| `con-comp-orden-invertido` | contradicciones | no | sí | `ok` | sí |
| `con-comp-formato-en-prosa` | contradicciones | no | sí | `ok` | sí |

## Limitaciones conocidas

- **`eq-grupo-mas-suelta`.** Falso rechazo. Un grupo no puede ser sumando: '3 filas de 10 y 5 sueltas' es ambiguo. Admitirlo abre 'dos filas de 3 y 4 filas de 3' como dos respuestas.
- **`con-parrafo-previo`.** Falso negativo por contrato: solo se revisa el ultimo parrafo. Basta un parrafo neutro despues de la conclusion contraria para que no se detecte.
- **`con-linea-con-id`.** Falso negativo aceptado. Una oracion con un producto se trata como parcial, aunque 'P01 no alcanza' implique que el pedido entero no alcanza. Es el costo de no castigar pedidos de varias lineas. El bloque sigue teniendo que ser correcto.
- **`con-recomendacion-enumerada`.** Falso negativo aceptado. La sucursal recomendada solo se reconoce cerca del verbo y en la misma clausula; una aposicion tras una coma se ignora.
- **`con-comp-total-prosa`.** Falso negativo: en composicion no hay revision de contradicciones. Un total distinto en la prosa ('quedan 5') no se compara con total_pendientes. Solo decide el bloque, que debe ser correcto en todos sus campos.
- **`con-comp-todo-alcanza`.** Falso negativo: la polaridad de 'alcanza' solo se revisa en disponibilidad. En composicion, 'alcanza para todos los pedidos' con pendientes en el bloque pasa. Extenderla exigiria distinguir pedido por pedido ('O1 alcanza, O2 no').
- **`con-comp-orden-invertido`.** Falso negativo: la prosa que asigna cantidades a otro pedido ('O1 queda con 4 pendientes') no se cruza con el bloque. Detectarlo requiere atar cifras a IDs de pedido en texto libre, con el riesgo de castigar calculos intermedios.
- **`con-comp-formato-en-prosa`.** Falso negativo: repetir un campo con otro valor en la prosa se detecta para 'alcanza: si' y 'sucursal: S3', pero no para 'O2_pendientes: 0' en composicion. No premia un valor incorrecto, pero si una explicacion incoherente con el bloque.
- **Sin caso asociado.** Mencionar la etiqueta literal <answer> en la prosa antes del bloque real se rechaza como multiple_answer_blocks. Es lo que pide el contrato, y puede castigar una respuesta correcta: conviene que el prompt no invite a nombrar la etiqueta.
- **Sin caso asociado.** Las etiquetas de una suma no se validan contra la instancia, porque el parser no la conoce: '20 gatos y 20 perros' vale 40. Es un riesgo acotado: la suma debe ser exacta, asi que no permite cubrir varias respuestas.
- **Sin caso asociado.** La respuesta correcta sin evidencia (adivinada o memorizada) pasa este modulo. La defensa es retrieved_required_data, en reward.py.

## Cobertura por familia

| Familia | Casos | Deben pasar | Deben rechazarse | Categorías cubiertas | Categorías sin casos |
|---|---:|---:|---:|---:|---|
| availability | 196 | 65 | 131 | 12 | — |
| selection | 58 | 19 | 39 | 12 | — |
| composition | 69 | 15 | 54 | 12 | — |

La familia con menos casos es `selection` (58). Una categoría sin casos en una familia no implica que el verificador falle ahí; implica que esa combinación no está medida.
