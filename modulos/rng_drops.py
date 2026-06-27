import json
import random
import math

class RNGDrops:
    def init(self, ruta_json):
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
       
        # Extraer estadísticas del jugador 
        ataque = max(1, stats_jugador.get("Ataque", 0))
        fuerza = max(1, stats_jugador.get("Fuerza", 0))
        
        # Extraer estadísticas del monstruo
        vida_monstruo = max(1, stats_monstruo.get("vida", 100))
        defensa_monstruo = max(0, stats_monstruo.get("defensa", 0))

        # Fórmula de Daño Base
        # Garantiza un mínimo de 1 de daño por golpe para evitar bucles infinitos
        daño_por_segundo = max(1, (ataque + fuerza) - defensa_monstruo)

        # Tiempo en segundos que toma derrotar al monstruo una vez
        tiempo_por_caza_segundos = vida_monstruo / daño_por_segundo
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