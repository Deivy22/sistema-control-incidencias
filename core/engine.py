
from dataclasses import dataclass, replace
import re
from typing import Final, List, Optional, Sequence, Tuple, Union
try:
    from .models import EstadoIncidente, Incidente, TipoIncidente, Usuario
except ImportError:
    from models import EstadoIncidente, Incidente, TipoIncidente, Usuario  # Soporte para ejecución aislada


# ============================================================================
# CONSTANTES INMUTABLES DE VALIDACIÓN (Puras, sin estado compartido mutable)
# ============================================================================

LONGITUD_MINIMA_DESCRIPCION: Final[int] = 15
LONGITUD_MAXIMA_DESCRIPCION: Final[int] = 1000
MINIMO_CARACTERES_UNICOS: Final[int] = 5
MAX_CARACTERES_REPETIDOS_CONSECUTIVOS: Final[int] = 4


# ============================================================================
# TIPO DE RESULTADO (Representación Funcional de Éxito / Fallo)
# ============================================================================

@dataclass(frozen=True)
class ResultadoValidacion:
    """
    Tipo inmutable que modela el resultado de una validación (Éxito o Fallo).
    
    Implementa `__bool__` para permitir que la función pura sea utilizada tanto
    como un tipo de resultado enriquecido (con motivo de fallo) o evaluada
    directamente como un booleano en contextos lógicos (`if resultado:`).
    """
    es_valido: bool
    motivo: str = ""

    def __bool__(self) -> bool:
        """Permite interoperabilidad transparente como booleano."""
        return self.es_valido


# ============================================================================
# 1. VALIDACIÓN PURA DE DESCRIPCIÓN
# ============================================================================

def validar_descripcion(
    descripcion: str,
    longitud_minima: int = LONGITUD_MINIMA_DESCRIPCION,
    longitud_maxima: int = LONGITUD_MAXIMA_DESCRIPCION,
    minimo_caracteres_unicos: int = MINIMO_CARACTERES_UNICOS,
    max_caracteres_repetidos_consecutivos: int = MAX_CARACTERES_REPETIDOS_CONSECUTIVOS,
) -> ResultadoValidacion:
    """
    Función Pura: Valida que la descripción de un incidente no sea spam ni contenido basura.

    Criterios funcionales de validación:
    - Longitud mínima y máxima aceptable.
    - Detección de caracteres idénticos consecutivos (ej. 'aaaaaaa', 'xxxxxx').
    - Diversidad de caracteres (entropía básica para descartar 'asdfasdfasdf' o repeticiones simples).
    - Mínimo de palabras reconocibles.

    Garantía de Pureza:
    - Determinista: para cualquier cadena idéntica, la respuesta es invariablemente la misma.
    - Sin efectos colaterales: no altera variables externas ni realiza operaciones de I/O.
    """
    texto_limpio: str = descripcion.strip()
    longitud: int = len(texto_limpio)

    # 1. Verificación de longitud mínima
    if longitud < longitud_minima:
        return ResultadoValidacion(
            es_valido=False,
            motivo=f"Longitud insuficiente ({longitud} caracteres). Mínimo requerido: {longitud_minima}."
        )

    # 2. Verificación de longitud máxima
    if longitud > longitud_maxima:
        return ResultadoValidacion(
            es_valido=False,
            motivo=f"Longitud excesiva ({longitud} caracteres). Máximo permitido: {longitud_maxima}."
        )

    # 3. Detección de caracteres idénticos repetidos consecutivamente (ej. 'aaaaaa')
    patron_repeticion = rf"(.)\1{{{max_caracteres_repetidos_consecutivos},}}"
    if re.search(patron_repeticion, texto_limpio):
        return ResultadoValidacion(
            es_valido=False,
            motivo="Contenido descartado por repetición excesiva de caracteres consecutivos."
        )

    # 4. Verificación de diversidad de caracteres (entropía básica)
    caracteres_unicos: int = len(set(texto_limpio.lower().replace(" ", "")))
    if caracteres_unicos < minimo_caracteres_unicos:
        return ResultadoValidacion(
            es_valido=False,
            motivo="Contenido descartado por baja variedad de caracteres (posible spam de patrones simples)."
        )

    # 5. Verificación de palabras mínimas
    palabras = [p for p in texto_limpio.split() if len(p) >= 2]
    if len(palabras) < 3:
        return ResultadoValidacion(
            es_valido=False,
            motivo="La descripción debe contener al menos 3 palabras significativas."
        )

    return ResultadoValidacion(es_valido=True, motivo="Descripción válida.")


