import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PAGE_SIZE = (1240, 1754)
MARGIN_X = 72
MARGIN_Y = 72

ROJO = "#D61F2C"
ROJO_DARK = "#A5121D"
NEGRO = "#0F0F0F"
GRIS_DARK = "#181818"
GRIS_MED = "#202020"
BLANCO = "#F7F7F7"
TEXTO_GRIS = "#A1A1AA"
VERDE = "#3DDB84"

FONT_REGULAR_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

FONT_BOLD_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _font(size, bold=False):
    candidates = FONT_BOLD_CANDIDATES if bold else FONT_REGULAR_CANDIDATES
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


def _new_page():
    image = Image.new("RGB", PAGE_SIZE, NEGRO)
    draw = ImageDraw.Draw(image)
    return image, draw


def _rounded(draw, box, fill, outline=None, width=1, radius=28):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _text(draw, pos, text, font, fill):
    draw.text(pos, text, font=font, fill=fill)


def _header(draw, title, subtitle):
    _rounded(draw, (MARGIN_X, MARGIN_Y, PAGE_SIZE[0] - MARGIN_X, 260), ROJO, radius=36)
    _text(draw, (MARGIN_X + 44, MARGIN_Y + 42), "POWER GYM", _font(46, bold=True), BLANCO)
    _text(draw, (MARGIN_X + 44, MARGIN_Y + 112), title, _font(56, bold=True), BLANCO)
    _text(draw, (MARGIN_X + 44, MARGIN_Y + 202), subtitle, _font(24), "#FFD7DA")


def _card(draw, x, y, w, h, title, value, subtitle, value_color=BLANCO):
    _rounded(draw, (x, y, x + w, y + h), GRIS_DARK, outline="#262626", width=2, radius=28)
    _text(draw, (x + 24, y + 20), title, _font(24, bold=True), TEXTO_GRIS)
    _text(draw, (x + 24, y + 66), value, _font(40, bold=True), value_color)
    _text(draw, (x + 24, y + 126), subtitle, _font(20), TEXTO_GRIS)


def _section_box(draw, x, y, w, title, rows, total_label=None, total_value=None, total_color=BLANCO, quantity_suffix=""):
    row_height = 42
    height = 84 + max(1, len(rows)) * row_height + (72 if total_label else 18)
    _rounded(draw, (x, y, x + w, y + height), GRIS_DARK, outline="#262626", width=2, radius=28)
    _text(draw, (x + 24, y + 20), title, _font(28, bold=True), BLANCO)
    yy = y + 74
    if not rows:
        _text(draw, (x + 24, yy), "Sin datos para este periodo.", _font(20), TEXTO_GRIS)
    for nombre, cantidad, monto, accent in rows:
        _text(draw, (x + 24, yy), str(nombre), _font(20, bold=True), BLANCO)
        _text(draw, (x + 360, yy), f"{cantidad}{quantity_suffix}", _font(18), TEXTO_GRIS)
        monto_bbox = draw.textbbox((0, 0), f"${monto:,.2f}", font=_font(20, bold=True))
        _text(draw, (x + w - 24 - (monto_bbox[2] - monto_bbox[0]), yy), f"${monto:,.2f}", _font(20, bold=True), accent)
        yy += row_height
    if total_label:
        _rounded(draw, (x + 18, y + height - 66, x + w - 18, y + height - 18), GRIS_MED, radius=18)
        _text(draw, (x + 36, y + height - 56), total_label, _font(20, bold=True), BLANCO)
        total_bbox = draw.textbbox((0, 0), f"${total_value:,.2f}", font=_font(22, bold=True))
        _text(draw, (x + w - 36 - (total_bbox[2] - total_bbox[0]), y + height - 58), f"${total_value:,.2f}", _font(22, bold=True), total_color)
    return height


def _footer(draw, text):
    bbox = draw.textbbox((0, 0), text, font=_font(18))
    x = PAGE_SIZE[0] - MARGIN_X - (bbox[2] - bbox[0])
    y = PAGE_SIZE[1] - MARGIN_Y + 10
    _text(draw, (x, y), text, _font(18), TEXTO_GRIS)


