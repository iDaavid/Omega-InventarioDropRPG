"""
servidor.py — Servidor RPG simulado con estructuras de datos académicas.

Implementa dos estructuras fundamentales:
1. Cola FIFO (collections.deque): Registro circular de las últimas N simulaciones.
2. Árbol Binario de Búsqueda (ABB): Ordenación jerárquica por horas de farmeo
   para clasificar rachas de suerte/mala suerte.

Referencia académica: Luis Joyanes Aguilar — Estructuras de Datos en Java/C++.
"""

from collections import deque
from datetime import datetime
from typing import Optional, List, Dict, Any, Deque



# ESTRUCTURA 1: ÁRBOL BINARIO DE BÚSQUEDA (ABB)
# Ordena simulaciones por horas de farmeo.
# Rama izquierda = buena suerte (menos horas).
# Rama derecha   = mala suerte (más horas).


class NodoCaceria:
    """Nodo individual del ABB. Almacena el resultado completo de una simulación."""

    def __init__(self, item: str, boss: str, intentos: int, horas: float, timestamp: str):
        self.item: str = item
        self.boss: str = boss
        self.intentos: int = intentos
        # Clave de ordenación del ABB: horas de farmeo invertidas
        self.horas: float = horas
        self.timestamp: str = timestamp
        self.izquierda: Optional['NodoCaceria'] = None
        self.derecha: Optional['NodoCaceria'] = None


