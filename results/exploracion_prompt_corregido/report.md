# Informe del piloto

- Etapa: `exploracion`; split `train`; semilla base 11; 5 por celda; 2 muestras.
- Entorno: GPU Tesla T4; torch 2.11.0+cu130; transformers 5.22.0.
- Código: `9853ef7d86081ad6`; fecha 2026-11-04T23:20:53+00:00.
- Archivos leídos: 3. Rollouts válidos: 540.
- Problemas de carga: ninguno.

## Estado por modelo

| Modelo | Estado | Rollouts | s/rollout (reloj) | Error |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | completo | 180/180 | 3.815 | — |
| `Qwen/Qwen3-1.7B+think` | completo | 180/180 | 14.89 | — |
| `unsloth/Llama-3.2-1B-Instruct` | completo | 180/180 | 3.434 | — |

## Resultados por modelo, condición, familia y dificultad

pass@1 usa la muestra 0 de cada instancia. pass@2 cuenta las instancias con al menos un acierto entre las primeras 2 muestras. El IC95 es de Wilson sobre instancias. La tasa por muestra se da sin IC porque las muestras están correlacionadas.

**Esta corrida tiene 2 muestras por instancia, así que aquí no existe pass@5.** pass@2 no es comparable con pass@5.

### `Qwen/Qwen3-1.7B`

| Condición | Familia | Nivel | n inst. | pass@1 | pass@2 | Tasa por muestra | Incompletas k=2 |
|---|---|---|---|---|---|---|---|
| tools | availability | easy | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | availability | medium | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | availability | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | selection | easy | 5 | 0.0 % (0/5; IC95 0–43) | 20.0 % (1/5; IC95 4–62) | 10.0 % | 0 |
| tools | selection | medium | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | selection | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | composition | easy | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | composition | medium | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | composition | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| visible | availability | easy | 5 | 40.0 % (2/5; IC95 12–77) | 80.0 % (4/5; IC95 38–96) | 40.0 % | 0 |
| visible | availability | medium | 5 | 40.0 % (2/5; IC95 12–77) | 60.0 % (3/5; IC95 23–88) | 40.0 % | 0 |
| visible | availability | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| visible | selection | easy | 5 | 100.0 % (5/5; IC95 57–100) | 100.0 % (5/5; IC95 57–100) | 90.0 % | 0 |
| visible | selection | medium | 5 | 20.0 % (1/5; IC95 4–62) | 20.0 % (1/5; IC95 4–62) | 10.0 % | 0 |
| visible | selection | hard | 5 | 0.0 % (0/5; IC95 0–43) | 20.0 % (1/5; IC95 4–62) | 10.0 % | 0 |
| visible | composition | easy | 5 | 60.0 % (3/5; IC95 23–88) | 100.0 % (5/5; IC95 57–100) | 70.0 % | 0 |
| visible | composition | medium | 5 | 20.0 % (1/5; IC95 4–62) | 20.0 % (1/5; IC95 4–62) | 10.0 % | 0 |
| visible | composition | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |

### `Qwen/Qwen3-1.7B+think`

