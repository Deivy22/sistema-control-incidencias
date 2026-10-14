"""
auth.py - Módulo de Autenticación Pura
Sistema de Control de Incidencias Ciudadanas
Paradigma: Programación Funcional

Este módulo implementa la lógica de autenticación del sistema mediante
funciones puras y transparentes referencialmente.
"""

from typing import Any, Mapping, Optional, Sequence
from core.models import Usuario, RolUsuario


def autenticar_usuario(
    user: str,
    password: str,
    base_datos: Sequence[Mapping[str, Any]]
) -> Optional[Usuario]:
    """
    Función Pura: Valida credenciales contra un catálogo de datos inmutable.

    Garantía de Pureza:
    - Transparencia Referencial: Depende estrictamente de los parámetros recibidos.
      No lee de disco, no consulta redes ni muta variables globales.
    - Cero Efectos Secundarios: La colección 'base_datos' no sufre alteraciones.
    - Retorno Determinista: Para un mismo par (user, password) y la misma base_datos,
      siempre retorna el mismo objeto Usuario o None.
    """
    usuario_limpio: str = user.strip()
    clave_limpia: str = password.strip()

    for registro in base_datos:
        reg_user = str(registro.get("username", "")).strip()
        reg_pass = str(registro.get("password", "")).strip()

        if reg_user == usuario_limpio and reg_pass == clave_limpia:
            # Creación de entidad inmutable Usuario
            return Usuario(
                id=int(registro["id"]),
                nombre=str(registro.get("nombre", usuario_limpio)),
                rol=registro["rol"],  # type: ignore
                sector=str(registro.get("sector", ""))
            )

    return None
