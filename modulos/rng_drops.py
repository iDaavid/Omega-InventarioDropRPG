import json
import random
import math

class RNGDrops:
    def __init__(self, ruta_json):
        self.ruta_json = ruta_json
        self.datos_mundo = self.cargar_datos()

    def cargar_datos(self):
        try:
            with open(self.ruta_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[Error] No se pudo cargar el archivo JSON: {e}")
            return {"zonas": {}}

    def guardar_datos(self):
        try:
            with open(self.ruta_json, 'w', encoding='utf-8') as f:
                json.dump(self.datos_mundo, f, indent=4, ensure_ascii=False)
            print("[Motor] Archivo JSON actualizado correctamente.")
            return True
        except Exception as e:
            print(f"[Error Crítico] No se pudo guardar el archivo: {e}")
            return False

    def obtener_zonas(self):
        return self.datos_mundo.get("zonas", {})

    def obtener_monstruo(self, id_zona, id_monstruo):
        zonas = self.obtener_zonas()
        zona = zonas.get(id_zona, {})
        monstruos = zona.get("monstruos", {})
        return monstruos.get(id_monstruo)

    def simular_hasta_drop(self, prob_base, usar_pity=False, pity_inc=0.0):
        intentos = 0
        prob_actual = prob_base
        
        # Bucle infinito hasta que caiga el drop
        while True:
            intentos += 1
            
            # Tirada de dados
            if random.random() < prob_actual:
                return intentos, min(prob_actual, 1.0)
            
            # Si el pity está activado, aumentamos la probabilidad de forma compasiva
            if usar_pity:
                prob_actual += pity_inc

    def intentos_para_probabilidad(self, prob_base, objetivo=0.90):
        if prob_base <= 0 or prob_base >= 1:
            return 1
        try:
            n = math.log(1 - objetivo) / math.log(1 - prob_base)
            return max(1, math.ceil(n))
        except ZeroDivisionError:
            return 1

    def calcular_tiempo_combate(self, stats_jugador, stats_monstruo):
        # --- NUEVO SISTEMA OSRS PURO ---
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

    def calcular_caceria_completa(self, id_zona, id_monstruo, nombre_item, stats_jugador, usar_pity=False):
        monstruo = self.obtener_monstruo(id_zona, id_monstruo)
        if not monstruo:
            return {"error": "El monstruo no existe."}
            
        loot_pool = monstruo.get("loot", {})
        item_data = loot_pool.get(nombre_item)
        if not item_data:
            return {"error": "El ítem seleccionado no pertenece al botín."}

        # --- LECTURA DE PROBABILIDAD 1/X ---
        # Asumimos que el JSON ahora guardará un entero llamado "probabilidad_x" (Ej: 50)
        denominador_x = item_data.get("probabilidad_x", 1)
        prob_base = 1.0 / denominador_x if denominador_x > 0 else 0
        
        # Configuración del incremento del pity (si existe en el JSON)
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
            "prob_formato": f"1/{denominador_x}",
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