# Informe del piloto

- Etapa: `piloto`; split `eval`; semilla base 2026; 10 por celda; 5 muestras.
- Entorno: GPU Tesla T4; torch 2.11.0+cu130; transformers 5.20.2.
- Código: `27f29db9ca698f3e`; fecha 2026-11-13T05:08:15+00:00.
- Archivos leídos: 3. Rollouts válidos: 2700.
- Problemas de carga: ninguno.

## Estado por modelo

| Modelo | Estado | Rollouts | s/rollout (reloj) | Error |
|---|---|---|---|---|
| `unsloth/Llama-3.2-1B-Instruct` | completo | 900/900 | 7.552 | — |
| `Qwen/Qwen3-1.7B` | completo | 900/900 | 6.009 | — |
| `Qwen/Qwen3-4B` | completo | 900/900 | 10.968 | — |

## Resultados por modelo, condición, familia y dificultad

pass@1 usa la muestra 0 de cada instancia. pass@5 cuenta las instancias con al menos un acierto entre las primeras 5 muestras. El IC95 es de Wilson sobre instancias. La tasa por muestra se da sin IC porque las muestras están correlacionadas.

### `Qwen/Qwen3-1.7B`

| Condición | Familia | Nivel | n inst. | pass@1 | pass@5 | Tasa por muestra | Incompletas k=5 |
|---|---|---|---|---|---|---|---|
| tools | availability | easy | 10 | 60.0 % (6/10; IC95 31–83) | 100.0 % (10/10; IC95 72–100) | 64.0 % | 0 |
| tools | availability | medium | 10 | 70.0 % (7/10; IC95 40–89) | 100.0 % (10/10; IC95 72–100) | 64.0 % | 0 |
| tools | availability | hard | 10 | 30.0 % (3/10; IC95 11–60) | 70.0 % (7/10; IC95 40–89) | 28.0 % | 0 |
| tools | selection | easy | 10 | 60.0 % (6/10; IC95 31–83) | 100.0 % (10/10; IC95 72–100) | 62.0 % | 0 |
| tools | selection | medium | 10 | 0.0 % (0/10; IC95 0–28) | 10.0 % (1/10; IC95 2–40) | 2.0 % | 0 |
| tools | selection | hard | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| tools | composition | easy | 10 | 0.0 % (0/10; IC95 0–28) | 30.0 % (3/10; IC95 11–60) | 12.0 % | 0 |
| tools | composition | medium | 10 | 0.0 % (0/10; IC95 0–28) | 10.0 % (1/10; IC95 2–40) | 2.0 % | 0 |
| tools | composition | hard | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| visible | availability | easy | 10 | 50.0 % (5/10; IC95 24–76) | 90.0 % (9/10; IC95 60–98) | 38.0 % | 0 |
| visible | availability | medium | 10 | 30.0 % (3/10; IC95 11–60) | 90.0 % (9/10; IC95 60–98) | 48.0 % | 0 |
| visible | availability | hard | 10 | 10.0 % (1/10; IC95 2–40) | 50.0 % (5/10; IC95 24–76) | 22.0 % | 0 |
| visible | selection | easy | 10 | 80.0 % (8/10; IC95 49–94) | 100.0 % (10/10; IC95 72–100) | 72.0 % | 0 |
| visible | selection | medium | 10 | 30.0 % (3/10; IC95 11–60) | 60.0 % (6/10; IC95 31–83) | 22.0 % | 0 |
| visible | selection | hard | 10 | 0.0 % (0/10; IC95 0–28) | 10.0 % (1/10; IC95 2–40) | 2.0 % | 0 |
| visible | composition | easy | 10 | 60.0 % (6/10; IC95 31–83) | 90.0 % (9/10; IC95 60–98) | 68.0 % | 0 |
| visible | composition | medium | 10 | 10.0 % (1/10; IC95 2–40) | 20.0 % (2/10; IC95 6–51) | 8.0 % | 0 |
| visible | composition | hard | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |

### `Qwen/Qwen3-4B`

