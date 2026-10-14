"""
Package data - Capa de Persistencia e I/O del Sistema
"""

from .file_handler import (
    guardar_incidentes,
    cargar_incidentes,
    guardar_usuarios,
    cargar_usuarios,
    guardar_tipos_incidente,
    cargar_tipos_incidente,
    RUTA_DEFAULT_JSON,
    RUTA_DEFAULT_USUARIOS_JSON,
    RUTA_DEFAULT_TIPOS_JSON,
)

__all__ = [
    "guardar_incidentes",
    "cargar_incidentes",
    "guardar_usuarios",
    "cargar_usuarios",
    "guardar_tipos_incidente",
    "cargar_tipos_incidente",
    "RUTA_DEFAULT_JSON",
    "RUTA_DEFAULT_USUARIOS_JSON",
    "RUTA_DEFAULT_TIPOS_JSON",
]
