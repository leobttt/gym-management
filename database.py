import sqlite3
import re
from datetime import date, timedelta
from pathlib import Path

from power_gym_app.receipts import delete_member_photo, delete_member_receipts, delete_photo_path, delete_receipt_file

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "socios.db"
FINANZAS_DB_PATH = BASE_DIR / "finanzas.db"

def conectar_socios():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    return con

def conectar_finanzas():
    return sqlite3.connect(FINANZAS_DB_PATH)


def _coerce_date(value):
    if value is None:
        return date.today()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _week_bounds(reference=None):
    ref = _coerce_date(reference)
    inicio = ref - timedelta(days=ref.weekday())
    fin = inicio + timedelta(days=6)
    return inicio, fin


def _month_bounds(periodo=None):
    if periodo is None:
        today = date.today()
        return today.replace(day=1), today.strftime("%Y-%m")
    if isinstance(periodo, date):
        inicio = periodo.replace(day=1)
        return inicio, inicio.strftime("%Y-%m")
    periodo_str = str(periodo)
    inicio = date.fromisoformat(f"{periodo_str}-01")
    return inicio, periodo_str


def _periodo_corte_semanal(hoy=None):
    ref = _coerce_date(hoy)
    inicio_semana_actual = ref - timedelta(days=ref.weekday())
    inicio_semana_objetivo = inicio_semana_actual - timedelta(days=7)
    fin_semana_objetivo = inicio_semana_objetivo + timedelta(days=6)
    periodo = f"{inicio_semana_objetivo.isocalendar()[0]}-W{inicio_semana_objetivo.isocalendar()[1]:02d}"
    return {
        "tipo": "corte_semanal",
        "periodo": periodo,
        "fecha_inicio": inicio_semana_objetivo.isoformat(),
        "fecha_fin": fin_semana_objetivo.isoformat(),
        "fecha_objetivo": inicio_semana_actual.isoformat(),
        "titulo": "Corte semanal pendiente",
        "descripcion": f"Genera el corte de caja de la semana {inicio_semana_objetivo.isoformat()} al {fin_semana_objetivo.isoformat()}.",
    }


def _periodo_reporte_mensual(hoy=None):
    ref = _coerce_date(hoy)
    primer_dia_mes_actual = ref.replace(day=1)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
    periodo = ultimo_dia_mes_anterior.strftime("%Y-%m")
    return {
        "tipo": "reporte_mensual",
        "periodo": periodo,
        "fecha_inicio": ultimo_dia_mes_anterior.replace(day=1).isoformat(),
        "fecha_fin": ultimo_dia_mes_anterior.isoformat(),
        "fecha_objetivo": primer_dia_mes_actual.isoformat(),
        "titulo": "Reporte mensual pendiente",
        "descripcion": f"Genera el reporte mensual de {periodo}.",
    }


def requiere_reinscripcion(fecha_alta, referencia=None):
    if not fecha_alta:
        return False
    try:
        alta = date.fromisoformat(str(fecha_alta))
    except ValueError:
        return False
    ref = _coerce_date(referencia)
    return (ref - alta).days >= 365


