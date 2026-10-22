"""
auth.py - Módulo de Autenticación Pura
Sistema de Control de Incidencias Ciudadanas
Paradigma: Programación Funcional

Este módulo implementa la lógica de autenticación del sistema mediante
funciones puras y transparentes referencialmente.
"""

from typing import Any, List, Mapping, Optional, Sequence
import re
from core.models import Usuario, RolUsuario
from core.engine import ResultadoValidacion

ROLES_PERMITIDOS: Sequence[str] = ("Admin", "Gobierno", "Comunidad")


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


def validar_datos_usuario(
    username: str,
    password: str,
    nombre: str,
    rol: str,
    sector: str,
    usuarios_existentes: Sequence[Mapping[str, Any]]
) -> ResultadoValidacion:
    """
    Función Pura: Valida exhaustivamente los datos para crear un nuevo usuario.

    Garantía de Pureza:
    - Transparencia referencial absoluta: no interactúa con I/O ni altera estado externo.
    - Determinismo matemático: para iguales argumentos, siempre retorna el mismo ResultadoValidacion.
    """
    user_limpio = username.strip()
    pwd_limpio = password.strip()
    nom_limpio = nombre.strip()
    rol_limpio = rol.strip()
    sec_limpio = sector.strip()

    # 1. Validación del Nombre Completo
    if len(nom_limpio) < 3:
        return ResultadoValidacion(
            es_valido=False,
            motivo=f"El nombre completo debe tener al menos 3 caracteres (actual: {len(nom_limpio)})."
        )

    # 2. Validación de Nombre de Usuario
    if len(user_limpio) < 3:
        return ResultadoValidacion(
            es_valido=False,
            motivo=f"El nombre de usuario debe tener al menos 3 caracteres (actual: {len(user_limpio)})."
        )

    if not re.match(r"^[a-zA-Z0-9_.-]+$", user_limpio):
        return ResultadoValidacion(
            es_valido=False,
            motivo="El nombre de usuario solo puede contener letras, números, puntos y guiones."
        )

    # 3. Verificación de unicidad declarativa
    user_casefold = user_limpio.casefold()
    ya_existe = any(
        str(reg.get("username", "")).strip().casefold() == user_casefold
        for reg in usuarios_existentes
    )
    if ya_existe:
        return ResultadoValidacion(
            es_valido=False,
            motivo=f"El nombre de usuario '{user_limpio}' ya está registrado. Seleccione uno diferente."
        )

    # 4. Validación de Contraseña
    if len(pwd_limpio) < 4:
        return ResultadoValidacion(
            es_valido=False,
            motivo=f"La contraseña debe tener al menos 4 caracteres (actual: {len(pwd_limpio)})."
        )

    # 5. Validación de Rol permitido
    if rol_limpio not in ROLES_PERMITIDOS:
        return ResultadoValidacion(
            es_valido=False,
            motivo=f"Rol '{rol_limpio}' no reconocido. Debe ser uno de: {', '.join(ROLES_PERMITIDOS)}."
        )

    # 6. Validación de Sector Territorial
    if rol_limpio == "Comunidad" and len(sec_limpio) < 3:
        return ResultadoValidacion(
            es_valido=False,
            motivo="Para usuarios con rol 'Comunidad', el sector territorial es obligatorio (mínimo 3 caracteres)."
        )

    return ResultadoValidacion(es_valido=True, motivo="Datos de usuario válidos.")


def construir_registro_usuario(
    nuevo_id: int,
    username: str,
    password: str,
    nombre: str,
    rol: str,
    sector: str = ""
) -> dict:
    """
    Función Pura: Construye un diccionario nuevo e independiente con los datos del usuario.
    """
    sec = sector.strip()
    if not sec:
        if rol == "Admin":
            sec = "Todos"
        elif rol == "Gobierno":
            sec = "Distrito"
        else:
            sec = "Sector General"

    return {
        "id": int(nuevo_id),
        "username": username.strip(),
        "password": password.strip(),
        "nombre": nombre.strip(),
        "rol": rol.strip(),
        "sector": sec,
    }


def agregar_usuario_inmutable(
    usuarios_existentes: Sequence[Mapping[str, Any]],
    nuevo_usuario: Mapping[str, Any]
) -> List[dict]:
    """
    Función Pura: Retorna una nueva lista que contiene todos los usuarios anteriores más el nuevo.
    Garantiza la inmutabilidad de la colección previa.
    """
    return [dict(u) for u in usuarios_existentes] + [dict(nuevo_usuario)]
