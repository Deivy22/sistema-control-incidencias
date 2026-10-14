"""
analisis.py - Funciones de Orden Superior, Closures y Operaciones Funcionales
Sistema de Control de Incidencias Ciudadanas
Paradigma: Programación Funcional

Este módulo concentra operaciones analíticas basadas en el paradigma funcional:
1. Closures Reales (Entornos léxicos cerrados sobre variables libres).
2. Funciones de Orden Superior (Higher-Order Functions): filter(), map(), reduce().
3. Inmutabilidad y Pureza: Ninguna colección de datos de entrada es mutada.
"""

from functools import reduce
from typing import Callable, List, Sequence
try:
    from .models import Incidente
except ImportError:
    from models import Incidente  # Soporte para ejecución aislada


# ============================================================================
# 1. CLOSURE REAL (HIGHER-ORDER FUNCTION)
# ============================================================================

def crear_filtro_por_sector(sector: str) -> Callable[[Incidente], bool]:
    
    sector_objetivo: str = sector.strip().casefold()

    def pertenece_a_sector(incidente: Incidente) -> bool:
        """
        Predicado puro que evalúa si el incidente pertenece al sector capturado.
        """
        return incidente.sector.strip().casefold() == sector_objetivo

    return pertenece_a_sector


# ============================================================================
# 2. FILTER Y MAP (COMPOSICIÓN DE TRANSFORMACIONES)
# ============================================================================

def _etiqueta_prioridad(nivel_prioridad: int) -> str:
    """
    Función pura auxiliar para mapear el nivel numérico a una etiqueta cualitativa.
    """
    match nivel_prioridad:
        case p if p >= 4:
            return "Crítico"
        case 3:
            return "Alto"
        case 2:
            return "Medio"
        case _:
            return "Bajo"


def _formatear_resumen_incidente(incidente: Incidente) -> str:
    """
    Función pura que proyecta un Incidente a una cadena de resumen estructurada.
    Ejemplo: 'ID: 1 - Choque - Crítico'
    """
    etiqueta = _etiqueta_prioridad(incidente.nivel_prioridad)
    return f"ID: {incidente.id} - {incidente.tipo_incidente} - {etiqueta}"


def filtrar_y_resumir_por_sector(
    incidentes: Sequence[Incidente],
    sector: str
) -> List[str]:
    
    # 1. Obtención del predicado mediante el closure
    predicado_sector = crear_filtro_por_sector(sector)

    # 2. Filtrado declarativo con filter()
    incidentes_filtrados = filter(predicado_sector, incidentes)

    # 3. Transformación proyectiva con map()
    resumenes = map(_formatear_resumen_incidente, incidentes_filtrados)

    # 4. Retorno de nueva colección materializada
    return list(resumenes)


# ============================================================================
# 3. REDUCE (PLEGADO / AGREGACIÓN PURA)
# ============================================================================

def calcular_prioridad_total(incidentes: Sequence[Incidente]) -> int:
    """
    Función Pura: Calcula la suma acumulada de los niveles de prioridad de una
    colección de incidentes utilizando 'functools.reduce'.

    Concepto Funcional (Fold Left):
    - Reduce procesa la secuencia aplicando recursivamente una función binaria acumuladora.
    - Se especifica un elemento neutro (0) como inicializador para garantizar:
      a) Comportamiento determinista si la secuencia está vacía (retorna 0).
      b) Totalidad de la función sin lanzar TypeError por secuencia vacía.

    Garantía de Inmutabilidad:
    - No requiere variables de estado mutables intermedias (como bucles con sumadores 'total += x').
    """
    return reduce(
        lambda acumulador, incidente: acumulador + incidente.nivel_prioridad,
        incidentes,
        0
    )


# ============================================================================
# 4. EXTRACCIÓN PROYECTIVA DE IDENTIFICADORES (HOF MAP)
# ============================================================================

def extraer_ids_incidentes(incidentes: Sequence[Incidente]) -> List[int]:
    """
    Función Pura de Orden Superior: Extrae los identificadores numéricos de una colección
    de incidentes utilizando 'map()'.

    Garantía de Pureza y Declaratividad:
    - Aplica proyección funcional: Incidente -> id.
    - No muta la colección de entrada 'incidentes'.
    - Transparencia referencial absoluta.
    """
    return list(map(lambda inc: inc.id, incidentes))

