"""
file_handler.py - Persistencia y Manejo de Archivos (Capa Impura de I/O)
Sistema de Control de Incidencias Ciudadanas
Arquitectura: Functional Core, Imperative Shell (FCIS)

========================================================================================
JUSTIFICACIÓN ARQUITECTÓNICA DE IMPUREZA:
========================================================================================
En Programación Funcional estricta, las operaciones de entrada/salida (Disk I/O) son
OPERACIONES IMPURAS POR DEFINICIÓN por las siguientes razones fundamentales:

1. EFECTOS SECUNDARIOS (Side Effects):
   Escribir en disco modifica el estado permanente del entorno exterior más allá de la memoria
   del proceso, alterando el almacenamiento secundario del sistema operativo.

2. PÉRDIDA DE TRANSPARENCIA REFERENCIAL:
   La función 'cargar_incidentes()' no es matemáticamente pura porque dos llamadas con idénticos
   argumentos pueden retornar resultados totalmente distintos si el archivo fue editado por otro
   proceso, eliminado o corrompido en el disco.

3. NO-DETERMINISMO Y MANEJO DE CONDICIONES AMBIENTALES:
   Las funciones de I/O están expuestas a fallos de hardware, permisos insuficientes, bloqueos de
   archivos o desconexiones, requiriendo manejo de excepciones de infraestructura.

SEPARACIÓN EN CAPAS (FCIS):
Siguiendo el principio de separar el Núcleo Funcional de la Concha Imperativa, este módulo
reside deliberadamente en '/data/' para confinar los efectos colaterales al borde del sistema,
evitando que la impureza del sistema de archivos contamine la lógica pura de '/core/'.
========================================================================================
"""

from dataclasses import asdict
import json
import logging
from pathlib import Path
from typing import List, Sequence, Union

from core.models import Incidente


# Configuración de ruta por defecto
DIRECTORIO_ACTUAL: Path = Path(__file__).resolve().parent
RUTA_DEFAULT_JSON: Path = DIRECTORIO_ACTUAL / "incidentes.json"

logger = logging.getLogger(__name__)


def obtener_datos_semilla() -> List[Incidente]:
    """
    Función pura auxiliar que provee el catálogo de incidentes de demostración
    en caso de que el archivo persistente no exista aún.
    """
    return [
        Incidente(
            id=1,
            sector="Sector Norte",
            descripcion="Colisión múltiple entre dos taxis bloqueando calzada principal.",
            tipo_incidente="Choque",
            estado="Reportado",
            nivel_prioridad=3
        ),
        Incidente(
            id=2,
            sector="Sector Centro",
            descripcion="Transformador averiado con chispas en poste de alumbrado público.",
            tipo_incidente="FallaElectrica",
            estado="Reportado",
            nivel_prioridad=4
        ),
        Incidente(
            id=3,
            sector="Sector Sur",
            descripcion="Desbordamiento de aguas negras frente a colegio distrital tras lluvia.",
            tipo_incidente="Alcantarillado",
            estado="Reportado",
            nivel_prioridad=2
        ),
        Incidente(
            id=4,
            sector="Sector Norte",
            descripcion="Poste inclinado con cableado de media tensión colgando sobre la acera.",
            tipo_incidente="FallaElectrica",
            estado="EnProceso",
            nivel_prioridad=5
        ),
    ]


def guardar_incidentes(
    incidentes: Sequence[Incidente],
    ruta_archivo: Union[Path, str] = RUTA_DEFAULT_JSON
) -> bool:
    """
    Función Impura: Serializa y escribe la lista de entidades Incidente en el disco en formato JSON.

    Efecto secundario:
    - Modifica o crea el archivo 'incidentes.json' en el sistema de archivos del usuario.

    Retorna:
    - True si la operación se completó exitosamente, False ante un error de E/S.
    """
    ruta = Path(ruta_archivo)
    try:
        # Asegurar existencia del directorio padre
        ruta.parent.mkdir(parents=True, exist_ok=True)

        # Serialización de los frozen dataclasses a diccionarios primitivos
        datos_serializables = [asdict(inc) for inc in incidentes]

        with open(ruta, mode="w", encoding="utf-8") as f:
            json.dump(datos_serializables, f, ensure_ascii=False, indent=2)

        return True

    except (IOError, OSError, TypeError) as e:
        logger.error(f"Fallo al guardar incidentes en '{ruta}': {e}")
        return False


