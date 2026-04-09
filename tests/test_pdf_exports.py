import tempfile
import unittest
from pathlib import Path

from power_gym_app.pdf_exports import export_corte_semanal_pdf, export_reporte_mensual_pdf


class PdfExportsTests(unittest.TestCase):
    def test_export_corte_semanal_pdf_creates_file(self):
        resumen = {
            "fecha_inicio": "2026-04-06",
            "fecha_fin": "2026-04-12",
            "ingresos_socios": 1500.0,
            "ventas_productos": 430.0,
            "gastos": 280.0,
            "neto": 1650.0,
            "pagos_count": 4,
            "ventas_count": 3,
            "gastos_count": 2,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "corte.pdf"
            export_corte_semanal_pdf(resumen, output)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 0)

    def test_export_reporte_mensual_pdf_creates_file(self):
        reporte = {
            "periodo": "2026-04",
            "mes_label": "Abril 2026",
            "socios_nuevos": 5,
            "ingresos_membresias": {
                "inscripciones": {"cantidad": 3, "monto": 900.0},
                "renovaciones": {"cantidad": 7, "monto": 2450.0},
                "total": 3350.0,
            },
            "ventas_productos_total": 1220.0,
            "productos_mas_vendidos": [
                {"producto": "Proteina", "cantidad": 4, "ingresos": 2000.0},
                {"producto": "Shaker", "cantidad": 3, "ingresos": 300.0},
            ],
            "gastos_por_categoria": [
                {"categoria": "Renta", "cantidad": 1, "monto": 1200.0},
                {"categoria": "Insumos", "cantidad": 2, "monto": 300.0},
            ],
            "gastos_total": 1500.0,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "reporte.pdf"
            export_reporte_mensual_pdf(reporte, output)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
