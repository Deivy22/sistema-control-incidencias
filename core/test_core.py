"""
test_core.py - Suite de Pruebas Unitarias (Estándar unittest)
Valida Pureza, Inmutabilidad, Pattern Matching, Closures y HOFs sin dependencias externas.
"""

import unittest
from dataclasses import FrozenInstanceError
from core.models import Usuario, Incidente
from core.engine import (
    validar_descripcion,
    es_descripcion_valida,
    adherir_voto_incidente,
    ha_votado_usuario,
    clasificar_incidente,
    validar_incidente_complejo,
    validar_transicion_estado,
    filtrar_por_permisos,
    actualizar_incidente,
    validar_tipo_incidente,
    validar_nuevo_tipo_incidente,
    agregar_tipo_inmutable,
    eliminar_incidente_por_id,
    ResultadoValidacion,
)
from core.auth import (
    autenticar_usuario,
    validar_datos_usuario,
    construir_registro_usuario,
    agregar_usuario_inmutable,
)
from core.analisis import (
    calcular_metricas_globales,
    crear_filtro_por_sector,
    filtrar_y_resumir_por_sector,
    calcular_prioridad_total,
    extraer_ids_incidentes,
)


class TestCoreFuncional(unittest.TestCase):

    def test_inmutabilidad_usuario(self):
        """Valida que Usuario sea estrictamente inmutable (@dataclass(frozen=True))."""
        user = Usuario(id=1, nombre="Carlos Pérez", rol="Comunidad")
        with self.assertRaises(FrozenInstanceError):
            user.nombre = "Nuevo Nombre"  # type: ignore

    def test_inmutabilidad_incidente(self):
        """Valida que Incidente sea estrictamente inmutable (@dataclass(frozen=True))."""
        incidente = Incidente(
            id=101,
            sector="Norte",
            descripcion="Fuga de agua en la avenida principal",
            tipo_incidente="Alcantarillado",
            estado="Reportado",
            nivel_prioridad=2
        )
        with self.assertRaises(FrozenInstanceError):
            incidente.nivel_prioridad = 5  # type: ignore

    def test_adherir_voto_incidente_pureza_e_inmutabilidad(self):
        """Valida que adherir_voto_incidente no mute el objeto original y devuelva uno nuevo."""
        original = Incidente(
            id=202,
            sector="Centro",
            descripcion="Poste de luz derribado tras tormenta",
            tipo_incidente="FallaElectrica",
            estado="Reportado",
            nivel_prioridad=1
        )

        actualizado = adherir_voto_incidente(original, incremento=2)

        # 1. El objeto original mantiene intacto su estado (inmutabilidad)
        self.assertEqual(original.nivel_prioridad, 1)

        # 2. El nuevo objeto tiene el nuevo estado
        self.assertEqual(actualizado.nivel_prioridad, 3)

        # 3. Son instancias distintas en memoria (no mutación in-situ)
        self.assertIsNot(original, actualizado)

        # 4. Los demás campos permanecen idénticos
        self.assertEqual(actualizado.id, original.id)
        self.assertEqual(actualizado.sector, original.sector)
        self.assertEqual(actualizado.descripcion, original.descripcion)
        self.assertEqual(actualizado.tipo_incidente, original.tipo_incidente)
        self.assertEqual(actualizado.estado, original.estado)

    def test_validar_descripcion_spam_y_legitima(self):
        """Valida detección pura de spam y cadenas sin sentido."""
        # Spam 1: Longitud insuficiente
        res_corta = validar_descripcion("Poco texto")
        self.assertFalse(res_corta.es_valido)
        self.assertIn("insuficiente", res_corta.motivo)

        # Spam 2: Caracteres idénticos repetidos ('aaaaaaa')
        res_repetida = validar_descripcion("aaaaaaaabbbbbbbbbb")
        self.assertFalse(res_repetida.es_valido)
        self.assertIn("repetición excesiva", res_repetida.motivo)

        # Spam 3: Baja variedad de caracteres
        res_baja_variedad = validar_descripcion("abababababababababab")
        self.assertFalse(res_baja_variedad.es_valido)
        self.assertIn("baja variedad", res_baja_variedad.motivo)

        # Descripción ciudadana legítima
        texto_legitimo = "Semáforo apagado en la intersección de la carrera 7 con calle 45."
        res_valida = validar_descripcion(texto_legitimo)
        self.assertTrue(res_valida.es_valido)
        self.assertTrue(bool(res_valida))
        self.assertTrue(es_descripcion_valida(texto_legitimo))

    def test_pattern_matching_clasificar_incidente(self):
        """Valida la clasificación por pattern matching de tipos de incidentes."""
        incidente_choque = Incidente(1, "Centro", "Choque en avenida principal", "Choque", "Reportado", 3)
        p_choque, dep_choque = clasificar_incidente(incidente_choque)
        self.assertEqual(p_choque, 3)
        self.assertEqual(dep_choque, "Secretaría de Movilidad y Tránsito")

        incidente_falla = Incidente(2, "Centro", "Falla electrica en el sector", "FallaElectrica", "Reportado", 1)
        p_falla, dep_falla = clasificar_incidente(incidente_falla)
        self.assertEqual(p_falla, 4)
        self.assertEqual(dep_falla, "Departamento de Alumbrado y Redes Eléctricas")

        incidente_alcan = Incidente(3, "Centro", "Dano en alcantarillado", "Alcantarillado", "Reportado", 2)
        p_alcan, dep_alcan = clasificar_incidente(incidente_alcan)
        self.assertEqual(p_alcan, 2)
        self.assertEqual(dep_alcan, "Empresa de Acueducto y Alcantarillado")

        # Fallback defensivo
        incidente_otro = Incidente(4, "Centro", "Otro tipo de incidente", "Otro", "Reportado", 1)  # type: ignore
        p_otro, dep_otro = clasificar_incidente(incidente_otro)
        self.assertEqual(p_otro, 1)
        self.assertEqual(dep_otro, "Dirección General de Atención Ciudadana")

    def test_validar_incidente_complejo(self):
        """Valida la función pura validar_incidente_complejo y sus reglas secuenciales."""
        # Caso 1: Incidente completamente válido
        inc_valido = Incidente(
            id=10,
            sector="Suba",
            descripcion="Fuga importante de agua en la vía principal del barrio.",
            tipo_incidente="Alcantarillado",
            estado="Reportado",
            nivel_prioridad=3
        )
        res = validar_incidente_complejo(inc_valido)
        self.assertTrue(res.es_valido)

        # Caso 2: Falla por descripción spam
        inc_spam = Incidente(
            id=11,
            sector="Suba",
            descripcion="asdfasdf",
            tipo_incidente="Choque",
            estado="Reportado",
            nivel_prioridad=2
        )
        res_spam = validar_incidente_complejo(inc_spam)
        self.assertFalse(res_spam.es_valido)
        self.assertIn("Descripción inválida", res_spam.motivo)

        # Caso 3: Falla por sector inválido (< 3 caracteres)
        inc_sector_invalido = Incidente(
            id=12,
            sector="  ",
            descripcion="Poste de energía a punto de caer sobre la calzada peatonal.",
            tipo_incidente="FallaElectrica",
            estado="Reportado",
            nivel_prioridad=3
        )
        res_sector = validar_incidente_complejo(inc_sector_invalido)
        self.assertFalse(res_sector.es_valido)
        self.assertIn("Sector territorial inválido", res_sector.motivo)

        # Caso 4: Falla por prioridad fuera de rango
        inc_prioridad_invalida = Incidente(
            id=13,
            sector="Chapinero",
            descripcion="Poste de energía a punto de caer sobre la calzada peatonal.",
            tipo_incidente="FallaElectrica",
            estado="Reportado",
            nivel_prioridad=15
        )
        res_prio = validar_incidente_complejo(inc_prioridad_invalida)
        self.assertFalse(res_prio.es_valido)
        self.assertIn("fuera de rango", res_prio.motivo)

        # Caso 5: Incoherencia estado vs prioridad crítica
        inc_incoherente = Incidente(
            id=14,
            sector="Chapinero",
            descripcion="Colisión múltiple con heridos graves en la autopista norte.",
            tipo_incidente="Choque",
            estado="Descartado",
            nivel_prioridad=5
        )
        res_inc = validar_incidente_complejo(inc_incoherente)
        self.assertFalse(res_inc.es_valido)
        self.assertIn("Incoherencia lógica", res_inc.motivo)

    def test_closure_filtro_por_sector(self):
        """Valida que crear_filtro_por_sector sea un closure real con ámbito léxico cerrado."""
        filtro_norte = crear_filtro_por_sector("Norte")
        inc_norte = Incidente(1, "Norte", "Desc valida de prueba para el sector", "Choque", "Reportado", 2)
        inc_sur = Incidente(2, "Sur", "Desc valida de prueba para el sector", "Choque", "Reportado", 2)

        self.assertTrue(callable(filtro_norte))
        self.assertTrue(filtro_norte(inc_norte))
        self.assertFalse(filtro_norte(inc_sur))

        # Verificación formal del closure (captura de variable libre)
        self.assertIsNotNone(filtro_norte.__closure__)
        self.assertEqual(len(filtro_norte.__closure__), 1)

    def test_filtrar_y_resumir_por_sector_filter_map(self):
        """Valida filter y map estructurados en filtrar_y_resumir_por_sector."""
        incidentes = [
            Incidente(1, "Centro", "Colision entre dos vehiculos particulares.", "Choque", "Reportado", 4),
            Incidente(2, "Norte", "Falla de transformador en zona residencial.", "FallaElectrica", "Reportado", 3),
            Incidente(3, "Centro", "Rebosamiento de aguas residuales en la calle.", "Alcantarillado", "Reportado", 2),
            Incidente(4, "Sur", "Poste inclinado con peligro inminente de caida.", "FallaElectrica", "Reportado", 1),
        ]

        resumenes_centro = filtrar_y_resumir_por_sector(incidentes, "Centro")

        # Debe contener solo los 2 del Centro transformados en strings
        self.assertEqual(len(resumenes_centro), 2)
        self.assertEqual(resumenes_centro[0], "ID: 1 - Choque - Crítico")
        self.assertEqual(resumenes_centro[1], "ID: 3 - Alcantarillado - Medio")

    def test_calcular_prioridad_total_reduce(self):
        """Valida el cálculo de prioridad acumulada mediante functools.reduce."""
        incidentes = [
            Incidente(1, "Centro", "Desc valida 1", "Choque", "Reportado", 4),
            Incidente(2, "Norte", "Desc valida 2", "FallaElectrica", "Reportado", 3),
            Incidente(3, "Centro", "Desc valida 3", "Alcantarillado", "Reportado", 2),
        ]
        total = calcular_prioridad_total(incidentes)
        self.assertEqual(total, 9)

        # Caso lista vacía: debe retornar 0 deterministicamente
        self.assertEqual(calcular_prioridad_total([]), 0)

    def test_filtrar_por_permisos_roles(self):
        """Valida que filtrar_por_permisos restrinja por rol y sector usando filter()."""
        incidentes = [
            Incidente(1, "Sector Norte", "Desc 1", "Choque", "Reportado", 3),
            Incidente(2, "Sector Centro", "Desc 2", "FallaElectrica", "Reportado", 4),
            Incidente(3, "Sector Norte", "Desc 3", "Alcantarillado", "Reportado", 2),
            Incidente(4, "Sector Sur", "Desc 4", "Choque", "Reportado", 1),
        ]

        admin = Usuario(id=1, nombre="Admin", rol="Admin", sector="Todos")
        gobierno = Usuario(id=2, nombre="Gobierno", rol="Gobierno", sector="Distrito")
        comunidad_norte = Usuario(id=3, nombre="Vecino Norte", rol="Comunidad", sector="Sector Norte")
        comunidad_sur = Usuario(id=4, nombre="Vecino Sur", rol="Comunidad", sector="Sector Sur")

        # Admin y Gobierno ven todo (4 incidentes)
        self.assertEqual(len(filtrar_por_permisos(incidentes, admin)), 4)
        self.assertEqual(len(filtrar_por_permisos(incidentes, gobierno)), 4)

        # Comunidad Norte solo ve los 2 de Sector Norte
        visibles_norte = filtrar_por_permisos(incidentes, comunidad_norte)
        self.assertEqual(len(visibles_norte), 2)
        for inc in visibles_norte:
            self.assertEqual(inc.sector, "Sector Norte")

        # Comunidad Sur solo ve el 1 de Sector Sur
        visibles_sur = filtrar_por_permisos(incidentes, comunidad_sur)
        self.assertEqual(len(visibles_sur), 1)
        self.assertEqual(visibles_sur[0].id, 4)

    def test_actualizar_incidente_inmutabilidad(self):
        """Valida que actualizar_incidente retorne una nueva copia sin mutar el original."""
        original = Incidente(1, "Sector Norte", "Fuga de gas", "FallaElectrica", "Reportado", 4)
        actualizado = actualizar_incidente(
            incidente_original=original,
            estado="EnProceso",
            nivel_prioridad=5
        )

        # 1. El original se mantiene inalterado
        self.assertEqual(original.estado, "Reportado")
        self.assertEqual(original.nivel_prioridad, 4)

        # 2. El nuevo objeto tiene las actualizaciones
        self.assertEqual(actualizado.estado, "EnProceso")
        self.assertEqual(actualizado.nivel_prioridad, 5)

        # 3. Campos no modificados se preservan
        self.assertEqual(actualizado.id, original.id)
        self.assertEqual(actualizado.sector, original.sector)
        self.assertEqual(actualizado.descripcion, original.descripcion)
        self.assertEqual(actualizado.tipo_incidente, original.tipo_incidente)

        # 4. Son identidades en memoria distintas
        self.assertIsNot(original, actualizado)

    def test_autenticar_usuario_pura(self):
        """Valida la función pura autenticar_usuario contra una base de datos inmutable."""
        bd_simulada = [
            {"id": 1, "username": "admin", "password": "secret_admin", "nombre": "Admin User", "rol": "Admin", "sector": "Todos"},
            {"id": 2, "username": "vecino", "password": "pass_vecino", "nombre": "Vecino Juan", "rol": "Comunidad", "sector": "Sector Sur"}
        ]

        # Caso éxito
        u = autenticar_usuario("admin", "secret_admin", bd_simulada)
        self.assertIsNotNone(u)
        self.assertEqual(u.nombre, "Admin User")
        self.assertEqual(u.rol, "Admin")

        # Caso clave errónea
        self.assertIsNone(autenticar_usuario("admin", "clave_falsa", bd_simulada))

        # Caso usuario inexistente
        self.assertIsNone(autenticar_usuario("inexistente", "cualquiera", bd_simulada))

    def test_validar_tipo_incidente_dinamico(self):
        """Valida que la función pura validar_tipo_incidente verifique la pertenencia al catálogo."""
        catalogo = ["Choque", "Falla Electrica", "Alcantarillado", "Infraestructura"]

        self.assertTrue(validar_tipo_incidente("Choque", catalogo))
        self.assertTrue(validar_tipo_incidente("falla electrica", catalogo))  # case-insensitive
        self.assertTrue(validar_tipo_incidente("Alcantarillado ", catalogo))  # strip whitespace
        self.assertFalse(validar_tipo_incidente("Inexistente", catalogo))

    def test_extraer_ids_incidentes_hof_map(self):
        """Valida que extraer_ids_incidentes proyecte los identificadores usando map()."""
        incidentes = [
            Incidente(10, "Sector Norte", "Desc 1", "Choque", "Reportado", 3),
            Incidente(25, "Sector Centro", "Desc 2", "FallaElectrica", "Reportado", 4),
            Incidente(42, "Sector Sur", "Desc 3", "Alcantarillado", "Reportado", 2),
        ]
        ids = extraer_ids_incidentes(incidentes)
        self.assertEqual(ids, [10, 25, 42])

        # Caso lista vacía
        self.assertEqual(extraer_ids_incidentes([]), [])

    def test_eliminar_incidente_por_id_pureza_e_inmutabilidad(self):
        """
        Valida que eliminar_incidente_por_id sea una función pura que no muta la lista original,
        utiliza filter y devuelve una nueva lista con el elemento excluido.
        """
        incidentes_originales = [
            Incidente(1, "Sector Norte", "Desc 1", "Choque", "Reportado", 3),
            Incidente(2, "Sector Centro", "Desc 2", "FallaElectrica", "Reportado", 4),
            Incidente(3, "Sector Sur", "Desc 3", "Alcantarillado", "Reportado", 2),
        ]
        # Copia superficial para verificar invariancia estricta de la lista original
        copia_referencia = list(incidentes_originales)

        # 1. Eliminar elemento existente (ID=2)
        resultado = eliminar_incidente_por_id(incidentes_originales, id_a_borrar=2)

        # 2. La lista original no sufrió mutación (regla funcional estricta)
        self.assertEqual(len(incidentes_originales), 3)
        self.assertEqual(incidentes_originales, copia_referencia)
        self.assertEqual([inc.id for inc in incidentes_originales], [1, 2, 3])

        # 3. La nueva lista contiene únicamente los elementos no coincidentes
        self.assertEqual(len(resultado), 2)
        self.assertEqual([inc.id for inc in resultado], [1, 3])

        # 4. Son identidades de lista distintas en memoria
        self.assertIsNot(resultado, incidentes_originales)

        # 5. Eliminar ID inexistente retorna nueva lista idéntica sin alterar nada
        resultado_inexistente = eliminar_incidente_por_id(incidentes_originales, id_a_borrar=999)
        self.assertEqual(len(resultado_inexistente), 3)
        self.assertEqual([inc.id for inc in resultado_inexistente], [1, 2, 3])
        self.assertIsNot(resultado_inexistente, incidentes_originales)

    def test_validar_datos_usuario_puro_exito(self):
        """Valida que validar_datos_usuario acepte datos conformes."""
        existentes = [{"id": 1, "username": "admin", "rol": "Admin"}]
        res = validar_datos_usuario(
            username="nuevo_vecino",
            password="password123",
            nombre="Juan Pérez",
            rol="Comunidad",
            sector="Sector Norte",
            usuarios_existentes=existentes
        )
        self.assertTrue(res.es_valido)
        self.assertEqual(res.motivo, "Datos de usuario válidos.")

    def test_validar_datos_usuario_puro_rechazos(self):
        """Valida rechazos específicos por reglas funcionales de validación."""
        existentes = [{"id": 1, "username": "carlos", "rol": "Comunidad"}]

        # 1. Nombre muy corto
        res_nom = validar_datos_usuario("user1", "pass123", "Al", "Comunidad", "Sector Norte", existentes)
        self.assertFalse(res_nom.es_valido)
        self.assertIn("al menos 3 caracteres", res_nom.motivo)

        # 2. Username muy corto
        res_usr = validar_datos_usuario("ab", "pass123", "Alberto", "Comunidad", "Sector Norte", existentes)
        self.assertFalse(res_usr.es_valido)
        self.assertIn("al menos 3 caracteres", res_usr.motivo)

        # 3. Username con caracteres especiales no permitidos
        res_char = validar_datos_usuario("user@#$", "pass123", "Alberto", "Comunidad", "Sector Norte", existentes)
        self.assertFalse(res_char.es_valido)
        self.assertIn("solo puede contener", res_char.motivo)

        # 4. Username duplicado (case-insensitive)
        res_dup = validar_datos_usuario("CARLOS", "pass123", "Carlos Otro", "Comunidad", "Sector Norte", existentes)
        self.assertFalse(res_dup.es_valido)
        self.assertIn("ya está registrado", res_dup.motivo)

        # 5. Contraseña corta
        res_pwd = validar_datos_usuario("usuario_nuevo", "12", "Alberto", "Comunidad", "Sector Norte", existentes)
        self.assertFalse(res_pwd.es_valido)
        self.assertIn("al menos 4 caracteres", res_pwd.motivo)

        # 6. Rol no reconocido
        res_rol = validar_datos_usuario("usuario_nuevo", "pass123", "Alberto", "SuperUser", "Sector Norte", existentes)
        self.assertFalse(res_rol.es_valido)
        self.assertIn("no reconocido", res_rol.motivo)

        # 7. Rol Comunidad sin sector
        res_sec = validar_datos_usuario("usuario_nuevo", "pass123", "Alberto", "Comunidad", "  ", existentes)
        self.assertFalse(res_sec.es_sec_err if hasattr(res_sec, "es_sec_err") else res_sec.es_valido)
        self.assertIn("obligatorio", res_sec.motivo)

    def test_construir_registro_usuario_y_agregar_inmutable(self):
        """Valida la construcción pura y la agregación no destructiva de usuarios."""
        existentes = [{"id": 1, "username": "admin", "rol": "Admin"}]
        copia_ref = list(existentes)

        nuevo = construir_registro_usuario(
            nuevo_id=2,
            username="laura_distrito",
            password="sec123password",
            nombre="Laura Méndez",
            rol="Gobierno",
            sector=""  # default automático para Gobierno -> "Distrito"
        )
        self.assertEqual(nuevo["id"], 2)
        self.assertEqual(nuevo["sector"], "Distrito")

        actualizada = agregar_usuario_inmutable(existentes, nuevo)

        # La lista original no se mutó
        self.assertEqual(len(existentes), 1)
        self.assertEqual(existentes, copia_ref)

        # La nueva lista contiene 2 elementos y no es la misma referencia
        self.assertEqual(len(actualizada), 2)
        self.assertIsNot(actualizada, existentes)
        self.assertEqual(actualizada[1]["username"], "laura_distrito")

    def test_validar_nuevo_tipo_incidente_puro(self):
        """Valida que validar_nuevo_tipo_incidente aplique reglas puras de dominio."""
        existentes = ["Choque", "Falla Electrica", "Alcantarillado"]

        # 1. Éxito con tipo válido
        res_ok = validar_nuevo_tipo_incidente("Fuga de Gas", existentes)
        self.assertTrue(res_ok.es_valido)

        # 2. Rechazo por longitud insuficiente
        res_corta = validar_nuevo_tipo_incidente("Ab", existentes)
        self.assertFalse(res_corta.es_valido)
        self.assertIn("al menos 3 caracteres", res_corta.motivo)

        # 3. Rechazo por duplicado case-insensitive
        res_dup = validar_nuevo_tipo_incidente("choque", existentes)
        self.assertFalse(res_dup.es_valido)
        self.assertIn("ya existe", res_dup.motivo)

        # 4. Rechazo por caracteres inválidos
        res_char = validar_nuevo_tipo_incidente("Tipo<script>alert(1)</script>", existentes)
        self.assertFalse(res_char.es_valido)
        self.assertIn("solo puede contener", res_char.motivo)

    def test_agregar_tipo_inmutable_puro(self):
        """Valida que agregar_tipo_inmutable preserve la colección original."""
        existentes = ["Choque", "Falla Electrica"]
        copia_ref = list(existentes)

        nueva_lista = agregar_tipo_inmutable(existentes, "Inundación")

        self.assertEqual(existentes, copia_ref)
        self.assertEqual(len(existentes), 2)
        self.assertEqual(len(nueva_lista), 3)
        self.assertIsNot(nueva_lista, existentes)
        self.assertIn("Inundación", nueva_lista)

    def test_voto_unico_por_usuario_puro(self):
        """Valida que un usuario solo pueda votar una vez y se registre en la tupla inmutable."""
        inc = Incidente(1, "Sector Norte", "Bache peligroso", "Infraestructura", "Reportado", 2)
        self.assertFalse(ha_votado_usuario(inc, usuario_id=5))

        # Primer voto del usuario 5
        inc_votado = adherir_voto_incidente(inc, incremento=1, usuario_id=5)
        self.assertEqual(inc_votado.nivel_prioridad, 3)
        self.assertTrue(ha_votado_usuario(inc_votado, usuario_id=5))
        self.assertEqual(inc_votado.usuarios_votantes, (5,))

        # La instancia original no se mutó
        self.assertEqual(inc.usuarios_votantes, ())
        self.assertEqual(inc.nivel_prioridad, 2)

        # Intento de segundo voto del mismo usuario debe lanzar ValueError
        with self.assertRaises(ValueError):
            adherir_voto_incidente(inc_votado, incremento=1, usuario_id=5)

    def test_validar_transicion_estado_gobierno(self):
        """Valida las transiciones operacionales de gobierno con y sin justificación."""
        # 1. Reportado -> EnProceso (Válido sin justificación)
        val_ini = validar_transicion_estado("Reportado", "EnProceso", "Gobierno")
        self.assertTrue(val_ini.es_valido)

        # 2. EnProceso -> Resuelto (Válido sin justificación)
        val_res = validar_transicion_estado("EnProceso", "Resuelto", "Gobierno")
        self.assertTrue(val_res.es_valido)

        # 3. Resuelto -> EnProceso (Reapertura técnica: requiere justificación)
        val_reap_err = validar_transicion_estado("Resuelto", "EnProceso", "Gobierno", justificacion="Corta")
        self.assertFalse(val_reap_err.es_valido)
        self.assertIn("justificación técnica", val_reap_err.motivo)

        val_reap_ok = validar_transicion_estado(
            "Resuelto", "EnProceso", "Gobierno",
            justificacion="Reapareció hundimiento tras tormenta nocturna"
        )
        self.assertTrue(val_reap_ok.es_valido)

        # 4. Descartado -> Reportado (Prohibido para gobierno, potestad de Admin)
        val_desc_err = validar_transicion_estado("Descartado", "Reportado", "Gobierno")
        self.assertFalse(val_desc_err.es_valido)
        self.assertIn("Solo el Administrador", val_desc_err.motivo)

    def test_validar_transicion_estado_admin(self):
        """Valida que Admin pueda mover a cualquier estado requiriendo justificación para reaperturas/descartes."""
        # Descartado -> Reportado (Rehabilitación administrativa con justificación)
        val_rehab_err = validar_transicion_estado("Descartado", "Reportado", "Admin", justificacion="")
        self.assertFalse(val_rehab_err.es_valido)

        val_rehab_ok = validar_transicion_estado(
            "Descartado", "Reportado", "Admin",
            justificacion="Revisión de solicitud comunitaria con evidencia fotográfica válida."
        )
        self.assertTrue(val_rehab_ok.es_valido)

    def test_calcular_metricas_globales_puro(self):
        """Valida el cálculo analítico puro de métricas mediante HOFs."""
        incidentes = [
            Incidente(1, "Sector Norte", "Desc 1", "Choque", "Resuelto", 3),
            Incidente(2, "Sector Norte", "Desc 2", "FallaElectrica", "EnProceso", 4),
            Incidente(3, "Sector Centro", "Desc 3", "Alcantarillado", "Reportado", 5),
            Incidente(4, "Sector Sur", "Desc 4", "Choque", "Descartado", 1),
        ]
        metricas = calcular_metricas_globales(incidentes)

        self.assertEqual(metricas["total"], 4)
        self.assertEqual(metricas["resueltos"], 1)
        self.assertEqual(metricas["en_proceso"], 1)
        self.assertEqual(metricas["reportados"], 1)
        self.assertEqual(metricas["descartados"], 1)
        self.assertEqual(metricas["tasa_resolucion"], 25.0)
        self.assertEqual(metricas["criticos_pendientes"], 2)  # IDs 2 y 3 (prio >= 4, activos)
        self.assertEqual(metricas["prioridad_total"], 13)
        self.assertEqual(metricas["promedio_prioridad"], 3.25)
        self.assertEqual(metricas["por_sector"]["Sector Norte"], 2)
        self.assertEqual(metricas["por_tipo"]["Choque"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