def es_descripcion_valida(descripcion: str) -> bool:
    """
    Función Pura de conveniencia: Retorna estrictamente un `bool` para la validación.
    """
    return bool(validar_descripcion(descripcion))


# ============================================================================
# 2. TRANSFORMACIÓN INMUTABLE
# ============================================================================

def ha_votado_usuario(incidente: Incidente, usuario_id: int) -> bool:
    """Función Pura: Retorna True si el usuario ya registró su voto para este incidente."""
    return usuario_id in incidente.usuarios_votantes


def adherir_voto_incidente(
    incidente: Incidente,
    incremento: int = 1,
    usuario_id: Optional[int] = None
) -> Incidente:
    """
    Función Pura: Incrementa el nivel de prioridad de un incidente reportado por la comunidad
    y opcionalmente registra el ID del votante asegurando la regla de unicidad por usuario.

    Garantía de Inmutabilidad:
    - El objeto original `incidente` jamás es mutado.
    - Se utiliza `replace()` del módulo dataclasses para generar un nuevo objeto `Incidente`.
    """
    if incremento < 0:
        raise ValueError("El incremento de votos/prioridad no puede ser un número negativo.")

    if usuario_id is not None and usuario_id in incidente.usuarios_votantes:
        raise ValueError(f"El usuario #{usuario_id} ya ha emitido su voto para el incidente #{incidente.id}.")

    nueva_prioridad: int = incidente.nivel_prioridad + incremento
    nuevos_votantes: Tuple[int, ...] = (
        incidente.usuarios_votantes + (usuario_id,)
        if usuario_id is not None
        else incidente.usuarios_votantes
    )
    
    return replace(
        incidente,
        nivel_prioridad=nueva_prioridad,
        usuarios_votantes=nuevos_votantes
    )


# ============================================================================
# 3. PATTERN MATCHING (CLASIFICACIÓN)
# ============================================================================

def clasificar_incidente(incidente: Union[Incidente, TipoIncidente, str]) -> Tuple[int, str]:

    match incidente:
        case Incidente(tipo_incidente="Choque") | "Choque":
            return (3, "Secretaría de Movilidad y Tránsito")

        case Incidente(tipo_incidente="FallaElectrica") | Incidente(tipo_incidente="Falla Electrica") | "FallaElectrica" | "Falla Electrica":
            return (4, "Departamento de Alumbrado y Redes Eléctricas")

        case Incidente(tipo_incidente="Alcantarillado") | "Alcantarillado":
            return (2, "Empresa de Acueducto y Alcantarillado")

        case Incidente(tipo_incidente="Infraestructura") | "Infraestructura":
            return (3, "Secretaría de Infraestructura y Vías")

        case Incidente(tipo_incidente="Seguridad Pública") | Incidente(tipo_incidente="Seguridad Publica") | "Seguridad Pública" | "Seguridad Publica":
            return (5, "Secretaría de Seguridad y Convivencia")

        case Incidente():
            return (1, "Dirección General de Atención Ciudadana")

        case _:
            return (1, "Dirección General de Atención Ciudadana")


