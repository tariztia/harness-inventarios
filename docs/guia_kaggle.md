# Guía para correr el modelo objetivo en Kaggle

`notebooks/qwen_objetivo_kaggle.ipynb` hace lo mismo que `qwen_objetivo_colab.ipynb`: línea base de Qwen3-1.7B sobre `eval` y respuestas sobre `train` para SFT/DPO. Sirve cuando Colab se queda sin cuota de GPU. Kaggle da 30 horas de GPU por semana, y una versión guardada corre en segundo plano hasta 12 horas, aunque el computador esté apagado.

## 1. Cuenta

Crea una cuenta en kaggle.com y verifica tu teléfono (*Settings > Phone verification*). Sin eso no se habilitan la GPU ni el acceso a Internet, que hace falta para descargar el modelo.

## 2. Dataset con el código y lo ya corrido

1. En Google Drive, haz clic derecho en la carpeta `inventory_harness` > *Descargar*. Drive entrega un zip con `inventory_harness_colab.zip` y `results/`.
2. En Kaggle: *Create > New Dataset*. Arrastra ese zip (Kaggle lo descomprime), ponle un nombre, déjalo **privado** y crea el dataset.

Si no hay corrida anterior, basta con subir `inventory_harness_colab.zip`.

## 3. Cuaderno

1. *Create > New Notebook*, y luego *File > Import Notebook*: sube `notebooks/qwen_objetivo_kaggle.ipynb`.
2. Panel derecho: *Add Input* > *Your Datasets* > el dataset del paso 2.
3. *Settings*: **Accelerator: GPU T4 x2** e **Internet: On**.
4. Opcional: ejecuta las celdas 1 y 2 a mano. La 2 debe decir `linea_base_qwen17b: copiada ... se continua`.
5. *Save Version* > **Save & Run All (Commit)** > *Save*. Ya puedes cerrar la página.

Con dos GPU, la línea base y las respuestas de `train` corren al mismo tiempo, una en cada GPU. El cuaderno se detiene a las 11 horas (`LIMITE_HORAS`) para guardar antes del tope de Kaggle.

## 4. Resultados

En la página del cuaderno, abre la versión guardada (*Version history*) y su pestaña **Output**. Descarga `resultados_qwen17b.zip`, que trae las carpetas `linea_base_qwen17b`, `trazas_qwen17b` y `datos_derivados_qwen17b`.

Si la corrida no alcanzó a terminar, crea un dataset nuevo con esas carpetas, que reemplace al anterior como entrada, y guarda otra versión: continúa donde quedó.

## Profesor Qwen3-8B (`qwen_profesor_kaggle.ipynb`)

Corre Qwen3-8B sobre las tareas de `train` para dar respuestas correctas donde Qwen3-1.7B no las tiene, y arma los datos SFT/DPO con ambos modelos. En float16 pesa 16 GB: se reparte entre las dos T4.

1. **Dataset nuevo** (*Create > New Dataset*, privado), con dos archivos: el `inventory_harness_colab.zip` actualizado (trae `scripts/pending_prompts.py`) y `resultados_qwen17b.zip`, la salida de la corrida del 1.7B.
2. **Cuaderno nuevo**: *File > Import Notebook* con `notebooks/qwen_profesor_kaggle.ipynb`. *Add Input* con ese dataset. *Settings*: **GPU T4 x2** e **Internet On**.
3. **Paso 1, prueba** (`PASO = 1`, ya viene así): *Save Version > Save & Run All (Commit)*. Corre 9 prompts donde el 1.7B nunca acertó, con 2 muestras. La sección 6 del log dice cuántos resolvió el 8B y cuánto tardó por respuesta.
4. **Paso 2, pendientes** (`PASO = 2`): los 71 prompts sin respuesta correcta. Agrega como entrada la salida de la versión anterior (*Add Input > Your Work*, el mismo cuaderno) para no repetir la prueba, y guarda otra versión.
5. **Paso 3, todo** (`PASO = 3`, opcional): los 180 prompts, para que todas las trazas SFT vengan del 8B. Igual que el paso 2, con la salida anterior como entrada.

