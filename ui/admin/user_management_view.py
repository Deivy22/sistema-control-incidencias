"""
user_management_view.py - Apartado Exclusivo del Administrador para Crear Usuarios
Sistema de Control de Incidencias Ciudadanas
Estilo: Paleta Pastel (Soft Sand & Peachy Delight)

Este módulo implementa el panel exclusivo para administradores que permite:
1. Crear nuevos usuarios con validación pura (nombre, username único, password, rol y sector).
2. Consultar el listado de usuarios actualmente registrados en el sistema.
3. Restricción estricta de acceso: Solo usuarios con rol 'Admin' pueden interactuar con este panel.
"""

import tkinter as tk
from typing import Optional
import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, LEFT, RIGHT, VERTICAL, W, X, Y
from ttkbootstrap.dialogs import Messagebox

from ui.state_manager import StateManager


class UserManagementView(tb.Frame):
    """
    Vista administrativa exclusiva para la gestión y creación de usuarios.
    """

    def __init__(
        self,
        parent: tk.Widget,
        state_manager: StateManager
    ) -> None:
        super().__init__(parent, style="Pastel.TFrame")
        self.state_manager = state_manager

        # Variables reactivas para el formulario
        self.var_nombre = tk.StringVar()
        self.var_username = tk.StringVar()
        self.var_password = tk.StringVar()
        self.var_rol = tk.StringVar(value="Comunidad")
        self.var_sector = tk.StringVar(value="Sector Norte")
        self.var_mensaje = tk.StringVar()
        self.var_conteo_usuarios = tk.StringVar(value="Usuarios Registrados: 0")
        self.var_mostrar_pwd = tk.BooleanVar(value=False)

        self._construir_interfaz()
        self.refrescar_tabla()

    def _construir_interfaz(self) -> None:
        """Construye la interfaz gráfica de dos columnas (Formulario + Tabla de usuarios)."""
        # 1. Banner superior explicativo
        banner = tb.Labelframe(
            self,
            text="👑 Panel Exclusivo de Administración de Usuarios",
            padding=12,
            style="Pastel.TLabelframe"
        )
        banner.pack(fill=X, padx=15, pady=(10, 10))

        tb.Label(
            banner,
            text="Sección restringida exclusivamente al Administrador General. Permite dar de alta cuentas para "
                 "ciudadanos (Comunidad), funcionarios distritales (Gobierno) y administradores (Admin).",
            style="PastelMuted.TLabel"
        ).pack(anchor=W)

        # 2. Contenedor principal de dos paneles (Izquierda: Formulario | Derecha: Tabla)
        paneles = tb.Frame(self, style="Pastel.TFrame")
        paneles.pack(fill=BOTH, expand=True, padx=15, pady=(0, 10))

        # Panel Izquierdo: Formulario de Creación de Usuario
        panel_form = tb.Labelframe(
            paneles,
            text="📝 Crear Nuevo Usuario",
            padding=20,
            style="Pastel.TLabelframe",
            width=420
        )
        panel_form.pack(side=LEFT, fill=BOTH, padx=(0, 10))
        panel_form.pack_propagate(False)

        # Campo: Nombre Completo
        tb.Label(
            panel_form,
            text="Nombre Completo:",
            font=("Segoe UI", 9, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 2))

        self.entry_nombre = tb.Entry(
            panel_form,
            textvariable=self.var_nombre,
            font=("Segoe UI", 9)
        )
        self.entry_nombre.pack(fill=X, pady=(0, 10))

        # Campo: Nombre de Usuario (Login)
        tb.Label(
            panel_form,
            text="Nombre de Usuario (Login):",
            font=("Segoe UI", 9, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 2))

        self.entry_username = tb.Entry(
            panel_form,
            textvariable=self.var_username,
            font=("Segoe UI", 9)
        )
        self.entry_username.pack(fill=X, pady=(0, 10))

        # Campo: Contraseña
        tb.Label(
            panel_form,
            text="Contraseña Inicial:",
            font=("Segoe UI", 9, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 2))

        frame_pwd = tb.Frame(panel_form, style="Pastel.TFrame")
        frame_pwd.pack(fill=X, pady=(0, 10))

        self.entry_pwd = tb.Entry(
            frame_pwd,
            textvariable=self.var_password,
            show="*",
            font=("Segoe UI", 9)
        )
        self.entry_pwd.pack(side=LEFT, fill=X, expand=True)

        btn_ver_pwd = tb.Checkbutton(
            frame_pwd,
            text="👁️",
            variable=self.var_mostrar_pwd,
            command=self._toggle_ver_password,
            style="Pastel.TCheckbutton"
        )
        btn_ver_pwd.pack(side=RIGHT, padx=(6, 0))

        # Campo: Rol en el Sistema
        tb.Label(
            panel_form,
            text="Rol del Usuario (RBAC):",
            font=("Segoe UI", 9, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 2))

        roles_disponibles = ["Comunidad", "Gobierno", "Admin"]
        self.combo_rol = tb.Combobox(
            panel_form,
            textvariable=self.var_rol,
            values=roles_disponibles,
            state="readonly",
            font=("Segoe UI", 9)
        )
        self.combo_rol.pack(fill=X, pady=(0, 10))
        self.combo_rol.bind("<<ComboboxSelected>>", self._on_rol_cambiado)

        # Campo: Sector Territorial
        tb.Label(
            panel_form,
            text="Sector Territorial:",
            font=("Segoe UI", 9, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 2))

        self.sectores_disponibles = [
            "Sector Norte",
            "Sector Centro",
            "Sector Sur",
            "Sector Occidental",
            "Sector Oriental",
            "Distrito",
            "Todos"
        ]
        self.combo_sector = tb.Combobox(
            panel_form,
            textvariable=self.var_sector,
            values=self.sectores_disponibles,
            font=("Segoe UI", 9)
        )
        self.combo_sector.pack(fill=X, pady=(0, 15))

        # Label de estado/feedback
        self.lbl_feedback = tb.Label(
            panel_form,
            textvariable=self.var_mensaje,
            wraplength=360,
            font=("Segoe UI", 8, "bold"),
            style="Pastel.TLabel"
        )
        self.lbl_feedback.pack(fill=X, pady=(0, 10))

        # Botones de Acción
        btn_crear = tb.Button(
            panel_form,
            text="➕ Registrar Usuario",
            style="PastelPeach.TButton",
            command=self._on_crear_usuario
        )
        btn_crear.pack(fill=X, ipady=3, pady=(0, 6))

        btn_limpiar = tb.Button(
            panel_form,
            text="🧹 Limpiar Campos",
            style="PastelNeutral.TButton",
            command=self._limpiar_formulario
        )
        btn_limpiar.pack(fill=X, ipady=2)

        # Panel Derecho: Listado de Usuarios Registrados
        panel_tabla = tb.Labelframe(
            paneles,
            text="👥 Usuarios Registrados en el Sistema",
            padding=15,
            style="Pastel.TLabelframe"
        )
        panel_tabla.pack(side=RIGHT, fill=BOTH, expand=True)

        # Barra superior con métrica y botón de recarga
        barra_info = tb.Frame(panel_tabla, style="Pastel.TFrame")
        barra_info.pack(fill=X, pady=(0, 8))

        tb.Label(
            barra_info,
            textvariable=self.var_conteo_usuarios,
            style="PastelBadge.TLabel"
        ).pack(side=LEFT)

        tb.Button(
            barra_info,
            text="🔄 Actualizar",
            style="PastelNeutral.TButton",
            command=self.refrescar_tabla
        ).pack(side=RIGHT)

        # Treeview de usuarios
        frame_tree = tb.Frame(panel_tabla, style="Pastel.TFrame")
        frame_tree.pack(fill=BOTH, expand=True)

        columnas = ("id", "username", "nombre", "rol", "sector")
        self.tree_usuarios = tb.Treeview(
            frame_tree,
            columns=columnas,
            show="headings",
            style="Pastel.Treeview",
            selectmode="browse"
        )

        self.tree_usuarios.heading("id", text="ID", anchor=W)
        self.tree_usuarios.heading("username", text="Usuario", anchor=W)
        self.tree_usuarios.heading("nombre", text="Nombre Completo", anchor=W)
        self.tree_usuarios.heading("rol", text="Rol", anchor=W)
        self.tree_usuarios.heading("sector", text="Sector Asignado", anchor=W)

        self.tree_usuarios.column("id", width=45, minwidth=40, stretch=False)
        self.tree_usuarios.column("username", width=120, minwidth=90)
        self.tree_usuarios.column("nombre", width=180, minwidth=130)
        self.tree_usuarios.column("rol", width=95, minwidth=80, stretch=False)
        self.tree_usuarios.column("sector", width=130, minwidth=100)

        scroll_y = tb.Scrollbar(frame_tree, orient=VERTICAL, command=self.tree_usuarios.yview)
        self.tree_usuarios.configure(yscrollcommand=scroll_y.set)

        self.tree_usuarios.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=RIGHT, fill=Y)

    def _toggle_ver_password(self) -> None:
        """Alterna la visibilidad de la contraseña en el campo de texto."""
        if self.var_mostrar_pwd.get():
            self.entry_pwd.configure(show="")
        else:
            self.entry_pwd.configure(show="*")

    def _on_rol_cambiado(self, event=None) -> None:
        """Adapta automáticamente el sector sugerido según el rol seleccionado."""
        rol = self.var_rol.get()
        if rol == "Admin":
            self.var_sector.set("Todos")
        elif rol == "Gobierno":
            self.var_sector.set("Distrito")
        elif rol == "Comunidad" and self.var_sector.get() in ("Todos", "Distrito"):
            self.var_sector.set("Sector Norte")

    def _on_crear_usuario(self) -> None:
        """Procesa la solicitud de creación de usuario delegando en el StateManager."""
        if not self.state_manager.puede_administrar_usuarios:
            Messagebox.show_warning(
                "Solo los administradores tienen permiso para crear nuevos usuarios.",
                title="Acceso Denegado"
            )
            return

        nombre = self.var_nombre.get().strip()
        username = self.var_username.get().strip()
        pwd = self.var_password.get().strip()
        rol = self.var_rol.get().strip()
        sector = self.var_sector.get().strip()

        exito, mensaje = self.state_manager.crear_usuario(
            username=username,
            password=pwd,
            nombre=nombre,
            rol=rol,
            sector=sector
        )

        if exito:
            self.lbl_feedback.configure(foreground="#2E7D32")
            self.var_mensaje.set(f"✅ {mensaje}")
            Messagebox.show_info(mensaje, title="Usuario Registrado")
            self._limpiar_formulario()
            self.refrescar_tabla()
        else:
            self.lbl_feedback.configure(foreground="#D9534F")
            self.var_mensaje.set(f"❌ {mensaje}")

    def _limpiar_formulario(self) -> None:
        """Limpia los campos del formulario."""
        self.var_nombre.set("")
        self.var_username.set("")
        self.var_password.set("")
        self.var_rol.set("Comunidad")
        self.var_sector.set("Sector Norte")
        self.entry_pwd.configure(show="*")
        self.var_mostrar_pwd.set(False)

    def refrescar_tabla(self) -> None:
        """Recarga el listado de usuarios desde el StateManager."""
        for item in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(item)

        usuarios = self.state_manager.obtener_usuarios()
        for u in usuarios:
            self.tree_usuarios.insert(
                "",
                tk.END,
                values=(
                    u.get("id", ""),
                    u.get("username", ""),
                    u.get("nombre", ""),
                    u.get("rol", ""),
                    u.get("sector", "")
                )
            )

        self.var_conteo_usuarios.set(f"Total Usuarios Registrados: {len(usuarios)}")

