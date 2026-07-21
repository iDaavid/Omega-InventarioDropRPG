import os
import traceback
import flet as ft
from modulos import rng_drops
from modulos.servidor import ServidorRPG
from modulos.inventario import InventarioJugador

# Rutas centralizadas (evita "magic strings" repetidas)
RUTA_DATOS = "datos/jefes.json"
RUTA_INVENTARIO = "datos/recursos.json"


def _borde(ancho=1, color="#1e3a5f"):
    """Helper: Flet 0.86.1 no tiene ft.border.all(). Construye el Border manualmente."""
    lado = ft.border.BorderSide(width=ancho, color=color)
    return ft.border.Border(left=lado, top=lado, right=lado, bottom=lado)


def buscar_clave_ci(diccionario, clave):
    """
    Búsqueda case-insensitive en las claves de un diccionario.
    Permite que el usuario escriba 'Scurrius' y encuentre 'scUrrius'.
    Retorna la clave REAL del dict, o None si no existe.
    """
    if not diccionario or not clave:
        return None
    clave_lower = clave.lower()
    for k in diccionario:
        if k.lower() == clave_lower:
            return k
    return None


def main(page: ft.Page):
    # ══════════════════════════════════════════
    # CONFIGURACIÓN DE VENTANA — Modern Dark UI
    # ══════════════════════════════════════════
    page.title = "Omega RPG — Simulador OSRS Predictivo"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1150
    page.window_height = 800
    page.padding = 25
    page.bgcolor = "#080c14"

    os.makedirs(os.path.dirname(RUTA_DATOS), exist_ok=True)

    # ══════════════════════════════════════════
    # INSTANCIACIÓN DE MÓDULOS
    # ══════════════════════════════════════════
    motor = rng_drops.RNGDrops(RUTA_DATOS)
    servidor = ServidorRPG()
    inventario = InventarioJugador(RUTA_INVENTARIO)

    # ══════════════════════════════════════════
    # WIDGETS DE INTERFAZ
    # ══════════════════════════════════════════
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

    # ═══ SnackBar para feedback visible sobre diálogos modales ═══
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

    # ══════════════════════════════════════════
    # EVENTOS EN CASCADA (Zona → Jefe → Loot)
    # ══════════════════════════════════════════
    def cargar_zonas():
        """Rellena el dropdown de zonas con las claves del JSON."""
        zonas = motor.datos_mundo.get("zonas", {})
        dd_zona.options = [ft.dropdown.Option(z) for z in zonas.keys()]
        if not dd_zona.options:
            dd_zona.options = [ft.dropdown.Option("Sin Datos")]
        dd_zona.update()

    def on_zona_change(e):
        """Al seleccionar zona, muestra SOLO los jefes de esa zona."""
        z = dd_zona.value
        jefes = motor.datos_mundo.get("zonas", {}).get(z, {}).get("monstruos", {})
        dd_jefe.options = [ft.dropdown.Option(j) for j in jefes.keys()]
        dd_jefe.value = None
        dd_loot.options = []
        dd_loot.value = None
        dd_jefe.update()
        dd_loot.update()

    def on_jefe_change(e):
        """Al seleccionar jefe, muestra SOLO los drops de ese jefe."""
        z = dd_zona.value
        j = dd_jefe.value
        if z and j:
            loot = motor.datos_mundo.get("zonas", {}).get(z, {}).get(
                "monstruos", {}).get(j, {}).get("loot", {})
            dd_loot.options = [ft.dropdown.Option(l) for l in loot.keys()]
        else:
            dd_loot.options = []
        dd_loot.value = None
        dd_loot.update()

    dd_zona.on_change = on_zona_change
    dd_jefe.on_change = on_jefe_change

    # ══════════════════════════════════════════
    # CONTROLADOR DEL SIMULADOR
    # ══════════════════════════════════════════
    def simular(e):
        try:
            if not dd_loot.value:
                log("[AVISO] Selecciona un drop objetivo en el menú 3.", "#f59e0b")
                return

            consola.controls.clear()
            log(f"▸ Calculando esperanza matemática para: {dd_loot.value}...", "#94a3b8")

            atk_val = txt_ataque.value or ""
            str_val = txt_fuerza.value or ""

            stats = {
                "Ataque": int(atk_val) if atk_val.isdigit() else 1,
                "Fuerza": int(str_val) if str_val.isdigit() else 1
            }

            resultado = motor.calcular_caceria_completa(
                id_zona=dd_zona.value,
                id_monstruo=dd_jefe.value,
                nombre_item=dd_loot.value,
                stats_jugador=stats,
                usar_pity=switch_pity.value
            )

            if "error" in resultado:
                log(f"[ERROR] {resultado['error']}", "#ef4444", True)
                return

            # ═══ Header ═══
            log(f"⚔️ {resultado.get('monstruo')}  →  🎯 {resultado.get('item')}", "#06b6d4", True)
            log(f"🎲 Drop Rate: {resultado.get('prob_formato')}  |  "
                f"⏱️ {resultado.get('tiempo_por_caza_seg'):.1f}s por kill")
            log("━" * 50, "#1e293b")

            # ═══ Estadística Teórica ═══
            log("📊 ESTADÍSTICA TEÓRICA (90% Certeza):", "#f59e0b", True)
            log(f"   Kills necesarios: {resultado['teorico']['intentos_90']}")
            log(f"   Horas de farmeo: {resultado['teorico']['tiempo_total_horas']} hrs")
            log("━" * 50, "#1e293b")

            # ═══ Simulación ═══
            log("🎮 SIMULACIÓN DE ESTA SESIÓN:", "#a855f7", True)
            log(f"   Drop obtenido en el Kill #{resultado['simulacion']['intentos']}")
            log(f"   Horas farmeadas: {resultado['simulacion']['tiempo_total_horas']} hrs")

            # ═══ Pity — SOLO se muestra cuando está activado ═══
            if switch_pity.value:
                log("━" * 50, "#1e293b")
                log("🎰 PITY SYSTEM [ACTIVO]:", "#f59e0b", True)
                log(f"   Probabilidad final alcanzada: "
                    f"{resultado['simulacion']['prob_final_alcanzada']}%")

            # ═══ Registro en Servidor (Cola FIFO + ABB) ═══
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

            # ═══ Inventario (Tabla Hash) ═══
            log("━" * 50, "#1e293b")
            log("🎒 INVENTARIO ACTUALIZADO:", "#f59e0b", True)
            log(f"   {nombre_item} ×{nueva_cant}  |  "
                f"Tipos: {inventario.total_tipos()}  |  Total: {inventario.total_items()}")

        except Exception:
            log(f"[ERROR DEL SISTEMA]\n{traceback.format_exc()}", "#ef4444", True)

    # ══════════════════════════════════════════
    # DIÁLOGO CRUD — Crear Jefes + Añadir Ítems
    # ══════════════════════════════════════════
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

        txt_item = ft.TextField(label="Nombre del Ítem", width=220, border_color="#1e3a5f")
        txt_prob_x = ft.TextField(
            label="1/X (número)", value="50", width=90, border_color="#1e3a5f"
        )

        # Lista visual de ítems añadidos en esta sesión del diálogo
        items_lista = ft.ListView(spacing=3, height=70)
        lbl_items_count = ft.Text("Ítems añadidos: 0", color="#64748b", size=11)
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

                hp_val = txt_hp.value or ""
                def_val = txt_def.value or ""

                motor.datos_mundo["zonas"][z_real]["monstruos"][j_id] = {
                    "nombre": j_id.replace("_", " ").title(),
                    "vida": int(hp_val) if hp_val.isdigit() else 100,
                    "defensa": int(def_val) if def_val.isdigit() else 10,
                    "loot": {}
                }

                motor.guardar_datos()
                cargar_zonas()

                # Forzar selección en dropdowns para que el nuevo jefe sea visible
                dd_zona.value = z_real
                dd_zona.update()
                on_zona_change(None)
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

        def guardar_item(e):
            """Añade un ítem al jefe. NO cierra el diálogo para permitir agregar varios seguidos."""
            try:
                z_id = (txt_nueva_zona.value or "").strip()
                j_id = (txt_nuevo_jefe.value or "").strip()
                item = (txt_item.value or "").strip()
                prob_val = (txt_prob_x.value or "").strip()

                if not z_id or not j_id or not item:
                    avisar("Llena Zona, Jefe y Nombre del ítem.", "#f59e0b")
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

                prob_x = int(prob_val) if prob_val.isdigit() else 0
                if prob_x <= 0:
                    avisar("La probabilidad debe ser un número mayor a 0.", "#ef4444")
                    return

                motor.datos_mundo["zonas"][z_real]["monstruos"][j_real].setdefault("loot", {})
                motor.datos_mundo["zonas"][z_real]["monstruos"][j_real]["loot"][item] = {
                    "item": item,
                    "probabilidad_x": prob_x,
                    "pity": {"probabilidad_incremento": (1.0 / prob_x) / 5}
                }
                motor.guardar_datos()

                # Actualizar dropdown si estamos viendo el mismo jefe
                if dd_zona.value == z_real and dd_jefe.value == j_real:
                    on_jefe_change(None)

                # Registro visual dentro del diálogo (NO cerrar, permitir más ítems)
                items_count[0] += 1
                items_lista.controls.append(
                    ft.Text(f"  ✅ {item} (1/{prob_x})", color="#22c55e", size=11)
                )
                lbl_items_count.value = f"Ítems añadidos: {items_count[0]}"
                items_lista.update()
                lbl_items_count.update()

                # Limpiar solo el campo de ítem, zona/jefe se mantienen
                txt_item.value = ""
                txt_item.update()

                avisar(f"'{item}' (1/{prob_x}) añadido a '{j_real}'.", "#22c55e")
            except Exception:
                avisar("Error al guardar ítem.", "#ef4444")
                log(f"[ERROR]\n{traceback.format_exc()}", "#ef4444")

        btn_guardar_jefe = ft.Button(
            content=ft.Text("💾 Crear Jefe", color="white"),
            bgcolor="#6366f1", on_click=guardar_jefe
        )
        btn_guardar_item = ft.Button(
            content=ft.Text("💎 Añadir Ítem", color="white"),
            bgcolor="#22c55e", on_click=guardar_item
        )

        vista_crear_jefe = ft.Column([
            ft.Text("IDs sin espacios. No importan mayúsculas/minúsculas.",
                    color="#f59e0b", size=11),
            txt_nueva_zona, txt_nuevo_jefe,
            ft.Row([txt_hp, txt_def]),
            btn_guardar_jefe
        ], spacing=10)

        vista_anadir_drops = ft.Column([
            ft.Text("Usa la misma Zona/Jefe. Puedes añadir varios ítems seguidos.",
                    color="#f59e0b", size=11),
            ft.Row([txt_item, txt_prob_x]),
            btn_guardar_item,
            ft.Divider(color="#1e293b"),
            lbl_items_count,
            items_lista
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
            ], width=420, height=400),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialogo())
            ]
        )
        page.show_dialog(dialogo_crud)
        page.update()

    def eliminar_jefe(e):
        try:
            z = dd_zona.value
            j = dd_jefe.value
            if z and j and j in motor.datos_mundo.get("zonas", {}).get(z, {}).get("monstruos", {}):
                del motor.datos_mundo["zonas"][z]["monstruos"][j]
                motor.guardar_datos()
                on_zona_change(None)
                log(f"❌ Jefe '{j}' eliminado de '{z}'.", "#ef4444", True)
            else:
                log("[AVISO] Selecciona un jefe válido para eliminarlo.", "#f59e0b")
        except Exception:
            log(f"[ERROR]\n{traceback.format_exc()}", "#ef4444")

    # ══════════════════════════════════════════
    # PANEL DE DATOS — Historial, Inventario, Ranking
    # ══════════════════════════════════════════
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

        # ═══ Pestaña 2: Inventario del Jugador (Tabla Hash) ═══
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

        # ═══ Pestaña 3: Ranking de Suerte (ABB In-Orden) ═══
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

        # ═══ Pestañas manuales ═══
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

    # ══════════════════════════════════════════
    # BOTONES PRINCIPALES
    # ══════════════════════════════════════════
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

    # ══════════════════════════════════════════
    # CONSTRUCCIÓN VISUAL — Modern Dark UI
    # ══════════════════════════════════════════
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

            ft.Row([btn_crud, btn_eliminar, btn_panel_datos], spacing=5),

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


if __name__ == "__main__":
    ft.run(main)