| Condición | Familia | Nivel | n inst. | pass@1 | pass@2 | Tasa por muestra | Incompletas k=2 |
|---|---|---|---|---|---|---|---|
| tools | availability | easy | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | availability | medium | 5 | 0.0 % (0/5; IC95 0–43) | 20.0 % (1/5; IC95 4–62) | 10.0 % | 0 |
| tools | availability | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | selection | easy | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | selection | medium | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | selection | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | composition | easy | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | composition | medium | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | composition | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| visible | availability | easy | 5 | 80.0 % (4/5; IC95 38–96) | 100.0 % (5/5; IC95 57–100) | 90.0 % | 0 |
| visible | availability | medium | 5 | 80.0 % (4/5; IC95 38–96) | 100.0 % (5/5; IC95 57–100) | 80.0 % | 0 |
| visible | availability | hard | 5 | 40.0 % (2/5; IC95 12–77) | 60.0 % (3/5; IC95 23–88) | 30.0 % | 0 |
| visible | selection | easy | 5 | 100.0 % (5/5; IC95 57–100) | 100.0 % (5/5; IC95 57–100) | 100.0 % | 0 |
| visible | selection | medium | 5 | 100.0 % (5/5; IC95 57–100) | 100.0 % (5/5; IC95 57–100) | 100.0 % | 0 |
| visible | selection | hard | 5 | 20.0 % (1/5; IC95 4–62) | 40.0 % (2/5; IC95 12–77) | 30.0 % | 0 |
| visible | composition | easy | 5 | 80.0 % (4/5; IC95 38–96) | 80.0 % (4/5; IC95 38–96) | 70.0 % | 0 |
| visible | composition | medium | 5 | 0.0 % (0/5; IC95 0–43) | 40.0 % (2/5; IC95 12–77) | 20.0 % | 0 |
| visible | composition | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |

### `unsloth/Llama-3.2-1B-Instruct`

| Condición | Familia | Nivel | n inst. | pass@1 | pass@2 | Tasa por muestra | Incompletas k=2 |
|---|---|---|---|---|---|---|---|
| tools | availability | easy | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | availability | medium | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | availability | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | selection | easy | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | selection | medium | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | selection | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | composition | easy | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | composition | medium | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| tools | composition | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| visible | availability | easy | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| visible | availability | medium | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| visible | availability | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| visible | selection | easy | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| visible | selection | medium | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| visible | selection | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| visible | composition | easy | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| visible | composition | medium | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |
| visible | composition | hard | 5 | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | 0.0 % | 0 |

## Comparación con y sin herramientas

| Modelo | Familia | Nivel | Visible pass@1 | Herramientas pass@1 | Dif. (h − v) | Visible pass@2 | Herramientas pass@2 |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | availability | easy | 40.0 % (2/5; IC95 12–77) | 0.0 % (0/5; IC95 0–43) | -40.0 pts | 80.0 % (4/5; IC95 38–96) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B` | availability | hard | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B` | availability | medium | 40.0 % (2/5; IC95 12–77) | 0.0 % (0/5; IC95 0–43) | -40.0 pts | 60.0 % (3/5; IC95 23–88) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B` | composition | easy | 60.0 % (3/5; IC95 23–88) | 0.0 % (0/5; IC95 0–43) | -60.0 pts | 100.0 % (5/5; IC95 57–100) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B` | composition | hard | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B` | composition | medium | 20.0 % (1/5; IC95 4–62) | 0.0 % (0/5; IC95 0–43) | -20.0 pts | 20.0 % (1/5; IC95 4–62) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B` | selection | easy | 100.0 % (5/5; IC95 57–100) | 0.0 % (0/5; IC95 0–43) | -100.0 pts | 100.0 % (5/5; IC95 57–100) | 20.0 % (1/5; IC95 4–62) |
| `Qwen/Qwen3-1.7B` | selection | hard | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 20.0 % (1/5; IC95 4–62) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B` | selection | medium | 20.0 % (1/5; IC95 4–62) | 0.0 % (0/5; IC95 0–43) | -20.0 pts | 20.0 % (1/5; IC95 4–62) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B+think` | availability | easy | 80.0 % (4/5; IC95 38–96) | 0.0 % (0/5; IC95 0–43) | -80.0 pts | 100.0 % (5/5; IC95 57–100) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B+think` | availability | hard | 40.0 % (2/5; IC95 12–77) | 0.0 % (0/5; IC95 0–43) | -40.0 pts | 60.0 % (3/5; IC95 23–88) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B+think` | availability | medium | 80.0 % (4/5; IC95 38–96) | 0.0 % (0/5; IC95 0–43) | -80.0 pts | 100.0 % (5/5; IC95 57–100) | 20.0 % (1/5; IC95 4–62) |
| `Qwen/Qwen3-1.7B+think` | composition | easy | 80.0 % (4/5; IC95 38–96) | 0.0 % (0/5; IC95 0–43) | -80.0 pts | 80.0 % (4/5; IC95 38–96) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B+think` | composition | hard | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B+think` | composition | medium | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 40.0 % (2/5; IC95 12–77) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B+think` | selection | easy | 100.0 % (5/5; IC95 57–100) | 0.0 % (0/5; IC95 0–43) | -100.0 pts | 100.0 % (5/5; IC95 57–100) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B+think` | selection | hard | 20.0 % (1/5; IC95 4–62) | 0.0 % (0/5; IC95 0–43) | -20.0 pts | 40.0 % (2/5; IC95 12–77) | 0.0 % (0/5; IC95 0–43) |
| `Qwen/Qwen3-1.7B+think` | selection | medium | 100.0 % (5/5; IC95 57–100) | 0.0 % (0/5; IC95 0–43) | -100.0 pts | 100.0 % (5/5; IC95 57–100) | 0.0 % (0/5; IC95 0–43) |
| `unsloth/Llama-3.2-1B-Instruct` | availability | easy | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) |
| `unsloth/Llama-3.2-1B-Instruct` | availability | hard | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) |
| `unsloth/Llama-3.2-1B-Instruct` | availability | medium | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) |
| `unsloth/Llama-3.2-1B-Instruct` | composition | easy | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) |
| `unsloth/Llama-3.2-1B-Instruct` | composition | hard | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) |
| `unsloth/Llama-3.2-1B-Instruct` | composition | medium | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) |
| `unsloth/Llama-3.2-1B-Instruct` | selection | easy | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) |
| `unsloth/Llama-3.2-1B-Instruct` | selection | hard | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) |
| `unsloth/Llama-3.2-1B-Instruct` | selection | medium | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) | +0.0 pts | 0.0 % (0/5; IC95 0–43) | 0.0 % (0/5; IC95 0–43) |

