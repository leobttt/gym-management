import re

with open("database.py", "r") as f:
    content = f.read()

# Add finanzas db path
content = content.replace('DB_PATH = "socios.db"', 'DB_PATH = "socios.db"\nFINANZAS_DB_PATH = "finanzas.db"')

# Rename conectar to conectar_socios
content = content.replace('def conectar():', 'def conectar_socios():\n    return sqlite3.connect(DB_PATH)\n\ndef conectar_finanzas():\n    return sqlite3.connect(FINANZAS_DB_PATH)\n\n# def conectar_socios(): # (placeholder we skip)')
content = content.replace('    return sqlite3.connect(DB_PATH)\n', '', 1) # remove the original return
content = content.replace('con = conectar()', 'con = conectar_socios()')

# Now restructure inicializar
inicializar_new = """def inicializar():
    con = conectar_socios()
    cur = con.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS socios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL,
            telefono    TEXT    NOT NULL,
            email       TEXT,
            fecha_alta  TEXT    NOT NULL
        )
    ''')
    try:
        cur.execute("ALTER TABLE socios ADD COLUMN foto TEXT")
    except sqlite3.OperationalError:
        pass

    cur.execute('''
        CREATE TABLE IF NOT EXISTS membresias (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            socio_id        INTEGER NOT NULL,
            fecha_inicio    TEXT    NOT NULL,
            fecha_fin       TEXT    NOT NULL,
            tipo            TEXT    NOT NULL,
            notificado      INTEGER DEFAULT 0,
            FOREIGN KEY (socio_id) REFERENCES socios(id)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS historial_notificaciones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            socio_id    INTEGER NOT NULL,
            fecha       TEXT    NOT NULL,
            metodo      TEXT    NOT NULL,
            FOREIGN KEY (socio_id) REFERENCES socios(id)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS pagos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            socio_id    INTEGER NOT NULL,
            fecha       TEXT    NOT NULL,
            monto       REAL    NOT NULL,
            metodo      TEXT    NOT NULL,
            concepto    TEXT    NOT NULL,
            FOREIGN KEY (socio_id) REFERENCES socios(id)
        )
    ''')
    con.commit()
    con.close()

    con_f = conectar_finanzas()
    cur_f = con_f.cursor()
    cur_f.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT    NOT NULL,
            monto       REAL    NOT NULL,
            concepto    TEXT    NOT NULL
        )
    ''')

    cur_f.execute('''
        CREATE TABLE IF NOT EXISTS ventas_productos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT    NOT NULL,
            monto       REAL    NOT NULL,
            concepto    TEXT    NOT NULL
        )
    ''')
    con_f.commit()
    con_f.close()
"""

content = re.sub(r'def inicializar\(\):.*?con\.close\(\)\n', inicializar_new, content, flags=re.DOTALL)

with open("database.py", "w") as f:
    f.write(content)