def validar_tipo_incidente(
    tipo: str,
    tipos_permitidos: Sequence[str]
) -> bool:
    """
    Función Pura: Valida si el tipo de incidente ingresado existe en la colección de tipos permitidos.

    Garantía de Pureza:
    - Transparencia referencial: depende exclusivamente de sus parámetros.
    - Sin mutaciones ni I/O.
    """
    tipo_limpio = tipo.strip().casefold()
    return any(t.strip().casefold() == tipo_limpio for t in tipos_permitidos)


def validar_nuevo_tipo_incidente(
    nuevo_tipo: str,
    tipos_existentes: Sequence[str]
) -> ResultadoValidacion:
    """
    Función Pura: Valida que un nuevo tipo de incidente cumpla con los requisitos del dominio.

    Criterios:
    - Longitud mínima: al menos 3 caracteres.
    - Longitud máxima: no mayor a 50 caracteres.
    - Caracteres permitidos: letras, números, espacios y guiones.
    - Unicidad: no existir previamente en el catálogo (comparación case-insensitive).

    Garantía de Pureza:
    - Transparencia referencial: sin efectos colaterales ni mutaciones.
    """
    tipo_limpio = nuevo_tipo.strip()

    if len(tipo_limpio) < 3:
        return ResultadoValidacion(
            es_valido=False,
            motivo=f"El tipo de incidente debe tener al menos 3 caracteres (longitud actual: {len(tipo_limpio)})."
        )

    if len(tipo_limpio) > 50:
        return ResultadoValidacion(
            es_valido=False,
            motivo=f"El tipo de incidente no debe exceder los 50 caracteres (longitud actual: {len(tipo_limpio)})."
        )

    if not re.match(r"^[\w\s\sáéíóúÁÉÍÓÚñÑüÜ-]+$", tipo_limpio):
        return ResultadoValidacion(
            es_valido=False,
            motivo="El tipo de incidente solo puede contener letras, números, espacios y guiones."
        )

    tipo_casefold = tipo_limpio.casefold()
    ya_existe = any(t.strip().casefold() == tipo_casefold for t in tipos_existentes)
    if ya_existe:
        return ResultadoValidacion(
            es_valido=False,
            motivo=f"El tipo de incidente '{tipo_limpio}' ya existe en el catálogo."
        )

    return ResultadoValidacion(es_valido=True, motivo="Tipo de incidente válido.")


def agregar_tipo_inmutable(
    tipos_existentes: Sequence[str],
    nuevo_tipo: str
) -> List[str]:
    """
    Función Pura: Retorna una nueva lista con el nuevo tipo incorporado.
    No muta la secuencia previa.
    """
    return list(tipos_existentes) + [nuevo_tipo.strip()]


# ============================================================================
# 4. RESTRICCIÓN DE LAMBDA: VALIDACIÓN COMPLEJA SECUENCIAL
# ============================================================================

def validar_incidente_complejo(incidente: Incidente) -> ResultadoValidacion:
    
    # 1. Validación secuencial: Integridad y anti-spam en la descripción
    val_desc = validar_descripcion(incidente.descripcion)
    if not val_desc.es_valido:
        return ResultadoValidacion(
            es_valido=False,
            motivo=f"Descripción inválida: {val_desc.motivo}"
        )

    # 2. Validación secuencial: Sector territorial válido
    sector_limpio = incidente.sector.strip()
    if len(sector_limpio) < 3:
        return ResultadoValidacion(
            es_valido=False,
            motivo=f"Sector territorial inválido ('{incidente.sector}'). Mínimo requerido: 3 caracteres."
        )

    # 3. Validación secuencial: Rango admisible de nivel de prioridad (1 a 10)
    if not (1 <= incidente.nivel_prioridad <= 10):
        return ResultadoValidacion(
            es_valido=False,
            motivo=f"Nivel de prioridad fuera de rango permitido [1, 10]: {incidente.nivel_prioridad}."
        )

    # 4. Validación secuencial: Coherencia de estado y prioridad crítica
    if incidente.nivel_prioridad >= 4 and incidente.estado == "Descartado":
        return ResultadoValidacion(
            es_valido=False,
            motivo="Incoherencia lógica: Un incidente con prioridad crítica no puede encontrarse en estado 'Descartado'."
        )

    return ResultadoValidacion(es_valido=True, motivo="Incidente válido en todas sus dimensiones.")