### Diagnóstico de herramientas (por muestra)

| Modelo | Familia | Nivel | Llamadas válidas | Argumentos correctos | Datos requeridos | Límite excedido | Correcta sin recompensa |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | availability | easy | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B` | availability | medium | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B` | availability | hard | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B` | selection | easy | 0.0 % (0/10) | 0.0 % (0/10) | 10.0 % (1/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B` | selection | medium | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B` | selection | hard | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B` | composition | easy | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B` | composition | medium | 10.0 % (1/10) | 10.0 % (1/10) | 10.0 % (1/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B` | composition | hard | 10.0 % (1/10) | 10.0 % (1/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B+think` | availability | easy | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B+think` | availability | medium | 10.0 % (1/10) | 10.0 % (1/10) | 10.0 % (1/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B+think` | availability | hard | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B+think` | selection | easy | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B+think` | selection | medium | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B+think` | selection | hard | 10.0 % (1/10) | 10.0 % (1/10) | 10.0 % (1/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B+think` | composition | easy | 20.0 % (2/10) | 20.0 % (2/10) | 20.0 % (2/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B+think` | composition | medium | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `Qwen/Qwen3-1.7B+think` | composition | hard | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `unsloth/Llama-3.2-1B-Instruct` | availability | easy | 20.0 % (2/10) | 20.0 % (2/10) | 20.0 % (2/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `unsloth/Llama-3.2-1B-Instruct` | availability | medium | 20.0 % (2/10) | 10.0 % (1/10) | 20.0 % (2/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `unsloth/Llama-3.2-1B-Instruct` | availability | hard | 20.0 % (2/10) | 20.0 % (2/10) | 30.0 % (3/10) | 10.0 % (1/10) | 0.0 % (0/10) |
| `unsloth/Llama-3.2-1B-Instruct` | selection | easy | 10.0 % (1/10) | 10.0 % (1/10) | 10.0 % (1/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `unsloth/Llama-3.2-1B-Instruct` | selection | medium | 10.0 % (1/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `unsloth/Llama-3.2-1B-Instruct` | selection | hard | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `unsloth/Llama-3.2-1B-Instruct` | composition | easy | 10.0 % (1/10) | 10.0 % (1/10) | 10.0 % (1/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `unsloth/Llama-3.2-1B-Instruct` | composition | medium | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |
| `unsloth/Llama-3.2-1B-Instruct` | composition | hard | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) | 0.0 % (0/10) |

`Correcta sin recompensa` cuenta respuestas finales correctas que no recibieron recompensa, por ejemplo sin haber obtenido los datos: una señal de adivinación.

## Comparación con líneas base

Cada regla se evalúa con `verify_final_text` sobre las mismas instancias que los rollouts. Las triviales y de azar no leen el inventario. Las marcadas como `error_razonable` o azar contado sí lo leen: son errores plausibles, no azar. El control usa `expected` y solo valida el formato; no se compara con los modelos. Las reglas miden solo el texto final; en `tools` el modelo necesita además evidencia.

| Regla | Clase | avail/easy | avail/medium | avail/hard | selec/easy | selec/medium | selec/hard | compo/easy | compo/medium | compo/hard |
|---|---|---|---|---|---|---|---|---|---|---|
| `control_expected` | control | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| `ignorar_reservas` | error_razonable | 2/5 | 2/5 | 2/5 | 1/5 | 1/5 | 0/5 | 1/5 | 0/5 | 0/5 |
| `no_descontar_stock` | error_razonable | — | — | — | — | — | — | 1/5 | 0/5 | 0/5 |
| `nunca_alcanza` | trivial | 0/5 | 0/5 | 0/5 | — | — | — | — | — | — |
| `primera_sucursal` | trivial | — | — | — | 1/5 | 1/5 | 0/5 | — | — | — |
| `primera_sucursal_contada` | error_razonable | — | — | — | 2/5 | 2/5 | 1/5 | — | — | — |
| `siempre_alcanza` | trivial | 2/5 | 2/5 | 2/5 | — | — | — | — | — | — |
| `sucursal_azar` | azar | — | — | — | 0/5 | 1/5 | 0/5 | — | — | — |
| `sucursal_azar_contada` | azar | — | — | — | 1/5 | 2/5 | 1/5 | — | — | — |
| `todo_atendido` | trivial | — | — | — | — | — | — | 1/5 | 0/5 | 0/5 |

`supera` significa que el límite inferior del IC de pass@1 queda sobre la tasa de la regla; `no_distinguible`, que la regla cae dentro del IC.

| Modelo | Condición | Familia | Nivel | Mejor sin inventario | pass@1 frente a ella | Mejor con inventario | pass@1 frente a ella |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | tools | availability | easy | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | tools | availability | medium | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | tools | availability | hard | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | tools | selection | easy | primera_sucursal 20.0 % | no_distinguible | primera_sucursal_contada 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | tools | selection | medium | primera_sucursal 20.0 % | no_distinguible | primera_sucursal_contada 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | tools | selection | hard | primera_sucursal 0.0 % | no_distinguible | primera_sucursal_contada 20.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | tools | composition | easy | todo_atendido 20.0 % | no_distinguible | ignorar_reservas 20.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | tools | composition | medium | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | tools | composition | hard | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | visible | availability | easy | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | visible | availability | medium | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | visible | availability | hard | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | visible | selection | easy | primera_sucursal 20.0 % | supera | primera_sucursal_contada 40.0 % | supera |
| `Qwen/Qwen3-1.7B` | visible | selection | medium | primera_sucursal 20.0 % | no_distinguible | primera_sucursal_contada 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | visible | selection | hard | primera_sucursal 0.0 % | no_distinguible | primera_sucursal_contada 20.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B` | visible | composition | easy | todo_atendido 20.0 % | supera | ignorar_reservas 20.0 % | supera |
| `Qwen/Qwen3-1.7B` | visible | composition | medium | todo_atendido 0.0 % | supera | ignorar_reservas 0.0 % | supera |
| `Qwen/Qwen3-1.7B` | visible | composition | hard | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | availability | easy | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | availability | medium | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | availability | hard | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | selection | easy | primera_sucursal 20.0 % | no_distinguible | primera_sucursal_contada 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | selection | medium | primera_sucursal 20.0 % | no_distinguible | primera_sucursal_contada 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | selection | hard | primera_sucursal 0.0 % | no_distinguible | primera_sucursal_contada 20.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | composition | easy | todo_atendido 20.0 % | no_distinguible | ignorar_reservas 20.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | composition | medium | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | tools | composition | hard | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | availability | easy | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | availability | medium | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | availability | hard | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | selection | easy | primera_sucursal 20.0 % | supera | primera_sucursal_contada 40.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | visible | selection | medium | primera_sucursal 20.0 % | supera | primera_sucursal_contada 40.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | visible | selection | hard | primera_sucursal 0.0 % | supera | primera_sucursal_contada 20.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | composition | easy | todo_atendido 20.0 % | supera | ignorar_reservas 20.0 % | supera |
| `Qwen/Qwen3-1.7B+think` | visible | composition | medium | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |
| `Qwen/Qwen3-1.7B+think` | visible | composition | hard | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | tools | availability | easy | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | tools | availability | medium | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | tools | availability | hard | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | tools | selection | easy | primera_sucursal 20.0 % | no_distinguible | primera_sucursal_contada 40.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | tools | selection | medium | primera_sucursal 20.0 % | no_distinguible | primera_sucursal_contada 40.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | tools | selection | hard | primera_sucursal 0.0 % | no_distinguible | primera_sucursal_contada 20.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | tools | composition | easy | todo_atendido 20.0 % | no_distinguible | ignorar_reservas 20.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | tools | composition | medium | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | tools | composition | hard | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | visible | availability | easy | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | visible | availability | medium | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | visible | availability | hard | siempre_alcanza 40.0 % | no_distinguible | ignorar_reservas 40.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | visible | selection | easy | primera_sucursal 20.0 % | no_distinguible | primera_sucursal_contada 40.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | visible | selection | medium | primera_sucursal 20.0 % | no_distinguible | primera_sucursal_contada 40.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | visible | selection | hard | primera_sucursal 0.0 % | no_distinguible | primera_sucursal_contada 20.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | visible | composition | easy | todo_atendido 20.0 % | no_distinguible | ignorar_reservas 20.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | visible | composition | medium | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |
| `unsloth/Llama-3.2-1B-Instruct` | visible | composition | hard | todo_atendido 0.0 % | no_distinguible | ignorar_reservas 0.0 % | no_distinguible |

## Distribución de errores

| Modelo | Condición | error_type | Muestras | Porcentaje |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | tools | `no_answer_block` | 87 | 96.7 % |
| `Qwen/Qwen3-1.7B` | tools | `wrong_value` | 2 | 2.2 % |
| `Qwen/Qwen3-1.7B` | tools | `ok` | 1 | 1.1 % |
| `Qwen/Qwen3-1.7B` | visible | `wrong_value` | 39 | 43.3 % |
| `Qwen/Qwen3-1.7B` | visible | `ok` | 27 | 30.0 % |
| `Qwen/Qwen3-1.7B` | visible | `no_answer_block` | 18 | 20.0 % |
| `Qwen/Qwen3-1.7B` | visible | `multiple_answer_blocks` | 3 | 3.3 % |
| `Qwen/Qwen3-1.7B` | visible | `ambiguous_value` | 2 | 2.2 % |
| `Qwen/Qwen3-1.7B` | visible | `invalid_value` | 1 | 1.1 % |
| `Qwen/Qwen3-1.7B+think` | tools | `no_answer_block` | 87 | 96.7 % |
| `Qwen/Qwen3-1.7B+think` | tools | `missing_field` | 2 | 2.2 % |
| `Qwen/Qwen3-1.7B+think` | tools | `ok` | 1 | 1.1 % |
| `Qwen/Qwen3-1.7B+think` | visible | `ok` | 52 | 57.8 % |
| `Qwen/Qwen3-1.7B+think` | visible | `no_answer_block` | 19 | 21.1 % |
| `Qwen/Qwen3-1.7B+think` | visible | `wrong_value` | 17 | 18.9 % |
| `Qwen/Qwen3-1.7B+think` | visible | `missing_field` | 1 | 1.1 % |
| `Qwen/Qwen3-1.7B+think` | visible | `ambiguous_value` | 1 | 1.1 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `no_answer_block` | 85 | 94.4 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `invalid_value` | 2 | 2.2 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `wrong_value` | 1 | 1.1 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `tool_limit_exceeded` | 1 | 1.1 % |
| `unsloth/Llama-3.2-1B-Instruct` | tools | `multiple_answer_blocks` | 1 | 1.1 % |
| `unsloth/Llama-3.2-1B-Instruct` | visible | `no_answer_block` | 88 | 97.8 % |
| `unsloth/Llama-3.2-1B-Instruct` | visible | `multiple_answer_blocks` | 2 | 2.2 % |

| Modelo | Condición | Muestras | parser_error | Contradicción |
|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | tools | 90 | 96.7 % (87/90) | 0.0 % (0/90) |
| `Qwen/Qwen3-1.7B` | visible | 90 | 26.7 % (24/90) | 0.0 % (0/90) |
| `Qwen/Qwen3-1.7B+think` | tools | 90 | 98.9 % (89/90) | 0.0 % (0/90) |
| `Qwen/Qwen3-1.7B+think` | visible | 90 | 23.3 % (21/90) | 0.0 % (0/90) |
| `unsloth/Llama-3.2-1B-Instruct` | tools | 90 | 98.9 % (89/90) | 0.0 % (0/90) |
| `unsloth/Llama-3.2-1B-Instruct` | visible | 90 | 100.0 % (90/90) | 0.0 % (0/90) |

## Clasificación según §6 de la propuesta (orientativa)

**Es una lectura orientativa, no una decisión ni un umbral del curso.** La propuesta define las categorías; los números son nuestros y están en `summary.json`. La certeza es `firme` solo si el IC completo cae en la categoría. Con un IC más ancho que 30 puntos se marca `IC muy ancho`: esa categoría es una lectura provisional y no debe usarse para decidir.

**54 de 54 celdas tienen un IC muy ancho.** Hacen falta más instancias antes de sacar conclusiones de ellas.

| Modelo | Condición | Familia | Nivel | Lectura | Certeza | Frente a regla trivial | Acción sugerida |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | tools | availability | easy | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | tools | availability | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | tools | availability | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | tools | selection | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | tools | selection | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | tools | selection | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | tools | composition | easy | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | tools | composition | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | tools | composition | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | visible | availability | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | visible | availability | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | visible | availability | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B` | visible | selection | easy | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-1.7B` | visible | selection | medium | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | no_distinguible | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-1.7B` | visible | selection | hard | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | visible | composition | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B` | visible | composition | medium | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | supera | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-1.7B` | visible | composition | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | tools | availability | easy | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | tools | availability | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | tools | availability | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | tools | selection | easy | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | tools | selection | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | tools | selection | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | tools | composition | easy | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | tools | composition | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | tools | composition | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `Qwen/Qwen3-1.7B+think` | visible | availability | easy | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | visible | availability | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | visible | availability | hard | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | visible | selection | easy | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-1.7B+think` | visible | selection | medium | Éxito cercano a 100 % | IC muy ancho, no concluir | supera | Poco margen: aumentar composición o variedad |
| `Qwen/Qwen3-1.7B+think` | visible | selection | hard | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | supera | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | visible | composition | easy | Acierto intermedio sin ganancia apreciable | IC muy ancho, no concluir | supera | Fuera de la tabla de §6: revisar a mano |
| `Qwen/Qwen3-1.7B+think` | visible | composition | medium | Acierto intermedio y pass@k mayor que pass@1 | IC muy ancho, no concluir | no_distinguible | Posible zona aprendible: profundizar |
| `Qwen/Qwen3-1.7B+think` | visible | composition | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | availability | easy | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | availability | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | availability | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | selection | easy | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | selection | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | selection | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | composition | easy | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | composition | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | tools | composition | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | availability | easy | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | availability | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | availability | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | selection | easy | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | selection | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | selection | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | composition | easy | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | composition | medium | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |
| `unsloth/Llama-3.2-1B-Instruct` | visible | composition | hard | Éxito cercano a 0 % incluso con k intentos | IC muy ancho, no concluir | no_distinguible | Señal escasa: simplificar, SFT o reconsiderar |

### Entre condiciones

| Modelo | Familia | Nivel | Lectura | Certeza | Acción sugerida |
|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | availability | easy | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B` | availability | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B` | availability | medium | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B` | composition | easy | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B` | composition | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B` | composition | medium | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B` | selection | easy | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |
| `Qwen/Qwen3-1.7B` | selection | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B` | selection | medium | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B+think` | availability | easy | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |
| `Qwen/Qwen3-1.7B+think` | availability | hard | Ningún patrón de §6 entre condiciones | IC muy ancho, no concluir | — |
| `Qwen/Qwen3-1.7B+think` | availability | medium | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |
| `Qwen/Qwen3-1.7B+think` | composition | easy | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |
| `Qwen/Qwen3-1.7B+think` | composition | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B+think` | composition | medium | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B+think` | selection | easy | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |
| `Qwen/Qwen3-1.7B+think` | selection | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `Qwen/Qwen3-1.7B+think` | selection | medium | Bien con datos visibles, mal con herramientas | IC muy ancho, no concluir | Priorizar harness y protocolo |
| `unsloth/Llama-3.2-1B-Instruct` | availability | easy | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | availability | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | availability | medium | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | composition | easy | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | composition | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | composition | medium | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | selection | easy | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | selection | hard | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |
| `unsloth/Llama-3.2-1B-Instruct` | selection | medium | Mal en ambas condiciones | IC muy ancho, no concluir | Aislar operaciones y ajustar niveles |

## Costo

| Modelo | Condición | Muestras | Tokens nuevos por muestra | s por muestra | Horas (suma de `usage.seconds`) | Llegó al tope de tokens |
|---|---|---|---|---|---|---|
| `Qwen/Qwen3-1.7B` | tools | 90 | 171 | 3.23 | 0.08 | 4.4 % (4/90) |
| `Qwen/Qwen3-1.7B` | visible | 90 | 452 | 4.40 | 0.11 | 12.2 % (11/90) |
| `Qwen/Qwen3-1.7B+think` | tools | 90 | 1124 | 14.47 | 0.36 | 21.1 % (19/90) |
| `Qwen/Qwen3-1.7B+think` | visible | 90 | 1161 | 15.30 | 0.38 | 21.1 % (19/90) |
| `unsloth/Llama-3.2-1B-Instruct` | tools | 90 | 440 | 4.01 | 0.10 | 28.9 % (26/90) |
| `unsloth/Llama-3.2-1B-Instruct` | visible | 90 | 333 | 2.85 | 0.07 | 10.0 % (9/90) |

`Llegó al tope de tokens` cuenta las muestras con alguna generación cortada por `max_new_tokens`, según `usage.stop_reasons`. En rollouts sin ese campo es una cota inferior. Un valor alto, sobre todo con thinking, indica respuestas cortadas.

## Instancias incompletas

Ninguna: todas las instancias vistas tienen 2 muestras.

## Revisión manual

`muestra_errores.jsonl` tiene 188 rollouts fallidos, estratificados por modelo, condición, familia, dificultad y error_type (hasta 3 por estrato). Sirve para verificar a mano si el verificador rechazó bien.