def export_corte_semanal_pdf(resumen, output_path):
    image, draw = _new_page()
    _header(
        draw,
        "Corte Semanal",
        f"Periodo: {resumen['fecha_inicio']} al {resumen['fecha_fin']}",
    )

    card_y = 320
    card_w = (PAGE_SIZE[0] - (MARGIN_X * 2) - 36) // 2
    card_h = 180
    cards = [
        ("Ingresos socios", resumen["ingresos_socios"], f"{resumen['pagos_count']} cobro(s)", BLANCO),
        ("Ventas productos", resumen["ventas_productos"], f"{resumen['ventas_count']} venta(s)", BLANCO),
        ("Gastos", resumen["gastos"], f"{resumen['gastos_count']} registro(s)", ROJO),
        ("Neto semanal", resumen["neto"], "Ingresos + ventas - gastos", VERDE if resumen["neto"] >= 0 else ROJO),
    ]
    for index, (title, amount, subtitle, color) in enumerate(cards):
        row = index // 2
        col = index % 2
        x = MARGIN_X + col * (card_w + 36)
        y = card_y + row * (card_h + 24)
        _card(draw, x, y, card_w, card_h, title, f"${amount:,.2f}", subtitle, color)

    section_y = card_y + (card_h + 24) * 2 + 24
    rows = [
        ("Cobros de membresia", resumen["pagos_count"], 0.0, BLANCO),
        ("Ventas registradas", resumen["ventas_count"], 0.0, BLANCO),
        ("Gastos registrados", resumen["gastos_count"], 0.0, BLANCO),
    ]
    height = 84 + len(rows) * 42 + 18
    _rounded(draw, (MARGIN_X, section_y, PAGE_SIZE[0] - MARGIN_X, section_y + height), GRIS_DARK, outline="#262626", width=2, radius=28)
    _text(draw, (MARGIN_X + 24, section_y + 20), "Detalle del corte", _font(28, bold=True), BLANCO)
    yy = section_y + 78
    for nombre, cantidad, _, _ in rows:
        _text(draw, (MARGIN_X + 24, yy), nombre, _font(20), BLANCO)
        qty = str(cantidad)
        bbox = draw.textbbox((0, 0), qty, font=_font(20, bold=True))
        _text(draw, (PAGE_SIZE[0] - MARGIN_X - 24 - (bbox[2] - bbox[0]), yy), qty, _font(20, bold=True), BLANCO)
        yy += 42

    _footer(draw, "Exportado desde Power Gym")
    path = Path(output_path)
    image.save(path, "PDF", resolution=150.0)
    return path


def export_reporte_mensual_pdf(reporte, output_path):
    pages = []
    image, draw = _new_page()
    pages.append(image)
    _header(draw, "Reporte Mensual", reporte["mes_label"])

    ingresos = reporte["ingresos_membresias"]
    card_y = 320
    card_w = (PAGE_SIZE[0] - (MARGIN_X * 2) - 54) // 3
    cards = [
        ("Membresias", ingresos["total"], "Inscripciones y renovaciones", BLANCO),
        ("Ventas productos", reporte["ventas_productos_total"], "Ventas del mes", BLANCO),
        ("Gastos", reporte["gastos_total"], "Egresos del mes", ROJO),
    ]
    for index, (title, amount, subtitle, color) in enumerate(cards):
        x = MARGIN_X + index * (card_w + 27)
        _card(draw, x, card_y, card_w, 180, title, f"${amount:,.2f}", subtitle, color)

    y = 540
    sections = [
        (
            "Ingresos por membresias",
            [
                ("Inscripciones", ingresos["inscripciones"]["cantidad"], ingresos["inscripciones"]["monto"], BLANCO),
                ("Renovaciones", ingresos["renovaciones"]["cantidad"], ingresos["renovaciones"]["monto"], BLANCO),
            ],
            "Total membresias",
            ingresos["total"],
            VERDE,
            " mov.",
        ),
        (
            "Productos mas vendidos",
            [(item["producto"], item["cantidad"], item["ingresos"], BLANCO) for item in reporte["productos_mas_vendidos"]],
            "Total ventas productos",
            reporte["ventas_productos_total"],
            VERDE,
            " pza(s)",
        ),
        (
            "Gastos por categoria",
            [(item["categoria"], item["cantidad"], item["monto"], ROJO) for item in reporte["gastos_por_categoria"]],
            "Total gastos",
            reporte["gastos_total"],
            ROJO,
            " gasto(s)",
        ),
    ]

    for title, rows, total_label, total_value, total_color, suffix in sections:
        box_height = 84 + max(1, len(rows)) * 42 + 72
        if y + box_height > PAGE_SIZE[1] - 140:
            image, draw = _new_page()
            pages.append(image)
            _header(draw, "Reporte Mensual", reporte["mes_label"])
            y = 320
        y += _section_box(draw, MARGIN_X, y, PAGE_SIZE[0] - (MARGIN_X * 2), title, rows, total_label, total_value, total_color, suffix) + 18

    actividad_rows = [
        ("Socios nuevos", reporte["socios_nuevos"], 0.0, BLANCO),
        ("Renovaciones", ingresos["renovaciones"]["cantidad"], 0.0, BLANCO),
    ]
    if y + 220 > PAGE_SIZE[1] - 140:
        image, draw = _new_page()
        pages.append(image)
        _header(draw, "Reporte Mensual", reporte["mes_label"])
        y = 320
    height = 84 + len(actividad_rows) * 42 + 18
    _rounded(draw, (MARGIN_X, y, PAGE_SIZE[0] - MARGIN_X, y + height), GRIS_DARK, outline="#262626", width=2, radius=28)
    _text(draw, (MARGIN_X + 24, y + 20), "Actividad de socios", _font(28, bold=True), BLANCO)
    yy = y + 78
    for nombre, cantidad, _, _ in actividad_rows:
        _text(draw, (MARGIN_X + 24, yy), nombre, _font(20), BLANCO)
        qty = str(cantidad)
        bbox = draw.textbbox((0, 0), qty, font=_font(20, bold=True))
        _text(draw, (PAGE_SIZE[0] - MARGIN_X - 24 - (bbox[2] - bbox[0]), yy), qty, _font(20, bold=True), BLANCO)
        yy += 42

    for page in pages:
        _footer(ImageDraw.Draw(page), "Exportado desde Power Gym")
    path = Path(output_path)
    pages[0].save(path, "PDF", resolution=150.0, save_all=True, append_images=pages[1:])
    return path