# ============================================================================
# 5. LÓGICA DE ROLES PURA (PERMISOS Y ACCESO DECLARATIVO)
# ============================================================================

def filtrar_por_permisos(
    incidentes: Sequence[Incidente],
    usuario: Usuario
) -> List[Incidente]:
    """
    Función Pura: Filtra una colección de incidentes según el rol y sector del usuario.

    Reglas de negocio funcionales:
    - Roles 'Admin' y 'Gobierno': Poseen alcance territorial global y acceden a todos los incidentes.
    - Rol 'Comunidad': Su acceso está estrictamente delimitado a su propio sector de residencia.
      Se utiliza la función de orden superior 'filter()' para restringir los resultados a aquellos
      incidentes cuyo sector coincida con 'usuario.sector'.

    Garantía de Pureza:
    - Transparencia referencial absoluta.
    - No muta las entidades de entrada ni la colección 'incidentes'.
    - Comportamiento puramente declarativo.
    """
    if usuario.rol in ('Admin', 'Gobierno'):
        return list(incidentes)

    # Rol 'Comunidad': filtrado declarativo por sector de pertenencia
    sector_usuario: str = usuario.sector.strip().casefold()

    def pertenece_a_sector_usuario(incidente: Incidente) -> bool:
        return incidente.sector.strip().casefold() == sector_usuario

    return list(filter(pertenece_a_sector_usuario, incidentes))


# ============================================================================
# 6. MODIFICACIÓN INMUTABLE DE INCIDENTES Y CONTROL DE TRANSICIONES
# ============================================================================

def validar_transicion_estado(
    estado_actual: str,
    nuevo_estado: str,
    rol_usuario: str,
    justificacion: str = ""
) -> ResultadoValidacion:
    """
    Función Pura: Valida la transición en el ciclo de vida de una incidencia.

    Reglas de negocio funcionales:
    - Comunidad: Sin permisos para modificar estados oficiales.
    - Gobierno:
      * Reportado -> EnProceso (Atención iniciada).
      * Reportado / EnProceso -> Descartado (Requiere justificación técnica >= 10 caracteres).
      * EnProceso -> Resuelto (Solución completada).
      * Resuelto -> EnProceso (Reapertura técnica por falla reincidente; requiere justificación >= 10 caracteres).
      * Descartado -> Bloqueado para gobierno (potestad exclusiva de Admin).
    - Admin:
      * Control total sobre cualquier estado.
      * Reaperturas (Resuelto -> EnProceso o Reportado) requieren justificación >= 10 caracteres.
      * Descarte (hacia Descartado) requiere justificación >= 10 caracteres.
      * Rehabilitación (desde Descartado a cualquier estado activo) requiere justificación >= 10 caracteres.
    """
    if rol_usuario not in ("Admin", "Gobierno"):
        return ResultadoValidacion(
            es_valido=False,
            motivo="Acceso denegado: El rol Comunidad no tiene autorización para modificar el estado de incidentes."
        )

    if estado_actual == nuevo_estado:
        return ResultadoValidacion(es_valido=True, motivo="Sin cambio de estado.")

    just_limpia = justificacion.strip()

    if rol_usuario == "Gobierno":
        if estado_actual == "Reportado" and nuevo_estado == "EnProceso":
            return ResultadoValidacion(es_valido=True, motivo="Atención de incidente iniciada por cuadrilla gubernamental.")

        if estado_actual in ("Reportado", "EnProceso") and nuevo_estado == "Descartado":
            if len(just_limpia) < 10:
                return ResultadoValidacion(
                    es_valido=False,
                    motivo="Para descartar un incidente se requiere una justificación técnica de al menos 10 caracteres."
                )
            return ResultadoValidacion(es_valido=True, motivo="Incidente descartado con justificación técnica.")

        if estado_actual == "EnProceso" and nuevo_estado == "Resuelto":
            return ResultadoValidacion(es_valido=True, motivo="Incidente resuelto satisfactoriamente.")

        if estado_actual == "Resuelto" and nuevo_estado == "EnProceso":
            if len(just_limpia) < 10:
                return ResultadoValidacion(
                    es_valido=False,
                    motivo="La reapertura de un incidente resuelto requiere una justificación técnica de al menos 10 caracteres."
                )
            return ResultadoValidacion(es_valido=True, motivo="Reapertura de incidente autorizada para gobierno.")

        if estado_actual == "Descartado":
            return ResultadoValidacion(
                es_valido=False,
                motivo="Solo el Administrador tiene autorización para rehabilitar un incidente que ya fue descartado."
            )

        return ResultadoValidacion(
            es_valido=False,
            motivo=f"Transición no permitida para Gobierno: no puede pasar de '{estado_actual}' a '{nuevo_estado}'."
        )

    if rol_usuario == "Admin":
        es_descarte = nuevo_estado == "Descartado"
        es_reapertura = estado_actual == "Resuelto" and nuevo_estado in ("EnProceso", "Reportado")
        es_rehabilitacion = estado_actual == "Descartado" and nuevo_estado in ("Reportado", "EnProceso", "Resuelto")

        if (es_descarte or es_reapertura or es_rehabilitacion) and len(just_limpia) < 10:
            tipo_accion = "descartar" if es_descarte else ("reabrir" if es_reapertura else "rehabilitar")
            return ResultadoValidacion(
                es_valido=False,
                motivo=f"Para {tipo_accion} una incidencia se requiere registrar una justificación de al menos 10 caracteres."
            )

        return ResultadoValidacion(es_valido=True, motivo=f"Transición administrativa autorizada hacia '{nuevo_estado}'.")

    return ResultadoValidacion(es_valido=False, motivo="Rol de usuario no autorizado.")


