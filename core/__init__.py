"""
Package core - Módulos fundamentales del Sistema de Control de Incidencias Ciudadanas
"""

from .models import Usuario, Incidente, RolUsuario, TipoIncidente, EstadoIncidente
from .engine import (
    ResultadoValidacion,
    validar_descripcion,
    es_descripcion_valida,
    adherir_voto_incidente,
    clasificar_incidente,
    validar_incidente_complejo,
    filtrar_por_permisos,
    actualizar_incidente,
    validar_tipo_incidente,
    eliminar_incidente_por_id,
)
from .analisis import (
    crear_filtro_por_sector,
    filtrar_y_resumir_por_sector,
    calcular_prioridad_total,
    extraer_ids_incidentes,
)
from .auth import autenticar_usuario

__all__ = [
    "Usuario",
    "Incidente",
    "RolUsuario",
    "TipoIncidente",
    "EstadoIncidente",
    "ResultadoValidacion",
    "validar_descripcion",
    "es_descripcion_valida",
    "adherir_voto_incidente",
    "clasificar_incidente",
    "validar_incidente_complejo",
    "filtrar_por_permisos",
    "actualizar_incidente",
    "validar_tipo_incidente",
    "eliminar_incidente_por_id",
    "crear_filtro_por_sector",
    "filtrar_y_resumir_por_sector",
    "calcular_prioridad_total",
    "extraer_ids_incidentes",
    "autenticar_usuario",
]
