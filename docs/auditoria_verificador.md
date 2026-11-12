# Auditoría del verificador contra respuestas reales

Complementa [robustez_verificador.md](robustez_verificador.md): esos casos los escribió el equipo; aquí se revisan las respuestas que dieron los modelos en las dos exploraciones (`results/exploracion_prompt_original` y `results/exploracion_prompt_corregido`). Hecha el 11 de noviembre de 2026 con el verificador de `7ed8c83`, sin cambios en `verifier.py` ni `numbers_es.py` desde entonces. La condición `tools` de esas corridas tenía el parser de llamadas roto, así que casi todo el material es de `visible`.

**Resultado:** 9 falsos rechazos entre 455 respuestas fallidas, por 2 causas (valores entre `< >` y varios pares en una línea), y 0 falsos positivos entre 119 aceptadas. **Actualización del 12 de noviembre:** la causa A2 (varios pares en una línea) ya se corrigió en el verificador. En la línea base de Qwen3-1.7B con herramientas resultó mucho más frecuente que aquí: 56 respuestas correctas rechazadas en 900 rollouts. La causa A1 sigue igual, porque el prompt vigente ya no la provoca. El resto del documento describe el verificador anterior al cambio.

## Alcance y método


- 1080 rollouts (2 prompts × 3 variantes × 2 condiciones × 90). Instancias regeneradas con `build_dataset("train", 5, 11)`.
- `expected` validado con un solucionador independiente, escrito aparte para esta auditoría: 45/45 instancias coinciden.
- Re-verifiqué cada texto final con el verificador actual (`verifier.py`/`numbers_es.py` no cambian desde 7ed8c83). En `visible` el veredicto coincide con el guardado en el 100 % de los casos.
- **En alcance (574):** las 540 `visible` y 34 `tools` que llegaron a una respuesta final tras observaciones, sin `tool_limit_exceeded` (en esos 23 el último mensaje es una tercera ronda de llamadas y no una respuesta).
  - Fuera de alcance quedaron 506 `tools`: sin observaciones (parser roto) o tercera ronda. Revisé aparte sus textos con error de parseo: solo aparecen patrones ya listados abajo y todos tienen valores incorrectos.
- Clasificación: reglas automáticas, corregidas a mano tras leer los textos.
  - `wrong_value`: comprobé que cada valor del bloque es un literal plano (dígitos, sí/no, S<n>), así que el parseo es fiel. Las 3 excepciones son igualdades aritméticas (`15 + 12 = 27`) y también se leyeron bien.
  - Errores de parseo (27), `multiple_answer_blocks` (26), `no_answer_block` de Qwen sin truncar (10) y los 73 sin bloque con contenido indeterminado: leídos uno por uno.
  - Resto de `no_answer_block` de Llama: lectura indulgente campo a campo (última línea `clave: valor`) y una muestra leída a mano de 26 textos.
  - Aceptados: los 119 leídos (bloque, último párrafo y líneas con conclusiones de toda la prosa).

Categorías:
- **a**: falso rechazo. Respuesta correcta e inequívoca, rechazada por una forma que es razonable aceptar.
- **b**: rechazo legítimo por formato. **b\*** marca los casos con contenido correcto pero fuera del contrato.
- **c**: valor incorrecto real, aunque además haya error de formato.

Errores que no aparecieron nunca: `contradiction`, `text_after_answer` y `duplicate_field`. `unknown_field` aparece solo 2 veces.

## Resumen por modelo y condición

