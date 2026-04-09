import tempfile
import unittest
from pathlib import Path

import generador_recibos
from power_gym_app import receipts


class RecibosTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.original_receipts_dir = receipts.RECEIPTS_DIR
        self.original_photos_dir = receipts.PHOTOS_DIR
        receipts.RECEIPTS_DIR = self.base_dir / "recibos_socios"
        receipts.PHOTOS_DIR = self.base_dir / "fotos_socios"
        generador_recibos.RECEIPTS_DIR = receipts.RECEIPTS_DIR

    def tearDown(self):
        receipts.RECEIPTS_DIR = self.original_receipts_dir
        receipts.PHOTOS_DIR = self.original_photos_dir
        generador_recibos.RECEIPTS_DIR = receipts.RECEIPTS_DIR
        self.temp_dir.cleanup()

    def test_generar_recibo_reutiliza_ruta_por_pago(self):
        ruta1 = generador_recibos.generar_recibo_jpg(
            "Socio Demo",
            350.0,
            "Efectivo",
            "Inscripción",
            "2026-04-08",
            7,
        )
        ruta2 = generador_recibos.generar_recibo_jpg(
            "Socio Demo",
            350.0,
            "Efectivo",
            "Inscripción",
            "2026-04-08",
            7,
        )

        self.assertEqual(ruta1, ruta2)
        self.assertTrue(Path(ruta1).exists())

    def test_delete_receipt_file_removes_jpg(self):
        ruta = generador_recibos.generar_recibo_jpg(
            "Socio Demo",
            200.0,
            "Tarjeta",
            "Renovación",
            "2026-04-09",
            12,
        )

        receipts.delete_receipt_file(12, 200.0, "Renovación", "2026-04-09")

        self.assertFalse(Path(ruta).exists())


if __name__ == "__main__":
    unittest.main()
