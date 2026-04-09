import sqlite3
from datetime import date
from pathlib import Path

from power_gym_app.receipts import delete_member_photo, delete_member_receipts, delete_photo_path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "socios.db"
FINANZAS_DB_PATH = BASE_DIR / "finanzas.db"

def conectar_socios():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    return con

def conectar_finanzas():
    return sqlite3.connect(FINANZAS_DB_PATH)

def inicializar():
    con = conectar_socios()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS socios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL,
            telefono    TEXT    NOT NULL,
            email       TEXT,
            fecha_alta  TEXT    NOT NULL
        )
    """)
    try:
        cur.execute("ALTER TABLE socios ADD COLUMN foto TEXT")
    except sqlite3.OperationalError:
        pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS membresias (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            socio_id        INTEGER NOT NULL,
            fecha_inicio    TEXT    NOT NULL,
            fecha_fin       TEXT    NOT NULL,
            tipo            TEXT    NOT NULL,
            notificado      INTEGER DEFAULT 0,
            FOREIGN KEY (socio_id) REFERENCES socios(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS historial_notificaciones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            socio_id    INTEGER NOT NULL,
            fecha       TEXT    NOT NULL,
            metodo      TEXT    NOT NULL,
            FOREIGN KEY (socio_id) REFERENCES socios(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            socio_id    INTEGER NOT NULL,
            fecha       TEXT    NOT NULL,
            monto       REAL    NOT NULL,
            metodo      TEXT    NOT NULL,
            concepto    TEXT    NOT NULL,
            FOREIGN KEY (socio_id) REFERENCES socios(id)
        )
    """)
    con.commit()
    con.close()

    con_f = conectar_finanzas()
    cur_f = con_f.cursor()
    cur_f.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT    NOT NULL,
            monto       REAL    NOT NULL,
            concepto    TEXT    NOT NULL
        )
    """)

    cur_f.execute("""
        CREATE TABLE IF NOT EXISTS ventas_productos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT    NOT NULL,
            monto       REAL    NOT NULL,
            concepto    TEXT    NOT NULL
        )
    """)

    cur_f.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL,
            costo       REAL    NOT NULL
        )
    """)
    con_f.commit()
    con_f.close()


def socios_por_vencer(dias=7, unnotified_only=True):
    con = conectar_socios()
    cur = con.cursor()
    hoy = date.today().isoformat()
    query = """
        SELECT s.id, s.nombre, s.telefono, m.fecha_fin, m.id
        FROM socios s
        JOIN membresias m ON s.id = m.socio_id
        WHERE m.fecha_fin BETWEEN ? AND date(?, '+' || ? || ' days')
    """
    if unnotified_only:
        query += " AND m.notificado = 0"
        
    cur.execute(query, (hoy, hoy, dias))
    resultado = cur.fetchall()
    con.close()
    return resultado

def obtener_socios_por_estado_notificacion(estado, unnotified_only=False):
    con = conectar_socios()
    cur = con.cursor()
    hoy = date.today().isoformat()
    
    query = """
        SELECT s.id, s.nombre, s.telefono, m.fecha_fin, m.id
        FROM socios s
        JOIN membresias m ON s.id = m.socio_id
    """
    
    params = []
    if estado == "Por Vencer":
        query += " WHERE m.fecha_fin BETWEEN ? AND date(?, '+7 days')"
        params.extend([hoy, hoy])
    elif estado == "Vencidos":
        query += " WHERE m.fecha_fin < ?"
        params.append(hoy)
    elif estado == "Activos":
        query += " WHERE m.fecha_fin > date(?, '+7 days')"
        params.append(hoy)
        
    if unnotified_only:
        query += " AND m.notificado = 0"
        
    cur.execute(query, params)
    resultado = cur.fetchall()
    con.close()
    return resultado

def marcar_notificado(membresia_id, socio_id, metodo):
    con = conectar_socios()
    cur = con.cursor()
    cur.execute("UPDATE membresias SET notificado=1 WHERE id=?", (membresia_id,))
    cur.execute("""
        INSERT INTO historial_notificaciones (socio_id, fecha, metodo)
        VALUES (?, ?, ?)
    """, (socio_id, date.today().isoformat(), metodo))
    con.commit()
    con.close()

def agregar_socio(nombre, telefono, foto, fecha_alta):
    con = conectar_socios()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO socios (nombre, telefono, foto, fecha_alta)
        VALUES (?, ?, ?, ?)
    """, (nombre, telefono, foto, fecha_alta))
    socio_id = cur.lastrowid
    con.commit()
    con.close()
    return socio_id

def agregar_membresia(socio_id, fecha_inicio, fecha_fin, tipo):
    con = conectar_socios()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO membresias (socio_id, fecha_inicio, fecha_fin, tipo)
        VALUES (?, ?, ?, ?)
    """, (socio_id, fecha_inicio, fecha_fin, tipo))
    con.commit()
    con.close()