def actualizar_incidente(
    incidente_original: Incidente,
    sector: Optional[str] = None,
    descripcion: Optional[str] = None,
    tipo_incidente: Optional[str] = None,
    estado: Optional[str] = None,
    nivel_prioridad: Optional[int] = None,
    justificacion_estado: Optional[str] = None,
) -> Incidente:
    """
    Función Pura: Retorna una nueva copia inmutable de 'Incidente' con los atributos
    actualizados según los parámetros provistos.
    """
    cambios = {}
    if sector is not None:
        cambios["sector"] = sector.strip()
    if descripcion is not None:
        cambios["descripcion"] = descripcion.strip()
    if tipo_incidente is not None:
        cambios["tipo_incidente"] = tipo_incidente
    if estado is not None:
        cambios["estado"] = estado
    if nivel_prioridad is not None:
        cambios["nivel_prioridad"] = nivel_prioridad
    if justificacion_estado is not None:
        cambios["justificacion_estado"] = justificacion_estado.strip()

    return replace(incidente_original, **cambios)


# ============================================================================
# 7. ELIMINACIÓN INMUTABLE DE INCIDENTES (FILTER)
# ============================================================================

def eliminar_incidente_por_id(
    lista_incidentes: Sequence[Incidente],
    id_a_borrar: int
) -> List[Incidente]:
    """
    Función Pura: Retorna una nueva lista de incidentes excluyendo aquel cuyo ID
    coincide con 'id_a_borrar'.

    Regla Funcional Estricta:
    - Está TERMINANTEMENTE PROHIBIDO mutar la lista original (sin .remove(), del ni .pop()).
    - Emplea la función de orden superior 'filter' garantizando la inmutabilidad y
      la transparencia referencial (pureza matemática).
    """
    return list(filter(lambda inc: inc.id != id_a_borrar, lista_incidentes))

