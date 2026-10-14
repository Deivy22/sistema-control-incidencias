"""
models.py - Modelado de Datos Inmutables
Sistema de Control de Incidencias Ciudadanas
Paradigma: Programación Funcional

Este módulo define las estructuras de datos nucleares del sistema.
Cumple con los principios funcionales de:
1. Inmutabilidad estricta: Uso de `@dataclass(frozen=True)` que impide la mutación de estado in-situ.
2. Tipado algebraico estático: Uso de Sum Types (Uniones y Literales) para restringir
   estados y roles a dominios válidos conocidos.
"""

from dataclasses import dataclass
from typing import Literal, Union


# ============================================================================
# TIPOS SUMA / UNIONES PARA EL DOMINIO (Algebraic Data Types)
# ============================================================================

# Definición de roles mediante Unión de Literales.
# Garantiza que el rol solo pueda ser uno de estos tres valores exactos en tiempo de tipado.
RolUsuario = Union[
    Literal['Comunidad'],
    Literal['Gobierno'],
    Literal['Admin']
]

# Definición de tipos de incidentes mediante Unión de Literales.
# Representa un tipo suma disjunto (Sum Type) de incidentes soportados por el dominio.
TipoIncidente = Union[
    Literal['Choque'],
    Literal['FallaElectrica'],
    Literal['Alcantarillado']
]

# Estados posibles del ciclo de vida de una incidencia ciudadana.
EstadoIncidente = Union[
    Literal['Reportado'],
    Literal['EnProceso'],
    Literal['Resuelto'],
    Literal['Descartado']
]


# ============================================================================
# ENTIDADES INMUTABLES (Frozen Dataclasses)
# ============================================================================

@dataclass(frozen=True)
class Usuario:
    """
    Entidad inmutable que representa a un actor del sistema.

    Principio de Inmutabilidad:
    - `frozen=True` genera automáticamente un método `__setattr__` que lanza
      `FrozenInstanceError` si se intenta modificar cualquier campo después de la creación.
    - No existen métodos mutadores (setters); cualquier cambio requiere crear una nueva instancia.
    """
    id: int
    nombre: str
    rol: RolUsuario
    sector: str = ""


@dataclass(frozen=True)
class Incidente:
    """
    Entidad inmutable que representa una incidencia reportada en la ciudad.

    Principio de Inmutabilidad:
    - Al ser `frozen=True`, el estado es persistente e inmutable en memoria.
    - Facilita el razonamiento formal, evita condiciones de carrera y asegura
      que las funciones que operen sobre él sean completamente libres de efectos secundarios.
    """
    id: int
    sector: str
    descripcion: str
    tipo_incidente: TipoIncidente
    estado: EstadoIncidente
    nivel_prioridad: int
