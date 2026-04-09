import webbrowser
from urllib.parse import quote

from power_gym_app.theme import fmt_date
from power_gym_app.validation import normalizar_telefono_whatsapp


def generar_mensaje(nombre, fecha_fin):
    fecha_legible = fmt_date(fecha_fin)
    return (
        f"Hola {nombre}\n"
        f"Te recordamos que tu membresía en Power Gym vence el {fecha_legible}.\n"
        f"¡Renuévala para seguir entrenando sin interrupciones!"
    )

def abrir_whatsapp(telefono, nombre, fecha_fin):
    tel = normalizar_telefono_whatsapp(telefono)
    mensaje = generar_mensaje(nombre, fecha_fin)
    url = f"https://wa.me/{tel}?text={quote(mensaje)}"
    webbrowser.open(url)
