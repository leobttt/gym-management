import os
import tempfile
import uuid
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from power_gym_app.receipts import RECEIPTS_DIR, build_receipt_path, ensure_asset_dirs

# Intentar cargar fuentes del sistema; si no, usar default de Pillow
def _fuente(size, bold=False):
    candidatos_bold = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    candidatos = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    lista = candidatos_bold if bold else candidatos
    for path in lista:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def generar_recibo_jpg(nombre_socio, monto, metodo, concepto, fecha=None, socio_id=None, temporal=False):
    """
    Genera un recibo tipo ticket en formato JPG.
    Retorna la ruta absoluta del archivo generado.
    """
    if fecha:
        fs = fecha
        if len(fs) >= 10:
            fecha_str = (
                f"{fs[8:10]}-{fs[5:7]}-{fs[0:4]} {fs[11:16]}"
                if " " in fs
                else f"{fs[8:10]}-{fs[5:7]}-{fs[0:4]}"
            )
        else:
            fecha_str = fs
    else:
        fecha_str = datetime.now().strftime("%d-%m-%Y %H:%M")

    ensure_asset_dirs()
    if temporal:
        filepath = os.path.join(tempfile.gettempdir(), f"recibo_preview_{uuid.uuid4().hex[:8]}.jpg")
    elif socio_id is not None:
        filepath = build_receipt_path(socio_id, monto, concepto, fecha_str)
    else:
        filepath = RECEIPTS_DIR / f"recibo_{uuid.uuid4().hex[:8]}.jpg"
    filepath = os.path.abspath(filepath)

    # Si ya existe y tiene socio_id, simplemente devolver la ruta
    if os.path.exists(filepath) and socio_id is not None and not temporal:
        return filepath

    # ── Dimensiones del ticket ──────────────────────────────────────────────
    W = 600
    PADDING = 40
    BG     = (255, 255, 255)
    ROJO   = (230, 57, 70)
    NEGRO  = (30, 30, 30)
    GRIS   = (120, 120, 120)
    LINEA  = (220, 220, 220)

    # Fuentes
    f_title  = _fuente(36, bold=True)
    f_sub    = _fuente(18)
    f_label  = _fuente(16, bold=True)
    f_value  = _fuente(16)
    f_total  = _fuente(28, bold=True)
    f_footer = _fuente(14)

    # Primera pasada: calcular altura necesaria
    # Header ~110 + campo nombre + concepto (multi-línea) + otros campos + total + footer
    def wrap_text(draw, text, font, max_width):
        """Divide texto en líneas que quepan en max_width."""
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines if lines else [""]

    # Crear imagen temporal para medir
    tmp = Image.new("RGB", (W, 1000), BG)
    d = ImageDraw.Draw(tmp)

    max_text_w = W - PADDING * 2
    nombre_lines = wrap_text(d, nombre_socio.upper(), f_value, max_text_w)
    concepto_lines = wrap_text(d, concepto, f_value, max_text_w)

    line_h = 22
    H = (
        110                             # Header rojo
        + 30                            # subtítulo "Comprobante de Pago"
        + 24                            # Fecha
        + 30                            # separador
        + 30 + len(nombre_lines) * line_h   # Socio
        + 20                            # espacio
        + 30 + len(concepto_lines) * line_h # Concepto
        + 20                            # espacio
        + 30                            # Método de pago: label
        + line_h                        # Método de pago: valor
        + 40                            # separador + espacio
        + 60                            # TOTAL
        + 50                            # Footer
        + PADDING
    )

    # ── Dibujar el recibo real ──────────────────────────────────────────────
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    y = 0

    # Header rojo
    draw.rectangle([0, 0, W, 110], fill=ROJO)
    title_bbox = draw.textbbox((0, 0), "POWER GYM", font=f_title)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((W - title_w) / 2, 20), "POWER GYM", font=f_title, fill=(255, 255, 255))
    sub_text = "Tu Gimnasio de Confianza"
    sub_bbox = draw.textbbox((0, 0), sub_text, font=f_sub)
    draw.text(((W - (sub_bbox[2] - sub_bbox[0])) / 2, 68), sub_text, font=f_sub, fill=(255, 220, 220))

    y = 120

    # Comprobante de Pago
    cp_text = "— COMPROBANTE DE PAGO —"
    cp_bbox = draw.textbbox((0, 0), cp_text, font=f_sub)
    draw.text(((W - (cp_bbox[2] - cp_bbox[0])) / 2, y), cp_text, font=f_sub, fill=GRIS)
    y += 30

    # Fecha
    fecha_text = f"Fecha: {fecha_str}"
    fg_bbox = draw.textbbox((0, 0), fecha_text, font=f_footer)
    draw.text(((W - (fg_bbox[2] - fg_bbox[0])) / 2, y), fecha_text, font=f_footer, fill=GRIS)
    y += 28

    # Línea separadora
    draw.line([PADDING, y, W - PADDING, y], fill=LINEA, width=2)
    y += 18

    # Socio
    draw.text((PADDING, y), "SOCIO:", font=f_label, fill=NEGRO)
    y += 24
    for line in nombre_lines:
        draw.text((PADDING, y), line, font=f_value, fill=NEGRO)
        y += line_h
    y += 16

    # Línea separadora
    draw.line([PADDING, y, W - PADDING, y], fill=LINEA, width=1)
    y += 14

    # Concepto
    draw.text((PADDING, y), "CONCEPTO:", font=f_label, fill=NEGRO)
    y += 24
    for line in concepto_lines:
        draw.text((PADDING, y), line, font=f_value, fill=NEGRO)
        y += line_h
    y += 16

    # Línea separadora
    draw.line([PADDING, y, W - PADDING, y], fill=LINEA, width=1)
    y += 14

    # Método de pago
    draw.text((PADDING, y), "MÉTODO DE PAGO:", font=f_label, fill=NEGRO)
    y += 24
    draw.text((PADDING, y), metodo, font=f_value, fill=NEGRO)
    y += line_h + 16

    # Línea gruesa antes del total
    draw.line([PADDING, y, W - PADDING, y], fill=ROJO, width=3)
    y += 14

    # TOTAL
    total_text = f"TOTAL: ${monto:,.2f}"
    t_bbox = draw.textbbox((0, 0), total_text, font=f_total)
    draw.text(((W - (t_bbox[2] - t_bbox[0])) / 2, y), total_text, font=f_total, fill=ROJO)
    y += 50

    # Línea separadora
    draw.line([PADDING, y, W - PADDING, y], fill=LINEA, width=1)
    y += 14

    # Footer
    footer_text = "¡Gracias por tu preferencia!"
    ft_bbox = draw.textbbox((0, 0), footer_text, font=f_footer)
    draw.text(((W - (ft_bbox[2] - ft_bbox[0])) / 2, y), footer_text, font=f_footer, fill=GRIS)

    img.save(filepath, "JPEG", quality=95)
    return filepath
