def calcular_drop_completo(self, id_jefe, nombre_item):
    jefe = self.obtener_jefe(id_jefe)
    if jefe is None:
        return {"error": "El jefe no existe en jefes.json"}

    item = self.obtener_probabilidad_item(jefe, nombre_item)
    if item is None:
        return {"error": "Ese ítem no está en el loot del jefe"}

    prob_base = item["probabilidad"]
    pity = item["pity"]

    intentos, prob_final = self.simular_hasta_drop(
        prob_base,
        pity["probabilidad_incremento"],
        pity["max_intentos"]
    )

    intentos_90 = self.intentos_para_probabilidad(prob_base, objetivo=0.90)

    return {
        "jefe": jefe["nombre"],
        "item": item["item"],
        "prob_base": prob_base,
        "pity": pity,
        "intentos": intentos,
        "prob_final": prob_final,
        "intentos_90": intentos_90
    }