| Condición | Familia | Nivel | n inst. | pass@1 | pass@5 | Tasa por muestra | Incompletas k=5 |
|---|---|---|---|---|---|---|---|
| tools | availability | easy | 10 | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) | 100.0 % | 0 |
| tools | availability | medium | 10 | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) | 100.0 % | 0 |
| tools | availability | hard | 10 | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) | 96.0 % | 0 |
| tools | selection | easy | 10 | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) | 100.0 % | 0 |
| tools | selection | medium | 10 | 90.0 % (9/10; IC95 60–98) | 100.0 % (10/10; IC95 72–100) | 84.0 % | 0 |
| tools | selection | hard | 10 | 0.0 % (0/10; IC95 0–28) | 30.0 % (3/10; IC95 11–60) | 10.0 % | 0 |
| tools | composition | easy | 10 | 80.0 % (8/10; IC95 49–94) | 100.0 % (10/10; IC95 72–100) | 88.0 % | 0 |
| tools | composition | medium | 10 | 60.0 % (6/10; IC95 31–83) | 90.0 % (9/10; IC95 60–98) | 48.0 % | 0 |
| tools | composition | hard | 10 | 10.0 % (1/10; IC95 2–40) | 10.0 % (1/10; IC95 2–40) | 6.0 % | 0 |
| visible | availability | easy | 10 | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) | 100.0 % | 0 |
| visible | availability | medium | 10 | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) | 98.0 % | 0 |
| visible | availability | hard | 10 | 90.0 % (9/10; IC95 60–98) | 90.0 % (9/10; IC95 60–98) | 76.0 % | 0 |
| visible | selection | easy | 10 | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) | 100.0 % | 0 |
| visible | selection | medium | 10 | 90.0 % (9/10; IC95 60–98) | 100.0 % (10/10; IC95 72–100) | 82.0 % | 0 |
| visible | selection | hard | 10 | 20.0 % (2/10; IC95 6–51) | 30.0 % (3/10; IC95 11–60) | 8.0 % | 0 |
| visible | composition | easy | 10 | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) | 98.0 % | 0 |
| visible | composition | medium | 10 | 70.0 % (7/10; IC95 40–89) | 90.0 % (9/10; IC95 60–98) | 68.0 % | 0 |
| visible | composition | hard | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |

### `unsloth/Llama-3.2-1B-Instruct`

| Condición | Familia | Nivel | n inst. | pass@1 | pass@5 | Tasa por muestra | Incompletas k=5 |
|---|---|---|---|---|---|---|---|
| tools | availability | easy | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| tools | availability | medium | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| tools | availability | hard | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| tools | selection | easy | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| tools | selection | medium | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| tools | selection | hard | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| tools | composition | easy | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| tools | composition | medium | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| tools | composition | hard | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| visible | availability | easy | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| visible | availability | medium | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| visible | availability | hard | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| visible | selection | easy | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| visible | selection | medium | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| visible | selection | hard | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| visible | composition | easy | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| visible | composition | medium | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |
| visible | composition | hard | 10 | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | 0.0 % | 0 |

## Comparación con y sin herramientas

