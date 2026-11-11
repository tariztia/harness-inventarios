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
