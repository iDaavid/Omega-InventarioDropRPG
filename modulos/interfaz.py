"""
interfaz.py — Interfaz gráfica completa del simulador Omega RPG.

Contiene toda la lógica de construcción de UI (widgets, diálogos, layouts)
usando Flet. Se importa desde main.py como punto de entrada.

Patrón: Función principal `main(page)` que Flet invoca al arrancar.
"""

import math
import os
import random
import traceback
import flet as ft
from modulos import rng_drops
from modulos.servidor import ServidorRPG
from modulos.inventario import InventarioJugador

# Rutas centralizadas con rutas absolutas (evita problemas de CWD)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DATOS = os.path.join(BASE_DIR, "datos", "jefes.json")
RUTA_INVENTARIO = os.path.join(BASE_DIR, "datos", "recursos.json")


def _borde(ancho=1, color="#1e3a5f"):
    """Helper: Flet 0.86.1 no tiene ft.border.all(). Construye el Border manualmente."""
    lado = ft.border.BorderSide(width=ancho, color=color)
    return ft.border.Border(left=lado, top=lado, right=lado, bottom=lado)


def buscar_clave_ci(diccionario, clave):
    """
    Busca en un diccionario sin importar si usas mayúsculas o minúsculas.
    Por ejemplo, si el usuario escribe "Scurrius" pero en los datos está como "scUrrius",
    igual lo encuentra. Devuelve la clave real que está en el diccionario, o None si no existe.
    """
    if not diccionario or not clave:
        return None
    clave_lower = clave.lower()
    for k in diccionario:
        if k.lower() == clave_lower:
            return k
    return None


def validar_entero(valor, minimo=1, maximo=None, nombre_campo="Campo"):
    """
    Valida que un valor sea un entero dentro de un rango.

    Args:
        valor: Valor a validar (str o None).
        minimo: Valor mínimo permitido.
        maximo: Valor máximo permitido (None = sin límite).
        nombre_campo: Nombre del campo para mensajes de error.

    Returns:
        tuple[bool, int, str]: (es_valido, valor_limpio, mensaje_error)
    """
    if valor is None or str(valor).strip() == "":
        return False, 0, f"{nombre_campo} no puede estar vacío."

    val_str = str(valor).strip()

    # Verificar que sea numérico (soportar negativos para validación)
    try:
        val_int = int(val_str)
    except ValueError:
        return False, 0, f"{nombre_campo} debe ser un número entero (recibido: '{val_str}')."

    if val_int < minimo:
        return False, 0, f"{nombre_campo} debe ser ≥ {minimo} (recibido: {val_int})."

    if maximo is not None and val_int > maximo:
        return False, 0, f"{nombre_campo} debe ser ≤ {maximo} (recibido: {val_int})."

    return True, val_int, ""


