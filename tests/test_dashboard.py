import unittest

from power_gym_app.dashboard import productos_recientes_desde_ventas


class DashboardTests(unittest.TestCase):
    def test_productos_recientes_deduplica_por_producto_y_toma_fecha_mas_reciente(self):
        ventas = [
            (1, "2026-04-01", "Proteina ($500.00 x 1), Creatina ($300.00 x 1)", 800.0),
            (2, "2026-04-03", "Proteina ($500.00 x 2)", 1000.0),
            (3, "2026-04-02", "Shaker ($100.00 x 1)", 100.0),
        ]

        recientes = productos_recientes_desde_ventas(ventas, limit=5)

        self.assertEqual(
            recientes,
            [
                ("Proteina", "2026-04-03"),
                ("Shaker", "2026-04-02"),
                ("Creatina", "2026-04-01"),
            ],
        )

    def test_productos_recientes_ignora_fragmentos_invalidos(self):
        ventas = [
            (1, "2026-04-01", "Venta manual, Proteina ($500.00 x 1)", 500.0),
        ]

        recientes = productos_recientes_desde_ventas(ventas, limit=5)

        self.assertEqual(recientes, [("Proteina", "2026-04-01")])


if __name__ == "__main__":
    unittest.main()