def _parsear_items_venta(concepto):
    items = []
    for fragmento in (concepto or "").split(", "):
        match = re.match(r"^(.*?)\s+\(\$([0-9,]+(?:\.[0-9]{2})?) x (\d+)\)$", fragmento.strip())
        if not match:
            continue
        nombre = match.group(1).strip()
        precio = float(match.group(2).replace(",", ""))
        cantidad = int(match.group(3))
        items.append((nombre, precio, cantidad))
    return items

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
        CREATE TABLE IF NOT EXISTS alertas_sistema (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo            TEXT NOT NULL,
            periodo         TEXT NOT NULL,
            fecha_objetivo  TEXT NOT NULL,
            atendida        INTEGER NOT NULL DEFAULT 0,
            fecha_atendida  TEXT,
            UNIQUE(tipo, periodo)
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
            concepto    TEXT    NOT NULL,
            categoria   TEXT    NOT NULL DEFAULT 'General'
        )
    """)
    try:
        cur_f.execute("ALTER TABLE gastos ADD COLUMN categoria TEXT NOT NULL DEFAULT 'General'")
    except sqlite3.OperationalError:
        pass

    cur_f.execute("""
        CREATE TABLE IF NOT EXISTS ventas_productos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT    NOT NULL,
            monto       REAL    NOT NULL,
            concepto    TEXT    NOT NULL
        )
    """)

    cur_f.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL UNIQUE
        )
    """)

    cur_f.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL,
            costo       REAL    NOT NULL,
            categoria_id INTEGER,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    """)
    
    try:
        cur_f.execute("ALTER TABLE productos ADD COLUMN categoria_id INTEGER")
    except sqlite3.OperationalError:
        pass
        
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


def actualizar_fecha_alta(socio_id, fecha_alta):
    con = conectar_socios()
    cur = con.cursor()
    cur.execute(
        """
        UPDATE socios
        SET fecha_alta=?
        WHERE id=?
    """,
        (fecha_alta, socio_id),
    )
    con.commit()
    con.close()

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


def limpiar_recibos_antiguos(referencia=None, max_age_days=90):
    ref = _coerce_date(referencia)
    cutoff = (ref - timedelta(days=max_age_days)).isoformat()
    con = conectar_socios()
    cur = con.cursor()
    cur.execute(
        """
        SELECT id, socio_id, monto, concepto, fecha
        FROM pagos
        WHERE fecha < ?
    """,
        (cutoff,),
    )
    pagos_antiguos = cur.fetchall()

    for pago_id, socio_id, monto, concepto, fecha in pagos_antiguos:
        delete_receipt_file(socio_id, monto, concepto, fecha)
        cur.execute("DELETE FROM pagos WHERE id=?", (pago_id,))

    con.commit()
    con.close()
    return len(pagos_antiguos)

# Finanzas Methods
def registrar_gasto(concepto, monto, categoria="General"):
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO gastos (fecha, monto, concepto, categoria)
        VALUES (?, ?, ?, ?)
    """, (date.today().isoformat(), monto, concepto, categoria))
    con.commit()
    con.close()

def obtener_gastos():
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("SELECT id, fecha, categoria, concepto, monto FROM gastos ORDER BY fecha DESC, id DESC")
    resultados = cur.fetchall()
    con.close()
    return resultados

def borrar_gasto(gasto_id):
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("DELETE FROM gastos WHERE id=?", (gasto_id,))
    con.commit()
    con.close()


