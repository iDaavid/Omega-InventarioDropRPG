import json
import random
import math

class RNGDrops:
    def __init__(self, ruta_json):
        self.ruta_json = ruta_json
        self.datos_mundo = self.cargar_datos()

    def cargar_datos(self):
        #Carga el archivo JSON 
        try:
            with open(self.ruta_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[Error] No se pudo cargar el archivo JSON: {e}")
            return {"zonas": {}}

    def obtener_zonas(self):
        #Devuelve el diccionario completo de zonas para el mapa 
        return self.datos_mundo.get("zonas", {})

    def obtener_monstruo(self, id_zona, id_monstruo):
        #Busca un monstruo específico dentro de una zona
        zonas = self.obtener_zonas()
        zona = zonas.get(id_zona, {})
        monstruos = zona.get("monstruos", {})
        return monstruos.get(id_monstruo)

    def simular_hasta_drop(self, prob_base, incremento, max_intentos):
        #Simula una racha de cacerías independientes hasta obtener el ítem o alcanzar el Hard Pity (Garantizado)
    
        intentos = 0
        prob_actual = prob_base

        while intentos < max_intentos:
            intentos += 1
            
            if random.random() < prob_actual:
                return intentos, min(prob_actual, 1.0)
            
            prob_actual += incremento

        return max_intentos, 1.0

    def intentos_para_probabilidad(self, prob_base, objetivo=0.90):
       
        if prob_base <= 0 or prob_base >= 1:
            return 1
        try:
            n = math.log(1 - objetivo) / math.log(1 - prob_base)
            return max(1, math.ceil(n))
        except ZeroDivisionError:
            return 1

    def calcular_tiempo_combate(self, stats_jugador, stats_monstruo):
        import math

        # 1. Leer estadísticas del jugador (Mínimo nivel 1)
        ataque = max(1, stats_jugador.get("Ataque", 1))
        fuerza = max(1, stats_jugador.get("Fuerza", 1))
        rango = max(1, stats_jugador.get("Alcance", 1))
        magia = max(1, stats_jugador.get("Magia", 1))

        # 2. Leer estadísticas del monstruo
        vida_monstruo = max(1, stats_monstruo.get("vida", 100))
        defensa_monstruo = max(1, stats_monstruo.get("defensa", 1))

        # 3. Detectar el estilo de combate automáticamente (el stat más alto)
        max_stat = max(ataque, rango, magia)
        
        if max_stat == rango:
            # Estilo Ranged
            nivel_precision = rango
            nivel_fuerza = rango
        elif max_stat == magia:
            # Estilo Magia
            nivel_precision = magia
            nivel_fuerza = magia
        else:
            # Estilo Melee por defecto
            nivel_precision = ataque
            nivel_fuerza = fuerza

        # 4. Cálculo de Max Hit (Sin equipo ni prayers)
        fuerza_efectiva = nivel_fuerza + 8
        max_hit = math.floor(0.5 + fuerza_efectiva)

        # 5. Cálculo de Attack Roll (Jugador) y Defence Roll (Monstruo)
        ataque_efectivo = nivel_precision + 8
        attack_roll = ataque_efectivo * 64
        
        defensa_efectiva = defensa_monstruo + 8
        defence_roll = defensa_efectiva * 64

        # 6. Cálculo de Hit Chance (Probabilidad de conectar el golpe)
        if attack_roll > defence_roll:
            hit_chance = 1 - ((defence_roll + 2) / (2 * (attack_roll + 1)))
        else:
            hit_chance = attack_roll / (2 * (defence_roll + 1))

        # 7. Cálculo de Daño Por Segundo (DPS)
        # En OSRS, un golpe exitoso hace un daño aleatorio entre 0 y el Max Hit.
        # Por lo tanto, el daño promedio por ataque es (Max Hit / 2) multiplicado por la probabilidad de acertar.
        dano_promedio_por_ataque = hit_chance * (max_hit / 2)

        # Asumimos una velocidad estándar de arma de OSRS (4 ticks = 2.4 segundos)
        velocidad_arma_segundos = 2.4
        
        dps_real = dano_promedio_por_ataque / velocidad_arma_segundos
        
        # Evitar DPS de cero absoluto para que el simulador no arroje errores de división
        dps_real = max(0.01, dps_real)

        # 8. Retornar el tiempo total de cacería en segundos
        tiempo_por_caza_segundos = vida_monstruo / dps_real
        return tiempo_por_caza_segundos

    def calcular_caceria_completa(self, id_zona, id_monstruo, nombre_item, stats_jugador):
     
        monstruo = self.obtener_monstruo(id_zona, id_monstruo)
        if not monstruo:
            return {"error": "El monstruo seleccionado no existe en esta zona."}

        loot_pool = monstruo.get("loot", {})
        item_data = loot_pool.get(nombre_item)
        if not item_data:
            return {"error": "El ítem seleccionado no pertenece al botín de este monstruo."}

        prob_base = item_data["probabilidad"]
        pity = item_data["pity"]
       # Simulación matemática del Drop con Pity
        intentos_simulados, prob_final = self.simular_hasta_drop(
            prob_base,
            pity["probabilidad_incremento"],
            pity["max_intentos"]
        )

        # Intentos teóricos según la varianza matemática (Certeza del 90%)
        intentos_teoricos = self.intentos_para_probabilidad(prob_base, objetivo=0.90)

        # Cálculo del tiempo de combate según Atributos de ambos
        tiempo_una_caza = self.calcular_tiempo_combate(stats_jugador, monstruo)

        # Estimación de tiempos totales (en minutos y horas)
        tiempo_total_segundos_simulado = intentos_simulados * tiempo_una_caza
        tiempo_total_segundos_teorico = intentos_teoricos * tiempo_una_caza

        return {
            "monstruo": monstruo["nombre"],
            "item": item_data["item"],
            "prob_base": prob_base,
            "pity_config": pity,
            "simulacion": {
                "intentos": intentos_simulados,
                "prob_final_alcanzada": round(prob_final * 100, 2),
                "tiempo_total_minutos": round(tiempo_total_segundos_simulado / 60, 2),
                "tiempo_total_horas": round(tiempo_total_segundos_simulado / 3600, 2)
            },
            "teorico_sin_pity": {
                "intentos_90": intentos_teoricos,
                "tiempo_total_minutos": round(tiempo_total_segundos_teorico / 60, 2),
                "tiempo_total_horas": round(tiempo_total_segundos_teorico / 3600, 2)
            },
            "tiempo_por_caza_seg": round(tiempo_una_caza, 2)
        }