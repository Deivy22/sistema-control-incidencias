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
from datetime import datetime
from typing import Callable, List, Optional, Sequence, Tuple

from core.models import EstadoIncidente, Incidente, TipoIncidente, Usuario
from core.engine import (
    actualizar_incidente,
    adherir_voto_incidente,
    agregar_tipo_inmutable,
    clasificar_incidente,
    eliminar_incidente_por_id,
    filtrar_por_permisos,
    ha_votado_usuario,
    validar_incidente_complejo,
    validar_nuevo_tipo_incidente,
    validar_tipo_incidente,
    validar_transicion_estado,
)
from core.analisis import (
    calcular_metricas_globales,
    crear_filtro_por_sector,
    filtrar_y_resumir_por_sector,
    calcular_prioridad_total,
    extraer_ids_incidentes,
)
from core.auth import (
    autenticar_usuario,
    validar_datos_usuario,
    construir_registro_usuario,
    agregar_usuario_inmutable,
)
from data.file_handler import (
    cargar_incidentes,
    guardar_incidentes,
    cargar_usuarios,
    guardar_usuarios,
    cargar_tipos_incidente,
    guardar_tipos_incidente,
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

    @property
    def puede_administrar_usuarios(self) -> bool:
        """Regla de roles: Solo 'Admin' tiene permisos exclusivos para gestionar y crear usuarios."""
        if self._usuario_actual is None:
            return False
        return self._usuario_actual.rol == "Admin"

    @property
    def puede_ver_metricas(self) -> bool:
        """Regla de roles: Solo 'Admin' y 'Gobierno' tienen acceso al panel de métricas."""
        if self._usuario_actual is None:
            return False
        return self._usuario_actual.rol in ("Admin", "Gobierno")

    def obtener_usuarios(self) -> List[dict]:
        """
        Retorna la lista de usuarios registrados recargada desde el almacenamiento persistente.
        """
        self._usuarios = cargar_usuarios()
        return [dict(u) for u in self._usuarios]

    def crear_usuario(
        self,
        username: str,
        password: str,
        nombre: str,
        rol: str,
        sector: str = ""
    ) -> Tuple[bool, str]:
        """
        Función Impura: Registra un nuevo usuario en el sistema.
        
        Garantías y Control de Acceso:
        - Acceso exclusivo al rol 'Admin'.
        - Delega la validación íntegra en la función pura 'validar_datos_usuario' de /core/auth.py.
        - Emplea transformaciones no destructivas ('agregar_usuario_inmutable') preservando la inmutabilidad.
        - Persiste en disco mediante 'guardar_usuarios' de /data/file_handler.py.
        """
        if not self.puede_administrar_usuarios:
            return False, "Acceso denegado: Solo los usuarios con rol 'Admin' pueden crear nuevos usuarios."

        # Cargar usuarios frescos desde el disco
        self._usuarios = cargar_usuarios()

        # Validación con función pura
        validacion = validar_datos_usuario(
            username=username,
            password=password,
            nombre=nombre,
            rol=rol,
            sector=sector,
            usuarios_existentes=self._usuarios
        )

        if not validacion.es_valido:
            return False, validacion.motivo

        # Asignación del próximo ID correlativo
        nuevo_id = max((int(u.get("id", 0)) for u in self._usuarios), default=0) + 1

        nuevo_registro = construir_registro_usuario(
            nuevo_id=nuevo_id,
            username=username,
            password=password,
            nombre=nombre,
            rol=rol,
            sector=sector
        )

        # Transformación inmutable de la colección
        self._usuarios = agregar_usuario_inmutable(self._usuarios, nuevo_registro)
        guardar_usuarios(self._usuarios)

        self._notificar()
        return True, f"Usuario '{nuevo_registro['username']}' ({nuevo_registro['rol']}) creado con éxito con ID #{nuevo_id}."

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

    def agregar_tipo_incidente(self, nuevo_tipo: str) -> Tuple[bool, str]:
        """
        Función Impura: Agrega un nuevo tipo de incidente al catálogo dinámico persistente.

        Garantías y Control de Roles:
        - Acceso exclusivo al rol 'Admin'.
        - Delega la validación en la función pura 'validar_nuevo_tipo_incidente' de /core/engine.py.
        - Emplea la función pura 'agregar_tipo_inmutable' para evitar mutación directa.
        - Persiste en disco mediante 'guardar_tipos_incidente' de /data/file_handler.py.
        - Notifica a observadores para refrescar los selectores de los formularios en vivo.
        """
        if not self.puede_administrar_usuarios:
            return False, "Acceso denegado: Solo los usuarios con rol 'Admin' pueden agregar tipos de incidente."

        self._tipos_incidente = cargar_tipos_incidente()

        validacion = validar_nuevo_tipo_incidente(nuevo_tipo, self._tipos_incidente)
        if not validacion.es_valido:
            return False, validacion.motivo

        self._tipos_incidente = agregar_tipo_inmutable(self._tipos_incidente, nuevo_tipo)
        guardar_tipos_incidente(self._tipos_incidente)

        self._notificar()
        return True, f"Tipo de incidente '{nuevo_tipo.strip()}' agregado exitosamente al catálogo."

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

        creador = self._usuario_actual.nombre if self._usuario_actual else "comunidad"
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M")

        candidato = Incidente(
            id=self._siguiente_id,
            sector=sector.strip(),
            descripcion=descripcion.strip(),
            tipo_incidente=tipo_incidente,  # type: ignore
            estado="Reportado",
            nivel_prioridad=prioridad_sugerida,
            fecha_reporte=fecha_hora,
            creado_por=creador,
            usuarios_votantes=(),
            justificacion_estado=""
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
        Función Impura: Incrementa votos delegando en la función pura 'adherir_voto_incidente'
        y haciendo cumplir la regla de 1 voto por usuario.
        """
        incidente_objetivo = self.obtener_incidente_por_id(incidente_id)
        if incidente_objetivo is None:
            return False, f"No se encontró el incidente #{incidente_id}."

        usuario_id = self._usuario_actual.id if self._usuario_actual else None

        if usuario_id is not None and ha_votado_usuario(incidente_objetivo, usuario_id):
            return False, f"Ya has registrado tu voto para el incidente #{incidente_id}. Cada usuario puede emitir un único voto."

        try:
            nuevo_incidente = adherir_voto_incidente(
                incidente=incidente_objetivo,
                incremento=incremento,
                usuario_id=usuario_id
            )
        except ValueError as e:
            return False, str(e)

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
        nivel_prioridad: int,
        justificacion: str = ""
    ) -> Tuple[bool, str]:
        """
        Función Impura: Modifica un incidente sin mutar el objeto original,
        validando transiciones lógicas de estado y delegando en 'actualizar_incidente'.
        """
        if not self.puede_modificar:
            return False, "Acceso denegado: El rol Comunidad no tiene permisos para modificar incidentes."

        incidente_original = self.obtener_incidente_por_id(incidente_id)
        if incidente_original is None:
            return False, f"No se encontró el incidente #{incidente_id} para modificar."

        if not validar_tipo_incidente(tipo_incidente, self._tipos_incidente):
            return False, f"El tipo '{tipo_incidente}' no es válido según el catálogo de incidentes."

        # Validación pura de transición de estado basada en rol y justificación
        val_transicion = validar_transicion_estado(
            estado_actual=incidente_original.estado,
            nuevo_estado=estado,
            rol_usuario=self._usuario_actual.rol,  # type: ignore
            justificacion=justificacion
        )
        if not val_transicion.es_valido:
            return False, val_transicion.motivo

        # DELEGACIÓN A FUNCIÓN PURA: genera una nueva copia inmutable sin mutar el original
        incidente_actualizado = actualizar_incidente(
            incidente_original=incidente_original,
            sector=sector,
            descripcion=descripcion,
            tipo_incidente=tipo_incidente,  # type: ignore
            estado=estado,                  # type: ignore
            nivel_prioridad=nivel_prioridad,
            justificacion_estado=justificacion if justificacion.strip() else incidente_original.justificacion_estado
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
        return True, f"Incidente #{incidente_id} actualizado con éxito ({val_transicion.motivo})."

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

    def obtener_metricas_sistema(self) -> dict:
        """
        Retorna el resumen analítico global de incidentes procesado mediante
        la función pura 'calcular_metricas_globales' de /core/analisis.py.
        """
        return calcular_metricas_globales(self._incidentes)