| prompt | modelo | cond | rollouts | en alcance | aceptados | a | b | c |
|---|---|---|---|---|---|---|---|---|
| corregido | Llama-3.2-1B | tools | 90 | 10 | 0 | 0 | 6 | 4 |
| corregido | Llama-3.2-1B | visible | 90 | 90 | 0 | 0 | 42 | 48 |
| corregido | Qwen3-1.7B | tools | 90 | 3 | 1 | 0 | 0 | 2 |
| corregido | Qwen3-1.7B | visible | 90 | 90 | 27 | 0 | 17 | 46 |
| corregido | Qwen3-1.7B+think | tools | 90 | 4 | 1 | 1 | 1 | 1 |
| corregido | Qwen3-1.7B+think | visible | 90 | 90 | 52 | 1 | 20 | 17 |
| original | Llama-3.2-1B | tools | 90 | 17 | 0 | 0 | 9 | 8 |
| original | Llama-3.2-1B | visible | 90 | 90 | 0 | 0 | 29 | 61 |
| original | Qwen3-1.7B | tools | 90 | 0 | 0 | 0 | 0 | 0 |
| original | Qwen3-1.7B | visible | 90 | 90 | 4 | 0 | 1 | 85 |
| original | Qwen3-1.7B+think | tools | 90 | 0 | 0 | 0 | 0 | 0 |
| original | Qwen3-1.7B+think | visible | 90 | 90 | 34 | 7 | 38 | 11 |
| **total** | | | 1080 | 574 | 119 | **9** | **163** | **283** |

## Detalle por error_type

| prompt | modelo | cond | error_type | a | b | c |
|---|---|---|---|---|---|---|
| corregido | Llama | tools | invalid_value | 0 | 0 | 2 |
| corregido | Llama | tools | multiple_answer_blocks | 0 | 0 | 1 |
| corregido | Llama | tools | no_answer_block | 0 | 6 | 0 |
| corregido | Llama | tools | wrong_value | 0 | 0 | 1 |
| corregido | Llama | visible | multiple_answer_blocks | 0 | 1 | 1 |
| corregido | Llama | visible | no_answer_block | 0 | 41 | 47 |
| corregido | Qwen | tools | wrong_value | 0 | 0 | 2 |
| corregido | Qwen | visible | ambiguous_value | 0 | 1 | 1 |
| corregido | Qwen | visible | invalid_value | 0 | 0 | 1 |
| corregido | Qwen | visible | multiple_answer_blocks | 0 | 3 | 0 |
| corregido | Qwen | visible | no_answer_block | 0 | 13 | 5 |
| corregido | Qwen | visible | wrong_value | 0 | 0 | 39 |
| corregido | Qwen+think | tools | missing_field | 1 | 0 | 1 |
| corregido | Qwen+think | tools | no_answer_block | 0 | 1 | 0 |
| corregido | Qwen+think | visible | ambiguous_value | 0 | 1 | 0 |
| corregido | Qwen+think | visible | missing_field | 1 | 0 | 0 |
| corregido | Qwen+think | visible | no_answer_block | 0 | 19 | 0 |
| corregido | Qwen+think | visible | wrong_value | 0 | 0 | 17 |
| original | Llama | tools | invalid_value | 0 | 1 | 3 |
| original | Llama | tools | missing_field | 0 | 1 | 0 |
| original | Llama | tools | multiple_answer_blocks | 0 | 2 | 3 |
| original | Llama | tools | no_answer_block | 0 | 3 | 1 |
| original | Llama | tools | unknown_field | 0 | 2 | 0 |
| original | Llama | tools | wrong_value | 0 | 0 | 1 |
| original | Llama | visible | invalid_value | 0 | 0 | 1 |
| original | Llama | visible | multiple_answer_blocks | 0 | 3 | 12 |
| original | Llama | visible | no_answer_block | 0 | 26 | 46 |
| original | Llama | visible | wrong_value | 0 | 0 | 2 |
| original | Qwen | visible | invalid_value | 0 | 1 | 2 |
| original | Qwen | visible | wrong_value | 0 | 0 | 83 |
| original | Qwen+think | visible | invalid_value | 6 | 0 | 0 |
| original | Qwen+think | visible | missing_field | 1 | 0 | 0 |
| original | Qwen+think | visible | no_answer_block | 0 | 38 | 0 |
| original | Qwen+think | visible | wrong_value | 0 | 0 | 11 |

Desglose de b (163):
- 84 cortados por tope de tokens. 57 se cortaron dentro de `<think>` con 2048 tokens (visible vacío); 27 se cortaron en texto visible: 15 de Llama, 11 de Qwen sin thinking con 768 tokens (3 de ellos a mitad del bloque de `composition_hard`) y 1 de Qwen+think después del `</think>`.
- 69 con formato inválido y contenido incompleto o ilegible.
- 9 b\* (ver abajo).
- 1 `<answer>no</answer>` sin `faltan`.

