"""
main_window.py - Contenedor Principal del Dashboard con Navegación por Pestañas
Sistema de Control de Incidencias Ciudadanas
Estilo: Paleta Pastel (Soft Sand & Soft Peachy Delight)

Solo se muestra tras un login exitoso.
Gestiona el ciclo de vida de los submódulos:
- /ui/incidents/list_view.py (Tabla de consulta)
- /ui/incidents/form_view.py (Formularios de creación y edición)
"""

import tkinter as tk
from typing import Callable, Optional
import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, LEFT, RIGHT, X
from ttkbootstrap.dialogs import Messagebox

from core.models import Incidente
from ui.incidents.list_view import IncidentesListView
from ui.incidents.form_view import IncidenteFormView
from ui.state_manager import StateManager


class MainWindow(tb.Frame):
    """
    Contenedor Principal del Dashboard post-autenticación.
    """

    def __init__(
        self,
        parent: tk.Widget,
        state_manager: StateManager,
        on_logout: Callable[[], None]
    ) -> None:
        super().__init__(parent, style="Pastel.TFrame")
        self.state_manager = state_manager
        self.on_logout = on_logout

        self.var_usuario_badge = tk.StringVar()
        self._construir_interfaz()

        # Suscripción reactiva al StateManager
        self.state_manager.suscribir(self.refrescar_dashboard)
        self.refrescar_dashboard()

    def _construir_interfaz(self) -> None:
        """Construye el encabezado de sesión, el notebook pastel y la barra de estado."""
        # 1. Encabezado de Sesión Pastel
        header = tb.Frame(self, style="PastelCard.TFrame", padding=(20, 12))
        header.pack(fill=X)

        tb.Label(
            header,
            text="🏛️ Sistema de Control de Incidencias Ciudadanas",
            style="PastelHeader.TLabel"
        ).pack(side=LEFT)

        # Contenedor derecho (Usuario + Logout)
        box_derecha = tb.Frame(header, style="PastelCard.TFrame")
        box_derecha.pack(side=RIGHT)

        lbl_user = tb.Label(
            box_derecha,
            textvariable=self.var_usuario_badge,
            style="PastelBadge.TLabel"
        )
        lbl_user.pack(side=LEFT, padx=(0, 12))

        btn_logout = tb.Button(
            box_derecha,
            text="🚪 Cerrar Sesión",
            style="PastelPeach.TButton",
            command=self._on_logout_click
        )
        btn_logout.pack(side=RIGHT)

        # 2. Notebook (Pestañas) Pastel
        self.notebook = tb.Notebook(self, style="Pastel.TNotebook")
        self.notebook.pack(fill=BOTH, expand=True, padx=15, pady=10)

        # Pestaña 1: Listado de Incidentes
        self.vista_lista = IncidentesListView(
            self.notebook,
            state_manager=self.state_manager,
            on_solicitar_edicion=self._on_solicitar_edicion
        )
        self.notebook.add(self.vista_lista, text="📋 Consultar Incidentes")

        # Pestaña 2: Formulario de Registro
        self.vista_crear = IncidenteFormView(
            self.notebook,
            state_manager=self.state_manager,
            modo="crear",
            on_accion_completada=self._on_registro_completado
        )
        self.notebook.add(self.vista_crear, text="📝 Registrar Incidente")

        # Pestaña 3: Formulario de Edición (Condicional a Roles)
        self.vista_editar = IncidenteFormView(
            self.notebook,
            state_manager=self.state_manager,
            modo="editar",
            on_accion_completada=self._on_edicion_completada
        )
        # La pestaña se agrega o remueve según 'puede_modificar'

        # 3. Barra de Estado
        self._crear_barra_estado()

    def _crear_barra_estado(self) -> None:
        status_bar = tb.Frame(self, padding=(15, 6), style="Pastel.TFrame")
        status_bar.pack(fill=X, side=tk.BOTTOM)

        tb.Label(
            status_bar,
            text="Sistema de Control de Incidencias Ciudadanas",
            style="PastelMuted.TLabel"
        ).pack(side=LEFT)

        tb.Label(
            status_bar,
            text="Estado: En línea",
            style="PastelMuted.TLabel"
        ).pack(side=RIGHT)

    # ========================================================================
    # INTERACCIÓN ENTRE PESTAÑAS Y FLUJO DE EDICIÓN
    # ========================================================================

    def _on_solicitar_edicion(self, incidente: Incidente) -> None:
        """
        Invocado al hacer doble clic en una fila o al presionar 'Editar Seleccionada'.
        Valida permisos y carga el incidente en la pestaña de Modificar.
        """
        if not self.state_manager.puede_modificar:
            Messagebox.show_warning(
                "El rol Comunidad tiene acceso de solo lectura y voto comunitario.\n"
                "La modificación oficial está restringida a Administradores y Gobierno.",
                title="Permisos Insuficientes"
            )
            return

        # Cargar datos en el formulario de edición
        self.state_manager.cargar_incidente_para_edicion(incidente)
        self.vista_editar.cargar_incidente(incidente)

        # Seleccionar automáticamente la pestaña de Modificar
        self.notebook.select(self.vista_editar)

    def _on_registro_completado(self) -> None:
        """Tras registrar un incidente, cambiar a la pestaña de consulta."""
        self.notebook.select(self.vista_lista)
        self.vista_lista.refrescar_tabla()

    def _on_edicion_completada(self) -> None:
        """Tras guardar una edición inmutable, volver a la tabla de consulta."""
        self.notebook.select(self.vista_lista)
        self.vista_lista.refrescar_tabla()

    def _on_logout_click(self) -> None:
        self.state_manager.cerrar_sesion()
        self.on_logout()

    # ========================================================================
    # ACTUALIZACIÓN REACTIVA Y CONTROL DE ROLES
    # ========================================================================

    def refrescar_dashboard(self) -> None:
        """Aplica las reglas de acceso por rol y refresca las vistas hijas."""
        usuario = self.state_manager.usuario_actual
        if usuario is None:
            return

        # Actualizar indicador de sesión
        self.var_usuario_badge.set(
            f"👤 {usuario.nombre} | Rol: {usuario.rol} | Sector: {usuario.sector}"
        )

        # GESTIÓN DE LA PESTAÑA MODIFICAR:
        # Si es Admin o Gobierno: se muestra.
        # Si es Comunidad: se oculta del notebook.
        tabs_actuales = self.notebook.tabs()
        id_tab_editar = str(self.vista_editar)

        if self.state_manager.puede_modificar:
            if id_tab_editar not in tabs_actuales:
                self.notebook.add(self.vista_editar, text="⚙️ Modificar Incidente")
        else:
            if id_tab_editar in tabs_actuales:
                self.notebook.forget(self.vista_editar)

        # Refrescar tabla y formularios
        self.vista_lista.refrescar_tabla()
        self.vista_crear.sincronizar_con_estado()
