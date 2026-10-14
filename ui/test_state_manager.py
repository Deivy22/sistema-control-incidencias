"""
test_state_manager.py - Pruebas del Gestor de Estado Impuro y Sesión
Valida la integración con persistencia, roles, autenticación y mutaciones inmutables.
"""

import unittest
from core.models import Usuario
from ui.state_manager import StateManager


class TestStateManager(unittest.TestCase):

    def setUp(self) -> None:
        self.sm = StateManager()

    def test_inicializacion_semillas_y_persistencia(self):
        """Verifica que el StateManager cargue datos persistentes desde disco."""
        incidentes = self.sm.obtener_incidentes_visibles()
        self.assertGreater(len(incidentes), 0)

    def test_autenticacion_real(self):
        """Verifica autenticación delegada al core usando usuarios.json."""
        # Éxito
        exito_adm, msg_adm = self.sm.autenticar("admin", "admin123")
        self.assertTrue(exito_adm)
        self.assertIsNotNone(self.sm.usuario_actual)
        self.assertEqual(self.sm.usuario_actual.rol, "Admin")

        # Fallo por contraseña errónea
        exito_err, msg_err = self.sm.autenticar("admin", "wrong_pass")
        self.assertFalse(exito_err)
        self.assertIn("inválidas", msg_err)

    def test_gestion_sesion_y_permisos(self):
        """Verifica la sesión y el control de privilegios de modificación."""
        admin = Usuario(id=1, nombre="Admin", rol="Admin", sector="Todos")
        comunidad = Usuario(id=2, nombre="Vecino", rol="Comunidad", sector="Sector Norte")

        self.sm.iniciar_sesion(admin)
        self.assertEqual(self.sm.usuario_actual, admin)
        self.assertTrue(self.sm.puede_modificar)

        self.sm.iniciar_sesion(comunidad)
        self.assertEqual(self.sm.usuario_actual, comunidad)
        self.assertFalse(self.sm.puede_modificar)

    def test_filtrado_por_permisos_en_state_manager(self):
        """Verifica que obtener_incidentes_visibles delegue en filtrar_por_permisos."""
        vecino_norte = Usuario(id=3, nombre="Vecino Norte", rol="Comunidad", sector="Sector Norte")
        self.sm.iniciar_sesion(vecino_norte)

        incidentes_visibles = self.sm.obtener_incidentes_visibles()
        self.assertGreater(len(incidentes_visibles), 0)
        for inc in incidentes_visibles:
            self.assertEqual(inc.sector, "Sector Norte")

    def test_modificar_incidente_permisos_e_inmutabilidad(self):
        """Verifica que solo roles autorizados puedan modificar incidentes inmutablemente."""
        admin = Usuario(id=1, nombre="Admin", rol="Admin", sector="Todos")
        comunidad = Usuario(id=2, nombre="Vecino", rol="Comunidad", sector="Sector Norte")

        # 1. Intento por usuario Comunidad debe ser rechazado
        self.sm.iniciar_sesion(comunidad)
        exito_com, msg_com = self.sm.modificar_incidente(
            incidente_id=1,
            sector="Sector Norte",
            descripcion="Fuga importante de agua en la avenida",
            tipo_incidente="Alcantarillado",
            estado="EnProceso",
            nivel_prioridad=5
        )
        self.assertFalse(exito_com)
        self.assertIn("Acceso denegado", msg_com)

        # 2. Intento por usuario Admin debe ser aprobado
        self.sm.iniciar_sesion(admin)
        exito_adm, msg_adm = self.sm.modificar_incidente(
            incidente_id=1,
            sector="Sector Norte",
            descripcion="Fuga importante de agua en la avenida principal reparándose.",
            tipo_incidente="Alcantarillado",
            estado="EnProceso",
            nivel_prioridad=5
        )
        self.assertTrue(exito_adm)

        inc_modificado = self.sm.obtener_incidente_por_id(1)
        self.assertIsNotNone(inc_modificado)
        self.assertEqual(inc_modificado.estado, "EnProceso")
        self.assertEqual(inc_modificado.nivel_prioridad, 5)

    def test_cargar_incidente_para_edicion(self):
        """Verifica el búfer de edición en StateManager."""
        inc = self.sm.obtener_incidente_por_id(1)
        self.assertIsNotNone(inc)
        self.sm.cargar_incidente_para_edicion(inc)
        self.assertEqual(self.sm.incidente_en_edicion, inc)

        self.sm.limpiar_edicion()
        self.assertIsNone(self.sm.incidente_en_edicion)

    def test_agregar_incidente_valido(self):
        """Verifica registro exitoso delegando la validación al Core."""
        admin = Usuario(id=1, nombre="Admin", rol="Admin", sector="Todos")
        self.sm.iniciar_sesion(admin)
        conteo_previo = len(self.sm.obtener_incidentes_visibles())

        exito, msg = self.sm.agregar_incidente(
            sector="Sector Norte",
            descripcion="Fuga importante de agua potable inundando la vía pública.",
            tipo_incidente="Alcantarillado"
        )
        self.assertTrue(exito)
        self.assertIn("registrado", msg)
        self.assertEqual(len(self.sm.obtener_incidentes_visibles()), conteo_previo + 1)

    def test_adherir_voto_inmutabilidad_en_coleccion(self):
        """Verifica que el voto use la transformación inmutable y reemplace el item."""
        admin = Usuario(id=1, nombre="Admin", rol="Admin", sector="Todos")
        self.sm.iniciar_sesion(admin)

        inc_original = self.sm.obtener_incidentes_visibles()[0]
        prioridad_previa = inc_original.nivel_prioridad

        exito, _ = self.sm.adherir_voto(inc_original.id, incremento=2)
        self.assertTrue(exito)

        inc_actualizado = self.sm.obtener_incidente_por_id(inc_original.id)
        self.assertEqual(inc_actualizado.nivel_prioridad, prioridad_previa + 2)
        self.assertIsNot(inc_original, inc_actualizado)

    def test_catalogo_tipos_dinamicos(self):
        """Verifica que StateManager retorne los tipos cargados desde tipos_incidente.json."""
        tipos = self.sm.obtener_tipos_incidente()
        self.assertIn("Choque", tipos)
        self.assertIn("Alcantarillado", tipos)
        self.assertGreater(len(tipos), 2)

    def test_obtener_ids_incidentes_map(self):
        """Verifica la extracción de IDs mediante la HOF map."""
        ids = self.sm.obtener_ids_incidentes()
        self.assertGreater(len(ids), 0)
        self.assertTrue(all(isinstance(i, int) for i in ids))

    def test_cerrar_sesion_y_reautenticar(self):
        """Verifica que cerrar sesión y volver a autenticarse funcione limpiamente."""
        self.sm.autenticar("admin", "admin123")
        self.assertIsNotNone(self.sm.usuario_actual)

        self.sm.cerrar_sesion()
        self.assertIsNone(self.sm.usuario_actual)

        # Re-autenticar con otro usuario
        exito, _ = self.sm.autenticar("carlos_norte", "comunidad123")
        self.assertTrue(exito)
        self.assertEqual(self.sm.usuario_actual.rol, "Comunidad")

    def test_eliminar_incidente_roles_e_inmutabilidad(self):
        """Verifica que solo el rol Admin pueda eliminar incidentes y que se preserve la inmutabilidad."""
        admin = Usuario(id=1, nombre="Admin", rol="Admin", sector="Todos")
        comunidad = Usuario(id=2, nombre="Vecino", rol="Comunidad", sector="Sector Norte")
        gobierno = Usuario(id=3, nombre="Funcionario", rol="Gobierno", sector="Distrito")

        # 1. Verificación de propiedad puede_eliminar
        self.sm.iniciar_sesion(comunidad)
        self.assertFalse(self.sm.puede_eliminar)

        self.sm.iniciar_sesion(gobierno)
        self.assertFalse(self.sm.puede_eliminar)

        self.sm.iniciar_sesion(admin)
        self.assertTrue(self.sm.puede_eliminar)

        # 2. Crear un incidente temporal para eliminar
        exito_crear, msg_crear = self.sm.agregar_incidente(
            sector="Sector Norte",
            descripcion="Incidente temporal creado para validar eliminación inmutable.",
            tipo_incidente="Choque"
        )
        self.assertTrue(exito_crear)
        id_temp = max(self.sm.obtener_ids_incidentes())
        inc_temp = self.sm.obtener_incidente_por_id(id_temp)
        self.assertIsNotNone(inc_temp)

        # Cargar en búfer de edición para verificar que se limpie al eliminar
        self.sm.cargar_incidente_para_edicion(inc_temp)
        self.assertEqual(self.sm.incidente_en_edicion, inc_temp)

        # 3. Intentar eliminar con rol Comunidad (debe fallar)
        self.sm.iniciar_sesion(comunidad)
        exito_com, msg_com = self.sm.eliminar_incidente(id_temp)
        self.assertFalse(exito_com)
        self.assertIn("Acceso denegado", msg_com)
        self.assertIsNotNone(self.sm.obtener_incidente_por_id(id_temp))

        # 4. Eliminar con rol Admin (debe tener éxito)
        self.sm.iniciar_sesion(admin)
        conteo_previo = len(self.sm.obtener_incidentes_visibles())
        exito_adm, msg_adm = self.sm.eliminar_incidente(id_temp)
        self.assertTrue(exito_adm)
        self.assertIn("eliminado", msg_adm)

        # Verificar que el incidente ya no existe en la colección
        self.assertIsNone(self.sm.obtener_incidente_por_id(id_temp))
        self.assertEqual(len(self.sm.obtener_incidentes_visibles()), conteo_previo - 1)

        # Verificar que el búfer de edición fue limpiado
        self.assertIsNone(self.sm.incidente_en_edicion)


if __name__ == "__main__":
    unittest.main(verbosity=2)