def obtener_socios():
    con = conectar_socios()
    cur = con.cursor()
    cur.execute("""
        SELECT s.id, s.nombre, s.telefono, s.foto, s.fecha_alta,
               m.fecha_inicio, m.fecha_fin, m.tipo
        FROM socios s
        LEFT JOIN membresias m ON s.id = m.socio_id
        ORDER BY m.fecha_fin ASC
    """)
    resultado = cur.fetchall()
    con.close()
    return resultado

def actualizar_socio(socio_id, nombre, telefono, foto):
    con = conectar_socios()
    cur = con.cursor()
    cur.execute("SELECT foto FROM socios WHERE id=?", (socio_id,))
    row = cur.fetchone()
    foto_anterior = row[0] if row else ""
    cur.execute("""
        UPDATE socios
        SET nombre=?, telefono=?, foto=?
        WHERE id=?
    """, (nombre, telefono, foto, socio_id))
    con.commit()
    con.close()
    if foto_anterior and foto_anterior != foto:
        delete_photo_path(foto_anterior)

def actualizar_membresia(socio_id, fecha_inicio, fecha_fin, tipo):
    con = conectar_socios()
    cur = con.cursor()
    cur.execute("SELECT id FROM membresias WHERE socio_id=?", (socio_id,))
    res = cur.fetchone()
    if res:
        cur.execute("""
            UPDATE membresias
            SET fecha_inicio=?, fecha_fin=?, tipo=?, notificado=0
            WHERE socio_id=?
        """, (fecha_inicio, fecha_fin, tipo, socio_id))
    else:
        cur.execute("""
            INSERT INTO membresias (socio_id, fecha_inicio, fecha_fin, tipo)
            VALUES (?, ?, ?, ?)
        """, (socio_id, fecha_inicio, fecha_fin, tipo))
    con.commit()
    con.close()

def borrar_socio(socio_id):
    con = conectar_socios()
    cur = con.cursor()
    
    cur.execute("SELECT foto FROM socios WHERE id=?", (socio_id,))
    row = cur.fetchone()
    foto_path = row[0] if row else ""

    delete_member_photo(foto_path, socio_id)
    delete_member_receipts(socio_id)

    cur.execute("DELETE FROM historial_notificaciones WHERE socio_id=?", (socio_id,))
    cur.execute("DELETE FROM membresias WHERE socio_id=?", (socio_id,))
    cur.execute("DELETE FROM pagos WHERE socio_id=?", (socio_id,))
    cur.execute("DELETE FROM socios WHERE id=?", (socio_id,))
    con.commit()
    con.close()

def registrar_pago(socio_id, monto, metodo, concepto):
    con = conectar_socios()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO pagos (socio_id, fecha, monto, metodo, concepto)
        VALUES (?, ?, ?, ?, ?)
    """, (socio_id, date.today().isoformat(), monto, metodo, concepto))
    con.commit()
    con.close()

def obtener_historial_pagos(socio_id):
    con = conectar_socios()
    cur = con.cursor()
    cur.execute("""
        SELECT id, fecha, concepto, monto, metodo
        FROM pagos
        WHERE socio_id = ?
        ORDER BY fecha DESC, id DESC
    """, (socio_id,))
    resultados = cur.fetchall()
    con.close()
    return resultados

def borrar_pago(pago_id):
    con = conectar_socios()
    cur = con.cursor()
    cur.execute("DELETE FROM pagos WHERE id=?", (pago_id,))
    con.commit()
    con.close()

def borrar_todos_pagos_socio(socio_id):
    con = conectar_socios()
    cur = con.cursor()
    cur.execute("DELETE FROM pagos WHERE socio_id=?", (socio_id,))
    con.commit()
    con.close()

    delete_member_receipts(socio_id)

# Finanzas Methods
def registrar_gasto(concepto, monto):
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO gastos (fecha, monto, concepto)
        VALUES (?, ?, ?)
    """, (date.today().isoformat(), monto, concepto))
    con.commit()
    con.close()

def obtener_gastos():
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("SELECT id, fecha, concepto, monto FROM gastos ORDER BY fecha DESC, id DESC")
    resultados = cur.fetchall()
    con.close()
    return resultados

def borrar_gasto(gasto_id):
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("DELETE FROM gastos WHERE id=?", (gasto_id,))
    con.commit()
    con.close()


def actualizar_gasto(gasto_id, concepto, monto):
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute(
        """
        UPDATE gastos
        SET concepto=?, monto=?
        WHERE id=?
    """,
        (concepto, monto, gasto_id),
    )
    con.commit()
    con.close()

