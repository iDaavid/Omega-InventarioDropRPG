"""
inventario.py — Inventario del jugador usando Tabla Hash (Diccionario Python).

Cada ítem obtenido en una simulación se acumula en un diccionario interno
donde la clave es el nombre del ítem y el valor es la cantidad apilada.

Operaciones principales:
- agregar_item(): O(1) amortizado — insert/update en la tabla hash.
- obtener_cantidad(): O(1) — lookup directo por clave.
- guardar()/cargar(): Persistencia en datos/recursos.json.

Referencia académica: Luis Joyanes Aguilar — Tablas Hash / Dispersión.
"""

import json
import os


class InventarioJugador:
    """
    Gestiona el banco de ítems del jugador usando un diccionario (tabla hash).

    La estructura interna es un dict[str, int] donde:
    - Clave (str): Nombre del ítem (e.g., "Vorkath Head").
    - Valor (int): Cantidad acumulada.

    Persiste los datos en un archivo JSON para sobrevivir entre sesiones.
    """

    def __init__(self, ruta_json):
        """
        Inicializa el inventario cargando datos existentes o creando uno vacío.

        Args:
            ruta_json: Ruta al archivo de persistencia (e.g., 'datos/recursos.json').
        """
        self.ruta_json = ruta_json
        # Tabla Hash interna: {"nombre_item": cantidad}
        self._items = self.cargar()

    def cargar(self):
        """
        Lee el inventario desde el archivo JSON.

        Returns:
            dict: Diccionario de ítems, o {} si el archivo no existe o está corrupto.
        """
        try:
            with open(self.ruta_json, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                # Validar que sea un diccionario plano
                if isinstance(datos, dict):
                    return datos
                return {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def guardar(self):
        """
        Persiste el inventario actual en el archivo JSON.

        Returns:
            bool: True si la escritura fue exitosa, False en caso de error.
        """
        try:
            os.makedirs(os.path.dirname(self.ruta_json), exist_ok=True)
            with open(self.ruta_json, 'w', encoding='utf-8') as f:
                json.dump(self._items, f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False

    def agregar_item(self, nombre, cantidad=1):
        """
        Añade un ítem al inventario. Si ya existe, incrementa la cantidad.

        Operación O(1) amortizado gracias a la tabla hash interna.

        Args:
            nombre: Nombre del ítem a agregar.
            cantidad: Cantidad a sumar (default=1).

        Returns:
            int: Nueva cantidad total del ítem en el inventario.
        """
        if not nombre or cantidad < 1:
            return self._items.get(nombre, 0)

        self._items[nombre] = self._items.get(nombre, 0) + cantidad
        # Persistir automáticamente después de cada cambio
        self.guardar()
        return self._items[nombre]

    def obtener_cantidad(self, nombre):
        """
        Consulta la cantidad de un ítem específico. O(1) lookup.

        Args:
            nombre: Nombre del ítem a consultar.

        Returns:
            int: Cantidad del ítem, o 0 si no existe.
        """
        return self._items.get(nombre, 0)

    def obtener_inventario_completo(self):
        """
        Devuelve una copia del inventario completo.

        Returns:
            dict: Copia del diccionario {nombre_item: cantidad}.
        """
        return dict(self._items)

    def obtener_items_ordenados(self):
        """
        Devuelve el inventario como lista de tuplas ordenadas por cantidad descendente.
        Útil para renderizar en la UI con los ítems más abundantes primero.

        Returns:
            list[tuple[str, int]]: Lista de (nombre, cantidad) ordenada desc.
        """
        return sorted(self._items.items(), key=lambda x: x[1], reverse=True)

    def total_items(self):
        """
        Calcula la cantidad total de ítems acumulados (suma de todas las cantidades).

        Returns:
            int: Total de ítems en el inventario.
        """
        return sum(self._items.values())

    def total_tipos(self):
        """
        Cantidad de tipos de ítems distintos en el inventario.

        Returns:
            int: Número de claves únicas en la tabla hash.
        """
        return len(self._items)
