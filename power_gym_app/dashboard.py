import re
from datetime import date, timedelta

import customtkinter as ctk

from power_gym_app.theme import (
    AMBAR,
    BLANCO,
    BORDER_SOFT,
    GRIS_DARK,
    GRIS_LIGHT,
    GRIS_MED,
    NEGRO,
    PANEL_ALT,
    ROJO,
    ROJO_DARK,
    ROJO_SUAVE,
    TEXTO_GRIS,
    VERDE,
    fmt_date,
    font_body,
    font_title,
)


def _extraer_nombre_producto(fragmento):
    cleaned = fragmento.strip()
    if not cleaned:
        return None
    match = re.match(r"^(.*?)\s*\(\$", cleaned)
    if not match:
        return None
    nombre = match.group(1).strip()
    return nombre or None


def productos_recientes_desde_ventas(ventas, limit=5):
    recientes = {}
    for _, fecha, concepto, _ in ventas:
        for fragmento in concepto.split(","):
            nombre = _extraer_nombre_producto(fragmento)
            if not nombre:
                continue
            fecha_actual = recientes.get(nombre)
            if fecha_actual is None or fecha > fecha_actual:
                recientes[nombre] = fecha
    items = sorted(recientes.items(), key=lambda item: (item[1], item[0]), reverse=True)
    return items[:limit]


def _month_label(periodo):
    meses = {
        "01": "Ene",
        "02": "Feb",
        "03": "Mar",
        "04": "Abr",
        "05": "May",
        "06": "Jun",
        "07": "Jul",
        "08": "Ago",
        "09": "Sep",
        "10": "Oct",
        "11": "Nov",
        "12": "Dic",
    }
    if isinstance(periodo, str) and len(periodo) >= 7:
        return meses.get(periodo[5:7], periodo[-5:])
    return str(periodo)
