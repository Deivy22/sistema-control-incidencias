import sys
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH

from ui.state_manager import StateManager
from ui.styles import aplicar_estilos_pastel
from ui.auth.login_view import LoginView
from ui.dashboard.main_window import MainWindow


class AppOrchestrator:
    """
    Orquestador de ciclo de vida de la aplicación.
    Gestiona la alternancia entre la pantalla de Login y el Dashboard de pestañas.
    """

    def __init__(self) -> None:
        # Estado impuro global del sistema
        self.state_manager = StateManager()

        # Ventana principal Tkinter con ttkbootstrap
        self.root = tb.Window(
            title="Sistema de Control de Incidencias Ciudadanas",
            themename="litera",
            size=(1240, 760),
            resizable=(True, True)
        )
        self.root.minsize(1020, 660)

        # Inyección de la paleta pastel (#FAF0E6, #FADADD, #2D2A26)
        aplicar_estilos_pastel(self.root.style, self.root)

        self.contenedor_principal: tb.Frame = None  # type: ignore
        self.vista_login: LoginView = None  # type: ignore
        self.vista_dashboard: MainWindow = None  # type: ignore

        # Mostrar pantalla inicial de Login
        self.mostrar_login()

    def mostrar_login(self) -> None:
        """
        Carga y muestra la pantalla real de autenticación.
        Destruye completamente el contenedor principal anterior y vuelve a instanciarlo
        desde cero para garantizar el correcto revinculado de callbacks y eventos.
        """
        if self.contenedor_principal is not None:
            self.contenedor_principal.destroy()

        self.contenedor_principal = tb.Frame(self.root, style="Pastel.TFrame")
        self.contenedor_principal.pack(fill=BOTH, expand=True)

        self.vista_login = LoginView(
            parent=self.contenedor_principal,
            state_manager=self.state_manager,
            on_login_success=self.mostrar_dashboard
        )
        self.vista_login.pack(fill=BOTH, expand=True)

    def mostrar_dashboard(self) -> None:
        """
        Carga y muestra el Dashboard de pestañas tras login exitoso.
        Destruye completamente el contenedor principal y lo inicializa limpio.
        """
        if self.contenedor_principal is not None:
            self.contenedor_principal.destroy()

        self.contenedor_principal = tb.Frame(self.root, style="Pastel.TFrame")
        self.contenedor_principal.pack(fill=BOTH, expand=True)

        self.vista_dashboard = MainWindow(
            parent=self.contenedor_principal,
            state_manager=self.state_manager,
            on_logout=self.mostrar_login
        )
        self.vista_dashboard.pack(fill=BOTH, expand=True)

    def iniciar(self) -> None:
        """Arranca el ciclo principal de eventos."""
        self.root.mainloop()


def main() -> None:
    app = AppOrchestrator()
    app.iniciar()


if __name__ == "__main__":
    main()
