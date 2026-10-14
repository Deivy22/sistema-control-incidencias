"""
login_view.py - Pantalla Real de Autenticación de Usuario
Sistema de Control de Incidencias Ciudadanas
Estilo: Paleta Pastel (Soft Sand & Peachy Delight)
"""

import tkinter as tk
from typing import Callable, Optional
import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, CENTER, LEFT, RIGHT, W, X
from ttkbootstrap.dialogs import Messagebox

from ui.state_manager import StateManager
from ui.styles import (
    COLOR_FONDO_GENERAL,
    COLOR_FONDO_TARJETA,
    COLOR_MELOCOTON_DELIGHT,
    COLOR_MELOCOTON_CALIDO,
    COLOR_TEXTO_OSCURO,
    COLOR_TEXTO_SECUNDARIO,
)


class LoginView(tb.Frame):
    """
    Vista de Login con campos de entrada reales de Usuario y Contraseña oculta.
    """

    def __init__(
        self,
        parent: tk.Widget,
        state_manager: StateManager,
        on_login_success: Callable[[], None]
    ) -> None:
        super().__init__(parent, style="Pastel.TFrame")
        self.state_manager = state_manager
        self.on_login_success = on_login_success

        self.var_usuario = tk.StringVar()
        self.var_password = tk.StringVar()
        self.var_mensaje_error = tk.StringVar()

        self._construir_interfaz()

    def _construir_interfaz(self) -> None:
        """Construye la tarjeta central de autenticación con estética pastel."""
        contenedor_central = tb.Frame(self, style="Pastel.TFrame")
        contenedor_central.place(relx=0.5, rely=0.5, anchor=CENTER)

        # Tarjeta de Login
        card = tb.Labelframe(
            contenedor_central,
            text="🔐 Acceso al Sistema Ciudadano",
            padding=35,
            style="Pastel.TLabelframe"
        )
        card.pack(fill=BOTH, expand=True)

        # Título
        tb.Label(
            card,
            text="Bienvenido al Sistema de Incidencias",
            font=("Segoe UI", 15, "bold"),
            style="Pastel.TLabel"
        ).pack(pady=(0, 4))

        tb.Label(
            card,
            text="Ingrese sus credenciales registradas para ingresar:",
            style="PastelMuted.TLabel"
        ).pack(pady=(0, 20))

        # Campo: Usuario
        tb.Label(
            card,
            text="Nombre de Usuario:",
            font=("Segoe UI", 10, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 4))

        self.entry_usuario = tb.Entry(
            card,
            textvariable=self.var_usuario,
            width=36,
            font=("Segoe UI", 10)
        )
        self.entry_usuario.pack(fill=X, pady=(0, 15))

        # Campo: Contraseña (con show="*")
        tb.Label(
            card,
            text="Contraseña:",
            font=("Segoe UI", 10, "bold"),
            style="Pastel.TLabel"
        ).pack(anchor=W, pady=(0, 4))

        self.entry_password = tb.Entry(
            card,
            textvariable=self.var_password,
            show="*",
            width=36,
            font=("Segoe UI", 10)
        )
        self.entry_password.pack(fill=X, pady=(0, 10))

        # Label de error reactivo
        lbl_error = tb.Label(
            card,
            textvariable=self.var_mensaje_error,
            foreground="#D9534F",
            font=("Segoe UI", 9, "bold"),
            wraplength=320,
            style="Pastel.TLabel"
        )
        lbl_error.pack(pady=(0, 10))

        # Botón Ingresar (Estilo Peachy Delight)
        btn_login = tb.Button(
            card,
            text="Ingresar al Sistema ➔",
            style="PastelPeach.TButton",
            command=self._on_submit_login
        )
        btn_login.pack(fill=X, ipady=4, pady=(0, 20))

        # Panel de Ayuda con Cuentas Demo
        frame_ayuda = tb.Labelframe(
            card,
            text="💡 Cuentas de Acceso Rápido",
            padding=12,
            style="Pastel.TLabelframe"
        )
        frame_ayuda.pack(fill=X)

        cuentas_demo = [
            ("admin", "admin123", "Admin (Global)"),
            ("gobierno", "gobierno123", "Gobierno (Distrital)"),
            ("carlos_norte", "comunidad123", "Comunidad (Sector Norte)"),
            ("mariana_centro", "comunidad123", "Comunidad (Sector Centro)"),
        ]

        for u, p, desc in cuentas_demo:
            btn_chip = tb.Button(
                frame_ayuda,
                text=f"{u} / {p} [{desc}]",
                style="PastelNeutral.TButton",
                command=lambda user=u, pwd=p: self._autocompletar(user, pwd)
            )
            btn_chip.pack(fill=X, pady=2)

        # Enlace de tecla Enter para iniciar sesión
        self.entry_password.bind("<Return>", lambda event: self._on_submit_login())
        self.entry_usuario.bind("<Return>", lambda event: self.entry_password.focus())

    def _autocompletar(self, user: str, pwd: str) -> None:
        """Autocompleta los campos para facilitar pruebas ágiles."""
        self.var_usuario.set(user)
        self.var_password.set(pwd)
        self.var_mensaje_error.set("")

    def _on_submit_login(self) -> None:
        """Procesa el intento de login delegando en el StateManager."""
        user = self.var_usuario.get().strip()
        pwd = self.var_password.get().strip()

        if not user or not pwd:
            self.var_mensaje_error.set("Por favor ingrese tanto el usuario como la contraseña.")
            return

        exito, mensaje = self.state_manager.autenticar(user, pwd)

        if exito:
            self.var_mensaje_error.set("")
            self.var_password.set("")
            self.on_login_success()
        else:
            self.var_mensaje_error.set(mensaje)
