"""
state_manager.py - Gestor de Estado Impuro, Sesión y Persistencia
Sistema de Control de Incidencias Ciudadanas
Arquitectura: Functional Core, Imperative Shell (FCIS)

Este módulo gestiona el estado mutable de la aplicación y la persistencia en disco:
- Conecta con '/data/file_handler.py' para cargar y guardar 'incidentes.json', 'usuarios.json'
  y el catálogo dinámico 'tipos_incidente.json'.
- Delega la autenticación a 'autenticar_usuario' en '/core/auth.py'.
- Delega transformaciones a 'actualizar_incidente' en '/core/engine.py'.
- Delega el filtrado de visualización a 'filtrar_por_permisos' en '/core/engine.py'.
- Delega la extracción de IDs a 'extraer_ids_incidentes' (map) en '/core/analisis.py'.
"""

from dataclasses import replace
from typing import Callable, List, Optional, Sequence, Tuple

from core.models import EstadoIncidente, Incidente, TipoIncidente, Usuario
from core.engine import (
    actualizar_incidente,
    adherir_voto_incidente,
    clasificar_incidente,
    eliminar_incidente_por_id,
    filtrar_por_permisos,
    validar_incidente_complejo,
    validar_tipo_incidente,
)
from core.analisis import (
    crear_filtro_por_sector,
    filtrar_y_resumir_por_sector,
    calcular_prioridad_total,
    extraer_ids_incidentes,
)
from core.auth import autenticar_usuario
from data.file_handler import (
    cargar_incidentes,
    guardar_incidentes,
    cargar_usuarios,
    cargar_tipos_incidente,
)


