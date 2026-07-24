"""
rng_drops.py — Motor de simulación RNG con sistema de probabilidades OSRS.

Soporta dos formatos de probabilidad:
- Formato simple: probabilidad_x (entero) → probabilidad = 1/X
- Formato fraccionario: probabilidad_num/probabilidad_den → probabilidad = num/den

Incluye sistema Pity (incremento progresivo de probabilidad por intento fallido).

Referencia académica: Luis Joyanes Aguilar — Algoritmos probabilísticos.
"""

import json
import random
import math
from typing import Optional


class RNGDrops:
    """Motor de simulación de drops con cálculo de combate estilo OSRS."""

    def __init__(self, ruta_json: str):
        """
        Inicializa el motor cargando los datos del mundo desde JSON.

        Args:
            ruta_json: Ruta al archivo de datos de bosses y zonas.
        """
        self.ruta_json = ruta_json
        self.datos_mundo = self.cargar_datos()

    def cargar_datos(self) -> dict:
        """
        Lee el archivo JSON de datos del mundo.

        Returns:
            dict: Datos del mundo con zonas, monstruos y loot.
        """
        try:
            with open(self.ruta_json, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                # Validar estructura mínima
                if not isinstance(datos, dict):
                    return {"zonas": {}}
                if "zonas" not in datos:
                    datos["zonas"] = {}
                return datos
        except FileNotFoundError:
            return {"zonas": {}}
        except json.JSONDecodeError as e:
            print(f"[Error] JSON corrupto, creando datos vacíos: {e}")
            return {"zonas": {}}

    def guardar_datos(self) -> bool:
        """
        Persiste los datos del mundo en el archivo JSON.

        Returns:
            bool: True si la escritura fue exitosa.
        """
        try:
            with open(self.ruta_json, 'w', encoding='utf-8') as f:
                json.dump(self.datos_mundo, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[Error Crítico] No se pudo guardar el archivo: {e}")
            return False

    def obtener_zonas(self) -> dict:
        """Retorna el diccionario de zonas del mundo."""
        return self.datos_mundo.get("zonas", {})

    def obtener_monstruo(self, id_zona: str, id_monstruo: str) -> Optional[dict]:
        """
        Busca un monstruo por zona e ID.

        Args:
            id_zona: Clave de la zona en el JSON.
            id_monstruo: Clave del monstruo dentro de la zona.

        Returns:
            dict | None: Datos del monstruo, o None si no existe.
        """
        zonas = self.obtener_zonas()
        zona = zonas.get(id_zona, {})
        monstruos = zona.get("monstruos", {})
        return monstruos.get(id_monstruo)

    @staticmethod
    def obtener_probabilidad(item_data: dict) -> float:
        """
        Calcula la probabilidad de un drop soportando ambos formatos.

        Formato fraccionario (prioridad): probabilidad_num / probabilidad_den
        Formato simple (fallback): 1 / probabilidad_x

        Args:
            item_data: Dict con los datos del ítem incluyendo probabilidad.

        Returns:
            float: Probabilidad como valor entre 0 y 1.
        """
        # Formato fraccionario tiene prioridad
        num = item_data.get("probabilidad_num")
        den = item_data.get("probabilidad_den")

        if num is not None and den is not None and den > 0:
            return num / den

        # Fallback al formato simple 1/X
        prob_x = item_data.get("probabilidad_x", 1)
        if prob_x > 0:
            return 1.0 / prob_x

        return 0.0

    @staticmethod
    def formato_probabilidad(item_data: dict) -> str:
        """
        Genera una representación legible de la probabilidad.

        Returns:
            str: Ej: '1/340' o '41/159'.
        """
        num = item_data.get("probabilidad_num")
        den = item_data.get("probabilidad_den")

        if num is not None and den is not None and den > 0:
            return f"{num}/{den}"

        prob_x = item_data.get("probabilidad_x", 1)
        return f"1/{prob_x}"

    def simular_hasta_drop(self, prob_base: float, usar_pity: bool = False,
                           pity_inc: float = 0.0) -> tuple:
        """
        Simula tiradas hasta obtener un drop.

        Args:
            prob_base: Probabilidad base del drop (0-1).
            usar_pity: Si True, incrementa la probabilidad con cada intento fallido.
            pity_inc: Incremento de probabilidad por intento fallido.

        Returns:
            tuple[int, float]: (intentos_necesarios, probabilidad_final_alcanzada).
        """
        if prob_base <= 0:
            return (1, 0.0)

        intentos = 0
        prob_actual = prob_base

        while True:
            intentos += 1

            # Tirada de dados
            if random.random() < prob_actual:
                return intentos, min(prob_actual, 1.0)

            # Si el pity está activado, aumentamos la probabilidad de forma compasiva
            if usar_pity:
                prob_actual += pity_inc

    def intentos_para_probabilidad(self, prob_base: float, objetivo: float = 0.90) -> int:
        """
        Calcula cuántos intentos se necesitan para tener una probabilidad
        acumulada `objetivo` de haber obtenido el drop al menos una vez.

        Fórmula: n = log(1 - objetivo) / log(1 - prob_base)

        Args:
            prob_base: Probabilidad base por intento.
            objetivo: Probabilidad acumulada deseada (default 0.90 = 90%).

        Returns:
            int: Cantidad de intentos necesarios.
        """
        if prob_base <= 0 or prob_base >= 1:
            return 1
        try:
            n = math.log(1 - objetivo) / math.log(1 - prob_base)
            return max(1, math.ceil(n))
        except (ZeroDivisionError, ValueError):
            return 1

    def calcular_tiempo_combate(self, stats_jugador: dict, stats_monstruo: dict) -> float:
        """
        Calcula el tiempo promedio de una kill usando el sistema de combate OSRS.

        Args:
            stats_jugador: Dict con 'Ataque' y 'Fuerza'.
            stats_monstruo: Dict con 'vida' y 'defensa'.

        Returns:
            float: Segundos por kill.
        """
        ataque = max(1, stats_jugador.get("Ataque", 1))
        fuerza = max(1, stats_jugador.get("Fuerza", 1))

        vida_monstruo = max(1, stats_monstruo.get("vida", 100))
        defensa_monstruo = max(1, stats_monstruo.get("defensa", 1))

        # 1. Fuerza -> Determina el Max Hit
        fuerza_efectiva = fuerza + 8
        max_hit = math.floor(0.5 + fuerza_efectiva)

        # 2. Ataque -> Determina la precisión (Attack Roll)
        ataque_efectivo = ataque + 8
        attack_roll = ataque_efectivo * 64
        defence_roll = (defensa_monstruo + 8) * 64

        # 3. Probabilidad de Impacto (Hit Chance)
        if attack_roll > defence_roll:
            hit_chance = 1 - ((defence_roll + 2) / (2 * (attack_roll + 1)))
        else:
            hit_chance = attack_roll / (2 * (defence_roll + 1))

        # 4. DPS Real (Daño promedio entre ticks de 2.4s)
        dano_promedio_por_ataque = hit_chance * (max_hit / 2)
        velocidad_arma_segundos = 2.4

        dps_real = max(0.01, dano_promedio_por_ataque / velocidad_arma_segundos)

        tiempo_por_caza_segundos = vida_monstruo / dps_real
        return tiempo_por_caza_segundos

    def calcular_caceria_completa(self, id_zona: str, id_monstruo: str,
                                  nombre_item: str, stats_jugador: dict,
                                  usar_pity: bool = False) -> dict:
        """
        Ejecuta una simulación completa: teórica + simulada.

        Args:
            id_zona: ID de la zona.
            id_monstruo: ID del monstruo.
            nombre_item: Nombre del ítem objetivo.
            stats_jugador: Stats del jugador {'Ataque': int, 'Fuerza': int}.
            usar_pity: Si activar el sistema Pity.

        Returns:
            dict: Resultado completo con estadísticas teóricas y simuladas.
        """
        monstruo = self.obtener_monstruo(id_zona, id_monstruo)
        if not monstruo:
            return {"error": "El monstruo no existe."}

        loot_pool = monstruo.get("loot", {})
        item_data = loot_pool.get(nombre_item)
        if not item_data:
            return {"error": "El ítem seleccionado no pertenece al botín."}

        # Calcular probabilidad usando el nuevo sistema dual
        prob_base = self.obtener_probabilidad(item_data)
        prob_formato = self.formato_probabilidad(item_data)

        if prob_base <= 0:
            return {"error": "La probabilidad del ítem es inválida (≤ 0)."}

        # Configuración del incremento del pity
        pity_config = item_data.get("pity", {"probabilidad_incremento": 0.0})

        # Simular
        intentos_simulados, prob_final = self.simular_hasta_drop(
            prob_base=prob_base,
            usar_pity=usar_pity,
            pity_inc=pity_config.get("probabilidad_incremento", 0.0)
        )

        intentos_teoricos = self.intentos_para_probabilidad(prob_base, objetivo=0.90)
        tiempo_una_caza = self.calcular_tiempo_combate(stats_jugador, monstruo)

        tiempo_simulado_horas = (intentos_simulados * tiempo_una_caza) / 3600
        tiempo_teorico_horas = (intentos_teoricos * tiempo_una_caza) / 3600

        return {
            "monstruo": monstruo["nombre"],
            "item": item_data["item"],
            "prob_formato": prob_formato,
            "usando_pity": usar_pity,
            "simulacion": {
                "intentos": intentos_simulados,
                "prob_final_alcanzada": round(prob_final * 100, 4),
                "tiempo_total_horas": round(tiempo_simulado_horas, 2)
            },
            "teorico": {
                "intentos_90": intentos_teoricos,
                "tiempo_total_horas": round(tiempo_teorico_horas, 2)
            },
            "tiempo_por_caza_seg": round(tiempo_una_caza, 2)
        }