| Modelo | Familia | Nivel | Visible pass@1 | Herramientas pass@1 | Dif. (h − v) | Visible pass@5 | Herramientas pass@5 |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | availability | easy | 50.0 % (5/10; IC95 24–76) | 60.0 % (6/10; IC95 31–83) | +10.0 pts | 90.0 % (9/10; IC95 60–98) | 100.0 % (10/10; IC95 72–100) |
| `Qwen/Qwen3-1.7B` | availability | hard | 10.0 % (1/10; IC95 2–40) | 30.0 % (3/10; IC95 11–60) | +20.0 pts | 50.0 % (5/10; IC95 24–76) | 70.0 % (7/10; IC95 40–89) |
| `Qwen/Qwen3-1.7B` | availability | medium | 30.0 % (3/10; IC95 11–60) | 70.0 % (7/10; IC95 40–89) | +40.0 pts | 90.0 % (9/10; IC95 60–98) | 100.0 % (10/10; IC95 72–100) |
| `Qwen/Qwen3-1.7B` | composition | easy | 60.0 % (6/10; IC95 31–83) | 0.0 % (0/10; IC95 0–28) | -60.0 pts | 90.0 % (9/10; IC95 60–98) | 30.0 % (3/10; IC95 11–60) |
| `Qwen/Qwen3-1.7B` | composition | hard | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | +0.0 pts | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) |
| `Qwen/Qwen3-1.7B` | composition | medium | 10.0 % (1/10; IC95 2–40) | 0.0 % (0/10; IC95 0–28) | -10.0 pts | 20.0 % (2/10; IC95 6–51) | 10.0 % (1/10; IC95 2–40) |
| `Qwen/Qwen3-1.7B` | selection | easy | 80.0 % (8/10; IC95 49–94) | 60.0 % (6/10; IC95 31–83) | -20.0 pts | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) |
| `Qwen/Qwen3-1.7B` | selection | hard | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | +0.0 pts | 10.0 % (1/10; IC95 2–40) | 0.0 % (0/10; IC95 0–28) |
| `Qwen/Qwen3-1.7B` | selection | medium | 30.0 % (3/10; IC95 11–60) | 0.0 % (0/10; IC95 0–28) | -30.0 pts | 60.0 % (6/10; IC95 31–83) | 10.0 % (1/10; IC95 2–40) |
| `Qwen/Qwen3-4B` | availability | easy | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) | +0.0 pts | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) |
| `Qwen/Qwen3-4B` | availability | hard | 90.0 % (9/10; IC95 60–98) | 100.0 % (10/10; IC95 72–100) | +10.0 pts | 90.0 % (9/10; IC95 60–98) | 100.0 % (10/10; IC95 72–100) |
| `Qwen/Qwen3-4B` | availability | medium | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) | +0.0 pts | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) |
| `Qwen/Qwen3-4B` | composition | easy | 100.0 % (10/10; IC95 72–100) | 80.0 % (8/10; IC95 49–94) | -20.0 pts | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) |
| `Qwen/Qwen3-4B` | composition | hard | 0.0 % (0/10; IC95 0–28) | 10.0 % (1/10; IC95 2–40) | +10.0 pts | 0.0 % (0/10; IC95 0–28) | 10.0 % (1/10; IC95 2–40) |
| `Qwen/Qwen3-4B` | composition | medium | 70.0 % (7/10; IC95 40–89) | 60.0 % (6/10; IC95 31–83) | -10.0 pts | 90.0 % (9/10; IC95 60–98) | 90.0 % (9/10; IC95 60–98) |
| `Qwen/Qwen3-4B` | selection | easy | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) | +0.0 pts | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) |
| `Qwen/Qwen3-4B` | selection | hard | 20.0 % (2/10; IC95 6–51) | 0.0 % (0/10; IC95 0–28) | -20.0 pts | 30.0 % (3/10; IC95 11–60) | 30.0 % (3/10; IC95 11–60) |
| `Qwen/Qwen3-4B` | selection | medium | 90.0 % (9/10; IC95 60–98) | 90.0 % (9/10; IC95 60–98) | +0.0 pts | 100.0 % (10/10; IC95 72–100) | 100.0 % (10/10; IC95 72–100) |
| `unsloth/Llama-3.2-1B-Instruct` | availability | easy | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | +0.0 pts | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) |
| `unsloth/Llama-3.2-1B-Instruct` | availability | hard | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | +0.0 pts | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) |
| `unsloth/Llama-3.2-1B-Instruct` | availability | medium | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | +0.0 pts | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) |
| `unsloth/Llama-3.2-1B-Instruct` | composition | easy | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | +0.0 pts | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) |
| `unsloth/Llama-3.2-1B-Instruct` | composition | hard | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | +0.0 pts | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) |
| `unsloth/Llama-3.2-1B-Instruct` | composition | medium | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | +0.0 pts | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) |
| `unsloth/Llama-3.2-1B-Instruct` | selection | easy | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | +0.0 pts | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) |
| `unsloth/Llama-3.2-1B-Instruct` | selection | hard | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | +0.0 pts | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) |
| `unsloth/Llama-3.2-1B-Instruct` | selection | medium | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) | +0.0 pts | 0.0 % (0/10; IC95 0–28) | 0.0 % (0/10; IC95 0–28) |

### Diagnóstico de herramientas (por muestra)

