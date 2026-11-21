# Comparación de estrategias de post-entrenamiento sobre un harness de inventarios

Integrantes: Tomás Ariztía, Arturo Herreros, Rodrigo Meza, Matías Retamales

Código, datos y resultados: https://github.com/tariztia/harness-inventarios

Proyecto de Investigación, IIC-3694 Inteligencia Artificial Generativa. Documento base de la propuesta inicial (Entrega 1) y del informe de avance (Entrega 2).

## 1. Introducción

Los avances recientes en razonamiento y uso de herramientas se han logrado entrenando modelos contra un entorno con un verificador que califica cada intento. En el Desafío de Investigación construimos uno de esos entornos: un harness de consultas sobre inventarios de una cadena de sucursales, con tareas generadas por código, respuestas calculadas por un solucionador independiente y un verificador que sirve como recompensa. También medimos la línea base de cinco modelos y generamos los datos derivados (trazas para SFT y pares para DPO).

El proyecto usa ese entorno para entrenar al modelo objetivo, Qwen3-1.7B con thinking, y comparar estrategias de entrenamiento con un presupuesto de cómputo comparable. Nos interesa menos el número final que entender qué aporta cada estrategia, cuándo falla y si el modelo aprende a explotar el verificador.

## 2. Revisión bibliográfica

**RL con recompensas verificables.** GRPO (Shao et al., 2024) reemplaza la red de valor de PPO por un baseline calculado con el promedio de las respuestas del mismo prompt, lo que reduce el costo de entrenamiento. DeepSeek-R1 (DeepSeek-AI, 2025) muestra que la capacidad de razonar puede incentivarse con RL puro, sin trayectorias etiquetadas por humanos. DAPO (Yu et al., 2025) sobremuestrea y descarta los prompts cuya precisión es 0 o 1, para que todos aporten gradiente; es la base de nuestra ablación, porque composición hard casi no da aciertos.

**SFT, DPO y generalización.** DPO (Rafailov et al., 2023) resuelve el problema de RLHF a partir de pares (elegida, rechazada) con una pérdida de clasificación simple (camino 5). LoRA (Hu et al., 2021) reduce los parámetros entrenables y la memoria, lo que hace viables SFT y DPO en una T4. Chu et al. (2025) encuentran que el RL generaliza a variantes no vistas mientras el SFT tiende a memorizar, y que el SFT sigue siendo necesario para estabilizar el formato de salida antes del RL. Es la referencia de nuestras preguntas sobre SFT previo y niveles no vistos.

**Reward hacking y auditoría.** Skalse et al. (2022) dan la primera definición formal de reward hacking: optimizar una recompensa imperfecta empeora el objetivo real. SWE-Bench+ (Aleithan et al., 2024) revisó a mano los parches exitosos de SWE-bench: en el 32,67 % la solución venía en el propio reporte y el 31,08 % pasaba con pruebas débiles. De ahí viene la auditoría manual de trazas exitosas que pide el enunciado.

