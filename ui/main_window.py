"""
main_window.py - Interfaz Gráfica con Navegación por Menús y Roles
Sistema de Control de Incidencias Ciudadanas
Tema: ttkbootstrap ('litera')

ARQUITECTURA DE NAVEGACIÓN Y ROLES:
1. Vista de Login Inicial: Selección de perfiles de prueba y asignación de roles.
2. Menú Principal por Pestañas (ttk.Notebook):
   - Pestaña 'Consultar Incidentes' (con filtrado por permisos puro vía StateManager).
   - Pestaña 'Registrar Incidente' (formulario con validación anti-spam).
   - Pestaña 'Modificar Incidentes' (exclusiva para roles 'Admin' y 'Gobierno';
     oculta/deshabilitada para el rol 'Comunidad').
3. Cero lógica de negocio en la UI: Toda consulta de datos para la tabla delega
   en `filtrar_por_permisos` a través de `StateManager`.
"""

import tkinter as tk
from typing import Dict, List, Optional
import ttkbootstrap as tb
from ttkbootstrap.constants import (
    BOTH, CENTER, DANGER, HORIZONTAL, INFO, LEFT, RIGHT,
    SUCCESS, VERTICAL, WARNING, W, X, Y
)
from ttkbootstrap.dialogs import Messagebox

from core.models import EstadoIncidente, Incidente, RolUsuario, TipoIncidente, Usuario
from ui.state_manager import StateManager