def main(page: ft.Page):
    
    # CONFIGURACIÓN DE VENTANA — Modern Dark UI
    
    page.title = "Omega RPG — Simulador OSRS Predictivo"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1150
    page.window_height = 800
    page.padding = 25
    page.bgcolor = "#080c14"

    os.makedirs(os.path.dirname(RUTA_DATOS), exist_ok=True)

    
    # INSTANCIACIÓN DE MÓDULOS
    
    motor = rng_drops.RNGDrops(RUTA_DATOS)
    servidor = ServidorRPG()
    inventario = InventarioJugador(RUTA_INVENTARIO)

    
    # WIDGETS DE INTERFAZ
    
    txt_ataque = ft.TextField(
        label="⚔️ Ataque (Precisión)", value="1", width=220,
        text_align="center", border_color="#6366f1",
        focused_border_color="#818cf8", cursor_color="#818cf8"
    )
    txt_fuerza = ft.TextField(
        label="💪 Fuerza (Max Hit)", value="1", width=220,
        text_align="center", border_color="#ef4444",
        focused_border_color="#f87171", cursor_color="#f87171"
    )

    dd_zona = ft.Dropdown(label="🗺️ Zona", width=220, border_color="#1e3a5f")
    dd_jefe = ft.Dropdown(label="👹 Jefe", width=220, border_color="#1e3a5f")
    dd_loot = ft.Dropdown(label="💎 Drop Objetivo", width=220, border_color="#1e3a5f")

    switch_pity = ft.Switch(label="🎰 Pity System", value=False, active_color="#f59e0b")
    consola = ft.ListView(expand=True, spacing=5, auto_scroll=True)

    # SnackBar para feedback visible sobre diálogos modales
    snack = ft.SnackBar(content=ft.Text(""), open=False)
    page.overlay.append(snack)

    def avisar(texto, color="white"):
        """Muestra un aviso flotante. Visible incluso con diálogos modales abiertos."""
        snack.content = ft.Text(texto, color="black")
        snack.bgcolor = color
        snack.open = True
        page.update()

    def log(texto, color="#22c55e", negrita=False):
        """Imprime una línea en la consola tipo terminal."""
        peso = ft.FontWeight.BOLD if negrita else ft.FontWeight.NORMAL
        consola.controls.append(
            ft.Text(texto, color=color, selectable=True,
                    font_family="Consolas", weight=peso, size=12)
        )
        consola.update()
        page.update()

    
    # EVENTOS EN CASCADA (Zona → Jefe → Loot)
    # Why: Flet 0.86.1 reemplazó on_change por on_select en ft.Dropdown.
    #      Usar on_change no dispara ningún evento — ese era el bug.
    
    def cargar_zonas():
        """Rellena el dropdown de zonas con las claves del JSON."""
        zonas = motor.datos_mundo.get("zonas", {})
        dd_zona.options = [ft.dropdown.Option(key=str(z), text=str(z)) for z in zonas.keys()]
        if not dd_zona.options:
            dd_zona.options = [ft.dropdown.Option(key="Sin Datos", text="Sin Datos")]
        dd_zona.update()
        page.update()

    def on_zona_select(e):
        """Al seleccionar zona, carga los jefes de esa zona en dd_jefe."""
        z = (dd_zona.value or "").strip()
        z_real = buscar_clave_ci(motor.datos_mundo.get("zonas", {}), z)

        jefes = {}
        if z_real:
            jefes = motor.datos_mundo.get("zonas", {})[z_real].get("monstruos", {})

        dd_jefe.options = [ft.dropdown.Option(key=str(j), text=str(j)) for j in jefes.keys()]
        dd_jefe.value = None
        dd_jefe.update()

        dd_loot.options = []
        dd_loot.value = None
        dd_loot.update()

        page.update()

    def on_jefe_select(e):
        """Al seleccionar jefe, carga los drops de ese jefe en dd_loot."""
        z = (dd_zona.value or "").strip()
        j = (dd_jefe.value or "").strip()

        z_real = buscar_clave_ci(motor.datos_mundo.get("zonas", {}), z)
        loot = {}
        if z_real:
            j_real = buscar_clave_ci(motor.datos_mundo.get("zonas", {})[z_real].get("monstruos", {}), j)
            if j_real:
                loot = motor.datos_mundo["zonas"][z_real]["monstruos"][j_real].get("loot", {})

        dd_loot.options = [ft.dropdown.Option(key=str(l), text=str(l)) for l in loot.keys()]
        dd_loot.value = None
        dd_loot.update()
        page.update()

    dd_zona.on_select = on_zona_select
    dd_jefe.on_select = on_jefe_select

    
    # CONTROLADOR DEL SIMULADOR
    
    def simular(e):
        try:
            # Validar selecciones de dropdowns
            if not dd_zona.value or dd_zona.value == "Sin Datos":
                log("[AVISO] Selecciona una zona primero.", "#f59e0b")
                return
            if not dd_jefe.value:
                log("[AVISO] Selecciona un jefe primero.", "#f59e0b")
                return
            if not dd_loot.value:
                log("[AVISO] Selecciona un drop objetivo.", "#f59e0b")
                return

            # Validar stats del jugador
            ok_atk, atk_int, err_atk = validar_entero(txt_ataque.value, 1, 99, "Ataque")
            if not ok_atk:
                log(f"[AVISO] {err_atk}", "#f59e0b")
                return

            ok_str, str_int, err_str = validar_entero(txt_fuerza.value, 1, 99, "Fuerza")
            if not ok_str:
                log(f"[AVISO] {err_str}", "#f59e0b")
                return

            # Resolver claves reales case-insensitive
            z_real = buscar_clave_ci(motor.datos_mundo.get("zonas", {}), dd_zona.value)
            if not z_real:
                log("[ERROR] Zona no encontrada en los datos.", "#ef4444")
                return
            j_real = buscar_clave_ci(
                motor.datos_mundo["zonas"][z_real].get("monstruos", {}), dd_jefe.value
            )
            if not j_real:
                log("[ERROR] Jefe no encontrado en la zona.", "#ef4444")
                return

            consola.controls.clear()
            log(f"▸ Calculando esperanza matemática para: {dd_loot.value}...", "#94a3b8")

            stats = {
                "Ataque": atk_int,
                "Fuerza": str_int
            }

            resultado = motor.calcular_caceria_completa(
                id_zona=z_real,
                id_monstruo=j_real,
                nombre_item=dd_loot.value,
                stats_jugador=stats,
                usar_pity=switch_pity.value
            )

            if "error" in resultado:
                log(f"[ERROR] {resultado['error']}", "#ef4444", True)
                return

            # Header
            log(f"⚔️ {resultado.get('monstruo')}  →  🎯 {resultado.get('item')}", "#06b6d4", True)
            log(f"🎲 Drop Rate: {resultado.get('prob_formato')}  |  "
                f"⏱️ {resultado.get('tiempo_por_caza_seg'):.1f}s por kill")
            log("━" * 50, "#1e293b")

            # Estadística Teórica 
            log("📊 ESTADÍSTICA TEÓRICA (90% Certeza):", "#f59e0b", True)
            log(f"   Kills necesarios: {resultado['teorico']['intentos_90']}")
            log(f"   Horas de farmeo: {resultado['teorico']['tiempo_total_horas']} hrs")
            log("━" * 50, "#1e293b")

            # Simulación 
            log("🎮 SIMULACIÓN DE ESTA SESIÓN:", "#a855f7", True)
            log(f"   Drop obtenido en el Kill #{resultado['simulacion']['intentos']}")
            log(f"   Horas farmeadas: {resultado['simulacion']['tiempo_total_horas']} hrs")

            # Pity — SOLO se muestra cuando está activado 
            if switch_pity.value:
                log("━" * 50, "#1e293b")
                log("🎰 PITY SYSTEM [ACTIVO — Solo simulación, no se guarda en inventario]:", "#f59e0b", True)
                log(f"   Probabilidad final alcanzada: "
                    f"{resultado['simulacion']['prob_final_alcanzada']}%")

            # Registro en Servidor e Inventario — SOLO si pity está desactivado 
            if not switch_pity.value:
                info_reg = servidor.registrar_simulacion(resultado)
                nombre_item = resultado.get("item", "")
                nueva_cant = inventario.agregar_item(nombre_item)

                log("━" * 50, "#1e293b")
                log("📡 REGISTRO EN SERVIDOR:", "#06b6d4", True)
                log(f"   Cola FIFO: {info_reg['posicion_cola']}/{servidor.MAX_HISTORIAL} registros")
                log(f"   Árbol ABB: {info_reg['total_en_arbol']} nodos")

                mejor = servidor.obtener_mejor_racha()
                peor = servidor.obtener_peor_racha()
                if mejor:
                    log(f"   🍀 Mejor racha: {mejor['item']} ({mejor['horas']}h)", "#22c55e")
                if peor:
                    log(f"   💀 Peor racha: {peor['item']} ({peor['horas']}h)", "#f87171")

                # Inventario (Tabla Hash) 
                log("━" * 50, "#1e293b")
                log("🎒 INVENTARIO ACTUALIZADO:", "#f59e0b", True)
                log(f"   {nombre_item} ×{nueva_cant}  |  "
                    f"Tipos: {inventario.total_tipos()}  |  Total: {inventario.total_items()}")
            else:
                log("━" * 50, "#1e293b")
                log("ℹ️ Pity activo → No se guardó en inventario ni servidor.", "#94a3b8")

        except Exception:
            log(f"[ERROR DEL SISTEMA]\n{traceback.format_exc()}", "#ef4444", True)

    
    # VENTANA PARA CREAR JEFES Y AÑADIR ÍTEMS (CRUD)
    
    def cerrar_dialogo():
        page.pop_dialog()
        page.update()

    def abrir_crud(e):
        # Pre-rellenar con la selección actual del dropdown
        zona_pre = dd_zona.value if dd_zona.value and dd_zona.value != "Sin Datos" else ""
        jefe_pre = dd_jefe.value or ""

        txt_nueva_zona = ft.TextField(
            label="ID Zona (Ej: volcan_infernal)", value=zona_pre,
            width=320, border_color="#1e3a5f"
        )
        txt_nuevo_jefe = ft.TextField(
            label="ID Jefe (Ej: demonio_mayor)", value=jefe_pre,
            width=320, border_color="#1e3a5f"
        )
        txt_hp = ft.TextField(label="Vida (HP)", value="100", width=145, border_color="#1e3a5f")
        txt_def = ft.TextField(label="Defensa", value="10", width=145, border_color="#1e3a5f")

        # Sistema de filas dinámicas para múltiples drops 
        filas_drops = ft.ListView(spacing=5, height=180, auto_scroll=True)
        # Why: Se eliminó items_pendientes — era dead code que nunca se consumía.

        def crear_fila_drop(indice_inicial=None):
            """Crea una fila de input para un drop con nombre, probabilidad y botón eliminar."""
            txt_nombre = ft.TextField(
                label="Nombre del Ítem", width=190, border_color="#1e3a5f",
                text_size=12
            )
            txt_prob = ft.TextField(
                label="1/X", value="50", width=70, border_color="#1e3a5f",
                text_size=12
            )

            fila_container = ft.Container(content=ft.Text(""))  # Placeholder

            def eliminar_fila(e):
                """Elimina esta fila de la lista visual."""
                if fila_container in filas_drops.controls:
                    filas_drops.controls.remove(fila_container)
                    filas_drops.update()

            btn_eliminar = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color="#ef4444", icon_size=18,
                tooltip="Eliminar fila",
                on_click=eliminar_fila
            )

            fila_container.content = ft.Row(
                [txt_nombre, txt_prob, btn_eliminar],
                spacing=5, vertical_alignment="center"
            )
            fila_container.padding = 4
            fila_container.border = _borde(1, "#1e293b")
            fila_container.border_radius = 6

            # Guardar refs en el container para poder leerlas al guardar
            fila_container.data = {"txt_nombre": txt_nombre, "txt_prob": txt_prob}

            return fila_container

        def agregar_fila_drop(e):
            """Añade una nueva fila de drop al formulario."""
            nueva_fila = crear_fila_drop()
            filas_drops.controls.append(nueva_fila)
            filas_drops.update()

        # Agregar una fila inicial por defecto
        filas_drops.controls.append(crear_fila_drop())

        btn_agregar_fila = ft.TextButton(
            content=ft.Text("➕ Agregar otro drop", color="#06b6d4", size=12),
            on_click=agregar_fila_drop
        )

        # Lista visual de ítems ya guardados en esta sesión del diálogo
        items_guardados_lista = ft.ListView(spacing=3, height=60)
        lbl_items_count = ft.Text("Ítems guardados: 0", color="#64748b", size=11)
        items_count = [0]

        def guardar_jefe(e):
            try:
                z_id = (txt_nueva_zona.value or "").strip()
                j_id = (txt_nuevo_jefe.value or "").strip()

                if not z_id or not j_id:
                    avisar("Llena los campos Zona y Jefe.", "#f59e0b")
                    return

                if "zonas" not in motor.datos_mundo:
                    motor.datos_mundo["zonas"] = {}

                # Búsqueda case-insensitive de la zona
                z_real = buscar_clave_ci(motor.datos_mundo["zonas"], z_id)
                if z_real is None:
                    # Zona nueva → crearla
                    motor.datos_mundo["zonas"][z_id] = {"nombre": z_id, "monstruos": {}}
                    z_real = z_id

                # Verificar duplicados case-insensitive del jefe
                j_real = buscar_clave_ci(
                    motor.datos_mundo["zonas"][z_real].get("monstruos", {}), j_id
                )
                if j_real is not None:
                    avisar(f"El jefe '{j_id}' ya existe en '{z_real}'.", "#ef4444")
                    return

                ok_hp, hp_int, err_hp = validar_entero(txt_hp.value, 1, 100000, "Vida (HP)")
                if not ok_hp:
                    avisar(err_hp, "#ef4444")
                    return

                ok_def, def_int, err_def = validar_entero(txt_def.value, 0, 100000, "Defensa")
                if not ok_def:
                    avisar(err_def, "#ef4444")
                    return

                motor.datos_mundo["zonas"][z_real]["monstruos"][j_id] = {
                    "nombre": j_id.replace("_", " ").title(),
                    "vida": hp_int,
                    "defensa": def_int,
                    "loot": {}
                }

                if not motor.guardar_datos():
                    avisar("Error Crítico: No se pudo guardar en el archivo JSON. Revisa permisos o OneDrive.", "#ef4444")
                    return
                
                cargar_zonas()

                # Forzar selección en dropdowns para que el nuevo jefe sea visible
                dd_zona.value = z_real
                dd_zona.update()
                on_zona_select(None)
                dd_jefe.value = j_id
                dd_jefe.update()

                # Pre-rellenar la pestaña 2 con los mismos IDs
                txt_nueva_zona.value = z_real
                txt_nuevo_jefe.value = j_id
                txt_nueva_zona.update()
                txt_nuevo_jefe.update()

                avisar(f"Jefe '{j_id}' creado en '{z_real}'. Añade ítems en pestaña 2.", "#22c55e")
                log(f"[OK] Jefe '{j_id}' creado en '{z_real}'.", "#22c55e", True)
            except Exception:
                avisar("Error al guardar jefe. Revisa la consola.", "#ef4444")
                log(f"[ERROR]\n{traceback.format_exc()}", "#ef4444")

        def guardar_todos_items(e):
            """Guarda todos los ítems de las filas de drop en batch."""
            try:
                z_id = (txt_nueva_zona.value or "").strip()
                j_id = (txt_nuevo_jefe.value or "").strip()

                if not z_id or not j_id:
                    avisar("Llena Zona y Jefe antes de guardar ítems.", "#f59e0b")
                    return

                # Búsqueda case-insensitive
                z_real = buscar_clave_ci(motor.datos_mundo.get("zonas", {}), z_id)
                if z_real is None:
                    avisar(f"Zona '{z_id}' no existe. Créala primero en pestaña 1.", "#ef4444")
                    return

                j_real = buscar_clave_ci(
                    motor.datos_mundo["zonas"][z_real].get("monstruos", {}), j_id
                )
                if j_real is None:
                    avisar(f"Jefe '{j_id}' no existe en '{z_real}'. Créalo primero.", "#ef4444")
                    return

                guardados = 0
                errores = 0

                for fila in list(filas_drops.controls):
                    if not hasattr(fila, 'data') or fila.data is None:
                        continue

                    txt_n = fila.data["txt_nombre"]
                    txt_p = fila.data["txt_prob"]

                    item_nombre = (txt_n.value or "").strip()

                    if not item_nombre:
                        continue  # Fila vacía, saltar

                    ok_prob, prob_x, _ = validar_entero(txt_p.value, 1, 1000000, "Probabilidad")
                    if not ok_prob:
                        errores += 1
                        continue

                    motor.datos_mundo["zonas"][z_real]["monstruos"][j_real].setdefault("loot", {})
                    motor.datos_mundo["zonas"][z_real]["monstruos"][j_real]["loot"][item_nombre] = {
                        "item": item_nombre,
                        "probabilidad_x": prob_x,
                        "pity": {"probabilidad_incremento": (1.0 / prob_x) / 5}
                    }

                    guardados += 1
                    items_count[0] += 1
                    items_guardados_lista.controls.append(
                        ft.Text(f"  ✅ {item_nombre} (1/{prob_x})", color="#22c55e", size=11)
                    )

                if guardados > 0:
                    if not motor.guardar_datos():
                        avisar("Error Crítico: No se pudo guardar ítems en el archivo JSON.", "#ef4444")
                        return

                    # Actualizar dropdown si estamos viendo el mismo jefe
                    if dd_zona.value == z_real and dd_jefe.value == j_real:
                        on_jefe_select(None)

                    lbl_items_count.value = f"Ítems guardados: {items_count[0]}"
                    items_guardados_lista.update()
                    lbl_items_count.update()

                    # Limpiar filas y agregar una nueva vacía
                    filas_drops.controls.clear()
                    filas_drops.controls.append(crear_fila_drop())
                    filas_drops.update()

                    avisar(f"{guardados} ítem(s) añadidos a '{j_real}'.", "#22c55e")
                else:
                    msg = "No hay ítems válidos para guardar."
                    if errores > 0:
                        msg += f" ({errores} con probabilidad inválida)"
                    avisar(msg, "#f59e0b")

            except Exception:
                avisar("Error al guardar ítems.", "#ef4444")
                log(f"[ERROR]\n{traceback.format_exc()}", "#ef4444")

        btn_guardar_jefe = ft.Button(
            content=ft.Text("💾 Crear Jefe", color="white"),
            bgcolor="#6366f1", on_click=guardar_jefe
        )
        btn_guardar_items = ft.Button(
            content=ft.Text("💾 Guardar todos los drops", color="white"),
            bgcolor="#22c55e", on_click=guardar_todos_items
        )

        vista_crear_jefe = ft.Column([
            ft.Text("IDs sin espacios. No importan mayúsculas/minúsculas.",
                    color="#f59e0b", size=11),
            txt_nueva_zona, txt_nuevo_jefe,
            ft.Row([txt_hp, txt_def]),
            btn_guardar_jefe
        ], spacing=10)

        vista_anadir_drops = ft.Column([
            ft.Text("Usa la misma Zona/Jefe. Añade múltiples drops a la vez.",
                    color="#f59e0b", size=11),
            filas_drops,
            ft.Row([btn_agregar_fila, btn_guardar_items], spacing=10),
            ft.Divider(color="#1e293b"),
            lbl_items_count,
            items_guardados_lista
        ], spacing=8)

        contenedor_vistas = ft.Container(content=vista_crear_jefe, padding=10)

        def cambiar_pestana(e, nombre_vista):
            if nombre_vista == "jefe":
                contenedor_vistas.content = vista_crear_jefe
            else:
                contenedor_vistas.content = vista_anadir_drops
            contenedor_vistas.update()

        dialogo_crud = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚙️ Gestor de Base de Datos"),
            content=ft.Column([
                ft.Row([
                    ft.TextButton(
                        content=ft.Text("1. Crear Jefe", color="#6366f1"),
                        on_click=lambda e: cambiar_pestana(e, "jefe")
                    ),
                    ft.TextButton(
                        content=ft.Text("2. Añadir Drops", color="#22c55e"),
                        on_click=lambda e: cambiar_pestana(e, "drops")
                    ),
                ]),
                ft.Divider(color="#1e293b"),
                contenedor_vistas
            ], width=420, height=450),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialogo())
            ]
        )
        page.show_dialog(dialogo_crud)
        page.update()

    def eliminar_jefe(e):
        """Elimina el jefe seleccionado usando búsqueda case-insensitive."""
        try:
            z = dd_zona.value
            j = dd_jefe.value
            if not z or not j:
                log("[AVISO] Selecciona un jefe válido para eliminarlo.", "#f59e0b")
                return

            z_real = buscar_clave_ci(motor.datos_mundo.get("zonas", {}), z)
            if not z_real:
                log("[AVISO] Zona no encontrada.", "#f59e0b")
                return

            j_real = buscar_clave_ci(
                motor.datos_mundo["zonas"][z_real].get("monstruos", {}), j
            )
            if not j_real:
                log("[AVISO] Jefe no encontrado en la zona.", "#f59e0b")
                return

            del motor.datos_mundo["zonas"][z_real]["monstruos"][j_real]
            motor.guardar_datos()
            on_zona_select(None)
            log(f"❌ Jefe '{j_real}' eliminado de '{z_real}'.", "#ef4444", True)
        except Exception:
            log(f"[ERROR]\n{traceback.format_exc()}", "#ef4444")

    
    # SIMULACIÓN DE 1 HORA — Farmeo por tiempo
    
    def simular_una_hora(e):
        """
        Simula 1 hora de farmeo contra el boss seleccionado.
        Kills = floor(3600 / tiempo_por_kill). El loot se guarda en inventario.
        """
        try:
            # Validar selecciones
            if not dd_zona.value or dd_zona.value == "Sin Datos":
                log("[AVISO] Selecciona una zona primero.", "#f59e0b")
                return
            if not dd_jefe.value:
                log("[AVISO] Selecciona un jefe primero.", "#f59e0b")
                return

            ok_atk, atk_v, err_atk = validar_entero(txt_ataque.value, 1, 99, "Ataque")
            if not ok_atk:
                log(f"[AVISO] {err_atk}", "#f59e0b")
                return
            ok_str, str_v, err_str = validar_entero(txt_fuerza.value, 1, 99, "Fuerza")
            if not ok_str:
                log(f"[AVISO] {err_str}", "#f59e0b")
                return

            # Resolver claves CI
            z_real = buscar_clave_ci(motor.datos_mundo.get("zonas", {}), dd_zona.value)
            if not z_real:
                log("[ERROR] Zona no encontrada.", "#ef4444")
                return
            j_real = buscar_clave_ci(
                motor.datos_mundo["zonas"][z_real].get("monstruos", {}), dd_jefe.value
            )
            if not j_real:
                log("[ERROR] Jefe no encontrado.", "#ef4444")
                return

            monstruo = motor.obtener_monstruo(z_real, j_real)
            if not monstruo:
                log("[ERROR] No se pudo obtener datos del monstruo.", "#ef4444")
                return

            loot_pool = monstruo.get("loot", {})
            if not loot_pool:
                log("[AVISO] Este boss no tiene loot definido.", "#f59e0b")
                return

            stats = {"Ataque": atk_v, "Fuerza": str_v}
            tiempo_por_kill = motor.calcular_tiempo_combate(stats, monstruo)

            if tiempo_por_kill <= 0:
                log("[ERROR] Tiempo por kill inválido.", "#ef4444")
                return

            n_kills = math.floor(3600 / tiempo_por_kill)
            if n_kills <= 0:
                log("[AVISO] Con estos stats, no puedes completar ni 1 kill en 1 hora.", "#f59e0b")
                return

            # Simular N kills
            loot_obtenido = {}
            for _ in range(n_kills):
                for item_name, item_data in loot_pool.items():
                    prob = rng_drops.RNGDrops.obtener_probabilidad(item_data)
                    if random.random() < prob:
                        loot_obtenido[item_name] = loot_obtenido.get(item_name, 0) + 1

            # Guardar loot en inventario
            for item_name, cantidad in loot_obtenido.items():
                inventario.agregar_item(item_name, cantidad)

            # Mostrar resultados en consola
            consola.controls.clear()
            log(f"⏱️ SIMULACIÓN DE 1 HORA — {monstruo.get('nombre', j_real)}", "#06b6d4", True)
            log(f"⚔️ {n_kills:,} kills  |  ⏱️ {tiempo_por_kill:.1f}s por kill", "#94a3b8")
            log(f"📊 Stats: ATK {atk_v} / STR {str_v}", "#94a3b8")
            log("━" * 50, "#1e293b")

            if not loot_obtenido:
                log("💨 No cayó ningún drop en esta hora.", "#64748b")
            else:
                log("🎒 LOOT OBTENIDO (guardado en inventario):", "#f59e0b", True)
                for item_name, cantidad in sorted(loot_obtenido.items(), key=lambda x: x[1], reverse=True):
                    item_data = loot_pool.get(item_name, {})
                    prob = rng_drops.RNGDrops.obtener_probabilidad(item_data)
                    esperado = n_kills * prob
                    prob_str = rng_drops.RNGDrops.formato_probabilidad(item_data)

                    # Color según suerte relativa
                    if cantidad > esperado * 1.3:
                        color_item, emoji = "#22c55e", "🍀"
                    elif cantidad < esperado * 0.7:
                        color_item, emoji = "#ef4444", "💀"
                    else:
                        color_item, emoji = "#f59e0b", "⚡"

                    log(
                        f"   {emoji} {item_name} ×{cantidad}  "
                        f"(esperado: {esperado:.1f})  [{prob_str}]",
                        color_item
                    )

            # Resumen de inventario
            log("━" * 50, "#1e293b")
            log(
                f"🎒 Inventario total: {inventario.total_tipos()} tipos  |  "
                f"{inventario.total_items()} ítems acumulados",
                "#f59e0b"
            )

        except Exception:
            log(f"[ERROR DEL SISTEMA]\n{traceback.format_exc()}", "#ef4444", True)

    
    # DIÁLOGO SIMULACIÓN MASIVA — Multi-Kill
    
    def abrir_simulacion_masiva(e):
        """
        Ventana que te deja simular la cantidad de kills que quieras contra un jefe
        y te muestra todo el loot que obtendrías. 
        """

        # Construir dropdown global de bosses (zona → boss)
        opciones_bosses = []
        boss_map = {}  # key: "zona|boss" → (zona_id, boss_id)
        for zona_id, zona_data in motor.datos_mundo.get("zonas", {}).items():
            for boss_id, boss_data in zona_data.get("monstruos", {}).items():
                label = f"{boss_data.get('nombre', boss_id)} ({zona_data.get('nombre', zona_id)})"
                key = f"{zona_id}|{boss_id}"
                opciones_bosses.append(ft.dropdown.Option(key=key, text=label))
                boss_map[key] = (zona_id, boss_id)

        dd_boss_global = ft.Dropdown(
            label="👹 Seleccionar Boss",
            width=380,
            border_color="#a855f7",
            options=opciones_bosses if opciones_bosses else [ft.dropdown.Option("Sin bosses")]
        )

        txt_n_kills = ft.TextField(
            label="🔢 Número de kills a simular",
            value="100", width=180,
            text_align="center",
            border_color="#a855f7",
            focused_border_color="#c084fc",
            cursor_color="#c084fc"
        )

        resultado_lista = ft.ListView(spacing=4, height=250, auto_scroll=True)

        def ejecutar_sim_masiva(e):
            """Ejecuta la simulación masiva de N kills."""
            try:
                resultado_lista.controls.clear()

                boss_key = dd_boss_global.value
                if not boss_key or boss_key == "Sin bosses":
                    resultado_lista.controls.append(
                        ft.Text("⚠️ Selecciona un boss primero.", color="#f59e0b")
                    )
                    resultado_lista.update()
                    return

                ok_n, n_kills, err_n = validar_entero(txt_n_kills.value, 1, 100000, "Kills")
                if not ok_n:
                    resultado_lista.controls.append(
                        ft.Text(f"⚠️ {err_n}", color="#f59e0b")
                    )
                    resultado_lista.update()
                    return


                zona_id, boss_id = boss_map[boss_key]
                monstruo = motor.obtener_monstruo(zona_id, boss_id)

                if not monstruo:
                    resultado_lista.controls.append(
                        ft.Text("❌ Boss no encontrado.", color="#ef4444")
                    )
                    resultado_lista.update()
                    return

                loot_pool = monstruo.get("loot", {})
                if not loot_pool:
                    resultado_lista.controls.append(
                        ft.Text("⚠️ Este boss no tiene loot definido.", color="#f59e0b")
                    )
                    resultado_lista.update()
                    return

                # Simular N kills usando RNGDrops.obtener_probabilidad()
                loot_obtenido = {}
                for _ in range(n_kills):
                    for item_name, item_data in loot_pool.items():
                        prob = rng_drops.RNGDrops.obtener_probabilidad(item_data)
                        if random.random() < prob:
                            loot_obtenido[item_name] = loot_obtenido.get(item_name, 0) + 1

                # Calcular tiempo total (usa stats del panel principal, con defaults seguros)
                _, atk_v, _ = validar_entero(txt_ataque.value, 1, 99, "Ataque")
                _, str_v, _ = validar_entero(txt_fuerza.value, 1, 99, "Fuerza")
                stats = {
                    "Ataque": atk_v if atk_v > 0 else 1,
                    "Fuerza": str_v if str_v > 0 else 1
                }
                tiempo_por_kill = motor.calcular_tiempo_combate(stats, monstruo)
                tiempo_total_horas = (n_kills * tiempo_por_kill) / 3600

                # Mostrar resultados
                resultado_lista.controls.append(
                    ft.Text(
                        f"⚔️ {monstruo.get('nombre', boss_id)} — {n_kills:,} kills simuladas",
                        color="#06b6d4", weight=ft.FontWeight.BOLD, size=14
                    )
                )
                resultado_lista.controls.append(
                    ft.Text(
                        f"⏱️ Tiempo total estimado: {tiempo_total_horas:.2f} horas",
                        color="#94a3b8", size=12
                    )
                )
                resultado_lista.controls.append(
                    ft.Text("━" * 45, color="#1e293b", size=10)
                )

                if not loot_obtenido:
                    resultado_lista.controls.append(
                        ft.Text("💨 No cayó ningún drop en estas kills.", color="#64748b", italic=True)
                    )
                else:
                    # Ordenar por cantidad descendente
                    for item_name, cantidad in sorted(loot_obtenido.items(), key=lambda x: x[1], reverse=True):
                        item_data = loot_pool.get(item_name, {})
                        prob = rng_drops.RNGDrops.obtener_probabilidad(item_data)
                        esperado = n_kills * prob

                        # Color según suerte
                        if cantidad > esperado * 1.3:
                            color = "#22c55e"  # Suerte
                            emoji = "🍀"
                        elif cantidad < esperado * 0.7:
                            color = "#ef4444"  # Mala suerte
                            emoji = "💀"
                        else:
                            color = "#f59e0b"  # Normal
                            emoji = "⚡"

                        prob_str = rng_drops.RNGDrops.formato_probabilidad(item_data)
                        resultado_lista.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Text(f"{emoji} {item_name}", color=color, size=12, expand=True),
                                    ft.Text(f"×{cantidad}", color="white",
                                            weight=ft.FontWeight.BOLD, size=12, width=60),
                                    ft.Text(f"(esperado: {esperado:.1f})", color="#64748b", size=10, width=110),
                                    ft.Text(f"[{prob_str}]", color="#475569", size=10, width=60),
                                ]),
                                padding=4,
                            )
                        )

                resultado_lista.update()
                page.update()

            except Exception:
                resultado_lista.controls.append(
                    ft.Text(f"[ERROR]\n{traceback.format_exc()}", color="#ef4444", size=10)
                )
                resultado_lista.update()

        btn_ejecutar = ft.Button(
            content=ft.Text("🎮 ¡Simular Kills!", color="white",
                            weight=ft.FontWeight.BOLD),
            bgcolor="#a855f7",
            on_click=ejecutar_sim_masiva
        )

        dialogo_masiva = ft.AlertDialog(
            modal=True,
            title=ft.Text("🎲 Simulación Masiva — Multi-Kill"),
            content=ft.Column([
                ft.Text("Selecciona un boss y la cantidad de kills a simular.",
                         color="#94a3b8", size=12),
                dd_boss_global,
                txt_n_kills,
                ft.Row([btn_ejecutar], alignment="center"),
                ft.Divider(color="#1e293b"),
                resultado_lista
            ], width=520, height=420),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialogo())
            ]
        )
        page.show_dialog(dialogo_masiva)
        page.update()

    
    # PANEL DE DATOS — Historial, Inventario, Ranking
    
    def abrir_panel_datos(e):
        """Diálogo con 3 pestañas: Cola FIFO, Tabla Hash, Árbol ABB."""

        # ═══ Pestaña 1: Historial Reciente (Cola FIFO) ═══
        lista_hist = ft.ListView(spacing=5, height=260, auto_scroll=True)
        historial = servidor.obtener_historial_reciente()

        if not historial:
            lista_hist.controls.append(
                ft.Text("Sin simulaciones registradas aún.", color="#64748b", italic=True)
            )
        else:
            for i, reg in enumerate(reversed(historial), 1):
                lista_hist.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"#{i}  {reg['item']}",
                                color="#06b6d4", weight=ft.FontWeight.BOLD, size=13
                            ),
                            ft.Text(
                                f"  {reg['boss']}  ·  {reg['intentos']} kills  ·  "
                                f"{reg['horas']}h  ·  {reg['timestamp']}",
                                color="#94a3b8", size=11
                            ),
                        ], spacing=2),
                        padding=8,
                        border=_borde(),
                        border_radius=8,
                    )
                )

        vista_hist = ft.Column([
            ft.Text(
                f"📡 Cola FIFO — Últimas {servidor.MAX_HISTORIAL} simulaciones",
                color="#06b6d4", weight=ft.FontWeight.BOLD
            ),
            ft.Text(
                f"Registros: {len(historial)}/{servidor.MAX_HISTORIAL}",
                color="#64748b", size=11
            ),
            lista_hist
        ], spacing=8)

        # Pestaña 2: Inventario del Jugador (Tabla Hash) 
        lista_inv = ft.ListView(spacing=5, height=260, auto_scroll=True)
        items_ord = inventario.obtener_items_ordenados()

        if not items_ord:
            lista_inv.controls.append(
                ft.Text("Inventario vacío. ¡Simula un drop!", color="#64748b", italic=True)
            )
        else:
            for nombre, cantidad in items_ord:
                lista_inv.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"💎 {nombre}", color="#f59e0b", size=13, expand=True),
                            ft.Container(
                                content=ft.Text(
                                    f"×{cantidad}", color="white",
                                    weight=ft.FontWeight.BOLD, size=13
                                ),
                                bgcolor="#334155", border_radius=8, padding=8,
                            )
                        ]),
                        padding=6,
                    )
                )

        vista_inv = ft.Column([
            ft.Text(
                "🎒 Inventario — Tabla Hash (dict)",
                color="#f59e0b", weight=ft.FontWeight.BOLD
            ),
            ft.Text(
                f"Tipos: {inventario.total_tipos()}  |  "
                f"Total acumulado: {inventario.total_items()}",
                color="#64748b", size=11
            ),
            lista_inv
        ], spacing=8)

        # Pestaña 3: Ranking de Suerte (ABB In-Orden) 
        lista_rank = ft.ListView(spacing=5, height=260, auto_scroll=True)
        ranking = servidor.obtener_ranking_suerte()

        if not ranking:
            lista_rank.controls.append(
                ft.Text("Sin datos. Realiza simulaciones primero.",
                        color="#64748b", italic=True)
            )
        else:
            total_rank = len(ranking)
            for i, reg in enumerate(ranking, 1):
                tercio = max(1, total_rank // 3)
                if i <= tercio:
                    color_r, emoji = "#22c55e", "🍀"
                elif i > total_rank - tercio:
                    color_r, emoji = "#f87171", "💀"
                else:
                    color_r, emoji = "#f59e0b", "⚡"

                lista_rank.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"{emoji} #{i}", color=color_r, size=12, width=55),
                            ft.Text(
                                f"{reg['item']} ({reg['boss']})",
                                color="#e2e8f0", size=12, expand=True
                            ),
                            ft.Text(
                                f"{reg['horas']} hrs",
                                color=color_r, weight=ft.FontWeight.BOLD, size=12
                            ),
                        ]),
                        padding=6,
                    )
                )

        mejor = servidor.obtener_mejor_racha()
        peor = servidor.obtener_peor_racha()
        resumen = ""
        if mejor and peor:
            resumen = (f"🍀 Mejor: {mejor['item']} ({mejor['horas']}h)  |  "
                       f"💀 Peor: {peor['item']} ({peor['horas']}h)")

        vista_rank = ft.Column([
            ft.Text(
                "🌳 Ranking de Suerte — ABB (In-Orden)",
                color="#22c55e", weight=ft.FontWeight.BOLD
            ),
            ft.Text(resumen, color="#64748b", size=11) if resumen else ft.Container(),
            ft.Text(
                f"Nodos en el árbol: {servidor.historial.tamano}",
                color="#64748b", size=11
            ),
            lista_rank
        ], spacing=8)

        # Pestañas manuales
        contenedor_panel = ft.Container(content=vista_hist, padding=10)

        def cambiar_panel(e, nombre):
            if nombre == "hist":
                contenedor_panel.content = vista_hist
            elif nombre == "inv":
                contenedor_panel.content = vista_inv
            else:
                contenedor_panel.content = vista_rank
            contenedor_panel.update()

        dialogo_datos = ft.AlertDialog(
            modal=True,
            title=ft.Text("📊 Panel de Datos del Servidor"),
            content=ft.Column([
                ft.Row([
                    ft.TextButton(
                        content=ft.Text("📡 Historial", color="#06b6d4"),
                        on_click=lambda e: cambiar_panel(e, "hist")
                    ),
                    ft.TextButton(
                        content=ft.Text("🎒 Inventario", color="#f59e0b"),
                        on_click=lambda e: cambiar_panel(e, "inv")
                    ),
                    ft.TextButton(
                        content=ft.Text("🌳 Ranking", color="#22c55e"),
                        on_click=lambda e: cambiar_panel(e, "rank")
                    ),
                ]),
                ft.Divider(color="#1e293b"),
                contenedor_panel
            ], width=520, height=420),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialogo())
            ]
        )
        page.show_dialog(dialogo_datos)
        page.update()

    
    # BOTONES PRINCIPALES
    
    btn_simular = ft.Button(
        content=ft.Text("▶️  ¡SIMULAR DROP!", color="white",
                        weight=ft.FontWeight.BOLD, size=14),
        bgcolor="#6366f1", height=48, on_click=simular
    )

    btn_crud = ft.TextButton(
        content=ft.Text("➕ Crear Jefe / Loot", color="#22c55e", size=12),
        on_click=abrir_crud
    )
    btn_eliminar = ft.TextButton(
        content=ft.Text("❌ Eliminar Jefe", color="#ef4444", size=12),
        on_click=eliminar_jefe
    )
    btn_panel_datos = ft.TextButton(
        content=ft.Text("📊 Historial / Inventario / Ranking", color="#06b6d4", size=12),
        on_click=abrir_panel_datos
    )
    btn_masiva = ft.TextButton(
        content=ft.Text("🎲 Simulación Masiva", color="#a855f7", size=12),
        on_click=abrir_simulacion_masiva
    )
    btn_1hora = ft.TextButton(
        content=ft.Text("⏱️ Simular 1 Hora", color="#06b6d4", size=12),
        on_click=simular_una_hora
    )

    
    # CONSTRUCCIÓN VISUAL — Modern Dark UI
    
    panel_izquierdo = ft.Container(
        content=ft.Column([
            ft.Text("⚔️ Stats OSRS", size=20,
                    weight=ft.FontWeight.BOLD, color="#e2e8f0"),
            ft.Divider(color="#1e3a5f"),
            txt_ataque,
            txt_fuerza,
            ft.Divider(color="#1e3a5f"),
            ft.Text("📖 Mecánica", size=14,
                    color="#94a3b8", weight=ft.FontWeight.BOLD),
            ft.Text("ATK → Hit Chance", size=11, color="#6366f1"),
            ft.Text("STR → Max Hit", size=11, color="#ef4444"),
        ], horizontal_alignment="center", spacing=12),
        width=260, padding=20, border_radius=16,
        bgcolor="#0f1729",
        border=_borde()
    )

    panel_derecho = ft.Container(
        content=ft.Column([
            ft.Text("🎯 Parámetros de Simulación", size=20,
                    weight=ft.FontWeight.BOLD, color="#e2e8f0"),
            ft.Row([dd_zona, dd_jefe, dd_loot], wrap=True, spacing=10),

            ft.Row([btn_simular, switch_pity], spacing=15),

            ft.Row([btn_crud, btn_eliminar, btn_panel_datos, btn_masiva, btn_1hora], spacing=5),

            ft.Container(
                content=consola, expand=True, padding=12, border_radius=12,
                bgcolor="#020617",
                border=_borde()
            )
        ], expand=True, spacing=12),
        expand=True, padding=20, border_radius=16,
        bgcolor="#0f1729",
        border=_borde()
    )

    page.add(
        ft.Row([panel_izquierdo, panel_derecho],
               expand=True, vertical_alignment="start", spacing=15)
    )
    cargar_zonas()