**Entorno y herramientas.** Nuestro entorno sigue la línea de Reasoning Gym (Stojanovski et al., 2025), generadores procedurales con verificadores para RL con recompensas verificables. El modelo objetivo es de la familia Qwen3 (Yang et al., 2025), y entrenaremos con la biblioteca TRL de Hugging Face (https://github.com/huggingface/trl).

## 3. Entorno a utilizar

Usamos nuestro propio entorno, descrito en el informe del Desafío (`docs/informe.md`). Es el único que conocemos a fondo y ya tiene los datos derivados listos.

**Tarea.** El modelo recibe una solicitud en español sobre inventarios y responde con un bloque `<answer>` de pares `clave: valor`. Hay tres familias (disponibilidad, selección y composición) con tres niveles cada una (easy, medium y hard) y dos condiciones: `visible`, con los datos en el prompt, y `tools`, donde el modelo debe pedirlos con `get_inventory`, con un máximo de dos rondas. La respuesta correcta se calcula por código y la recompensa es 1 solo si todos los campos coinciden.

**Particiones.** Las instancias se generan por código con semillas reproducibles, en tres particiones: `train`, `eval` y `test`. Una de las cinco plantillas de redacción de cada familia solo aparece en `test`, para medir generalización a redacciones nuevas.

**Verificador.** Es determinista, acepta formas equivalentes (`3`, `tres`, `20-17`), rechaza respuestas ambiguas o múltiples y vuelve a ejecutar las llamadas contra el inventario real para evitar observaciones inventadas. Pasa 326 de 334 casos adversariales escritos por el equipo y se corrigió tras una auditoría con respuestas reales.

**Línea base del modelo objetivo** (Qwen3-1.7B con thinking, partición `eval`, 90 instancias por condición, 5 muestras por instancia):

| Condición | pass@1 | pass@5 |
|---|---|---|
| Datos visibles | 58/90 (64 %) | 80/90 (89 %) |
| Con herramientas | 37/90 (41 %) | 62/90 (69 %) |

Por dificultad (% sobre 30 instancias), con herramientas, el pass@1 baja de 63 % en easy a 43 % en medium y 17 % en hard. Con datos visibles baja de 90 % a 60 % y 43 %. En todos los niveles pass@5 supera con claridad a pass@1, lo que deja espacio para que el entrenamiento refuerce lo que el modelo ya hace a veces. La excepción es composición hard, que no da señal: 0/10 con herramientas y 2/10 con datos visibles, incluso con 5 intentos.

**Datos derivados.** 170 trazas para SFT y 106 pares para DPO sobre los 180 prompts de `train`, generados con Qwen3-8B con thinking como profesor y filtrados con el verificador. Las respuestas rechazadas de los pares son, en 105 de 106 casos, del propio modelo objetivo.

## 4. Propuesta de investigación

### 4.1 Preguntas de investigación

1. ¿Qué aporta cada estrategia (SFT, DPO, RLVR) sobre el modelo base, medido por pass@1 y pass@5 en `eval`?
2. ¿El SFT previo acelera o limita el aprendizaje con RLVR? Se compara SFT seguido de RL contra RL solo, con la misma cantidad de pasos de RL.
3. ¿Cuánto generaliza cada estrategia a `test`, que usa una plantilla de redacción nueva, y a niveles de dificultad no vistos? Para esto entrenamos solo con easy y medium, y medimos también en hard.
4. ¿Aparece reward hacking y bajo qué condiciones?

### 4.2 Caminos de entrenamiento

| Camino | Qué se entrena | Datos |
|---|---|---|
| 1. Modelo base | Nada | Línea base ya medida |
| 2. Solo SFT | LoRA sobre Qwen3-1.7B | 170 trazas del profesor |
| 3. SFT y luego RLVR | El modelo del camino 2, con GRPO | Prompts de `train`, recompensa del verificador |
| 4. Solo RLVR | GRPO desde el modelo base | Prompts de `train`, recompensa del verificador |
| 5. DPO | LoRA sobre Qwen3-1.7B | 106 pares (elegida, rechazada) |

Todos los caminos parten del mismo modelo y se evalúan con el mismo protocolo de la línea base: partición `eval`, 5 muestras, temperatura 0,7. El presupuesto comparable se fijará en horas de GPU o en número de respuestas generadas, y se definirá tras las primeras corridas, cuando conozcamos el costo de cada camino.

### 4.3 Diseño experimental

**Métricas.** pass@1 y pass@5 por familia, nivel y condición, con intervalos de Wilson al 95 % sobre instancias, como en la línea base. Todos los resultados finales se reportan con la versión final del verificador. Si lo corregimos durante el proyecto, se vuelven a evaluar los rollouts guardados con `scripts/reevaluate.py` para que las cifras sean comparables.

**Semillas.** Una semilla de entrenamiento por camino como mínimo. Si el cómputo alcanza, repetimos los caminos 3 y 4 con una segunda semilla, porque el RL es el más variable.

**Auditoría manual.** Revisaremos a mano una muestra de trazas con recompensa 1 de cada camino (alrededor de 50 por camino) y estimaremos qué fracción son aciertos genuinos: datos pedidos y usados, razonamiento coherente y respuesta correcta por las razones correctas.

**Más prompts de entrenamiento.** Los 180 prompts de `train` son pocos para RL. Generaremos más instancias de entrenamiento con otra semilla y las filtraremos por huella contra `eval` y `test`. No se debe regenerar `eval` con otro `n_per_cell`, porque eso cambia las instancias.

### 4.4 Nivel de complejidad

El núcleo es el nivel 1 del enunciado: estudiar métodos existentes con código público (SFT, DPO y GRPO de TRL) y analizarlos bajo distintas condiciones. Como ablación, probaremos una mejora incremental del nivel 3, a partir de DAPO: filtrar los grupos sin señal o usar un currículo por dificultad. Se compara contra GRPO base con las mismas condiciones. Es opcional y dependerá del tiempo y del cómputo que quede.

### 4.5 Reward hacking previsto

Del informe del Desafío conocemos puntos débiles donde un modelo entrenado contra el verificador podría explotar la recompensa. Los vigilaremos desde las primeras corridas:

- **Respuestas constantes en `visible`.** Responder siempre "sí, faltan 0" acierta 50 % de disponibilidad, y "todo se atiende" acierta 30 % de composición. En `tools` este atajo no sirve, porque se exige haber pedido los datos.
- **Llamadas sin etiqueta.** El harness las acepta para medir qué datos pide el modelo, así que la recompensa no empuja hacia el formato estándar.
- **Prosa que contradice al bloque.** La revisión de contradicciones es débil y no cubre composición. Una explicación incoherente con un bloque correcto recibe 1.
- **Sumas con etiquetas.** `20 gatos y 20 perros` vale 40, porque las etiquetas no se validan contra la instancia.
- **Respuestas cortadas o muy largas.** Un tope de tokens bajo castiga el razonamiento largo. Uno alto puede premiar respuestas que se extienden sin necesidad.

El ciclo que documentaremos es entrenar, mirar trazas con recompensa alta, detectar qué explota el modelo, corregir el verificador o el entorno y volver a entrenar, y reportar el efecto de cada corrección.

### 4.6 Riesgos

- **Composición hard no da señal**, con 0/10 y 2/10 en el objetivo, ni siquiera con 5 intentos. La excluiremos del RL inicial o la usaremos solo al final.
- **La condición `tools` tiene varios turnos**, y el GRPO estándar de TRL genera una sola respuesta por prompt. Empezaremos con RL sobre `visible`, donde hay buena señal (64 % y 89 %), y extenderemos a `tools` si alcanza el tiempo.
- **Pocas trazas de SFT.** 170 ejemplos alcanzan para ver un efecto, pero son pocos. Podemos ampliarlos con el profesor sobre las instancias nuevas de `train`.
- **Formato en selección con herramientas.** 47 de 150 respuestas del objetivo vienen sin claves (`S2|29|0`). El SFT podría corregirlo, y es una de las primeras cosas que mediremos. No cambiaremos el prompt durante el proyecto: invalidaría las trazas y la línea base.
- **Cómputo.** RL es el camino más caro. Las pruebas de SFT y DPO caben en las dos T4 de Kaggle, y el RL se correrá en Peteroa (GPU H100), a donde tendremos acceso desde el 23 de noviembre.

## 5. Plan de trabajo

| Fecha | Hito |
|---|---|
| 21 y 22 de noviembre | Scripts de SFT, DPO y GRPO con TRL, probados con pocos pasos. Instrucciones para Peteroa. |
| 23 de noviembre | Acceso a Peteroa. Primeras corridas cortas de SFT y GRPO, con curvas de recompensa. |
| 24 y 25 de noviembre | Más corridas. Informe de avance con línea base, implementación y curvas (Entrega 2). |
| 26 de noviembre al 4 de diciembre | Los cinco caminos con presupuesto comparable, evaluación en `eval` y `test`, auditoría manual, ablación y correcciones al verificador. |
| 5 a 9 de diciembre | Paper de 7 páginas, poster y video (Entrega 3). |

## Referencias

Aleithan, R., Xue, H., Mohajer, M. M., Nnorom, E., Uddin, G., y Wang, S. (2024). SWE-Bench+: Enhanced coding benchmark for LLMs. arXiv:2410.06992.

Chu, T., et al. (2025). SFT memorizes, RL generalizes: A comparative study of foundation model post-training. arXiv:2501.17161.

DeepSeek-AI (2025). DeepSeek-R1: Incentivizing reasoning capability in LLMs via reinforcement learning. Nature, 645, 633–638. arXiv:2501.12948.

Hu, E. J., et al. (2021). LoRA: Low-rank adaptation of large language models. arXiv:2106.09685.

Rafailov, R., et al. (2023). Direct preference optimization: Your language model is secretly a reward model. arXiv:2305.18290.

Shao, Z., et al. (2024). DeepSeekMath: Pushing the limits of mathematical reasoning in open language models. arXiv:2402.03300.

Skalse, J., et al. (2022). Defining and characterizing reward hacking. arXiv:2209.13085.

Stojanovski, Z., et al. (2025). Reasoning Gym: Reasoning environments for reinforcement learning with verifiable rewards. NeurIPS 2025. arXiv:2505.24760.

Yang, A., et al. (2025). Qwen3 technical report. arXiv:2505.09388.

Yu, Q., et al. (2025). DAPO: An open-source LLM reinforcement learning system at scale. arXiv:2503.14476.
