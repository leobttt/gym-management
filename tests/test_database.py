import tempfile
import unittest
from pathlib import Path

import database
import generador_recibos
from power_gym_app import receipts


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.original_db_path = database.DB_PATH
        self.original_finanzas_path = database.FINANZAS_DB_PATH
        self.original_receipts_dir = receipts.RECEIPTS_DIR
        self.original_generador_receipts_dir = generador_recibos.RECEIPTS_DIR
        database.DB_PATH = self.base_dir / "socios.db"
        database.FINANZAS_DB_PATH = self.base_dir / "finanzas.db"
        receipts.RECEIPTS_DIR = self.base_dir / "recibos_socios"
        generador_recibos.RECEIPTS_DIR = receipts.RECEIPTS_DIR
        database.inicializar()

    def tearDown(self):
        database.DB_PATH = self.original_db_path
        database.FINANZAS_DB_PATH = self.original_finanzas_path
        receipts.RECEIPTS_DIR = self.original_receipts_dir
        generador_recibos.RECEIPTS_DIR = self.original_generador_receipts_dir
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

    def test_obtener_corte_semanal_resume_ingresos_ventas_y_gastos(self):
        socio_id = database.agregar_socio("Semana Demo", "5511111111", "", "2026-04-07")
        con = database.conectar_socios()
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO pagos (socio_id, fecha, monto, metodo, concepto)
            VALUES (?, ?, ?, ?, ?)
        """,
            (socio_id, "2026-04-07", 350.0, "Efectivo", "Inscripción"),
        )
        con.commit()
        con.close()

        con_f = database.conectar_finanzas()
        cur_f = con_f.cursor()
        cur_f.execute(
            """
            INSERT INTO ventas_productos (fecha, monto, concepto)
            VALUES (?, ?, ?)
        """,
            ("2026-04-08", 450.0, "Proteina ($450.00 x 1)"),
        )
        cur_f.execute(
            """
            INSERT INTO gastos (fecha, monto, concepto, categoria)
            VALUES (?, ?, ?, ?)
        """,
            ("2026-04-09", 200.0, "Limpieza", "Insumos"),
        )
        con_f.commit()
        con_f.close()

        resumen = database.obtener_corte_semanal("2026-04-08")

        self.assertEqual(resumen["fecha_inicio"], "2026-04-06")
        self.assertEqual(resumen["fecha_fin"], "2026-04-12")
        self.assertEqual(resumen["ingresos_socios"], 350.0)
        self.assertEqual(resumen["ventas_productos"], 450.0)
        self.assertEqual(resumen["gastos"], 200.0)
        self.assertEqual(resumen["neto"], 600.0)

    def test_obtener_reporte_mensual_agrega_productos_gastos_y_renovaciones(self):
        socio_id = database.agregar_socio("Reporte Demo", "5522222222", "", "2026-04-01")
        con = database.conectar_socios()
        cur = con.cursor()
        cur.executemany(
            """
            INSERT INTO pagos (socio_id, fecha, monto, metodo, concepto)
            VALUES (?, ?, ?, ?, ?)
        """,
            [
                (socio_id, "2026-04-01", 300.0, "Efectivo", "Inscripción"),
                (socio_id, "2026-04-10", 350.0, "Tarjeta", "Renovación"),
            ],
        )
        con.commit()
        con.close()

        con_f = database.conectar_finanzas()
        cur_f = con_f.cursor()
        cur_f.execute(
            """
            INSERT INTO ventas_productos (fecha, monto, concepto)
            VALUES (?, ?, ?)
        """,
            ("2026-04-10", 1000.0, "Proteina ($500.00 x 2), Shaker ($100.00 x 1)"),
        )
        cur_f.executemany(
            """
            INSERT INTO gastos (fecha, monto, concepto, categoria)
            VALUES (?, ?, ?, ?)
        """,
            [
                ("2026-04-11", 1200.0, "Renta local", "Renta"),
                ("2026-04-12", 150.0, "Toallas", "Insumos"),
            ],
        )
        con_f.commit()
        con_f.close()

        reporte = database.obtener_reporte_mensual("2026-04")

        self.assertEqual(reporte["socios_nuevos"], 1)
        self.assertEqual(reporte["ingresos_membresias"]["inscripciones"]["monto"], 300.0)
        self.assertEqual(reporte["ingresos_membresias"]["renovaciones"]["monto"], 350.0)
        self.assertEqual(reporte["ingresos_membresias"]["renovaciones"]["cantidad"], 1)
        self.assertEqual(reporte["productos_mas_vendidos"][0]["producto"], "Proteina")
        self.assertEqual(reporte["productos_mas_vendidos"][0]["cantidad"], 2)
        self.assertEqual(reporte["gastos_por_categoria"][0]["categoria"], "Renta")
        self.assertEqual(reporte["gastos_total"], 1350.0)

    def test_alertas_sistema_generan_pendientes_y_se_pueden_atender(self):
        socio_id = database.agregar_socio("Alerta Sistema", "5510000000", "", "2026-04-08")
        con = database.conectar_socios()
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO pagos (socio_id, fecha, monto, metodo, concepto)
            VALUES (?, ?, ?, ?, ?)
        """,
            (socio_id, "2026-04-08", 350.0, "Efectivo", "Inscripción"),
        )
        cur.execute(
            """
            INSERT INTO pagos (socio_id, fecha, monto, metodo, concepto)
            VALUES (?, ?, ?, ?, ?)
        """,
            (socio_id, "2026-03-15", 350.0, "Efectivo", "Renovación"),
        )
        con.commit()
        con.close()

        alertas = database.obtener_alertas_sistema_pendientes("2026-04-08")

        tipos = {alerta["tipo"] for alerta in alertas}
        self.assertIn("corte_semanal", tipos)
        self.assertIn("reporte_mensual", tipos)

        corte = next(alerta for alerta in alertas if alerta["tipo"] == "corte_semanal")
        self.assertEqual(corte["fecha_inicio"], "2026-04-06")
        self.assertEqual(corte["fecha_fin"], "2026-04-12")
        database.marcar_alerta_sistema_atendida(corte["id"])

        restantes = database.obtener_alertas_sistema_pendientes("2026-04-08")
        tipos_restantes = {alerta["tipo"] for alerta in restantes}
        self.assertNotIn("corte_semanal", tipos_restantes)
        self.assertIn("reporte_mensual", tipos_restantes)

    def test_alertas_sistema_no_aparecen_sin_datos(self):
        alertas = database.obtener_alertas_sistema_pendientes("2026-04-08")
        self.assertEqual(alertas, [])

    def test_socios_por_vencer_y_marcar_notificado_ocultan_alerta(self):
        socio_id = database.agregar_socio("Alerta Demo", "5533333333", "", "2026-04-01")
        con = database.conectar_socios()
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO membresias (socio_id, fecha_inicio, fecha_fin, tipo, notificado)
            VALUES (?, ?, ?, ?, 0)
        """,
            (socio_id, "2026-04-01", "2026-04-10", "Mensual"),
        )
        membresia_id = cur.lastrowid
        con.commit()
        con.close()

        pendientes = database.socios_por_vencer(dias=7, unnotified_only=True)
        self.assertEqual(len(pendientes), 1)
        self.assertEqual(pendientes[0][0], socio_id)

        database.marcar_notificado(membresia_id, socio_id, "manual")

        pendientes_despues = database.socios_por_vencer(dias=7, unnotified_only=True)
        self.assertEqual(pendientes_despues, [])

    def test_requiere_reinscripcion_despues_de_un_ano(self):
        self.assertFalse(database.requiere_reinscripcion("2025-04-09", "2026-04-08"))
        self.assertTrue(database.requiere_reinscripcion("2025-04-08", "2026-04-08"))

    def test_actualizar_fecha_alta_reinicia_antiguedad(self):
        socio_id = database.agregar_socio("Reinscripcion Demo", "5544444444", "", "2025-01-01")

        database.actualizar_fecha_alta(socio_id, "2026-04-08")

        socios = database.obtener_socios()
        self.assertEqual(socios[0][4], "2026-04-08")

    def test_limpiar_recibos_antiguos_borra_pagos_y_archivos_mayores_a_tres_meses(self):
        socio_id = database.agregar_socio("Recibo Demo", "5555555555", "", "2025-01-01")
        con = database.conectar_socios()
        cur = con.cursor()
        cur.executemany(
            """
            INSERT INTO pagos (socio_id, fecha, monto, metodo, concepto)
            VALUES (?, ?, ?, ?, ?)
        """,
            [
                (socio_id, "2026-01-01", 300.0, "Efectivo", "Inscripción"),
                (socio_id, "2026-04-01", 350.0, "Tarjeta", "Renovación"),
            ],
        )
        con.commit()
        con.close()

        ruta_antigua = Path(receipts.build_receipt_path(socio_id, 300.0, "Inscripción", "2026-01-01"))
        ruta_antigua.parent.mkdir(exist_ok=True)
        ruta_antigua.write_bytes(b"old")
        ruta_reciente = Path(receipts.build_receipt_path(socio_id, 350.0, "Renovación", "2026-04-01"))
        ruta_reciente.write_bytes(b"recent")

        borrados = database.limpiar_recibos_antiguos("2026-04-08")

        self.assertEqual(borrados, 1)
        self.assertFalse(ruta_antigua.exists())
        self.assertTrue(ruta_reciente.exists())
        pagos = database.obtener_historial_pagos(socio_id)
        self.assertEqual(len(pagos), 1)
        self.assertEqual(pagos[0][2], "Renovación")


if __name__ == "__main__":
    unittest.main()