def registrar_venta(concepto, monto):
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO ventas_productos (fecha, monto, concepto)
        VALUES (?, ?, ?)
    """, (date.today().isoformat(), monto, concepto))
    con.commit()
    con.close()

def obtener_ventas():
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("SELECT id, fecha, concepto, monto FROM ventas_productos ORDER BY fecha DESC, id DESC")
    resultados = cur.fetchall()
    con.close()
    return resultados

def borrar_venta(venta_id):
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("DELETE FROM ventas_productos WHERE id=?", (venta_id,))
    con.commit()
    con.close()

def borrar_todas_ventas():
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("DELETE FROM ventas_productos")
    con.commit()
    con.close()

def agregar_producto(nombre, costo):
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO productos (nombre, costo)
        VALUES (?, ?)
    """, (nombre, costo))
    con.commit()
    con.close()

def obtener_productos():
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("SELECT id, nombre, costo FROM productos ORDER BY nombre ASC")
    resultados = cur.fetchall()
    con.close()
    return resultados

def borrar_producto(producto_id):
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("DELETE FROM productos WHERE id=?", (producto_id,))
    con.commit()
    con.close()



def obtener_metricas_dashboard():
    con = conectar_socios()
    cur = con.cursor()
    hoy = date.today().isoformat()
    mes_actual = hoy[:7]
    
    cur.execute("""
        SELECT m.fecha_fin
        FROM socios s
        JOIN membresias m ON s.id = m.socio_id
    """)
    membresias = cur.fetchall()
    
    activos = 0
    por_vencer = 0
    vencidos = 0
    
    from datetime import date as dt_date
    hoy_date = dt_date.today()
    
    for (fecha_fin,) in membresias:
        if fecha_fin:
            ff = dt_date.fromisoformat(fecha_fin)
            diff = (ff - hoy_date).days
            if diff < 0:
                vencidos += 1
            elif 0 <= diff <= 5:
                por_vencer += 1
            else:
                activos += 1
                
    cur.execute("""
        SELECT SUM(monto) FROM pagos 
        WHERE strftime('%Y-%m', fecha) = ?
    """, (mes_actual,))
    ingresos_row = cur.fetchone()
    ingresos = ingresos_row[0] if ingresos_row and ingresos_row[0] else 0.0
    con.close()
    
    # Finanzas
    con_f = conectar_finanzas()
    cur_f = con_f.cursor()
    try:
        cur_f.execute("""
            SELECT SUM(monto) FROM gastos 
            WHERE strftime('%Y-%m', fecha) = ?
        """, (mes_actual,))
        gastos_row = cur_f.fetchone()
        gastos = gastos_row[0] if gastos_row and gastos_row[0] else 0.0
    except sqlite3.OperationalError:
        gastos = 0.0

    try:
        cur_f.execute("""
            SELECT SUM(monto) FROM ventas_productos 
            WHERE strftime('%Y-%m', fecha) = ?
        """, (mes_actual,))
        ventas_row = cur_f.fetchone()
        ventas_productos = ventas_row[0] if ventas_row and ventas_row[0] else 0.0
    except sqlite3.OperationalError:
        ventas_productos = 0.0
    
    con_f.close()
    
    return activos, por_vencer, vencidos, ingresos, gastos, ventas_productos

def obtener_datos_charts():
    con = conectar_socios()
    cur = con.cursor()
    
    # Donut Chart: membresias activas por tipo
    cur.execute("""
        SELECT m.tipo, COUNT(*)
        FROM membresias m
         WHERE m.fecha_fin >= date('now')
        GROUP BY m.tipo
    """)
    donut_data = cur.fetchall()
    
    # Line chart: nuevos socios por mes (ultimos 6 meses)
    cur.execute("""
        SELECT strftime('%Y-%m', fecha_alta) as mes, COUNT(*)
        FROM socios
        GROUP BY mes
        ORDER BY mes ASC
        LIMIT 6
    """)
    line_data = cur.fetchall()
    
    con.close()
    return donut_data, line_data

def obtener_recientes():
    con = conectar_socios()
    cur = con.cursor()
    hoy = date.today().isoformat()
    
    # ultimos 5 socios
    cur.execute("""
        SELECT s.nombre, s.fecha_alta, m.tipo
        FROM socios s
        LEFT JOIN membresias m ON s.id = m.socio_id
        ORDER BY s.id DESC LIMIT 5
    """)
    recientes = cur.fetchall()
    
    # 5 socios por vencer (excluyendo vencidos)
    cur.execute("""
        SELECT s.nombre, s.telefono, m.fecha_fin
        FROM socios s
        JOIN membresias m ON s.id = m.socio_id
        WHERE m.fecha_fin >= ? AND m.fecha_fin <= date(?, '+7 days')
        ORDER BY m.fecha_fin ASC LIMIT 5
    """, (hoy, hoy))
    vencimientos = cur.fetchall()
    
    con.close()
    return recientes, vencimientos