def actualizar_gasto(gasto_id, concepto, monto, categoria="General"):
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute(
        """
        UPDATE gastos
        SET concepto=?, monto=?, categoria=?
        WHERE id=?
    """,
        (concepto, monto, categoria, gasto_id),
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

def agregar_categoria(nombre):
    con = conectar_finanzas()
    cur = con.cursor()
    try:
        cur.execute("""
            INSERT INTO categorias (nombre)
            VALUES (?)
        """, (nombre,))
        con.commit()
    except sqlite3.IntegrityError:
        pass  # Evitar duplicados
    finally:
        con.close()

def obtener_categorias():
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
    resultados = cur.fetchall()
    con.close()
    return resultados

def agregar_producto(nombre, costo, categoria_id=None):
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO productos (nombre, costo, categoria_id)
        VALUES (?, ?, ?)
    """, (nombre, costo, categoria_id))
    con.commit()
    con.close()

def obtener_productos():
    con = conectar_finanzas()
    cur = con.cursor()
    cur.execute("""
        SELECT p.id, p.nombre, p.costo, c.nombre 
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        ORDER BY p.nombre ASC
    """)
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


def sincronizar_alertas_sistema(hoy=None):
    ref = _coerce_date(hoy)
    alertas = []
    if ref.weekday() >= 0:
        alertas.append(_periodo_corte_semanal(ref))
    if ref.day >= 1:
        alertas.append(_periodo_reporte_mensual(ref))

    con = conectar_socios()
    cur = con.cursor()
    for alerta in alertas:
        cur.execute(
            """
            INSERT OR IGNORE INTO alertas_sistema (tipo, periodo, fecha_objetivo)
            VALUES (?, ?, ?)
        """,
            (alerta["tipo"], alerta["periodo"], alerta["fecha_objetivo"]),
        )
    con.commit()
    con.close()


def obtener_alertas_sistema_pendientes(hoy=None):
    ref = _coerce_date(hoy)
    sincronizar_alertas_sistema(ref)
    definiciones = {
        "corte_semanal": _periodo_corte_semanal(ref),
        "reporte_mensual": _periodo_reporte_mensual(ref),
    }
    con = conectar_socios()
    cur = con.cursor()
    cur.execute(
        """
        SELECT id, tipo, periodo, fecha_objetivo
        FROM alertas_sistema
        WHERE atendida = 0
          AND fecha_objetivo <= ?
        ORDER BY fecha_objetivo ASC, id ASC
    """,
        (ref.isoformat(),),
    )
    rows = cur.fetchall()
    con.close()
    resultado = []
    for alert_id, tipo, periodo, fecha_objetivo in rows:
        base = definiciones.get(tipo)
        if base is None or base["periodo"] != periodo:
            if tipo == "corte_semanal":
                año, semana = periodo.split("-W")
                inicio = date.fromisocalendar(int(año), int(semana), 1)
                base = {
                    "titulo": "Corte semanal pendiente",
                    "descripcion": f"Genera el corte de caja de la semana {inicio.isoformat()} al {(inicio + timedelta(days=6)).isoformat()}.",
                }
            else:
                inicio, _ = _month_bounds(periodo)
                ultimo = (inicio.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                base = {
                    "titulo": "Reporte mensual pendiente",
                    "descripcion": f"Genera el reporte mensual de {periodo}.",
                }
        resultado.append(
            {
                "id": alert_id,
                "tipo": tipo,
                "periodo": periodo,
                "fecha_objetivo": fecha_objetivo,
                "titulo": base["titulo"],
                "descripcion": base["descripcion"],
            }
        )
    return resultado


def marcar_alerta_sistema_atendida(alerta_id):
    con = conectar_socios()
    cur = con.cursor()
    cur.execute(
        """
        UPDATE alertas_sistema
        SET atendida = 1, fecha_atendida = ?
        WHERE id = ?
    """,
        (date.today().isoformat(), alerta_id),
    )
    con.commit()
    con.close()


def obtener_corte_semanal(fecha_referencia=None):
    inicio, fin = _week_bounds(fecha_referencia)
    inicio_iso = inicio.isoformat()
    fin_iso = fin.isoformat()

    con = conectar_socios()
    cur = con.cursor()
    cur.execute(
        """
        SELECT COUNT(*), COALESCE(SUM(monto), 0)
        FROM pagos
        WHERE fecha BETWEEN ? AND ?
          AND (concepto LIKE 'Inscrip%' OR concepto LIKE 'Renov%')
    """,
        (inicio_iso, fin_iso),
    )
    pagos_count, ingresos_socios = cur.fetchone()
    con.close()

    con_f = conectar_finanzas()
    cur_f = con_f.cursor()
    cur_f.execute(
        """
        SELECT COUNT(*), COALESCE(SUM(monto), 0)
        FROM ventas_productos
        WHERE fecha BETWEEN ? AND ?
    """,
        (inicio_iso, fin_iso),
    )
    ventas_count, ventas_productos = cur_f.fetchone()
    cur_f.execute(
        """
        SELECT COUNT(*), COALESCE(SUM(monto), 0)
        FROM gastos
        WHERE fecha BETWEEN ? AND ?
    """,
        (inicio_iso, fin_iso),
    )
    gastos_count, gastos = cur_f.fetchone()
    con_f.close()

    ingresos_socios = float(ingresos_socios or 0)
    ventas_productos = float(ventas_productos or 0)
    gastos = float(gastos or 0)
    return {
        "fecha_inicio": inicio_iso,
        "fecha_fin": fin_iso,
        "ingresos_socios": ingresos_socios,
        "ventas_productos": ventas_productos,
        "gastos": gastos,
        "neto": ingresos_socios + ventas_productos - gastos,
        "pagos_count": int(pagos_count or 0),
        "ventas_count": int(ventas_count or 0),
        "gastos_count": int(gastos_count or 0),
    }


def obtener_reporte_mensual(periodo=None):
    inicio, periodo_str = _month_bounds(periodo)
    meses = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }

    con = conectar_socios()
    cur = con.cursor()
    cur.execute(
        """
        SELECT COUNT(*), COALESCE(SUM(monto), 0)
        FROM pagos
        WHERE strftime('%Y-%m', fecha) = ?
          AND concepto LIKE 'Inscrip%'
    """,
        (periodo_str,),
    )
    altas_count, ingresos_inscripciones = cur.fetchone()
    cur.execute(
        """
        SELECT COUNT(*), COALESCE(SUM(monto), 0)
        FROM pagos
        WHERE strftime('%Y-%m', fecha) = ?
          AND concepto LIKE 'Renov%'
    """,
        (periodo_str,),
    )
    renovaciones_count, ingresos_renovaciones = cur.fetchone()
    cur.execute(
        """
        SELECT COUNT(*)
        FROM socios
        WHERE strftime('%Y-%m', fecha_alta) = ?
    """,
        (periodo_str,),
    )
    socios_nuevos = int(cur.fetchone()[0] or 0)
    con.close()

    con_f = conectar_finanzas()
    cur_f = con_f.cursor()
    cur_f.execute(
        """
        SELECT categoria, COUNT(*), COALESCE(SUM(monto), 0)
        FROM gastos
        WHERE strftime('%Y-%m', fecha) = ?
        GROUP BY categoria
        ORDER BY SUM(monto) DESC, categoria ASC
    """,
        (periodo_str,),
    )
    gastos_por_categoria = [
        {"categoria": categoria or "General", "cantidad": int(cantidad or 0), "monto": float(monto or 0)}
        for categoria, cantidad, monto in cur_f.fetchall()
    ]

    cur_f.execute(
        """
        SELECT fecha, concepto, monto
        FROM ventas_productos
        WHERE strftime('%Y-%m', fecha) = ?
        ORDER BY fecha DESC, id DESC
    """,
        (periodo_str,),
    )
    ventas = cur_f.fetchall()
    con_f.close()

    productos = {}
    ventas_monto_total = 0.0
    for _, concepto, monto in ventas:
        ventas_monto_total += float(monto or 0)
        for nombre, precio, cantidad in _parsear_items_venta(concepto):
            item = productos.setdefault(nombre, {"producto": nombre, "cantidad": 0, "ingresos": 0.0})
            item["cantidad"] += cantidad
            item["ingresos"] += precio * cantidad

    productos_mas_vendidos = sorted(
        productos.values(),
        key=lambda item: (item["cantidad"], item["ingresos"], item["producto"]),
        reverse=True,
    )[:10]

    ingresos_inscripciones = float(ingresos_inscripciones or 0)
    ingresos_renovaciones = float(ingresos_renovaciones or 0)
    gastos_total = sum(item["monto"] for item in gastos_por_categoria)
    return {
        "periodo": periodo_str,
        "mes_label": f"{meses[inicio.month]} {inicio.year}",
        "socios_nuevos": socios_nuevos,
        "ingresos_membresias": {
            "inscripciones": {"cantidad": int(altas_count or 0), "monto": ingresos_inscripciones},
            "renovaciones": {"cantidad": int(renovaciones_count or 0), "monto": ingresos_renovaciones},
            "total": ingresos_inscripciones + ingresos_renovaciones,
        },
        "ventas_productos_total": ventas_monto_total,
        "productos_mas_vendidos": productos_mas_vendidos,
        "gastos_por_categoria": gastos_por_categoria,
        "gastos_total": gastos_total,
    }
