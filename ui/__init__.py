"""
Package ui - Capa Visual y de Estado Impuro
Sistema de Control de Incidencias Ciudadanas
"""

from .state_manager import StateManager
from .styles import aplicar_estilos_pastel
from .dashboard.main_window import MainWindow
from .auth.login_view import LoginView
from .incidents.list_view import IncidentesListView
from .incidents.form_view import IncidenteFormView

__all__ = [
    "StateManager",
    "aplicar_estilos_pastel",
    "MainWindow",
    "LoginView",
    "IncidentesListView",
    "IncidenteFormView",
]