class ArbolHistorial:
    """
    Árbol Binario de Búsqueda (ABB), este clasifica simulaciones por horas.

    Complejidad promedio: O(log n) para inserción y búsqueda.
    Peor caso (árbol degenerado): O(n) — aceptable por el volumen de datos
    del proyecto/programa.
    """

    def __init__(self):
        self.raiz: Optional[NodoCaceria] = None
        self._tamano: int = 0

    @property
    def tamano(self) -> int:
        """Cantidad total de nodos en el árbol."""
        return self._tamano

    def insertar(self, item: str, boss: str, intentos: int, horas: float, timestamp: Optional[str] = None) -> None:
        """
        Inserta un nuevo resultado de simulación en el ABB.

        Args:
            item: Nombre del ítem obtenido.
            boss: Nombre del jefe derrotado.
            intentos: Cantidad de kills hasta obtener el drop.
            horas: Horas de farmeo invertidas (clave de ordenación).
            timestamp: Marca temporal. Si es None, usa datetime.now().
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.raiz is None:
            self.raiz = NodoCaceria(item, boss, intentos, horas, timestamp)
        else:
            self._insertar_recursivo(self.raiz, item, boss, intentos, horas, timestamp)
        self._tamano += 1

    def _insertar_recursivo(self, nodo_actual: NodoCaceria, item: str, boss: str, intentos: int, horas: float, timestamp: str) -> None:
        """Aquí se recorre el árbol recursivamente para encontrar la posición correcta."""
        if horas < nodo_actual.horas:
            if nodo_actual.izquierda is None:
                nodo_actual.izquierda = NodoCaceria(item, boss, intentos, horas, timestamp)
            else:
                self._insertar_recursivo(nodo_actual.izquierda, item, boss, intentos, horas, timestamp)
        else:
            if nodo_actual.derecha is None:
                nodo_actual.derecha = NodoCaceria(item, boss, intentos, horas, timestamp)
            else:
                self._insertar_recursivo(nodo_actual.derecha, item, boss, intentos, horas, timestamp)

    def obtener_en_orden(self) -> List[Dict[str, Any]]:
        """
        Recorrido In-Orden (Izquierda → Raíz → Derecha).
        Devuelve todas las simulaciones ordenadas de menor a mayor horas.

        Returns:
            list[dict]: Lista de resultados ordenados por horas ascendente.
        """
        resultado: List[Dict[str, Any]] = []
        self._in_orden_recursivo(self.raiz, resultado)
        return resultado

    def _in_orden_recursivo(self, nodo_actual: Optional[NodoCaceria], lista: List[Dict[str, Any]]) -> None:
        """Recorrido recursivo in-orden del subárbol."""
        if nodo_actual is not None:
            self._in_orden_recursivo(nodo_actual.izquierda, lista)
            lista.append({
                "item": nodo_actual.item,
                "boss": nodo_actual.boss,
                "intentos": nodo_actual.intentos,
                "horas": nodo_actual.horas,
                "timestamp": nodo_actual.timestamp
            })
            self._in_orden_recursivo(nodo_actual.derecha, lista)

    def obtener_minimo(self) -> Optional[Dict[str, Any]]:
        """
        Encuentra la mejor racha (menos horas de farmeo).
        Navega siempre a la izquierda hasta llegar a una hoja.

        Returns:
            dict | None: Nodo con menor cantidad de horas, o None si el árbol está vacío.
        """
        if self.raiz is None:
            return None
        nodo = self.raiz
        while nodo.izquierda is not None:
            nodo = nodo.izquierda
        return {
            "item": nodo.item, "boss": nodo.boss,
            "intentos": nodo.intentos, "horas": nodo.horas,
            "timestamp": nodo.timestamp
        }

    def obtener_maximo(self) -> Optional[Dict[str, Any]]:
        """
        Encuentra la peor racha (más horas de farmeo).
        Navega siempre a la derecha hasta llegar a una hoja.

        Returns:
            dict | None: Nodo con mayor cantidad de horas, o None si el árbol está vacío.
        """
        if self.raiz is None:
            return None
        nodo = self.raiz
        while nodo.derecha is not None:
            nodo = nodo.derecha
        return {
            "item": nodo.item, "boss": nodo.boss,
            "intentos": nodo.intentos, "horas": nodo.horas,
            "timestamp": nodo.timestamp
        }

    def buscar_por_rango(self, horas_min: float, horas_max: float) -> List[Dict[str, Any]]:
        """
        Búsqueda por rango en el ABB. Este devuelve simulaciones donde
        horas_min <= horas <= horas_max.

        Aprovecha la propiedad BST para podar ramas irrelevantes,
        logrando complejidad promedio O(log n + k) donde k = resultados.

        Args:
            horas_min: Límite inferior del rango.
            horas_max: Límite superior del rango.

        Returns:
            list[dict]: Simulaciones dentro del rango, ordenadas.
        """
        resultado: List[Dict[str, Any]] = []
        self._buscar_rango_recursivo(self.raiz, horas_min, horas_max, resultado)
        return resultado

    def _buscar_rango_recursivo(self, nodo: Optional[NodoCaceria], h_min: float, h_max: float, lista: List[Dict[str, Any]]) -> None:
        """Poda ramas que no pueden contener valores en el rango."""
        if nodo is None:
            return
        # Solo se explora la izquierda si el nodo actual podría tener hijos menores dentro del rango
        if nodo.horas > h_min:
            self._buscar_rango_recursivo(nodo.izquierda, h_min, h_max, lista)
        # Incluir nodo actual si está dentro del rango
        if h_min <= nodo.horas <= h_max:
            lista.append({
                "item": nodo.item, "boss": nodo.boss,
                "intentos": nodo.intentos, "horas": nodo.horas,
                "timestamp": nodo.timestamp
            })
        # Solo se explora derecha si el nodo actual podría tener hijos mayores dentro del rango
        if nodo.horas < h_max:
            self._buscar_rango_recursivo(nodo.derecha, h_min, h_max, lista)



# ESTRUCTURA 2: COLA FIFO + ORQUESTADOR
# Cola circular (deque) para las últimas N simulaciones.


class ServidorRPG:
    """
    Servidor simulado que arma las estructuras de datos del proyecto.

    Combina:
    - Cola FIFO (deque con maxlen) para historial reciente.
    - Árbol Binario de Búsqueda para ranking por suerte.

    El servidor no persiste datos entre sesiones intencionalmente,
    ya que, su propósito es demostrar las estructuras en memoria.
    """

    MAX_HISTORIAL: int = 10

    def __init__(self):
        # Cola FIFO: al alcanzar MAX_HISTORIAL, descarta automáticamente el más antiguo
        self.cola_eventos: Deque[Dict[str, Any]] = deque(maxlen=self.MAX_HISTORIAL)
        # ABB para clasificación por horas de farmeo
        self.historial: ArbolHistorial = ArbolHistorial()

    def registrar_simulacion(self, resultado: Dict[str, Any]) -> Dict[str, int]:
        """
        Punto de entrada principal. Recibe el resultado de una simulación
        y lo distribuye a ambas estructuras de datos.

        Args:
            resultado: dict con claves 'item', 'monstruo', 'simulacion.intentos',
                       'simulacion.tiempo_total_horas'.

        Returns:
            dict: Resumen del registro con posición en cola y tamaño del ABB.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        item = resultado.get("item", "Desconocido")
        boss = resultado.get("monstruo", "Desconocido")
        intentos = resultado.get("simulacion", {}).get("intentos", 0)
        horas = resultado.get("simulacion", {}).get("tiempo_total_horas", 0.0)

        # Registro estructurado para la cola FIFO
        registro = {
            "item": str(item),
            "boss": str(boss),
            "intentos": int(intentos),
            "horas": float(horas),
            "timestamp": timestamp
        }

        # Encolar en la FIFO (si está llena, deque descarta el más antiguo)
        self.cola_eventos.append(registro)

        # Insertar en el ABB ordenado por horas
        self.historial.insertar(registro["item"], registro["boss"], registro["intentos"], registro["horas"], timestamp)

        return {
            "posicion_cola": len(self.cola_eventos),
            "total_en_arbol": self.historial.tamano
        }

    def obtener_historial_reciente(self) -> List[Dict[str, Any]]:
        """
        Devuelve las últimas N simulaciones en orden FIFO (más antigua primero).

        Returns:
            list[dict]: Lista de hasta MAX_HISTORIAL registros.
        """
        return list(self.cola_eventos)

    def obtener_ranking_suerte(self) -> List[Dict[str, Any]]:
        """
        Devuelve todas las simulaciones ordenadas por horas (recorrido in-orden del ABB).
        Las primeras entradas son las de mejor suerte (menos horas).

        Returns:
            list[dict]: Simulaciones ordenadas ascendentemente por horas.
        """
        return self.historial.obtener_en_orden()

    def obtener_mejor_racha(self) -> Optional[Dict[str, Any]]:
        """
        Devuelve la simulación con menor cantidad de horas de farmeo.
        Operación O(log n) promedio — recorre la rama izquierda del ABB.

        Returns:
            dict | None: Mejor racha o None si no hay datos.
        """
        return self.historial.obtener_minimo()

    def obtener_peor_racha(self) -> Optional[Dict[str, Any]]:
        """
        Devuelve la simulación con mayor cantidad de horas de farmeo.
        Operación O(log n) promedio — recorre la rama derecha del ABB.

        Returns:
            dict | None: Peor racha o None si no hay datos.
        """
        return self.historial.obtener_maximo()

    def obtener_simulaciones_por_rango(self, horas_min: float, horas_max: float) -> List[Dict[str, Any]]:
        """
        Filtra simulaciones por rango de horas usando búsqueda BST.

        Args:
            horas_min: Límite inferior de horas.
            horas_max: Límite superior de horas.

        Returns:
            list[dict]: Simulaciones dentro del rango.
        """
        return self.historial.buscar_por_rango(horas_min, horas_max)