| Modelo | Familia | Nivel | Llamadas válidas | Argumentos correctos | Datos requeridos | Límite excedido | Correcta sin recompensa |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | availability | easy | 100.0 % (50/50) | 100.0 % (50/50) | 100.0 % (50/50) | 14.0 % (7/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-1.7B` | availability | medium | 100.0 % (50/50) | 100.0 % (50/50) | 100.0 % (50/50) | 2.0 % (1/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-1.7B` | availability | hard | 100.0 % (50/50) | 100.0 % (50/50) | 92.0 % (46/50) | 8.0 % (4/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-1.7B` | selection | easy | 100.0 % (50/50) | 100.0 % (50/50) | 82.0 % (41/50) | 8.0 % (4/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-1.7B` | selection | medium | 100.0 % (50/50) | 100.0 % (50/50) | 26.0 % (13/50) | 0.0 % (0/50) | 2.0 % (1/50) |
| `Qwen/Qwen3-1.7B` | selection | hard | 100.0 % (50/50) | 98.0 % (49/50) | 2.0 % (1/50) | 4.0 % (2/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-1.7B` | composition | easy | 100.0 % (50/50) | 100.0 % (50/50) | 100.0 % (50/50) | 74.0 % (37/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-1.7B` | composition | medium | 98.0 % (49/50) | 94.0 % (47/50) | 52.0 % (26/50) | 8.0 % (4/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-1.7B` | composition | hard | 100.0 % (50/50) | 100.0 % (50/50) | 22.0 % (11/50) | 26.0 % (13/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-4B` | availability | easy | 100.0 % (50/50) | 100.0 % (50/50) | 100.0 % (50/50) | 0.0 % (0/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-4B` | availability | medium | 100.0 % (50/50) | 100.0 % (50/50) | 100.0 % (50/50) | 0.0 % (0/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-4B` | availability | hard | 100.0 % (50/50) | 100.0 % (50/50) | 100.0 % (50/50) | 0.0 % (0/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-4B` | selection | easy | 100.0 % (50/50) | 100.0 % (50/50) | 100.0 % (50/50) | 0.0 % (0/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-4B` | selection | medium | 100.0 % (50/50) | 100.0 % (50/50) | 100.0 % (50/50) | 0.0 % (0/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-4B` | selection | hard | 100.0 % (50/50) | 100.0 % (50/50) | 84.0 % (42/50) | 0.0 % (0/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-4B` | composition | easy | 100.0 % (50/50) | 100.0 % (50/50) | 100.0 % (50/50) | 0.0 % (0/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-4B` | composition | medium | 100.0 % (50/50) | 100.0 % (50/50) | 100.0 % (50/50) | 0.0 % (0/50) | 0.0 % (0/50) |
| `Qwen/Qwen3-4B` | composition | hard | 98.0 % (49/50) | 98.0 % (49/50) | 84.0 % (42/50) | 0.0 % (0/50) | 0.0 % (0/50) |
| `unsloth/Llama-3.2-1B-Instruct` | availability | easy | 88.0 % (44/50) | 60.0 % (30/50) | 92.0 % (46/50) | 28.0 % (14/50) | 0.0 % (0/50) |
| `unsloth/Llama-3.2-1B-Instruct` | availability | medium | 88.0 % (44/50) | 66.0 % (33/50) | 92.0 % (46/50) | 32.0 % (16/50) | 0.0 % (0/50) |
| `unsloth/Llama-3.2-1B-Instruct` | availability | hard | 82.0 % (41/50) | 46.0 % (23/50) | 80.0 % (40/50) | 30.0 % (15/50) | 0.0 % (0/50) |
| `unsloth/Llama-3.2-1B-Instruct` | selection | easy | 92.0 % (46/50) | 66.0 % (33/50) | 78.0 % (39/50) | 30.0 % (15/50) | 0.0 % (0/50) |
| `unsloth/Llama-3.2-1B-Instruct` | selection | medium | 70.0 % (35/50) | 52.0 % (26/50) | 26.0 % (13/50) | 30.0 % (15/50) | 0.0 % (0/50) |
| `unsloth/Llama-3.2-1B-Instruct` | selection | hard | 78.0 % (39/50) | 50.0 % (25/50) | 12.0 % (6/50) | 30.0 % (15/50) | 0.0 % (0/50) |
| `unsloth/Llama-3.2-1B-Instruct` | composition | easy | 72.0 % (36/50) | 50.0 % (25/50) | 78.0 % (39/50) | 22.0 % (11/50) | 0.0 % (0/50) |
| `unsloth/Llama-3.2-1B-Instruct` | composition | medium | 84.0 % (42/50) | 48.0 % (24/50) | 62.0 % (31/50) | 28.0 % (14/50) | 0.0 % (0/50) |
| `unsloth/Llama-3.2-1B-Instruct` | composition | hard | 74.0 % (37/50) | 38.0 % (19/50) | 32.0 % (16/50) | 32.0 % (16/50) | 0.0 % (0/50) |

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

Cada fila se compara con la tasa de la regla sobre las mismas instancias de ese modelo y condición. `supera` significa que el límite inferior del IC de pass@1 queda sobre la tasa de la regla; `no_distinguible`, que la regla cae dentro del IC. Son muchas comparaciones con IC95 sin corrección por multiplicidad: algún `supera` puede ser casual.

| Modelo | Condición | Familia | Nivel | Mejor sin inventario | pass@1 frente a ella | Mejor con inventario | pass@1 frente a ella |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | tools | availability | easy | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | tools | availability | medium | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | tools | availability | hard | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | tools | selection | easy | primera_sucursal 0.0 % | supera | primera_sucursal_contada 30.0 % | supera |
| `Qwen/Qwen3-1.7B` | tools | selection | medium | primera_sucursal 0.0 % | no_distinguible | primera_sucursal_contada 20.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | tools | selection | hard | primera_sucursal 10.0 % | no_distinguible | sucursal_azar_contada 30.0 % | por_debajo |
| `Qwen/Qwen3-1.7B` | tools | composition | easy | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `Qwen/Qwen3-1.7B` | tools | composition | medium | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `Qwen/Qwen3-1.7B` | tools | composition | hard | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `Qwen/Qwen3-1.7B` | visible | availability | easy | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | visible | availability | medium | siempre_alcanza 50.0 % | no_distinguible | ignorar_reservas 50.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | visible | availability | hard | siempre_alcanza 50.0 % | por_debajo | ignorar_reservas 50.0 % | por_debajo |
| `Qwen/Qwen3-1.7B` | visible | selection | easy | primera_sucursal 0.0 % | supera | primera_sucursal_contada 30.0 % | supera |
| `Qwen/Qwen3-1.7B` | visible | selection | medium | primera_sucursal 0.0 % | supera | primera_sucursal_contada 20.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | visible | selection | hard | primera_sucursal 10.0 % | no_distinguible | sucursal_azar_contada 30.0 % | por_debajo |
| `Qwen/Qwen3-1.7B` | visible | composition | easy | todo_atendido 30.0 % | supera | ignorar_reservas 30.0 % | supera |
| `Qwen/Qwen3-1.7B` | visible | composition | medium | todo_atendido 30.0 % | no_distinguible | ignorar_reservas 30.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | visible | composition | hard | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `Qwen/Qwen3-4B` | tools | availability | easy | siempre_alcanza 50.0 % | supera | ignorar_reservas 50.0 % | supera |
| `Qwen/Qwen3-4B` | tools | availability | medium | siempre_alcanza 50.0 % | supera | ignorar_reservas 50.0 % | supera |
| `Qwen/Qwen3-4B` | tools | availability | hard | siempre_alcanza 50.0 % | supera | ignorar_reservas 50.0 % | supera |
| `Qwen/Qwen3-4B` | tools | selection | easy | primera_sucursal 0.0 % | supera | primera_sucursal_contada 30.0 % | supera |
| `Qwen/Qwen3-4B` | tools | selection | medium | primera_sucursal 0.0 % | supera | primera_sucursal_contada 20.0 % | supera |
| `Qwen/Qwen3-4B` | tools | selection | hard | primera_sucursal 10.0 % | no_distinguible | sucursal_azar_contada 30.0 % | por_debajo |
| `Qwen/Qwen3-4B` | tools | composition | easy | todo_atendido 30.0 % | supera | ignorar_reservas 30.0 % | supera |
| `Qwen/Qwen3-4B` | tools | composition | medium | todo_atendido 30.0 % | supera | ignorar_reservas 30.0 % | supera |
| `Qwen/Qwen3-4B` | tools | composition | hard | todo_atendido 30.0 % | no_distinguible | ignorar_reservas 30.0 % | no_distinguible |
| `Qwen/Qwen3-4B` | visible | availability | easy | siempre_alcanza 50.0 % | supera | ignorar_reservas 50.0 % | supera |
| `Qwen/Qwen3-4B` | visible | availability | medium | siempre_alcanza 50.0 % | supera | ignorar_reservas 50.0 % | supera |
| `Qwen/Qwen3-4B` | visible | availability | hard | siempre_alcanza 50.0 % | supera | ignorar_reservas 50.0 % | supera |
| `Qwen/Qwen3-4B` | visible | selection | easy | primera_sucursal 0.0 % | supera | primera_sucursal_contada 30.0 % | supera |
| `Qwen/Qwen3-4B` | visible | selection | medium | primera_sucursal 0.0 % | supera | primera_sucursal_contada 20.0 % | supera |
| `Qwen/Qwen3-4B` | visible | selection | hard | primera_sucursal 10.0 % | no_distinguible | sucursal_azar_contada 30.0 % | no_distinguible |
| `Qwen/Qwen3-4B` | visible | composition | easy | todo_atendido 30.0 % | supera | ignorar_reservas 30.0 % | supera |
| `Qwen/Qwen3-4B` | visible | composition | medium | todo_atendido 30.0 % | supera | ignorar_reservas 30.0 % | supera |
| `Qwen/Qwen3-4B` | visible | composition | hard | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | tools | availability | easy | siempre_alcanza 50.0 % | por_debajo | ignorar_reservas 50.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | tools | availability | medium | siempre_alcanza 50.0 % | por_debajo | ignorar_reservas 50.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | tools | availability | hard | siempre_alcanza 50.0 % | por_debajo | ignorar_reservas 50.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | tools | selection | easy | primera_sucursal 0.0 % | no_distinguible | primera_sucursal_contada 30.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | tools | selection | medium | primera_sucursal 0.0 % | no_distinguible | primera_sucursal_contada 20.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | tools | selection | hard | primera_sucursal 10.0 % | no_distinguible | sucursal_azar_contada 30.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | tools | composition | easy | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | tools | composition | medium | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | tools | composition | hard | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | visible | availability | easy | siempre_alcanza 50.0 % | por_debajo | ignorar_reservas 50.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | visible | availability | medium | siempre_alcanza 50.0 % | por_debajo | ignorar_reservas 50.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | visible | availability | hard | siempre_alcanza 50.0 % | por_debajo | ignorar_reservas 50.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | visible | selection | easy | primera_sucursal 0.0 % | no_distinguible | primera_sucursal_contada 30.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | visible | selection | medium | primera_sucursal 0.0 % | no_distinguible | primera_sucursal_contada 20.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | visible | selection | hard | primera_sucursal 10.0 % | no_distinguible | sucursal_azar_contada 30.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | visible | composition | easy | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | visible | composition | medium | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |
| `unsloth/Llama-3.2-1B-Instruct` | visible | composition | hard | todo_atendido 30.0 % | por_debajo | ignorar_reservas 30.0 % | por_debajo |

## Distribución de errores

| Modelo | Condición | error_type | Muestras | Porcentaje |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | tools | `wrong_value` | 198 | 44.0 % |
| `Qwen/Qwen3-1.7B` | tools | `ok` | 117 | 26.0 % |
| `Qwen/Qwen3-1.7B` | tools | `tool_limit_exceeded` | 72 | 16.0 % |
| `Qwen/Qwen3-1.7B` | tools | `no_answer_block` | 45 | 10.0 % |
| `Qwen/Qwen3-1.7B` | tools | `invalid_value` | 8 | 1.8 % |
| `Qwen/Qwen3-1.7B` | tools | `multiple_answer_blocks` | 4 | 0.9 % |
| `Qwen/Qwen3-1.7B` | tools | `ambiguous_value` | 2 | 0.4 % |
| `Qwen/Qwen3-1.7B` | tools | `unknown_field` | 2 | 0.4 % |
| `Qwen/Qwen3-1.7B` | tools | `missing_evidence` | 1 | 0.2 % |
| `Qwen/Qwen3-1.7B` | tools | `missing_field` | 1 | 0.2 % |
| `Qwen/Qwen3-1.7B` | visible | `wrong_value` | 187 | 41.6 % |
| `Qwen/Qwen3-1.7B` | visible | `ok` | 140 | 31.1 % |
| `Qwen/Qwen3-1.7B` | visible | `no_answer_block` | 98 | 21.8 % |
| `Qwen/Qwen3-1.7B` | visible | `multiple_answer_blocks` | 12 | 2.7 % |
| `Qwen/Qwen3-1.7B` | visible | `invalid_value` | 6 | 1.3 % |
| `Qwen/Qwen3-1.7B` | visible | `ambiguous_value` | 6 | 1.3 % |
| `Qwen/Qwen3-1.7B` | visible | `contradiction` | 1 | 0.2 % |
| `Qwen/Qwen3-4B` | tools | `ok` | 316 | 70.2 % |
| `Qwen/Qwen3-4B` | tools | `wrong_value` | 73 | 16.2 % |
| `Qwen/Qwen3-4B` | tools | `no_answer_block` | 45 | 10.0 % |
| `Qwen/Qwen3-4B` | tools | `multiple_answer_blocks` | 16 | 3.6 % |
| `Qwen/Qwen3-4B` | visible | `ok` | 315 | 70.0 % |
| `Qwen/Qwen3-4B` | visible | `no_answer_block` | 70 | 15.6 % |
| `Qwen/Qwen3-4B` | visible | `wrong_value` | 53 | 11.8 % |
| `Qwen/Qwen3-4B` | visible | `multiple_answer_blocks` | 11 | 2.4 % |
| `Qwen/Qwen3-4B` | visible | `unknown_field` | 1 | 0.2 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `no_answer_block` | 268 | 59.6 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `tool_limit_exceeded` | 131 | 29.1 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `wrong_value` | 19 | 4.2 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `multiple_answer_blocks` | 11 | 2.4 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `invalid_value` | 10 | 2.2 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `ambiguous_value` | 7 | 1.6 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `missing_field` | 2 | 0.4 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `contradiction` | 1 | 0.2 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `unknown_field` | 1 | 0.2 % |
| `unsloth/Llama-3.2-1B-Instruct` | visible | `no_answer_block` | 431 | 95.8 % |
| `unsloth/Llama-3.2-1B-Instruct` | visible | `multiple_answer_blocks` | 17 | 3.8 % |
| `unsloth/Llama-3.2-1B-Instruct` | visible | `ambiguous_value` | 1 | 0.2 % |
| `unsloth/Llama-3.2-1B-Instruct` | visible | `wrong_value` | 1 | 0.2 % |

| Modelo | Condición | Muestras | parser_error | Contradicción |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | tools | 450 | 29.8 % (134/450) | 0.0 % (0/450) |
| `Qwen/Qwen3-1.7B` | visible | 450 | 27.1 % (122/450) | 0.2 % (1/450) |
| `Qwen/Qwen3-4B` | tools | 450 | 13.6 % (61/450) | 0.0 % (0/450) |
| `Qwen/Qwen3-4B` | visible | 450 | 18.2 % (82/450) | 0.0 % (0/450) |
| `unsloth/Llama-3.2-1B-Instruct` | tools | 450 | 95.6 % (430/450) | 0.2 % (1/450) |
| `unsloth/Llama-3.2-1B-Instruct` | visible | 450 | 99.8 % (449/450) | 0.0 % (0/450) |

## Clasificación según §6 de la propuesta (orientativa)

**Es una lectura orientativa, no una decisión ni un umbral del curso.** La propuesta define las categorías; los números son nuestros y están en `summary.json`. La certeza es `firme` solo si el IC completo cae en la categoría (y, si la categoría depende de la ganancia de pass@k sobre pass@1, también el IC de esa ganancia). Con un IC más ancho que 30 puntos se marca `IC muy ancho`: esa categoría es una lectura provisional y no debe usarse para decidir. `(solo pass@1)` indica que no hubo pass@k utilizable (sin muestras o con denominador distinto por instancias incompletas); el motivo está en `summary.json`.

**24 de 54 celdas tienen un IC muy ancho.** Hacen falta más instancias antes de sacar conclusiones de ellas.

| Modelo | Condición | Familia | Nivel | Lectura | Certeza | Frente a regla trivial | Acción sugerida |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | tools | availability | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | tools | availability | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | tools | availability | hard | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | tools | selection | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | tools | selection | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | tools | selection | hard | Éxito cercano a 0 % incluso con k intentos | tentativa | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | tools | composition | easy | pass@1 cercano a 0 %, pero pass@k mayor | IC muy ancho, no concluir | por_debajo | Señal escasa pero presente: candidata a SFT antes de RL |
| `Qwen/Qwen3-1.7B` | tools | composition | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | tools | composition | hard | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | visible | availability | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | visible | availability | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | visible | availability | hard | pass@1 cercano a 0 %, pero pass@k mayor | IC muy ancho, no concluir | por_debajo | Señal escasa pero presente: candidata a SFT antes de RL |
| `Qwen/Qwen3-1.7B` | visible | selection | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | visible | selection | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | visible | selection | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | visible | composition | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | visible | composition | medium | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-1.7B` | visible | composition | hard | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-4B` | tools | availability | easy | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-4B` | tools | availability | medium | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-4B` | tools | availability | hard | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-4B` | tools | selection | easy | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-4B` | tools | selection | medium | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-4B` | tools | selection | hard | pass@1 cercano a 0 %, pero pass@k mayor | IC muy ancho, no concluir | no_distinguible | Señal escasa pero presente: candidata a SFT antes de RL |
| `Qwen/Qwen3-4B` | tools | composition | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-4B` | tools | composition | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-4B` | tools | composition | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-4B` | visible | availability | easy | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-4B` | visible | availability | medium | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-4B` | visible | availability | hard | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-4B` | visible | selection | easy | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-4B` | visible | selection | medium | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-4B` | visible | selection | hard | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-4B` | visible | composition | easy | Éxito cercano a 100 % | tentativa | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-4B` | visible | composition | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-4B` | visible | composition | hard | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | availability | easy | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | availability | medium | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | availability | hard | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | selection | easy | Éxito cercano a 0 % incluso con k intentos | tentativa | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | selection | medium | Éxito cercano a 0 % incluso con k intentos | tentativa | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | selection | hard | Éxito cercano a 0 % incluso con k intentos | tentativa | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | composition | easy | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | composition | medium | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | composition | hard | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | availability | easy | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | availability | medium | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | availability | hard | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | selection | easy | Éxito cercano a 0 % incluso con k intentos | tentativa | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | selection | medium | Éxito cercano a 0 % incluso con k intentos | tentativa | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | selection | hard | Éxito cercano a 0 % incluso con k intentos | tentativa | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | composition | easy | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | composition | medium | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | composition | hard | Éxito cercano a 0 % incluso con k intentos | tentativa | por_debajo | Señal escasa: simplificar, SFT o reconsiderar |

### Entre condiciones

| Modelo | Familia | Nivel | Lectura | Certeza | Acción sugerida |
|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | availability | easy | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B` | availability | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B` | availability | medium | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B` | composition | easy | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B` | composition | hard | Mal en ambas condiciones | firme | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B` | composition | medium | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B` | selection | easy | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B` | selection | hard | Mal en ambas condiciones | firme | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B` | selection | medium | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-4B` | availability | easy | Ningún patrón de §6 entre condiciones | tentativa | — |
| `Qwen/Qwen3-4B` | availability | hard | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-4B` | availability | medium | Ningún patrón de §6 entre condiciones | tentativa | — |
| `Qwen/Qwen3-4B` | composition | easy | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-4B` | composition | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-4B` | composition | medium | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-4B` | selection | easy | Ningún patrón de §6 entre condiciones | tentativa | — |
| `Qwen/Qwen3-4B` | selection | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-4B` | selection | medium | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `unsloth/Llama-3.2-1B-Instruct` | availability | easy | Mal en ambas condiciones | firme | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | availability | hard | Mal en ambas condiciones | firme | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | availability | medium | Mal en ambas condiciones | firme | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | composition | easy | Mal en ambas condiciones | firme | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | composition | hard | Mal en ambas condiciones | firme | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | composition | medium | Mal en ambas condiciones | firme | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | selection | easy | Mal en ambas condiciones | firme | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | selection | hard | Mal en ambas condiciones | firme | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | selection | medium | Mal en ambas condiciones | firme | Aislar operaciones y ajustar niveles |

## Costo

| Modelo | Condición | Muestras | Tokens nuevos por muestra | s por muestra | Horas (suma de `usage.seconds`) | Llegó al tope de tokens |
|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | tools | 450 | 372 | 7.41 | 0.93 | 2.4 % (11/450) |
| `Qwen/Qwen3-1.7B` | visible | 450 | 441 | 4.56 | 0.57 | 12.7 % (57/450) |
| `Qwen/Qwen3-4B` | tools | 450 | 494 | 13.05 | 1.63 | 13.6 % (61/450) |
| `Qwen/Qwen3-4B` | visible | 450 | 443 | 8.84 | 1.11 | 18.0 % (81/450) |
| `unsloth/Llama-3.2-1B-Instruct` | tools | 450 | 1084 | 11.83 | 1.48 | 46.9 % (211/450) |
| `unsloth/Llama-3.2-1B-Instruct` | visible | 450 | 394 | 3.23 | 0.40 | 13.3 % (60/450) |

`Llegó al tope de tokens` cuenta las muestras con alguna generación cortada por `max_new_tokens`, según `usage.stop_reasons`. En rollouts sin ese campo es una cota inferior. Un valor alto, sobre todo con thinking, indica respuestas cortadas.

## Instancias incompletas

Ninguna: todas las instancias vistas tienen 5 muestras.

## Revisión manual

`muestra_errores.jsonl` tiene 349 rollouts fallidos, estratificados por modelo, condición, familia, dificultad y error_type (hasta 3 por estrato). Sirve para verificar a mano si el verificador rechazó bien.
