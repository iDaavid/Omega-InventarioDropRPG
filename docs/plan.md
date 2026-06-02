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
