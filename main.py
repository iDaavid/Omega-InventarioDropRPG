import customtkinter as ctk
from modulos import rng_drops

# --- PARTE 1: CONFIGURACIÓN BASE DEL ENTORNO ---
# Configuramos un tema oscuro con acentos azules, ideal para interfaces de juegos
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Creamos la clase principal que hereda de la ventana de CustomTkinter
class GestorRPG(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuramos la ventana
        self.title("Gestor RPG - Simulador Predictivo")
        self.geometry("800x600")
        self.minsize(600, 500)
        
        # --- PARTE 2: MEMORIA DEL SISTEMA (ESTADO LOCAL) ---
        # En una app de escritorio, las variables viven todo el tiempo en la memoria RAM
        self.stats = {
            "Ataque": 1, 
            "Fuerza": 1, 
            "Defensa": 1, 
            "Puntos de Vida": 10, 
            "Alcance": 1, 
            "Magia": 1
        }
        
        # Variables especiales de Tkinter para capturar texto de la interfaz
        self.nombre_personaje = ctk.StringVar(value="")
        self.botin_objetivo = ctk.StringVar(value="Ninguno")
        
        # Conectamos el motor matemático (Integrante 2)
        # Nota: Recuerda que necesitas tu archivo jefes.json creado para que no falle
        self.motor_rng = rng_drops.RNGDrops("datos/jefes.json")
        
        # Ejecutamos la construcción visual
        self.construir_interfaz()

    def construir_interfaz(self):
        # 1. Configurar la cuadrícula principal (Grid)
        self.grid_columnconfigure(0, weight=1) # Columna izquierda
        self.grid_columnconfigure(1, weight=2) # Columna derecha (más ancha)
        self.grid_rowconfigure(0, weight=1)

        # --- FRAME IZQUIERDO: ESTADÍSTICAS ---
        self.frame_stats = ctk.CTkFrame(self)
        self.frame_stats.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(self.frame_stats, text="🛡️ Atributos", font=("Helvetica", 18, "bold")).pack(pady=15)

        # Generamos las cajas de texto (Entries) para cada stat automáticamente
        self.entradas_stats = {}
        for stat in self.stats.keys():
            frame_fila = ctk.CTkFrame(self.frame_stats, fg_color="transparent")
            frame_fila.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(frame_fila, text=stat, width=100, anchor="w").pack(side="left")
            
            entrada = ctk.CTkEntry(frame_fila, width=60, justify="center")
            entrada.insert(0, str(self.stats[stat])) # Ponemos el valor por defecto
            entrada.pack(side="right")
            self.entradas_stats[stat] = entrada

        # --- FRAME DERECHO: SIMULADOR Y RESULTADOS ---
        self.frame_sim = ctk.CTkFrame(self)
        self.frame_sim.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        ctk.CTkLabel(self.frame_sim, text="🎯 Objetivo de Cacería", font=("Helvetica", 18, "bold")).pack(pady=15)
        
        # Selector de Botín (Drop Menu)
        items = ["Semilla de Limpwurt", "Semilla de Ranarr", "Semilla de torstol"] # Lista acortada para la prueba
        self.combo_botin = ctk.CTkOptionMenu(
            self.frame_sim, 
            values=items, 
            variable=self.botin_objetivo,
            font=("Helvetica", 14)
        )
        self.combo_botin.pack(pady=10)

        # El Gatillo (Botón)
        self.btn_simular = ctk.CTkButton(
            self.frame_sim, 
            text="¡Simular Cacería!", 
            font=("Helvetica", 14, "bold"),
            fg_color="#8B0000", # Rojo oscuro sangre
            hover_color="#600000",
            command=self.ejecutar_simulacion
        )
        self.btn_simular.pack(pady=20)
        
        # Consola de Salida de Resultados
        self.caja_resultados = ctk.CTkTextbox(
            self.frame_sim, 
            width=400, 
            height=300, 
            font=("Consolas", 14),
            text_color="#00FF00" # Verde terminal
        )
        self.caja_resultados.pack(pady=10, padx=20, fill="both", expand=True)
        self.caja_resultados.insert("0.0", "> Sistema listo...\n> Esperando parámetros para calcular el farmeo...\n")
    def ejecutar_simulacion(self):
        # 1. Recopilar los stats actuales de las cajas de texto
        stats_actuales = {}
        for stat, entry in self.entradas_stats.items():
            try:
                stats_actuales[stat] = int(entry.get())
            except ValueError:
                # Si el usuario escribe letras por error, asumimos un 1
                stats_actuales[stat] = 1 

        # 2. Leer el ítem seleccionado del menú
        item_deseado = self.botin_objetivo.get()

        # 3. Limpiar la consola verde antes de escribir
        self.caja_resultados.delete("0.0", "end")
        self.caja_resultados.insert("0.0", f"> Calculando esperanza matemática para: {item_deseado}...\n\n")

        # 4. Ejecutar el motor del Integrante 2
        # Asumimos que el JSON tiene la zona "bosque_oscuro" y al "dragon_anciano"
        resultado = self.motor_rng.calcular_caceria_completa(
            id_zona="bosque_oscuro",
            id_monstruo="dragon_anciano",
            nombre_item=item_deseado,
            stats_jugador=stats_actuales
        )

        # 5. Imprimir los resultados en nuestra consola de forma estilizada
        if "error" in resultado:
            self.caja_resultados.insert("end", f"[ERROR FATAL] {resultado['error']}\n")
        else:
            self.caja_resultados.insert("end", f"⚔️ Jefe Objetivo: {resultado['monstruo']}\n")
            self.caja_resultados.insert("end", f"⏱️ Tiempo por Kill (DPS): {resultado['tiempo_por_caza_seg']} seg\n")
            self.caja_resultados.insert("end", "-"*40 + "\n")
            self.caja_resultados.insert("end", f"📊 ESTADÍSTICA TEÓRICA (90% Certeza):\n")
            self.caja_resultados.insert("end", f"   - Kills necesarios: {resultado['teorico_sin_pity']['intentos_90']}\n")
            self.caja_resultados.insert("end", f"   - Horas de farmeo:  {resultado['teorico_sin_pity']['tiempo_total_horas']} hrs\n")
            self.caja_resultados.insert("end", "-"*40 + "\n")
            self.caja_resultados.insert("end", f"🎲 SIMULACIÓN APLICANDO SISTEMA PITY:\n")
            self.caja_resultados.insert("end", f"   - Kills simulados:  {resultado['simulacion']['intentos']}\n")
            self.caja_resultados.insert("end", f"   - Horas de farmeo:  {resultado['simulacion']['tiempo_total_horas']} hrs\n")
            self.caja_resultados.insert("end", f"   - RNG Final Alcanzado: {resultado['simulacion']['prob_final_alcanzada']}%\n")
# --- PUNTO DE ENTRADA ---
if __name__ == "__main__":
    app = GestorRPG()
    app.mainloop() # Este es el bucle infinito que mantiene la ventana abierta