## Falsos rechazos (a): 9 rollouts, 2 causas

### A1. Valor envuelto en `<...>`: 6 rollouts

- Todos de Qwen3-1.7B+think, visible, prompt original: availability medium_0000#0, medium_0002#1, easy_0003#0, easy_0003#1, medium_0003#0 y medium_0003#1.
- Reproducción (train_availability_medium_0000, esperado no/3):
  ```
  <answer>
  alcanza: <no>
  faltan: <3>
  </answer>
  ```
  → `invalid_value` ("marcado dentro del valor", campo `alcanza`).
- Causa: `numbers_es.py:111-112` rechaza cualquier `<`, `>` o `&` en el valor. Ese chequeo corre antes de quitar envoltorios (`_WRAPPERS`, `numbers_es.py:100`, bucle 116-126), y `<...>` no está entre ellos. Se llega por `_to_bool`/`_to_int` (`verifier.py:205`/`187`).
- Origen: el prompt original decía "cada marcador entre < > reemplazado por su valor" con `<número>`. El patrón también aparece con valores erróneos: 1 Qwen y 1 Llama en alcance y 11 fuera de alcance, todos incorrectos. Con el prompt corregido hay 0 casos.
- Prototipo (probado fuera del repo): quitar un envoltorio `<v>` que cubra todo el valor, con `v` sin `<>&`. Pasan a 1 exactamente estos 6 de los 1160 mensajes evaluados. Ninguno de los 323 casos adversariales cambia.
- Recomendación: **aceptar como limitación**, porque el prompt vigente ya lo resolvió. Si se reutiliza el prompt original o datos SFT con `<…>`, aplicar ese cambio y agregar el caso adversarial `faltan: <3>` (debe pasar) y `faltan: <b>3</b>` (debe fallar).

### A2. Varios pares `clave: valor` en una misma línea: 3 rollouts

