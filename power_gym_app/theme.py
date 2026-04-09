import customtkinter as ctk
from PIL import Image
from power_gym_app.paths import get_resource_root

ROOT_DIR = get_resource_root()
ICONS_DIR = ROOT_DIR / "icons"

ROJO = "#D61F2C"
ROJO_DARK = "#A5121D"
NEGRO = "#0F0F0F"
GRIS_DARK = "#181818"
GRIS_MED = "#202020"
GRIS_LIGHT = "#2E2E2E"
BLANCO = "#F7F7F7"
TEXTO_GRIS = "#A1A1AA"
VERDE = "#3DDB84"
AMBAR = "#F59E0B"
ROJO_SUAVE = "#331417"
PANEL_ALT = "#141414"
BORDER_SOFT = "#262626"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


TITLE_FONT = "Bebas Neue"
BODY_FONT = "DM Sans"


def font_title(size, weight="normal"):
    return ctk.CTkFont(family=TITLE_FONT, size=size, weight=weight)


def font_body(size, weight="normal"):
    return ctk.CTkFont(family=BODY_FONT, size=size, weight=weight)


def cargar_ctk_icono(nombre, size=(20, 20)):
    path = ICONS_DIR / nombre
    if not path.exists():
        return None
    try:
        img = Image.open(path).convert("RGBA")
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception:
        return None
def cargar_iconos_globales():
    return {
        "dashboard": cargar_ctk_icono("dashboard.png", (18, 18)),
        "dashboard_card": cargar_ctk_icono("dashboard.png", (28, 28)),
        "alerta": cargar_ctk_icono("campana.png", (18, 18)),
        "usuarios": cargar_ctk_icono("persona.png", (18, 18)),
        "usuarios_card": cargar_ctk_icono("persona.png", (28, 28)),
        "usuario": cargar_ctk_icono("agregar.png", (24, 24)),
        "dolar": cargar_ctk_icono("signo de pesos.png", (24, 24)),
        "dolar_card": cargar_ctk_icono("signo de pesos.png", (28, 28)),
        "dinero-neto": cargar_ctk_icono("signo de pesos.png", (28, 28)),
        "contrato": cargar_ctk_icono("historial.png", (24, 24)),
        "gastos": cargar_ctk_icono("gastos.png", (24, 24)),
        "gastos_card": cargar_ctk_icono("gastos.png", (28, 28)),
        "gastos_small": cargar_ctk_icono("gastos.png", (18, 18)),
        "ventas": cargar_ctk_icono("carrito-de-compras.png", (24, 24)),
        "ventas_card": cargar_ctk_icono("carrito-de-compras.png", (28, 28)),
        "ventas_small": cargar_ctk_icono("icono-ventas-menu.png", (18, 18)),
        "grafico": cargar_ctk_icono("dashboard.png", (24, 24)),
        "camara": cargar_ctk_icono("tomar-foto.png", (24, 24)),
        "rayo": cargar_ctk_icono("tomar-foto.png", (24, 24)),
        "telefono": cargar_ctk_icono("telefono.png", (24, 24)),
        "check": cargar_ctk_icono("actualizar.png", (24, 24)),
        "ojo": cargar_ctk_icono("ver.png", (24, 24)),
        "lista": cargar_ctk_icono("historial.png", (24, 24)),
        "lapiz": cargar_ctk_icono("lapiz.png", (24, 24)),
        "regreso": cargar_ctk_icono("regreso.png", (24, 24)),
        "renovar": cargar_ctk_icono("actualizar.png", (24, 24)),
        "eliminar": cargar_ctk_icono("basura.png", (24, 24)),
        "basura": cargar_ctk_icono("basura.png", (24, 24)),
        "camara": cargar_ctk_icono("camara.png", (24, 24)),
        "exportar": cargar_ctk_icono("exportar.png", (24, 24)),
        "reporte": cargar_ctk_icono("reporte.png", (24, 24)),
    }


def fmt_date(iso_str):
    if not iso_str or len(iso_str) < 10:
        return iso_str
    return f"{iso_str[8:10]}-{iso_str[5:7]}-{iso_str[0:4]}"