Cada versión deja en *Output* `resultados_qwen8b.zip`, con `trazas_qwen8b`, `datos_derivados_qwen8b` y las listas de pendientes.

### Corrida grande con vLLM (pasos 0 y 4)

Con `transformers`, el 8B generó ~21 tok/s en las dos T4 (360 rollouts tomaron 6,9 h de GPU), así que ~7.200 rollouts serían del orden de 100 h. vLLM atiende muchas secuencias a la vez y se espera que sea mucho más rápido, pero **su velocidad real en la T4 de Kaggle no está medida**: el paso 0 la mide.

- **Paso 0, prueba de velocidad** (`PASO = 0`, `BACKEND = "vllm"`): 18 instancias de `train` con 4 muestras (144 rollouts). En el log, la sección 6b imprime los tok/s y el porcentaje de aciertos. Con ~21 tok/s como referencia de `transformers`, decide si la corrida grande cabe en la cuota de Kaggle. Para comprobar que vLLM no cambia los resultados, repite con `BACKEND = "hf"` (más lento: baja `HUMO_N` a 9 y `MUESTRAS_HUMO` a 2) y compara los aciertos de las dos carpetas.
- **Paso 4, corrida grande** (`PASO = 4`): 100 instancias por celda (900 en total, que incluyen las 90 de antes) con 4 muestras por prompt en las dos condiciones. Para repartirla, cada persona pone un `SHARD` distinto (`"1/3"`, `"2/3"`, `"3/3"`) con el mismo zip de código; cada una obtiene su `resultados_trazas_<modelo>_vllm_parte<i>de<N>.zip`. Si una sesión no termina, agrega su salida como entrada y vuelve a correr: continúa donde quedó.
- `MODELO = "Qwen/Qwen3-1.7B"` en el paso 4 genera las respuestas incorrectas para los pares DPO sobre las mismas instancias.
- Los datos SFT/DPO se arman después, en el repositorio, juntando todas las carpetas: `python scripts/build_training_data.py <partes del 8B> <partes del 1.7B> --out results/datos_derivados`. Las partes deben ser disjuntas, venir del mismo zip y tener la misma semilla y el mismo `n_per_cell`; si no, el script lo avisa.
- Una carpeta hecha con `transformers` no se puede continuar con vLLM (ni al revés): `run_pilot.py` lo rechaza porque la configuración de generación cambió.
- Si vLLM no arranca en la T4, el log lo dirá en la instalación o en la carga del modelo; las alternativas son un checkpoint AWQ en una sola GPU o una sesión corta de Colab con A100.

## Línea base de otros modelos (`linea_base_otros_kaggle.ipynb`)

Mide pass@1 y pass@5 sobre `eval`, con las mismas instancias que la línea base de Qwen3-1.7B con thinking, para Llama-3.2-1B, Qwen3-1.7B y Qwen3-4B sin thinking (GPU 0) y Qwen3-0.6B con thinking (GPU 1). No usa `train`.

1. **Dataset** (*Create > New Dataset*, privado) con `dist/inventory_harness_colab.zip`. Está en el repo; se regenera con `python scripts/package_for_colab.py` cuando cambia el código.
2. **Cuaderno nuevo**: *File > Import Notebook* con `notebooks/linea_base_otros_kaggle.ipynb`. *Add Input* con ese dataset. *Settings*: **GPU T4 x2** e **Internet On**.
3. *Save Version > Save & Run All (Commit)*.
4. En *Output* queda `resultados_otros_modelos.zip`, con `linea_base_sin_think` y `linea_base_qwen06b`. Si la tanda con thinking no terminó, agrega esa salida como entrada (*Add Input > Your Work*) y guarda otra versión: continúa donde quedó.
