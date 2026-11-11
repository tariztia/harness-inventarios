# Guía para correr el piloto en Google Colab

No hace falta GPU local ni conocer el proyecto. Necesitas una cuenta de Google y, en tu computador, este repositorio con `uv` instalado.

## 1. Generar el zip

En la carpeta del proyecto:

```bash
uv run python scripts/package_for_colab.py
```

Crea `dist/inventory_harness_colab.zip` y lo prueba en una carpeta vacía. Debe terminar con `Comprobado desde una carpeta vacia.`

## 2. Subirlo a Drive

En [Google Drive](https://drive.google.com), crea la carpeta `inventory_harness` en *Mi unidad* y sube ahí el zip. Debe quedar así: `Mi unidad/inventory_harness/inventory_harness_colab.zip`.

## 3. Abrir el cuaderno y activar la GPU

1. En [Colab](https://colab.research.google.com), usa *Archivo > Subir cuaderno* y elige `notebooks/piloto_colab.ipynb`. Para la línea base y las respuestas del modelo objetivo, elige en cambio `notebooks/qwen_objetivo_colab.ipynb`, que se ejecuta completo con *Ejecutar todo*.
2. Usa *Entorno de ejecución > Cambiar tipo de entorno de ejecución > GPU T4 > Guardar*.

## 4. Ejecutar la exploración

Ejecuta *Entorno de ejecución > Ejecutar todo*. Colab pedirá permiso para usar Drive: acéptalo.

El cuaderno comprueba la GPU, instala dependencias, corre las pruebas del núcleo, hace una prueba de humo y luego la exploración. La sección 5 imprime un rollout completo por modelo. Revísalos: el modelo debería llamar a `get_inventory` y terminar con un bloque `<answer>`.

Mantén la pestaña abierta. La exploración corre Qwen3-1.7B y Qwen3-8B con thinking, y guarda en `results/exploracion_parser_nuevo`. Qwen3-8B no cabe en 16 bits en una T4, así que ahí se carga en 8 bits. La exploración anterior de 3 variantes tomó cerca de una hora en una T4; Qwen3-8B será más lento. Las líneas `TOTAL ...` muestran el tiempo real restante.

El piloto no corre con *Ejecutar todo*: está protegido por `EJECUTAR_PILOTO = False`.

## 5. Devolver los resultados de la exploración

Al terminar, descarga o comparte **`Mi unidad/inventory_harness/resultados_inventory_harness.zip`**, creado por la sección 8. Ese es el único archivo que necesitamos. Espera nuestra revisión antes de correr el piloto.

## 6. Ejecutar el piloto

Solo cuando te lo pidamos:

1. En la sección 4, ajusta `THINKING_PILOTO` como te indiquemos y pon `EJECUTAR_PILOTO = True`.
2. Ejecuta las secciones 1 a 4. La prueba de humo se puede saltar.
3. Ejecuta la sección 7. Su primera celda calcula el tiempo con lo medido en tu exploración.
4. Ejecuta la sección 8 y devuelve el mismo zip, que ahora incluye ambas etapas.

Son 3.600 rollouts por variante. Tiempos medidos en una T4 durante la exploración: 3,8 s por rollout sin thinking y 14,9 s con thinking, es decir, unas 4 y 15 horas. Las corridas reales con herramientas pueden tardar más por las rondas extra. Puede requerir más de una sesión.

## Si Colab se desconecta

No se pierde nada importante: los rollouts se guardan en Drive a medida que terminan.

1. Vuelve a conectar y comprueba que la GPU siga activa. Si Colab no te da GPU, se agotó la cuota gratuita: espera unas horas o hasta el día siguiente.
2. Ejecuta las secciones 1 a 4, sin cambiar la configuración.
3. Ejecuta de nuevo la celda de la etapa que estaba corriendo. Continúa sin duplicar.

Si aparece `ya contiene otra corrida` o `OMITIDO`, cambiaste la configuración de esa etapa. Vuelve a los valores anteriores. No borres archivos de `results/`. Si aparece un modelo con estado `no_cargo` en el informe, los demás siguen sin problema: revisa el mensaje de error.

## Opcional: modelos restringidos

El cuaderno usa `Qwen/Qwen3-1.7B` y `unsloth/Llama-3.2-1B-Instruct`, que no piden token. Gemma aporta una comparación útil, pero no es necesario. Requiere aprobación manual, que puede tardar.

1. Crea una cuenta en [Hugging Face](https://huggingface.co).
2. Solicita acceso en [`google/gemma-3-1b-it`](https://huggingface.co/google/gemma-3-1b-it). Espera la confirmación.
3. Crea un token de lectura en *Settings > Access Tokens*.
4. En Colab, abre *Secrets* (icono de llave), crea `HF_TOKEN` con ese valor y activa el acceso del cuaderno. Nunca lo escribas en una celda.
5. En la sección 4, pon `USAR_GEMMA = True`.
