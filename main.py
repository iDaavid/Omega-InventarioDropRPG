import streamlit as st

# Configuración de página minimalista
st.set_page_config(page_title="Gestor RPG", page_icon="⚔️")

# Inicialización del estado
if 'nombre' not in st.session_state:
    st.session_state.nombre = ""
    st.session_state.stats = {
        "Ataque": 0, "Fuerza": 0, "Defensa": 0, 
        "Puntos de Vida": 0, "Alcance": 0, "Magia": 0
    }
    st.session_state.botin = "Ninguno"

def modificar_stat(stat, delta):
    st.session_state.stats[stat] += delta
    st.rerun()

# --- Menú lateral ---
st.sidebar.title("Menú")
menu = st.sidebar.radio("Navegación", ["Registro", "Selección de Botín", "Resumen"])

# --- Interfaz Principal ---
if menu == "Registro":
    # El título solo aparece aquí
    st.title("⚔️ Registro de Personaje")
    st.header("Ajustar Atributos")
    st.session_state.nombre = st.text_input("Nombre del personaje", st.session_state.nombre)
    
    st.write("### Estadísticas")
    lista_stats = ["Ataque", "Fuerza", "Defensa", "Puntos de Vida", "Alcance", "Magia"]
    
    for stat in lista_stats:
        cols = st.columns([2, 1, 1])
        cols[0].write(f"**{stat}**: {st.session_state.stats[stat]}")
        
        if cols[1].button("-", key=f"btn_min_{stat}"):
            modificar_stat(stat, -1)
        if cols[2].button("+", key=f"btn_plus_{stat}"):
            modificar_stat(stat, 1)

elif menu == "Selección de Botín":
    st.header("Elección del Botín")
    items = [
        "Semilla de Limpwurt", "Semilla de fresas", "Semilla de Marrentill",
        "Baya de jangerberry", "Semilla de tarromin", "Semilla de sangre salvaje",
        "Semilla de sandía", "Semilla de Harralander", "Semilla de Ranarr",
        "Semilla de baya blanca", "Esporas de hongos", "Semilla de linaria",
        "Semilla de iriti", "Semilla de belladona", "Semilla de hiedra venenosa",
        "Semilla de cactus", "Semilla de Avantoe", "Semilla de Kwuarm",
        "Semilla de boca de dragón", "Semilla de cacantina", "Semilla de Lantadyme",
        "Semilla de maleza enana", "Semilla de torstol"
    ]
    st.session_state.botin = st.selectbox("Selecciona tu objetivo:", items, index=items.index(st.session_state.botin) if st.session_state.botin in items else 0)

else:
    st.header("Resumen del Personaje")
    if st.session_state.nombre:
        st.write(f"**Nombre:** {st.session_state.nombre}")
        st.write("**Estadísticas Finales:**")
        st.table(st.session_state.stats)
        st.info(f"**Botín objetivo:** {st.session_state.botin}")
    else:
        st.warning("Por favor, completa el registro primero en la pestaña 'Registro'.")