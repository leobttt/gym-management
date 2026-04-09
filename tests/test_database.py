import tempfile
import unittest
from pathlib import Path

import database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.original_db_path = database.DB_PATH
        self.original_finanzas_path = database.FINANZAS_DB_PATH
        database.DB_PATH = self.base_dir / "socios.db"
        database.FINANZAS_DB_PATH = self.base_dir / "finanzas.db"
        database.inicializar()

    def tearDown(self):
        database.DB_PATH = self.original_db_path
        database.FINANZAS_DB_PATH = self.original_finanzas_path
        self.temp_dir.cleanup()

    def test_agregar_y_obtener_socio(self):
        socio_id = database.agregar_socio("Prueba Uno", "5512345678", "", "2026-04-08")
        database.agregar_membresia(socio_id, "2026-04-08", "2026-05-08", "Mensual")

        socios = database.obtener_socios()

        self.assertEqual(len(socios), 1)
        self.assertEqual(socios[0][1], "Prueba Uno")
        self.assertEqual(socios[0][2], "5512345678")
        self.assertEqual(socios[0][3], "")
        self.assertEqual(socios[0][7], "Mensual")

    def test_finanzas_tables_exist(self):
        database.agregar_producto("Proteína", 500.0)
        database.registrar_gasto("Renta", 1200.0)
        database.registrar_venta("Proteína", 500.0)

        self.assertEqual(len(database.obtener_productos()), 1)
        self.assertEqual(len(database.obtener_gastos()), 1)
        self.assertEqual(len(database.obtener_ventas()), 1)


if __name__ == "__main__":
    unittest.main()