def cargar_incidentes(
    ruta_archivo: Union[Path, str] = RUTA_DEFAULT_JSON
) -> List[Incidente]:
    """
    Función Impura: Lee y deserializa la lista de incidentes desde el archivo JSON especificado.

    Efecto secundario:
    - Lee del sistema de archivos local.
    - Si el archivo no existe, lo crea automáticamente inicializándolo con datos semilla.

    Retorna:
    - Lista de objetos inmutables 'Incidente' reconstruidos desde el disco.
    """
    ruta = Path(ruta_archivo)

    # Si no existe, inicializar con datos semilla para garantizar una primera ejecución consistente
    if not ruta.exists():
        semillas = obtener_datos_semilla()
        guardar_incidentes(semillas, ruta)
        return semillas

    try:
        with open(ruta, mode="r", encoding="utf-8") as f:
            contenido = json.load(f)

        incidentes: List[Incidente] = []
        for item in contenido:
            # Reconstrucción de la instancia inmutable
            inc = Incidente(
                id=int(item["id"]),
                sector=str(item["sector"]),
                descripcion=str(item["descripcion"]),
                tipo_incidente=item["tipo_incidente"],
                estado=item["estado"],
                nivel_prioridad=int(item["nivel_prioridad"])
            )
            incidentes.append(inc)

        return incidentes

    except (IOError, json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Error al cargar incidentes desde '{ruta}': {e}. Retornando datos semilla de respaldo.")
        return obtener_datos_semilla()


# ============================================================================
# PERSISTENCIA DE USUARIOS (AUTENTICACIÓN)
# ============================================================================

RUTA_DEFAULT_USUARIOS_JSON: Path = DIRECTORIO_ACTUAL / "usuarios.json"


def cargar_usuarios(
    ruta_archivo: Union[Path, str] = RUTA_DEFAULT_USUARIOS_JSON
) -> List[dict]:
    """
    Función Impura: Carga el listado de credenciales y perfiles de usuarios desde JSON.
    """
    ruta = Path(ruta_archivo)
    if not ruta.exists():
        logger.warning(f"Archivo de usuarios '{ruta}' no encontrado. Retornando lista vacía.")
        return []

    try:
        with open(ruta, mode="r", encoding="utf-8") as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Error al leer '{ruta}': {e}")
        return []


def guardar_usuarios(
    usuarios: Sequence[dict],
    ruta_archivo: Union[Path, str] = RUTA_DEFAULT_USUARIOS_JSON
) -> bool:
    """
    Función Impura: Escribe la lista de usuarios en disco.
    """
    ruta = Path(ruta_archivo)
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta, mode="w", encoding="utf-8") as f:
            json.dump(list(usuarios), f, ensure_ascii=False, indent=2)
        return True
    except (IOError, OSError) as e:
        logger.error(f"Error al guardar usuarios en '{ruta}': {e}")
        return False


# ============================================================================
# CATÁLOGO DINÁMICO DE TIPOS DE INCIDENTE
# ============================================================================

RUTA_DEFAULT_TIPOS_JSON: Path = DIRECTORIO_ACTUAL / "tipos_incidente.json"

TIPOS_INCIDENTE_SEMILLA: List[str] = [
    "Choque",
    "Falla Electrica",
    "Alcantarillado",
    "Infraestructura",
    "Seguridad Pública",
]


def cargar_tipos_incidente(
    ruta_archivo: Union[Path, str] = RUTA_DEFAULT_TIPOS_JSON
) -> List[str]:
    """
    Función Impura: Carga la lista dinámica de tipos de incidente desde JSON.
    Si el archivo no existe, lo crea con la lista semilla por defecto.
    """
    ruta = Path(ruta_archivo)
    if not ruta.exists():
        guardar_tipos_incidente(TIPOS_INCIDENTE_SEMILLA, ruta)
        return list(TIPOS_INCIDENTE_SEMILLA)

    try:
        with open(ruta, mode="r", encoding="utf-8") as f:
            datos = json.load(f)
            if isinstance(datos, list):
                return [str(item) for item in datos]
            return list(TIPOS_INCIDENTE_SEMILLA)
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Error al leer '{ruta}': {e}. Usando lista semilla.")
        return list(TIPOS_INCIDENTE_SEMILLA)


def guardar_tipos_incidente(
    tipos: Sequence[str],
    ruta_archivo: Union[Path, str] = RUTA_DEFAULT_TIPOS_JSON
) -> bool:
    """
    Función Impura: Guarda la lista de tipos de incidente en disco.
    """
    ruta = Path(ruta_archivo)
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta, mode="w", encoding="utf-8") as f:
            json.dump(list(tipos), f, ensure_ascii=False, indent=2)
        return True
    except (IOError, OSError) as e:
        logger.error(f"Error al guardar tipos en '{ruta}': {e}")
        return False