class DashboardMixin:
    def mostrar_inicio(self):
        from database import obtener_datos_charts, obtener_metricas_dashboard, obtener_recientes

        self._limpiar_main()
        page = self._build_topbar(
            "inicio",
            "Panel de Control",
            "Dashboard / Rendimiento",
            primary_action={"text": "Nuevo socio", "image": self.icons["usuario"], "command": self.nuevo_socio},
            show_notifications=False,
        )

        activos, por_vencer, vencidos, ingresos, gastos, ventas_productos = obtener_metricas_dashboard()
        socios_recientes, vencimientos = obtener_recientes()
        donut_data, line_data_db = obtener_datos_charts()
        ingresos_netos = ingresos + ventas_productos - gastos
        comparativos = self._comparativos_mensuales()

        scroll = ctk.CTkScrollableFrame(page, fg_color=NEGRO, scrollbar_button_color=NEGRO, scrollbar_button_hover_color=NEGRO)
        scroll.pack(fill="both", expand=True)

        intro = ctk.CTkFrame(scroll, fg_color="transparent")
        intro.pack(fill="x", padx=24, pady=(18, 6))
        ctk.CTkLabel(intro, text="Resumen de finanzas y crecimiento", font=font_title(28), text_color=BLANCO).pack(anchor="w")
        ctk.CTkLabel(
            intro,
            text="Indicadores financieros, crecimiento y renovaciones en una sola vista.",
            font=font_body(13),
            text_color=TEXTO_GRIS,
        ).pack(anchor="w")

        metrics = ctk.CTkFrame(scroll, fg_color="transparent")
        metrics.pack(fill="x", padx=24, pady=(8, 12))
        metrics.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self._metric_card(metrics, 0, "Socios activos", str(activos), self.icons.get("usuarios_card") or self.icons.get("usuarios"), f"{por_vencer} por vencer / {vencidos} vencidos", AMBAR if por_vencer or vencidos else VERDE)
        self._metric_card(metrics, 1, "Ingresos socios", f"${ingresos:,.0f}", self.icons.get("dolar_card") or self.icons.get("dolar"), self._delta_text(comparativos["ingresos"]), self._delta_color(comparativos["ingresos"]))
        self._metric_card(metrics, 2, "Ventas productos", f"${ventas_productos:,.0f}", self.icons.get("ventas_card") or self.icons.get("ventas"), self._delta_text(comparativos["ventas"]), self._delta_color(comparativos["ventas"]))
        self._metric_card(metrics, 3, "Gastos", f"${gastos:,.0f}", self.icons.get("gastos_card") or self.icons.get("gastos"), self._delta_text(comparativos["gastos"], invert=True), self._delta_color(comparativos["gastos"], invert=True))
        self._metric_card(metrics, 4, "Ingresos netos", f"${ingresos_netos:,.0f}", self.icons.get("dinero-neto"), self._delta_text(comparativos["neto"]), self._delta_color(comparativos["neto"]), highlighted=True)

        charts = ctk.CTkFrame(scroll, fg_color="transparent")
        charts.pack(fill="x", padx=24, pady=(0, 12))
        charts.grid_columnconfigure(0, weight=1, uniform="dashboard_cards")
        charts.grid_columnconfigure(1, weight=1, uniform="dashboard_cards")

        box_line = ctk.CTkFrame(charts, fg_color=GRIS_DARK, corner_radius=22, border_width=1, border_color=BORDER_SOFT)
        box_line.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ctk.CTkLabel(box_line, text="Crecimiento de socios", font=font_title(24), text_color=BLANCO).pack(anchor="w", padx=18, pady=(18, 0))
        ctk.CTkLabel(box_line, text="Altas registradas en los últimos meses", font=font_body(12), text_color=TEXTO_GRIS).pack(anchor="w", padx=18, pady=(0, 4))
        cv_line = ctk.CTkCanvas(box_line, bg=GRIS_DARK, highlightthickness=0, height=176)
        cv_line.pack(fill="both", expand=True, padx=14, pady=(2, 12))
        cv_line.bind("<Configure>", lambda e: self._draw_line_canvas(cv_line, cv_line.winfo_width(), cv_line.winfo_height(), line_data_db))
        cv_line.bind("<Leave>", lambda e: self._hide_chart_tooltip())

        box_donut = ctk.CTkFrame(charts, fg_color=GRIS_DARK, corner_radius=22, border_width=1, border_color=BORDER_SOFT)
        box_donut.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ctk.CTkLabel(box_donut, text="Distribución por plan", font=font_title(24), text_color=BLANCO).pack(anchor="w", padx=18, pady=(18, 0))
        ctk.CTkLabel(box_donut, text="Membresías activas por categoría", font=font_body(12), text_color=TEXTO_GRIS).pack(anchor="w", padx=18, pady=(0, 6))

        donut_content = ctk.CTkFrame(box_donut, fg_color="transparent")
        donut_content.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        donut_content.grid_columnconfigure(0, weight=1)
        donut_content.grid_columnconfigure(1, weight=1)

        cv_donut = ctk.CTkCanvas(donut_content, bg=GRIS_DARK, highlightthickness=0, width=190, height=190)
        cv_donut.grid(row=0, column=0, sticky="nsew")
        legend = ctk.CTkFrame(donut_content, fg_color="transparent")
        legend.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self._draw_donut_canvas(cv_donut, donut_data, legend)
        cv_donut.bind("<Leave>", lambda e: self._hide_chart_tooltip())

        bottom = ctk.CTkFrame(scroll, fg_color="transparent")
        bottom.pack(fill="x", padx=24, pady=(0, 18))
        bottom.grid_columnconfigure(0, weight=1, uniform="dashboard_bottom")
        bottom.grid_columnconfigure(1, weight=1, uniform="dashboard_bottom")

        box_rec = ctk.CTkFrame(bottom, fg_color=GRIS_DARK, corner_radius=22, border_width=1, border_color=BORDER_SOFT)
        box_rec.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ctk.CTkLabel(box_rec, text="Socios recientes", font=font_title(24), text_color=BLANCO).pack(anchor="w", padx=18, pady=(18, 10))
        if not socios_recientes:
            ctk.CTkLabel(box_rec, text="Aún no hay socios.", text_color=TEXTO_GRIS, font=font_body(13)).pack(pady=20)
        for nom, fal, tipo in socios_recientes:
            self._render_reciente(box_rec, nom, fal, tipo)
        ctk.CTkFrame(box_rec, fg_color="transparent", height=14).pack()

        box_act = ctk.CTkFrame(bottom, fg_color=GRIS_DARK, corner_radius=22, border_width=1, border_color=BORDER_SOFT)
        box_act.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ctk.CTkLabel(box_act, text="Próximos a vencer", font=font_title(24), text_color=BLANCO).pack(anchor="w", padx=18, pady=(18, 10))
        if not vencimientos:
            ctk.CTkLabel(box_act, text="No hay vencimientos cercanos.", text_color=TEXTO_GRIS, font=font_body(13)).pack(pady=20)
        for nom, tel, fec in vencimientos:
            self._render_vencimiento(box_act, nom, fec)
        ctk.CTkFrame(box_act, fg_color="transparent", height=14).pack()

        # Mantiene el scroll estable al final del panel y evita el rebote
        ctk.CTkFrame(scroll, fg_color="transparent", height=36).pack(fill="x")

    def _comparativos_mensuales(self):
        from database import conectar_finanzas, conectar_socios

        hoy = date.today().replace(day=1)
        mes_actual = hoy.strftime("%Y-%m")
        mes_anterior = (hoy - timedelta(days=1)).strftime("%Y-%m")

        con = conectar_socios()
        cur = con.cursor()
        cur.execute("SELECT COALESCE(SUM(monto), 0) FROM pagos WHERE strftime('%Y-%m', fecha)=?", (mes_actual,))
        ingresos_actual = float(cur.fetchone()[0] or 0)
        cur.execute("SELECT COALESCE(SUM(monto), 0) FROM pagos WHERE strftime('%Y-%m', fecha)=?", (mes_anterior,))
        ingresos_prev = float(cur.fetchone()[0] or 0)
        con.close()

        con_f = conectar_finanzas()
        cur_f = con_f.cursor()
        cur_f.execute("SELECT COALESCE(SUM(monto), 0) FROM ventas_productos WHERE strftime('%Y-%m', fecha)=?", (mes_actual,))
        ventas_actual = float(cur_f.fetchone()[0] or 0)
        cur_f.execute("SELECT COALESCE(SUM(monto), 0) FROM ventas_productos WHERE strftime('%Y-%m', fecha)=?", (mes_anterior,))
        ventas_prev = float(cur_f.fetchone()[0] or 0)
        cur_f.execute("SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE strftime('%Y-%m', fecha)=?", (mes_actual,))
        gastos_actual = float(cur_f.fetchone()[0] or 0)
        cur_f.execute("SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE strftime('%Y-%m', fecha)=?", (mes_anterior,))
        gastos_prev = float(cur_f.fetchone()[0] or 0)
        con_f.close()

        return {
            "ingresos": ingresos_actual - ingresos_prev,
            "ventas": ventas_actual - ventas_prev,
            "gastos": gastos_actual - gastos_prev,
            "neto": (ingresos_actual + ventas_actual - gastos_actual) - (ingresos_prev + ventas_prev - gastos_prev),
        }

    def _metric_card(self, parent, column, title, value, icon, delta_text, delta_color, highlighted=False):
        fg_color = ROJO if highlighted else GRIS_DARK
        border_color = ROJO if highlighted else BORDER_SOFT
        title_color = "#FFD8DC" if highlighted else TEXTO_GRIS
        value_color = BLANCO
        card = ctk.CTkFrame(parent, fg_color=fg_color, corner_radius=20, border_width=1, border_color=border_color)
        card.grid(row=0, column=column, sticky="ew", padx=5)
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(14, 8))
        badge = ctk.CTkFrame(top, fg_color="transparent", width=46, height=46)
        badge.pack(side="left")
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text="", image=icon, text_color=ROJO if highlighted else BLANCO).pack(expand=True)
        ctk.CTkLabel(top, text="Tendencia" if highlighted else "Live", font=font_body(10, "bold"), text_color=title_color).pack(side="right")
        ctk.CTkLabel(card, text=title, font=font_body(13, "bold"), text_color=title_color).pack(anchor="w", padx=14)
        ctk.CTkLabel(card, text=value, font=font_title(28), text_color=value_color).pack(anchor="w", padx=14, pady=(0, 4))
        ctk.CTkLabel(card, text=delta_text, font=font_body(11, "bold"), text_color=delta_color).pack(anchor="w", padx=14, pady=(0, 14))

    def _delta_text(self, delta, invert=False):
        if delta == 0:
            return "Sin cambio vs mes anterior"
        arrow = "▼" if delta < 0 else "▲"
        amount = abs(delta)
        prefix = "Menor" if invert and delta < 0 else "Mayor" if invert else "Variación"
        return f"{arrow} {prefix} ${amount:,.0f} vs mes anterior"

    def _delta_color(self, delta, invert=False):
        if delta == 0:
            return TEXTO_GRIS
        positivo = delta > 0
        if invert:
            positivo = not positivo
        return VERDE if positivo else ROJO

    def _ensure_chart_tooltip(self):
        if hasattr(self, "_chart_tooltip") and self._chart_tooltip.winfo_exists():
            return
        self._chart_tooltip = ctk.CTkToplevel(self)
        self._chart_tooltip.withdraw()
        self._chart_tooltip.overrideredirect(True)
        self._chart_tooltip.attributes("-topmost", True)
        self._chart_tooltip.configure(fg_color=NEGRO)
        label = ctk.CTkLabel(
            self._chart_tooltip,
            text="",
            fg_color=NEGRO,
            text_color=BLANCO,
            corner_radius=10,
            font=font_body(11),
            padx=10,
            pady=6,
        )
        label.pack()
        self._chart_tooltip_label = label

    def _show_chart_tooltip(self, x_root, y_root, text):
        self._ensure_chart_tooltip()
        self._chart_tooltip_label.configure(text=text)
        self._chart_tooltip.geometry(f"+{x_root + 12}+{y_root + 12}")
        self._chart_tooltip.deiconify()

    def _hide_chart_tooltip(self):
        if hasattr(self, "_chart_tooltip") and self._chart_tooltip.winfo_exists():
            self._chart_tooltip.withdraw()

    def _draw_line_canvas(self, canvas, width, height, data):
        canvas.delete("all")
        if width < 40 or height < 40:
            return
        if not data:
            canvas.create_text(width / 2, height / 2, text="Sin datos", fill=TEXTO_GRIS, font=(font_body(14).cget("family"), 14))
            return

        pad_top = 12
        pad_bottom = 32
        pad_left = 28
        pad_right = 12
        w_draw = width - pad_left - pad_right
        h_draw = height - pad_top - pad_bottom
        max_val = max((v for _, v in data), default=1)
        max_val = max(max_val, 1)
        points = []

        canvas.create_rectangle(0, 0, width, height, fill=GRIS_DARK, outline="")
        canvas.create_line(pad_left, pad_top, pad_left, height - pad_bottom, fill=GRIS_LIGHT)
        canvas.create_line(pad_left, height - pad_bottom, width - pad_right, height - pad_bottom, fill=GRIS_LIGHT)
        canvas.create_text(pad_left - 10, pad_top, text=str(max_val), fill=TEXTO_GRIS, anchor="e", font=(font_body(10).cget("family"), 10))
        canvas.create_text(pad_left - 10, height - pad_bottom, text="0", fill=TEXTO_GRIS, anchor="e", font=(font_body(10).cget("family"), 10))

        for i, (label, val) in enumerate(data):
            x = pad_left + i * (w_draw / max(1, len(data) - 1))
            y = height - pad_bottom - (val / max_val) * h_draw
            points.append((x, y, label, val))
            canvas.create_line(x, pad_top, x, height - pad_bottom, fill=GRIS_LIGHT, dash=(2, 5))
            canvas.create_text(x, height - 10, text=_month_label(label), fill=TEXTO_GRIS, font=(font_body(10).cget("family"), 10))

        fill_points = [(pad_left, height - pad_bottom)] + [(x, y) for x, y, _, _ in points] + [(points[-1][0], height - pad_bottom)]
        flat_fill = []
        for x, y in fill_points:
            flat_fill.extend([x, y])
        canvas.create_polygon(flat_fill, fill="#4A2A2D", outline="")
        if len(points) > 1:
            canvas.create_line([coord for point in points for coord in point[:2]], fill=ROJO, width=3)

        for x, y, label, val in points:
            item = canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill=BLANCO, outline=ROJO, width=2)
            canvas.tag_bind(item, "<Enter>", lambda e, lbl=label, valor=val: self._show_chart_tooltip(e.x_root, e.y_root, f"{lbl}\n{valor} socios"))
            canvas.tag_bind(item, "<Leave>", lambda e: self._hide_chart_tooltip())

    def _draw_donut_canvas(self, canvas, data, legend_parent):
        for widget in legend_parent.winfo_children():
            widget.destroy()
        canvas.delete("all")
        width = max(canvas.winfo_width(), 190)
        height = max(canvas.winfo_height(), 190)
        canvas.configure(width=width, height=height)

        if not data:
            canvas.create_text(width / 2, height / 2, text="Sin planes activos", fill=TEXTO_GRIS, font=(font_body(13).cget("family"), 13))
            return

        colors = [ROJO, "#FA5252", "#FF8787", "#7C3AED", "#F59E0B", "#22C55E"]
        total = sum(valor for _, valor in data) or 1
        start = 90
        bbox = (22, 22, width - 22, height - 22)

        unico_plan = len(data) == 1
        for idx, (label, valor) in enumerate(data):
            extent = -359.9 if unico_plan else -((valor / total) * 360)
            color = colors[idx % len(colors)]
            item = canvas.create_arc(
                bbox,
                start=start,
                extent=extent,
                fill=color,
                outline=color if unico_plan else GRIS_DARK,
                width=2,
            )
            canvas.tag_bind(item, "<Enter>", lambda e, lbl=label, v=valor: self._show_chart_tooltip(e.x_root, e.y_root, f"{lbl}\n{v} socios"))
            canvas.tag_bind(item, "<Leave>", lambda e: self._hide_chart_tooltip())
            start += extent

            row = ctk.CTkFrame(legend_parent, fg_color="transparent")
            row.pack(fill="x", pady=6)
            ctk.CTkFrame(row, fg_color=color, width=10, height=10, corner_radius=5).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=label, font=font_body(12, "bold"), text_color=BLANCO).pack(side="left")
            ctk.CTkLabel(row, text=f"{valor}", font=font_body(12), text_color=TEXTO_GRIS).pack(side="right")

        canvas.create_oval(58, 58, width - 58, height - 58, fill=GRIS_DARK, outline=GRIS_DARK)
        canvas.create_text(width / 2, height / 2 - 10, text="Planes", fill=TEXTO_GRIS, font=(font_body(11).cget("family"), 11))
        canvas.create_text(width / 2, height / 2 + 14, text=str(total), fill=BLANCO, font=(font_title(22).cget("family"), 22))

    def _render_reciente(self, parent, nom, fal, tipo):
        fila = ctk.CTkFrame(parent, fg_color=PANEL_ALT, corner_radius=16, border_width=1, border_color=BORDER_SOFT)
        fila.pack(fill="x", padx=16, pady=5)
        avatar = ctk.CTkFrame(fila, fg_color=ROJO_SUAVE, border_width=2, border_color=ROJO, width=42, height=42, corner_radius=21)
        avatar.pack(side="left", padx=12, pady=12)
        avatar.pack_propagate(False)
        ini = "".join([w[0].upper() for w in nom.split()[:2]]) if nom else "?"
        ctk.CTkLabel(avatar, text=ini, font=font_body(13, "bold"), text_color=ROJO).pack(expand=True)

        text_box = ctk.CTkFrame(fila, fg_color="transparent")
        text_box.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text_box, text=nom, font=font_body(13, "bold"), text_color=BLANCO).pack(anchor="w", pady=(10, 0))
        ctk.CTkLabel(text_box, text=f"Se unió: {fmt_date(fal)}", font=font_body(11), text_color=TEXTO_GRIS).pack(anchor="w", pady=(0, 10))

        self._plan_badge_dashboard(fila, tipo or "Sin plan").pack(side="right", padx=16)

    def _render_vencimiento(self, parent, nom, fec):
        txt_estado = "Venció el" if fec < date.today().isoformat() else "Vence el"
        color_dot = ROJO if fec < date.today().isoformat() else AMBAR
        fila = ctk.CTkFrame(parent, fg_color=PANEL_ALT, corner_radius=16, border_width=1, border_color=BORDER_SOFT)
        fila.pack(fill="x", padx=16, pady=5)
        avatar = ctk.CTkFrame(fila, fg_color=ROJO_SUAVE, border_width=2, border_color=ROJO, width=42, height=42, corner_radius=21)
        avatar.pack(side="left", padx=12, pady=12)
        avatar.pack_propagate(False)
        ini = "".join([w[0].upper() for w in nom.split()[:2]]) if nom else "?"
        ctk.CTkLabel(avatar, text=ini, font=font_body(13, "bold"), text_color=ROJO).pack(expand=True)

        ca = ctk.CTkFrame(fila, fg_color="transparent")
        ca.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(ca, text=nom, font=font_body(13, "bold"), text_color=BLANCO).pack(anchor="w", pady=(10, 0))
        ctk.CTkLabel(ca, text=f"{txt_estado} {fmt_date(fec)}", font=font_body(11), text_color=TEXTO_GRIS).pack(anchor="w", pady=(0, 10))
        ctk.CTkFrame(fila, fg_color=color_dot, width=10, height=10, corner_radius=5).pack(side="right", padx=16)

    def _plan_badge_dashboard(self, parent, plan):
        colors = {
            "Mensual": "#223B2A",
            "Bimestral": "#3B2F1E",
            "Trimestral": "#1E3345",
            "Semestral": "#4A2E17",
            "Anual": "#3A2446",
            "Sin plan": PANEL_ALT,
        }
        return ctk.CTkLabel(
            parent,
            text=plan,
            width=100,
            height=28,
            corner_radius=14,
            fg_color=colors.get(plan, PANEL_ALT),
            text_color=BLANCO,
            font=font_body(11, "bold"),
        )