class MainWindow:
    """
    Ventana Principal con Sistema de Navegación, Gestión de Sesión y Control de Roles.
    """

    def __init__(self, state_manager: StateManager) -> None:
        self.state_manager = state_manager

        # Ventana principal
        self.root = tb.Window(
            title="Sistema de Control de Incidencias Ciudadanas - Gestión por Roles",
            themename="litera",
            size=(1200, 750),
            resizable=(True, True)
        )
        self.root.minsize(1000, 650)

        # Usuarios de prueba preconfigurados
        self.usuarios_demo: List[Usuario] = [
            Usuario(id=1, nombre="Admin General (Dpto. Central)", rol="Admin", sector="Todos"),
            Usuario(id=2, nombre="Dra. Gómez (Secretaría de Tránsito)", rol="Gobierno", sector="Distrito"),
            Usuario(id=3, nombre="Carlos Vega (Vecino Líder)", rol="Comunidad", sector="Sector Norte"),
            Usuario(id=4, nombre="Mariana Ruiz (Vecina Centro)", rol="Comunidad", sector="Sector Centro"),
            Usuario(id=5, nombre="Jorge Castro (Vecino Sur)", rol="Comunidad", sector="Sector Sur"),
        ]

        # Variables reactivas de Tkinter
        self.var_usuario_combo = tk.StringVar()
        self.var_info_usuario = tk.StringVar()

        # Variables de registro
        self.var_reg_sector = tk.StringVar()
        self.var_reg_tipo = tk.StringVar(value="Choque")

        # Variables de filtrado en tabla
        self.var_filtro_sector = tk.StringVar()
        self.var_filtro_activo_texto = tk.StringVar(value="Filtro: Todos")
        self.var_prioridad_total_texto = tk.StringVar(value="Prioridad Acumulada: 0")
        self.var_conteo_incidentes_texto = tk.StringVar(value="Total Visibles: 0")

        # Variables de modificación (Admin/Gobierno)
        self.var_mod_id = tk.StringVar()
        self.var_mod_estado = tk.StringVar(value="Reportado")
        self.var_mod_prioridad = tk.IntVar(value=1)

        # Contenedores raíz para navegación (Login vs App Principal)
        self.contenedor_login = tb.Frame(self.root)
        self.contenedor_principal = tb.Frame(self.root)

        # Construcción de vistas
        self._construir_vista_login()
        self._construir_vista_principal()

        # Suscripción al StateManager (Observer)
        self.state_manager.suscribir(self.refrescar_ui)

        # Iniciar en la pantalla de Login
        self.mostrar_vista_login()

    # ========================================================================
    # NAVEGACIÓN: ALTERNANCIA ENTRE VISTAS
    # ========================================================================

    def mostrar_vista_login(self) -> None:
        """Muestra la vista de autenticación y oculta la vista principal."""
        self.contenedor_principal.pack_forget()
        self.contenedor_login.pack(fill=BOTH, expand=True)

    def mostrar_vista_principal(self) -> None:
        """Muestra el menú principal por pestañas y oculta el login."""
        self.contenedor_login.pack_forget()
        self.contenedor_principal.pack(fill=BOTH, expand=True)
        self._aplicar_permisos_interfaz()
        self.refrescar_ui()

    # ========================================================================
    # 1. VISTA DE LOGIN (AUTENTICACIÓN)
    # ========================================================================

    def _construir_vista_login(self) -> None:
        """Construye la tarjeta central de inicio de sesión."""
        login_wrapper = tb.Frame(self.contenedor_login, padding=40)
        login_wrapper.place(relx=0.5, rely=0.5, anchor=CENTER)

        card = tb.Labelframe(
            login_wrapper,
            text="🔐 Autenticación y Selección de Rol",
            padding=30,
            bootstyle="primary"
        )
        card.pack(fill=BOTH, expand=True)

        tb.Label(
            card,
            text="Sistema de Control de Incidencias Ciudadanas",
            font=("Segoe UI", 16, "bold"),
            bootstyle="primary"
        ).pack(pady=(0, 5))

        tb.Label(
            card,
            text="Seleccione un perfil de usuario para validar el control de acceso basado en roles (RBAC):",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(pady=(0, 20))

        # Selector de usuario
        tb.Label(card, text="Usuario y Rol del Sistema:", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(0, 5))

        opciones_usuarios = [
            f"{u.id}. {u.nombre} [{u.rol}] - Sector: {u.sector}"
            for u in self.usuarios_demo
        ]
        self.combo_usuarios = tb.Combobox(
            card,
            textvariable=self.var_usuario_combo,
            values=opciones_usuarios,
            state="readonly",
            width=50,
            bootstyle="info"
        )
        self.combo_usuarios.pack(fill=X, pady=(0, 15))
        self.combo_usuarios.current(0)
        self.combo_usuarios.bind("<<ComboboxSelected>>", self._on_cambio_usuario_seleccionado)

        # Panel de detalles de privilegios
        self.lbl_detalles_rol = tb.Label(
            card,
            textvariable=self.var_info_usuario,
            font=("Segoe UI", 9, "italic"),
            bootstyle="info",
            wraplength=420,
            justify=LEFT
        )
        self.lbl_detalles_rol.pack(fill=X, pady=(0, 20))
        self._actualizar_info_rol(self.usuarios_demo[0])

        # Botón Ingresar
        btn_ingresar = tb.Button(
            card,
            text="🚀 Ingresar al Sistema",
            bootstyle="primary",
            command=self._on_iniciar_sesion
        )
        btn_ingresar.pack(fill=X, ipady=5)

    def _on_cambio_usuario_seleccionado(self, event=None) -> None:
        """Actualiza la descripción de privilegios según el usuario elegido."""
        idx = self.combo_usuarios.current()
        if 0 <= idx < len(self.usuarios_demo):
            self._actualizar_info_rol(self.usuarios_demo[idx])

    def _actualizar_info_rol(self, usuario: Usuario) -> None:
        """Genera el texto descriptivo de los privilegios del rol."""
        if usuario.rol == "Admin":
            texto = "👑 Privilegios: Acceso global a todos los sectores. Puede registrar, votar y modificar cualquier incidente."
        elif usuario.rol == "Gobierno":
            texto = "🏛️ Privilegios: Supervisión distrital completa. Puede registrar, votar y resolver/modificar incidencias de la ciudad."
        else:
            texto = f"🏘️ Privilegios: Restringido a '{usuario.sector}'. Solo puede ver incidentes de su sector, registrar y adherir votos comunitarios."
        self.var_info_usuario.set(texto)

    def _on_iniciar_sesion(self) -> None:
        """Inicia sesión con el usuario elegido y transiciona a la vista principal."""
        idx = self.combo_usuarios.current()
        if not (0 <= idx < len(self.usuarios_demo)):
            Messagebox.show_warning("Seleccione un usuario válido.", title="Atención")
            return

        usuario_elegido = self.usuarios_demo[idx]
        self.state_manager.iniciar_sesion(usuario_elegido)
        self.mostrar_vista_principal()

    # ========================================================================
    # 2. VISTA PRINCIPAL (MENÚ CON PESTAÑAS TTK.NOTEBOOK)
    # ========================================================================

    def _construir_vista_principal(self) -> None:
        """Construye el menú principal por pestañas."""
        # 1. Encabezado con información de sesión
        self._crear_encabezado_sesion()

        # 2. Menú de Pestañas (Notebook)
        self.notebook = tb.Notebook(self.contenedor_principal, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=True, padx=15, pady=10)

        # Pestaña 1: Consultar / Ver Incidentes
        self.tab_consultar = tb.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_consultar, text="📋 Consultar Incidentes")
        self._construir_pestana_consultar(self.tab_consultar)

        # Pestaña 2: Registrar Incidente
        self.tab_registrar = tb.Frame(self.notebook, padding=25)
        self.notebook.add(self.tab_registrar, text="📝 Registrar Incidente")
        self._construir_pestana_registrar(self.tab_registrar)

        # Pestaña 3: Modificar Incidente (Condicional a Roles)
        self.tab_modificar = tb.Frame(self.notebook, padding=25)
        # Se agregará o removerá dinámicamente según 'puede_modificar'
        self._construir_pestana_modificar(self.tab_modificar)

        # 3. Barra de estado inferior
        self._crear_barra_estado()

    def _crear_encabezado_sesion(self) -> None:
        """Banner superior con identificación de sesión y botón de desconexión."""
        header = tb.Frame(self.contenedor_principal, bootstyle="primary", padding=(20, 12))
        header.pack(fill=X)

        tb.Label(
            header,
            text="🏛️ Sistema de Control de Incidencias Ciudadanas",
            font=("Segoe UI", 15, "bold"),
            bootstyle="inverse-primary"
        ).pack(side=LEFT)

        # Contenedor de usuario a la derecha
        box_derecha = tb.Frame(header, bootstyle="primary")
        box_derecha.pack(side=RIGHT)

        self.lbl_sesion_info = tb.Label(
            box_derecha,
            text="",
            font=("Segoe UI", 9, "bold"),
            bootstyle="inverse-primary",
            padding=(10, 4)
        )
        self.lbl_sesion_info.pack(side=LEFT, padx=10)

        btn_logout = tb.Button(
            box_derecha,
            text="🚪 Cerrar Sesión",
            bootstyle="danger-outline",
            command=self._on_cerrar_sesion
        )
        btn_logout.pack(side=RIGHT)

    def _on_cerrar_sesion(self) -> None:
        """Cierra la sesión y retorna a la vista de login."""
        self.state_manager.cerrar_sesion()
        self.mostrar_vista_login()

    # ========================================================================
    # PESTAÑA 1: CONSULTAR INCIDENTES (TABLA Y FILTROS)
    # ========================================================================

    def _construir_pestana_consultar(self, parent: tb.Frame) -> None:
        """Construye la vista de consulta tabular."""
        # Barra superior de filtros y métricas
        barra_herramientas = tb.Labelframe(parent, text="🔍 Filtros Territoriales y Métricas", padding=10, bootstyle="info")
        barra_herramientas.pack(fill=X, pady=(0, 10))

        tb.Label(barra_herramientas, text="Sector:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(0, 5))
        entry_filtro = tb.Entry(barra_herramientas, textvariable=self.var_filtro_sector, width=18, bootstyle="info")
        entry_filtro.pack(side=LEFT, padx=(0, 8))

        tb.Button(
            barra_herramientas,
            text="Filtrar Sector",
            bootstyle="info-outline",
            command=self._on_aplicar_filtro
        ).pack(side=LEFT, padx=3)

        tb.Button(
            barra_herramientas,
            text="Ver Todos",
            bootstyle="secondary-outline",
            command=self._on_limpiar_filtro
        ).pack(side=LEFT, padx=3)

        tb.Button(
            barra_herramientas,
            text="📑 Ver Resúmenes (map)",
            bootstyle="secondary",
            command=self._on_mostrar_resumenes_map
        ).pack(side=LEFT, padx=8)

        # Badges métricos a la derecha
        tb.Label(
            barra_herramientas,
            textvariable=self.var_prioridad_total_texto,
            font=("Segoe UI", 9, "bold"),
            bootstyle="info",
            padding=(6, 2)
        ).pack(side=RIGHT, padx=4)

        tb.Label(
            barra_herramientas,
            textvariable=self.var_filtro_activo_texto,
            font=("Segoe UI", 9, "bold"),
            bootstyle="secondary",
            padding=(6, 2)
        ).pack(side=RIGHT, padx=4)

        # Tabla Treeview
        frame_tabla = tb.Frame(parent)
        frame_tabla.pack(fill=BOTH, expand=True)

        columnas = ("id", "sector", "tipo", "prioridad", "estado", "departamento", "descripcion")
        self.tree = tb.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            bootstyle="primary",
            selectmode="browse"
        )

        self.tree.heading("id", text="ID", anchor=W)
        self.tree.heading("sector", text="Sector", anchor=W)
        self.tree.heading("tipo", text="Tipo", anchor=W)
        self.tree.heading("prioridad", text="Prioridad", anchor=W)
        self.tree.heading("estado", text="Estado", anchor=W)
        self.tree.heading("departamento", text="Dpto. Responsable", anchor=W)
        self.tree.heading("descripcion", text="Descripción", anchor=W)

        self.tree.column("id", width=45, minwidth=40, stretch=False)
        self.tree.column("sector", width=120, minwidth=100)
        self.tree.column("tipo", width=110, minwidth=90)
        self.tree.column("prioridad", width=75, minwidth=60, stretch=False)
        self.tree.column("estado", width=95, minwidth=80, stretch=False)
        self.tree.column("departamento", width=220, minwidth=180)
        self.tree.column("descripcion", width=360, minwidth=200)

        scroll_y = tb.Scrollbar(frame_tabla, orient=VERTICAL, command=self.tree.yview)
        scroll_x = tb.Scrollbar(frame_tabla, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_x.pack(side=tk.BOTTOM, fill=X)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=RIGHT, fill=Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Barra de acciones inferiores
        barra_acciones = tb.Frame(parent, padding=(0, 10))
        barra_acciones.pack(fill=X)

        tb.Button(
            barra_acciones,
            text="👍 Adherir Voto (+1 Prioridad)",
            bootstyle="success",
            command=self._on_adherir_voto
        ).pack(side=LEFT)

        tb.Label(
            barra_acciones,
            text="ℹ️ Los incidentes mostrados respetan el filtrado puro por permisos (filtrar_por_permisos).",
            font=("Segoe UI", 8, "italic"),
            bootstyle="secondary"
        ).pack(side=RIGHT)

    # ========================================================================
    # PESTAÑA 2: REGISTRAR INCIDENTE (FORMULARIO)
    # ========================================================================

    def _construir_pestana_registrar(self, parent: tb.Frame) -> None:
        """Construye el formulario dedicado de registro de incidencias."""
        card_form = tb.Labelframe(
            parent,
            text="📝 Formulario de Nuevo Reporte Ciudadano",
            padding=25,
            bootstyle="info"
        )
        card_form.pack(fill=BOTH, expand=True)

        tb.Label(card_form, text="Sector Territorial:", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(0, 4))
        sectores = ["Sector Norte", "Sector Centro", "Sector Sur", "Sector Occidental", "Sector Oriental"]
        self.combo_reg_sector = tb.Combobox(
            card_form,
            textvariable=self.var_reg_sector,
            values=sectores,
            bootstyle="info",
            width=40
        )
        self.combo_reg_sector.pack(fill=X, pady=(0, 15))

        tb.Label(card_form, text="Tipo de Incidente (Sum Type):", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(0, 4))
        tipos = ["Choque", "FallaElectrica", "Alcantarillado"]
        self.combo_reg_tipo = tb.Combobox(
            card_form,
            textvariable=self.var_reg_tipo,
            values=tipos,
            state="readonly",
            bootstyle="info",
            width=40
        )
        self.combo_reg_tipo.pack(fill=X, pady=(0, 15))

        tb.Label(card_form, text="Descripción Detallada:", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(0, 4))
        self.txt_reg_descripcion = tb.Text(card_form, height=6, font=("Segoe UI", 10), wrap="word")
        self.txt_reg_descripcion.pack(fill=BOTH, expand=True, pady=(0, 20))

        btn_guardar = tb.Button(
            card_form,
            text="➕ Registrar Incidente en el Sistema",
            bootstyle="primary",
            command=self._on_registrar_incidente
        )
        btn_guardar.pack(fill=X, ipady=6)

    # ========================================================================
    # PESTAÑA 3: MODIFICAR INCIDENTE (EXCLUSIVA ADMIN / GOBIERNO)
    # ========================================================================

    def _construir_pestana_modificar(self, parent: tb.Frame) -> None:
        """Construye la pestaña de gestión de estado (oculta para Comunidad)."""
        card_mod = tb.Labelframe(
            parent,
            text="⚙️ Gestión y Modificación Oficial de Incidencias (Admin / Gobierno)",
            padding=25,
            bootstyle="warning"
        )
        card_mod.pack(fill=BOTH, expand=True)

        tb.Label(
            card_mod,
            text="⚠️ Esta sección permite cambiar el ciclo de vida y prioridad de incidencias. Restringida por rol.",
            font=("Segoe UI", 9, "bold"),
            bootstyle="warning"
        ).pack(anchor=W, pady=(0, 20))

        # ID del incidente a modificar
        tb.Label(card_mod, text="ID del Incidente:", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(0, 4))
        entry_id = tb.Entry(card_mod, textvariable=self.var_mod_id, state="readonly", width=20, bootstyle="secondary")
        entry_id.pack(anchor=W, pady=(0, 15))

        # Nuevo Estado
        tb.Label(card_mod, text="Estado del Incidente:", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(0, 4))
        estados_disponibles = ["Reportado", "EnProceso", "Resuelto", "Descartado"]
        self.combo_mod_estado = tb.Combobox(
            card_mod,
            textvariable=self.var_mod_estado,
            values=estados_disponibles,
            state="readonly",
            bootstyle="warning",
            width=30
        )
        self.combo_mod_estado.pack(anchor=W, pady=(0, 15))

        # Nivel de Prioridad
        tb.Label(card_mod, text="Nivel de Prioridad (1 a 10):", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(0, 4))
        spin_prioridad = tb.Spinbox(
            card_mod,
            from_=1,
            to=10,
            textvariable=self.var_mod_prioridad,
            width=15,
            bootstyle="warning"
        )
        spin_prioridad.pack(anchor=W, pady=(0, 25))

        btn_aplicar_mod = tb.Button(
            card_mod,
            text="💾 Guardar Cambios Oficiales",
            bootstyle="warning",
            command=self._on_aplicar_modificacion
        )
        btn_aplicar_mod.pack(fill=X, ipady=6)

    # ========================================================================
    # GESTIÓN DINÁMICA DE PERMISOS EN LA INTERFAZ
    # ========================================================================

    def _aplicar_permisos_interfaz(self) -> None:
        """
        Regla de Negocio:
        Oculta o deshabilita la pestaña de 'Modificar' si el usuario tiene rol 'Comunidad'.
        """
        usuario = self.state_manager.usuario_actual
        if usuario is None:
            return

        # Actualización del badge de sesión
        self.lbl_sesion_info.config(text=f"👤 {usuario.nombre} | Rol: {usuario.rol} | Sector: {usuario.sector}")

        # Configuración por defecto del sector en el formulario de registro
        if usuario.rol == "Comunidad":
            self.var_reg_sector.set(usuario.sector)
        else:
            self.var_reg_sector.set("Sector Norte")

        # Control de visualización de la pestaña de modificación
        tabs_actuales = self.notebook.tabs()
        tab_mod_id = str(self.tab_modificar)

        if self.state_manager.puede_modificar:
            # Si tiene permisos y no está agregada, agregarla
            if tab_mod_id not in tabs_actuales:
                self.notebook.add(self.tab_modificar, text="⚙️ Modificar Incidentes")
        else:
            # Si es Comunidad, ocultar/remover la pestaña
            if tab_mod_id in tabs_actuales:
                self.notebook.forget(self.tab_modificar)

    def _crear_barra_estado(self) -> None:
        """Barra inferior con indicadores de estado."""
        status_bar = tb.Frame(self.contenedor_principal, padding=(15, 6), bootstyle="light")
        status_bar.pack(fill=X, side=tk.BOTTOM)

        lbl_conteo = tb.Label(
            status_bar,
            textvariable=self.var_conteo_incidentes_texto,
            font=("Segoe UI", 9)
        )
        lbl_conteo.pack(side=LEFT)

        lbl_arquitectura = tb.Label(
            status_bar,
            font=("Segoe UI", 8, "italic"),
            bootstyle="secondary"
        )
        lbl_arquitectura.pack(side=RIGHT)

    # ========================================================================
    # CALLBACKS DE ACCIONES (DELEGAN ESTRICTAMENTE AL STATE_MANAGER)
    # ========================================================================

    def _on_registrar_incidente(self) -> None:
        sector = self.var_reg_sector.get().strip()
        tipo = self.var_reg_tipo.get().strip()
        descripcion = self.txt_reg_descripcion.get("1.0", tk.END).strip()

        if not sector:
            Messagebox.show_warning("El sector territorial es requerido.", title="Validación")
            return
        if not descripcion:
            Messagebox.show_warning("La descripción no puede estar vacía.", title="Validación")
            return

        exito, mensaje = self.state_manager.agregar_incidente(sector, descripcion, tipo)  # type: ignore

        if exito:
            Messagebox.show_info(mensaje, title="Registro Exitoso")
            self.txt_reg_descripcion.delete("1.0", tk.END)
            # Cambiar a la pestaña de consulta para ver el registro
            self.notebook.select(self.tab_consultar)
        else:
            Messagebox.show_error(mensaje, title="Rechazado por Validación Funcional")

    def _on_adherir_voto(self) -> None:
        seleccion = self.tree.selection()
        if not seleccion:
            Messagebox.show_warning("Seleccione un incidente de la tabla para votar.", title="Atención")
            return

        item = self.tree.item(seleccion[0])
        incidente_id = int(item["values"][0])

        exito, mensaje = self.state_manager.adherir_voto(incidente_id, incremento=1)
        if exito:
            self._seleccionar_por_id(incidente_id)
        else:
            Messagebox.show_error(mensaje, title="Error")

    def _on_tree_select(self, event=None) -> None:
        """Carga los datos del incidente seleccionado en el formulario de modificación."""
        seleccion = self.tree.selection()
        if seleccion:
            item = self.tree.item(seleccion[0])
            valores = item["values"]
            self.var_mod_id.set(str(valores[0]))
            # Prioridad limpia (quitar el icono de estrella)
            raw_prio = str(valores[3]).replace("★", "").strip()
            self.var_mod_prioridad.set(int(raw_prio))
            self.var_mod_estado.set(str(valores[4]))

    def _on_aplicar_modificacion(self) -> None:
        """Aplica cambios sobre un incidente (Solo Admin/Gobierno)."""
        if not self.var_mod_id.get():
            Messagebox.show_warning(
                "Seleccione primero un incidente en la pestaña 'Consultar' para modificarlo.",
                title="Atención"
            )
            return

        incidente_id = int(self.var_mod_id.get())
        nuevo_estado = self.var_mod_estado.get()
        nueva_prio = self.var_mod_prioridad.get()

        exito, mensaje = self.state_manager.modificar_incidente(
            incidente_id=incidente_id,
            nuevo_estado=nuevo_estado,  # type: ignore
            nueva_prioridad=nueva_prio
        )

        if exito:
            Messagebox.show_info(mensaje, title="Modificación Exitosa")
            self.notebook.select(self.tab_consultar)
        else:
            Messagebox.show_error(mensaje, title="Error en Modificación")

    def _on_aplicar_filtro(self) -> None:
        sector = self.var_filtro_sector.get().strip()
        if not sector:
            Messagebox.show_warning("Ingrese el sector que desea filtrar.", title="Filtro")
            return
        self.state_manager.aplicar_filtro_sector(sector)

    def _on_limpiar_filtro(self) -> None:
        self.var_filtro_sector.set("")
        self.state_manager.limpiar_filtro()

    def _on_mostrar_resumenes_map(self) -> None:
        sector = self.state_manager.filtro_sector_actual
        if not sector:
            Messagebox.show_info(
                "Aplique primero un filtro por sector para proyectar sus resúmenes con map().",
                title="Resúmenes por Sector"
            )
            return

        resumenes = self.state_manager.obtener_resumenes_sector()
        if not resumenes:
            Messagebox.show_info(f"No hay incidentes visibles en '{sector}'.", title="Sin Resultados")
            return

        texto = "\n".join(f"• {r}" for r in resumenes)
        Messagebox.show_info(
            f"Resúmenes procesados con map() para '{sector}':\n\n{texto}",
            title=f"Resumen Funcional: {sector}"
        )

    # ========================================================================
    # ACTUALIZACIÓN REACTIVA DE LA VISTA
    # ========================================================================

    def refrescar_ui(self) -> None:
        """
        Reconstruye la vista de la tabla consultando los incidentes permitidos
        a través de 'state_manager.obtener_incidentes_visibles()'.
        """
        for item in self.tree.get_children():
            self.tree.delete(item)

        # DELEGACIÓN AL STATE MANAGER (QUE EJECUTA filtrar_por_permisos)
        incidentes_visibles = self.state_manager.obtener_incidentes_visibles()

        for inc in incidentes_visibles:
            dpto = self.state_manager.obtener_info_departamento(inc)
            self.tree.insert(
                "",
                tk.END,
                values=(
                    inc.id,
                    inc.sector,
                    inc.tipo_incidente,
                    f"★ {inc.nivel_prioridad}",
                    inc.estado,
                    dpto,
                    inc.descripcion
                )
            )

        filtro_actual = self.state_manager.filtro_sector_actual
        self.var_filtro_activo_texto.set(f"Filtro: {filtro_actual}" if filtro_actual else "Filtro: Todos")

        prioridad_total = self.state_manager.obtener_prioridad_total_visible()
        self.var_prioridad_total_texto.set(f"Prioridad Total (Reduce): {prioridad_total}")
        self.var_conteo_incidentes_texto.set(f"Total Incidentes Visibles: {len(incidentes_visibles)}")

    def _seleccionar_por_id(self, incidente_id: int) -> None:
        for item in self.tree.get_children():
            valores = self.tree.item(item, "values")
            if valores and int(valores[0]) == incidente_id:
                self.tree.selection_set(item)
                self.tree.focus(item)
                break

    def iniciar(self) -> None:
        self.root.mainloop()