class StateManager:
    """
    Gestor de Estado Impuro de la Aplicación.
    """

    def __init__(self) -> None:
        # Carga impura desde disco
        self._incidentes: List[Incidente] = cargar_incidentes()
        self._usuarios: List[dict] = cargar_usuarios()
        self._tipos_incidente: List[str] = cargar_tipos_incidente()

        # Estado de sesión
        self._usuario_actual: Optional[Usuario] = None

        # Filtro complementario de sector
        self._filtro_sector: Optional[str] = None

        # Incidente actualmente cargado para edición en el formulario
        self._incidente_en_edicion: Optional[Incidente] = None

        # Siguiente ID correlativo
        max_id = max((inc.id for inc in self._incidentes), default=0)
        self._siguiente_id: int = max_id + 1

        # Observadores (Patrón Observer)
        self._subscriptores: List[Callable[[], None]] = []

    # ========================================================================
    # GESTIÓN DE SESIÓN Y AUTENTICACIÓN
    # ========================================================================

    @property
    def usuario_actual(self) -> Optional[Usuario]:
        return self._usuario_actual

    @property
    def puede_modificar(self) -> bool:
        """Regla de roles: Solo 'Admin' y 'Gobierno' pueden modificar incidencias."""
        if self._usuario_actual is None:
            return False
        return self._usuario_actual.rol in ('Admin', 'Gobierno')

    @property
    def puede_eliminar(self) -> bool:
        """Regla de roles: Solo 'Admin' puede eliminar registros de incidentes."""
        if self._usuario_actual is None:
            return False
        return self._usuario_actual.rol == "Admin"

    def autenticar(self, user: str, password: str) -> Tuple[bool, str]:
        """
        Función Impura: Autentica al usuario delegando la validación de credenciales
        a la función pura 'autenticar_usuario' de /core/auth.py.
        """
        # Refrescar usuarios por si hubo cambios en disco
        self._usuarios = cargar_usuarios()
        usuario_validado = autenticar_usuario(user, password, self._usuarios)

        if usuario_validado is None:
            return False, "Credenciales inválidas. Verifique su nombre de usuario y contraseña."

        self.iniciar_sesion(usuario_validado)
        return True, f"Bienvenido/a, {usuario_validado.nombre} ({usuario_validado.rol})."

    def iniciar_sesion(self, usuario: Usuario) -> None:
        """Inicia la sesión y notifica a los observadores."""
        self._usuario_actual = usuario
        self._filtro_sector = None
        self._incidente_en_edicion = None
        self._notificar()

    def cerrar_sesion(self) -> None:
        """
        Finaliza la sesión actual y limpia observadores de la vista saliente
        para evitar llamadas zombi a widgets destruidos.
        """
        self._usuario_actual = None
        self._filtro_sector = None
        self._incidente_en_edicion = None
        self._subscriptores.clear()

    # ========================================================================
    # OBSERVADORES (PATRÓN OBSERVER SEGURO)
    # ========================================================================

    def suscribir(self, callback: Callable[[], None]) -> None:
        if callback not in self._subscriptores:
            self._subscriptores.append(callback)

    def desuscribir(self, callback: Callable[[], None]) -> None:
        if callback in self._subscriptores:
            self._subscriptores.remove(callback)

    def _notificar(self) -> None:
        copia = list(self._subscriptores)
        for callback in copia:
            try:
                callback()
            except Exception:
                # Si el callback falla por widget destruido, remover limpiamente
                if callback in self._subscriptores:
                    self._subscriptores.remove(callback)

    # ========================================================================
    # CATÁLOGO DINÁMICO DE TIPOS Y EXTRACCIÓN DE IDENTIFICADORES
    # ========================================================================

    def obtener_tipos_incidente(self) -> List[str]:
        """
        Retorna la lista de tipos de incidente cargados dinámicamente desde /data/tipos_incidente.json.
        """
        # Recargar en caliente si hubo cambios
        self._tipos_incidente = cargar_tipos_incidente()
        return list(self._tipos_incidente)

    def obtener_ids_incidentes(self) -> List[int]:
        """
        Retorna la lista de IDs de incidentes existentes proyectados
        mediante la función pura de orden superior 'extraer_ids_incidentes' (map) de /core/analisis.py.
        """
        return extraer_ids_incidentes(self._incidentes)

    # ========================================================================
    # MUTACIONES CON DELEGACIÓN PURA Y PERSISTENCIA AUTOMÁTICA
    # ========================================================================

    def agregar_incidente(
        self,
        sector: str,
        descripcion: str,
        tipo_incidente: str
    ) -> Tuple[bool, str]:
        """
        Función Impura: Registra un nuevo incidente delegando validación de tipo y compleja al core.
        """
        # Validación pura del tipo dinámico
        if not validar_tipo_incidente(tipo_incidente, self._tipos_incidente):
            return False, f"El tipo de incidente '{tipo_incidente}' no es válido según el catálogo activo."

        prioridad_sugerida, _ = clasificar_incidente(tipo_incidente)

        candidato = Incidente(
            id=self._siguiente_id,
            sector=sector.strip(),
            descripcion=descripcion.strip(),
            tipo_incidente=tipo_incidente,  # type: ignore
            estado="Reportado",
            nivel_prioridad=prioridad_sugerida
        )

        validacion = validar_incidente_complejo(candidato)
        if not validacion.es_valido:
            return False, validacion.motivo

        self._incidentes.append(candidato)
        self._siguiente_id += 1
        guardar_incidentes(self._incidentes)

        self._notificar()
        return True, f"Incidente #{candidato.id} registrado correctamente."

    def adherir_voto(self, incidente_id: int, incremento: int = 1) -> Tuple[bool, str]:
        """
        Función Impura: Incrementa votos delegando en la función pura 'adherir_voto_incidente'.
        """
        incidente_objetivo = self.obtener_incidente_por_id(incidente_id)
        if incidente_objetivo is None:
            return False, f"No se encontró el incidente #{incidente_id}."

        nuevo_incidente = adherir_voto_incidente(incidente_objetivo, incremento)

        self._incidentes = [
            nuevo_incidente if inc.id == incidente_id else inc
            for inc in self._incidentes
        ]
        guardar_incidentes(self._incidentes)

        self._notificar()
        return True, f"Voto adherido al incidente #{incidente_id}. Nueva prioridad: {nuevo_incidente.nivel_prioridad}."

    def modificar_incidente(
        self,
        incidente_id: int,
        sector: str,
        descripcion: str,
        tipo_incidente: str,
        estado: str,
        nivel_prioridad: int
    ) -> Tuple[bool, str]:
        """
        Función Impura: Modifica un incidente sin mutar el objeto original,
        delegando en la función pura 'actualizar_incidente' de /core/engine.py.
        """
        if not self.puede_modificar:
            return False, "Acceso denegado: El rol Comunidad no tiene permisos para modificar incidentes."

        incidente_original = self.obtener_incidente_por_id(incidente_id)
        if incidente_original is None:
            return False, f"No se encontró el incidente #{incidente_id} para modificar."

        if not validar_tipo_incidente(tipo_incidente, self._tipos_incidente):
            return False, f"El tipo '{tipo_incidente}' no es válido según el catálogo de incidentes."

        # DELEGACIÓN A FUNCIÓN PURA: genera una nueva copia inmutable sin mutar el original
        incidente_actualizado = actualizar_incidente(
            incidente_original=incidente_original,
            sector=sector,
            descripcion=descripcion,
            tipo_incidente=tipo_incidente,  # type: ignore
            estado=estado,                  # type: ignore
            nivel_prioridad=nivel_prioridad
        )

        validacion = validar_incidente_complejo(incidente_actualizado)
        if not validacion.es_valido:
            return False, validacion.motivo

        self._incidentes = [
            incidente_actualizado if inc.id == incidente_id else inc
            for inc in self._incidentes
        ]
        guardar_incidentes(self._incidentes)

        self._incidente_en_edicion = None
        self._notificar()
        return True, f"Incidente #{incidente_id} actualizado con éxito."

    def eliminar_incidente(self, incidente_id: int) -> Tuple[bool, str]:
        """
        Función Impura: Elimina un incidente delegando en la función pura
        'eliminar_incidente_por_id' de /core/engine.py.
        Garantiza inmutabilidad y persiste la nueva colección en disco.
        """
        if not self.puede_eliminar:
            return False, "Acceso denegado: Solo los usuarios con rol 'Admin' pueden eliminar registros."

        incidente_objetivo = self.obtener_incidente_por_id(incidente_id)
        if incidente_objetivo is None:
            return False, f"No se encontró el incidente #{incidente_id} para eliminar."

        # DELEGACIÓN A FUNCIÓN PURA: genera una nueva lista sin mutar la original
        self._incidentes = eliminar_incidente_por_id(self._incidentes, incidente_id)
        guardar_incidentes(self._incidentes)

        # Si el incidente eliminado estaba cargado en edición, limpiar el búfer
        if self._incidente_en_edicion and self._incidente_en_edicion.id == incidente_id:
            self._incidente_en_edicion = None

        self._notificar()
        return True, f"Incidente #{incidente_id} eliminado exitosamente."

    def obtener_incidente_por_id(self, incidente_id: int) -> Optional[Incidente]:
        return next((inc for inc in self._incidentes if inc.id == incidente_id), None)

    # ========================================================================
    # GESTIÓN DEL INCIDENTE EN EDICIÓN
    # ========================================================================

    @property
    def incidente_en_edicion(self) -> Optional[Incidente]:
        return self._incidente_en_edicion

    def cargar_incidente_para_edicion(self, incidente: Incidente) -> None:
        self._incidente_en_edicion = incidente
        self._notificar()

    def limpiar_edicion(self) -> None:
        self._incidente_en_edicion = None
        self._notificar()

    # ========================================================================
    # FILTRADO Y CONSULTAS PURAS
    # ========================================================================

    def aplicar_filtro_sector(self, sector: Optional[str]) -> None:
        if sector is None or not sector.strip():
            self._filtro_sector = None
        else:
            self._filtro_sector = sector.strip()
        self._notificar()

    def limpiar_filtro(self) -> None:
        self._filtro_sector = None
        self._notificar()

    @property
    def filtro_sector_actual(self) -> Optional[str]:
        return self._filtro_sector

    def obtener_incidentes_visibles(self) -> List[Incidente]:
        """
        Retorna la lista de incidentes visibles invocando 'filtrar_por_permisos'
        de /core/engine.py según el usuario activo.
        """
        if self._usuario_actual is not None:
            permitidos = filtrar_por_permisos(self._incidentes, self._usuario_actual)
        else:
            permitidos = list(self._incidentes)

        if self._filtro_sector:
            filtro_closure = crear_filtro_por_sector(self._filtro_sector)
            return list(filter(filtro_closure, permitidos))

        return permitidos

    def obtener_resumenes_sector(self) -> List[str]:
        if self._filtro_sector:
            return filtrar_y_resumir_por_sector(self.obtener_incidentes_visibles(), self._filtro_sector)
        return []

    def obtener_prioridad_total_visible(self) -> int:
        return calcular_prioridad_total(self.obtener_incidentes_visibles())

    def obtener_info_departamento(self, incidente: Incidente) -> str:
        _, departamento = clasificar_incidente(incidente)
        return departamento
