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
    clasificar_incidente,
    validar_incidente_complejo,
    filtrar_por_permisos,
    actualizar_incidente,
    validar_tipo_incidente,
    eliminar_incidente_por_id,
    ResultadoValidacion,
)
from core.auth import autenticar_usuario
from core.analisis import (
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