Todos de Qwen3-1.7B+think, con el bloque justo después de `</think>`.
- `<answer>alcanza: sí faltan: 0</answer>`: corregido, visible, availability_medium_0001#0 (esperado sí/0). Da `missing_field faltan`.
- `<answer>O1_atendidas: 11O1_pendientes: 0O2_atendidas: 15O2_pendientes: 7total_pendientes: 7</answer>`: corregido, **tools**, composition_easy_0004#0, todo correcto. Da `missing_field total_pendientes`. Tenía `missing_records=0`, así que habría valido 1.
- `<answer>O1_atendidas: 10<O1_pendientes: 7<O2_atendidas: 0<O2_pendientes: 6<total_pendientes: 13</answer>`: original, visible, composition_easy_0003#0, correcto. Da `missing_field`.
- Un cuarto caso del mismo formato (corregido tools composition_easy_0002#1) tiene valores incorrectos y es c.

Causa: `_line_pairs` (`verifier.py:133-149`) admite un par por línea. `line.partition(":")` (`verifier.py:141`) deja el resto de la línea como valor de la primera clave, y `_require` (`verifier.py:247-250`, llamado en 258/274) falla antes de leer valores.

Es una decisión explícita del equipo: el caso adversarial `fmt-sin-saltos` (`tests/adversarial_cases.py:219`, `alcanza: no; faltan: 3` → `missing_field`).

Prototipo (probado fuera del repo): partir la línea cuando contiene 2 o más inicios de clave conocida seguidos de `:` (regex con `(?<![A-Za-z_])`, separadores espacio, `,`, `;` o nada).
- Entre los 1160 mensajes evaluados cambian solo los 2 primeros (0→1). El de `<` sigue en 0 porque `10<` es `invalid_value`.
- Entre los 323 adversariales cambia solo `fmt-sin-saltos` (0→1).
- Comprobaciones: `faltan: 3 faltan: 4` → `duplicate_field`; `faltan: 3 (o faltan: 4)` → `duplicate_field`; `alcanza: no alcanza faltan: 3` → ok; pegado con un valor erróneo → `wrong_value`.

Recomendación: **cambiar el verificador** con esa división por claves conocidas y actualizar `fmt-sin-saltos` a `should_pass=True`. Hay que actualizar también la tabla del contrato ("una línea `clave: valor`"). Si el equipo prefiere mantener el formato estricto como parte de lo que se entrena, queda como limitación documentada. En ese caso conviene decirlo en el prompt ("una clave por línea", que el prompt corregido ya no dice; el original sí).

## Rechazos legítimos con contenido correcto (b\*): 9 rollouts

No los considero falsos rechazos, pero conviene conocerlos.

- **Sin etiquetas, con líneas `clave: valor` correctas al final: 6 rollouts.**
  - Qwen3-1.7B, corregido, visible: availability easy_0000#0, easy_0001#0, medium_0001#0, hard_0002#1 y hard_0004#0. Los 5 son sí/0 y varios tienen el razonamiento erróneo.
  - Llama, original, visible: availability_easy_0002#1.
  - Reproducción: `...\n\nalcanza: sí\nfaltan: 0` → `no_answer_block` (`verifier.py:91-93`).
  - Recomendación: **mantener**. Aceptarlos obliga a buscar la respuesta en texto libre, donde las líneas intermedias `faltan: 3` son trampa directa. El SFT debe enseñar las etiquetas.
- **Bloque sin cerrar al EOS: 1 rollout** (Llama, original, visible, availability_hard_0003#0, texto completo `9 <answer>\nalcanza: no\nfaltan: 20`, stop `eos`).
  - Causa: `verifier.py:94-95`. `restore_answer_close` (`rollout.py:107-115`) solo repone el cierre si el stop fue `answer`.
  - Recomendación: **mantener**. Como recompensa de TRL el verificador no ve el `stop_reason`, así que aceptar bloques abiertos también aceptaría los truncados por longitud (p. ej. `total_pendientes: 4` cortado de `45`).
- **Placeholder `sí o no` copiado en el bloque, con la prosa correcta: 1 rollout** (Qwen3-1.7B, corregido, visible, availability_easy_0003#1; la prosa dice "No" y `faltan: 3`).
  - Causa: `_DOUBT_RE` (`numbers_es.py:131-141`, palabra `o`) en `parse_bool_value` (`numbers_es.py:614`).
  - Con el prompt corregido el literal `alcanza: sí o no` aparece en 6 rollouts: 3 en bloque y 3 sin bloque.
  - Recomendación: **cambiar el prompt**. `sí o no` es el único marcador que, copiado tal cual, parece una respuesta. Por ejemplo `alcanza: SI_O_NO` o un ejemplo con valor real seguido de "usa sí o no".
- **Respuesta correcta solo en prosa: 1 rollout** (Llama, corregido, visible, availability_easy_0000#1). Mantener.

## Falsos positivos

**0 de 119 aceptados.**
- Todos los bloques aceptados tienen valores literales planos.
- 91 de 119 no tienen prosa visible antes del bloque (86 Qwen+think, porque todo el razonamiento queda en `<think>`). En ellos la revisión de contradicciones no tiene nada que mirar.
- Leí los 28 con prosa: ninguna conclusión contradice el bloque ni propone otra respuesta.

Observaciones no atribuibles al verificador:
- La revisión de contradicciones no se activó en ninguno de los 1080 rollouts, así que no está probada contra salidas reales. Con thinking es un no-op.
- Algunas respuestas aceptadas son correctas por azar: Qwen sin thinking con el prompt original contesta sí/0 en 10 de 30 rollouts de availability, y sí/0 es la respuesta esperada en 6 de 15 instancias. `baselines.py` ya tiene `_always_enough`, así que conviene vigilarlo en RL.

## Otras recomendaciones (configuración, no verificador)

- 57 respuestas de Qwen+think se cortaron dentro de `<think>` con 2048 tokens: 19 con el prompt corregido (21 % de visible) y 38 con el original. Subir `max_new_tokens` o limitar el pensamiento.
- Qwen sin thinking cortado a 768 tokens: 11 con el prompt corregido. Incluye 3 bloques de `composition_hard` a medio escribir.
