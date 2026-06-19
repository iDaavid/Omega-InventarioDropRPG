| Estructura de datos | ¿En qué parte del proyecto se usará? (ej. módulo, función, caso de uso) | ¿Qué operaciones específicas se necesitarán? | ¿Se implementará desde cero o se usará alguna biblioteca? |
| :--- | :--- | :--- | :--- |
| Pila | Interfaz Gráfica (GUI). Sistema de navegación (volver a la pantalla anterior) o "deshacer" (ej. recuperar un ítem vendido/descartado por error). | `push` (apilar acción/ventana), `pop` (desapilar para volver/deshacer). | Biblioteca nativa (Listas de Python simulando la pila). |
| Cola | Módulo del Servidor (`servidor.py`). Simular el procesamiento secuencial de peticiones (ataques al jefe, validación de recolección de loot). | `enqueue` (encolar evento de combate), `dequeue` (procesar resultado). | Biblioteca nativa (`collections.deque` o `queue.Queue`). |
| Lista enlazada | Interfaz Gráfica (GUI) / Logs. Registro visual secuencial de los drops obtenidos (el historial o *scroll log* que ve el jugador). | `append` (agregar nuevo mensaje al final), `traverse` (recorrer para renderizar). | Biblioteca nativa (Listas de Python). |
| Árbol binario | No se usará en este alcance. | N/A | N/A |
| Árbol AVL | No se usará. La cantidad de ítems a buscar no justifica la complejidad de mantener ramas balanceadas. | N/A | N/A |
| Árbol 2-3 | No se usará. | N/A | N/A |
| Árbol B | No se usará. El almacenamiento y persistencia de datos se gestionará directamente con lectura/escritura de archivos `.json`. | N/A | N/A |
| Grafo | No se usará. Nuestro enfoque actual es inventario y matemáticas (RNG); no hay mapas, movimiento ni misiones interconectadas. | N/A | N/A |
| Hashing | Módulos `inventario.py` y `rng_drops.py`. Núcleo de las *Loot Tables* de los jefes (probabilidades) y el inventario del jugador. | `insert` (agregar ítem nuevo), `get` (consultar probabilidad/cantidad), `update` (sumar recursos). | Biblioteca nativa (Diccionarios de Python `dict`). |

## Distribución de Tareas

* **David Herrera:** Responsable de `main.py` y `servidor.py`. Gestionará la cola de peticiones, la orquestación del flujo principal y asegurará que los módulos se comuniquen correctamente.
* **Luis Bernay:** Responsable de `rng_drops.py` y la estructura de `jefes.json`. Se enfocará en la precisión de las probabilidades, la implementación del sistema "Pity" y la lógica matemática de obtención de ítems.
* **Carlos Chinchilla:** Responsable de la capa visual del juego. Diseñará la interfaz para que sea intuitiva, renderizará los logs del historial usando listas y gestionará la navegación mediante pilas.
* **Mahlon Romero:** Responsable de `inventario.py` y la persistencia de datos. Asegurará que los recursos se guarden/carguen correctamente, implementará el manejo de errores (try-except) y realizará pruebas de integración para asegurar que todo el sistema sea robusto.
