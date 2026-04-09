import customtkinter as ctk
import tkinter.filedialog as fd
import tkinter.messagebox as mb

from database import (
    borrar_gasto,
    borrar_producto,
    borrar_venta,
    obtener_categorias,
    obtener_corte_semanal,
    obtener_gastos,
    obtener_productos,
    obtener_reporte_mensual,
    obtener_ventas,
    registrar_venta,
)
from power_gym_app.dialogs import (
    VentanaFinanzaForm,
    VentanaHistorialVentas,
    VentanaNuevoProducto,
    VentanaNuevaCategoria,
)
from power_gym_app.pdf_exports import export_corte_semanal_pdf, export_reporte_mensual_pdf
from power_gym_app.theme import (
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


class VentasMixin:
    def mostrar_corte_semanal(self):
        self._limpiar_main()
        page = self._build_topbar(
            "corte_semanal",
            "Corte Semanal",
            "Finanzas / Caja semanal",
            primary_action={"text": "Exportar corte", "image": self.icons["exportar"], "command": self.exportar_corte_semanal},
        )
        self._corte_semanal_data = obtener_corte_semanal()

        scroll = ctk.CTkScrollableFrame(page, fg_color=NEGRO, scrollbar_button_color=NEGRO, scrollbar_button_hover_color=NEGRO)
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        intro = ctk.CTkFrame(scroll, fg_color="transparent")
        intro.pack(fill="x", padx=8, pady=(8, 8))
        ctk.CTkLabel(intro, text="Resumen de caja de la semana", font=font_title(28), text_color=BLANCO).pack(anchor="w")
        ctk.CTkLabel(
            intro,
            text=f"Periodo: {fmt_date(self._corte_semanal_data['fecha_inicio'])} al {fmt_date(self._corte_semanal_data['fecha_fin'])}",
            font=font_body(13),
            text_color=TEXTO_GRIS,
        ).pack(anchor="w", pady=(2, 0))

        metrics = ctk.CTkFrame(scroll, fg_color="transparent")
        metrics.pack(fill="x", padx=8, pady=(6, 10))
        metrics.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for idx, (titulo, monto, extra, color) in enumerate([
            ("Ingresos socios", self._corte_semanal_data["ingresos_socios"], f"{self._corte_semanal_data['pagos_count']} cobro(s)", BLANCO),
            ("Ventas productos", self._corte_semanal_data["ventas_productos"], f"{self._corte_semanal_data['ventas_count']} venta(s)", BLANCO),
            ("Gastos", self._corte_semanal_data["gastos"], f"{self._corte_semanal_data['gastos_count']} registro(s)", ROJO),
            ("Neto semanal", self._corte_semanal_data["neto"], "Ingresos + ventas - gastos", VERDE if self._corte_semanal_data["neto"] >= 0 else ROJO),
        ]):
            card = ctk.CTkFrame(metrics, fg_color=GRIS_DARK, corner_radius=20, border_width=1, border_color=BORDER_SOFT)
            card.grid(row=0, column=idx, sticky="nsew", padx=5)
            ctk.CTkLabel(card, text=titulo, font=font_body(13, "bold"), text_color=TEXTO_GRIS).pack(anchor="w", padx=14, pady=(14, 4))
            ctk.CTkLabel(card, text=f"${monto:,.2f}", font=font_title(26), text_color=color).pack(anchor="w", padx=14)
            ctk.CTkLabel(card, text=extra, font=font_body(11), text_color=TEXTO_GRIS).pack(anchor="w", padx=14, pady=(0, 14))

        detail = ctk.CTkFrame(scroll, fg_color=GRIS_DARK, corner_radius=22, border_width=1, border_color=BORDER_SOFT)
        detail.pack(fill="x", padx=8, pady=(4, 12))
        ctk.CTkLabel(detail, text="Detalle del corte", font=font_title(24), text_color=BLANCO).pack(anchor="w", padx=18, pady=(18, 6))
        for titulo, valor in [
            ("Cobros de membresía", self._corte_semanal_data["pagos_count"]),
            ("Ventas registradas", self._corte_semanal_data["ventas_count"]),
            ("Gastos registrados", self._corte_semanal_data["gastos_count"]),
        ]:
            fila = ctk.CTkFrame(detail, fg_color="transparent")
            fila.pack(fill="x", padx=18, pady=4)
            ctk.CTkLabel(fila, text=titulo, font=font_body(13), text_color=BLANCO).pack(side="left")
            ctk.CTkLabel(fila, text=str(valor), font=font_body(13, "bold"), text_color=BLANCO).pack(side="right")

        ctk.CTkFrame(scroll, fg_color="transparent", height=36).pack(fill="x")

    def exportar_corte_semanal(self):
        resumen = getattr(self, "_corte_semanal_data", None) or obtener_corte_semanal()
        default_name = f"corte_semanal_{resumen['fecha_fin']}.pdf"
        ruta = fd.asksaveasfilename(defaultextension=".pdf", initialfile=default_name, filetypes=[("Archivos PDF", "*.pdf")], title="Guardar corte semanal")
        if not ruta:
            return
        try:
            export_corte_semanal_pdf(resumen, ruta)
            mb.showinfo("Exportación lista", "El corte semanal se exportó correctamente en PDF.")
        except OSError as exc:
            mb.showerror("Error", f"No se pudo exportar el corte semanal:\n{exc}")

    def mostrar_reporte_mensual(self):
        self._limpiar_main()
        page = self._build_topbar(
            "reporte_mensual",
            "Reporte Mensual",
            "Finanzas / Resumen mensual",
            primary_action={"text": "Exportar reporte", "image": self.icons["exportar"], "command": self.exportar_reporte_mensual},
        )
        self._reporte_mensual_data = obtener_reporte_mensual()

        content = ctk.CTkScrollableFrame(
            page,
            fg_color=NEGRO,
            scrollbar_button_color=GRIS_MED,
            scrollbar_button_hover_color=ROJO_DARK,
        )
        content.pack(fill="both", expand=True, padx=16, pady=12)

        intro = ctk.CTkFrame(content, fg_color="transparent")
        intro.pack(fill="x", padx=8, pady=(8, 8))
        ctk.CTkLabel(intro, text=self._reporte_mensual_data["mes_label"], font=font_title(28), text_color=BLANCO).pack(anchor="w")
        ctk.CTkLabel(
            intro,
            text="Resumen agregado del mes para consultar resultados sin depender de historiales largos en pantalla.",
            font=font_body(13),
            text_color=TEXTO_GRIS,
        ).pack(anchor="w", pady=(2, 0))

        metrics = ctk.CTkFrame(content, fg_color="transparent")
        metrics.pack(fill="x", padx=8, pady=(6, 10))
        metrics.grid_columnconfigure((0, 1, 2, 3), weight=1)
        ingresos = self._reporte_mensual_data["ingresos_membresias"]
        for idx, (titulo, valor, extra, color) in enumerate([
            ("Ingresos membresías", ingresos["total"], f"{ingresos['inscripciones']['cantidad']} inscripciones / {ingresos['renovaciones']['cantidad']} renovaciones", BLANCO),
            ("Ventas productos", self._reporte_mensual_data["ventas_productos_total"], f"{len(self._reporte_mensual_data['productos_mas_vendidos'])} producto(s) con venta", BLANCO),
            ("Gastos", self._reporte_mensual_data["gastos_total"], f"{len(self._reporte_mensual_data['gastos_por_categoria'])} categoría(s)", ROJO),
            ("Socios nuevos", float(self._reporte_mensual_data["socios_nuevos"]), "Altas registradas en el mes", BLANCO),
        ]):
            card = ctk.CTkFrame(metrics, fg_color=GRIS_DARK, corner_radius=20, border_width=1, border_color=BORDER_SOFT)
            card.grid(row=0, column=idx, sticky="nsew", padx=5)
            ctk.CTkLabel(card, text=titulo, font=font_body(13, "bold"), text_color=TEXTO_GRIS).pack(anchor="w", padx=14, pady=(14, 4))
            valor_texto = str(int(valor)) if titulo == "Socios nuevos" else f"${valor:,.2f}"
            ctk.CTkLabel(card, text=valor_texto, font=font_title(26), text_color=color).pack(anchor="w", padx=14)
            ctk.CTkLabel(card, text=extra, font=font_body(11), text_color=TEXTO_GRIS, wraplength=190, justify="left").pack(anchor="w", padx=14, pady=(0, 14))

        self._render_reporte_section(content, "Ingresos por membresías", [
            ("Inscripciones", ingresos["inscripciones"]["cantidad"], ingresos["inscripciones"]["monto"]),
            ("Renovaciones", ingresos["renovaciones"]["cantidad"], ingresos["renovaciones"]["monto"]),
        ], total_label="Total membresías", total_value=ingresos["total"], total_color=VERDE)

        productos_rows = [
            (item["producto"], item["cantidad"], item["ingresos"])
            for item in self._reporte_mensual_data["productos_mas_vendidos"]
        ]
        self._render_reporte_section(
            content,
            "Productos más vendidos",
            productos_rows,
            empty_text="No hay productos desglosados para este mes.",
            total_label="Total ventas productos",
            total_value=self._reporte_mensual_data["ventas_productos_total"],
            total_color=VERDE,
            quantity_suffix=" pza(s)",
        )

        gastos_rows = [
            (item["categoria"], item["cantidad"], item["monto"])
            for item in self._reporte_mensual_data["gastos_por_categoria"]
        ]
        self._render_reporte_section(
            content,
            "Gastos por categoría",
            gastos_rows,
            empty_text="No hay gastos registrados este mes.",
            total_label="Total gastos",
            total_value=self._reporte_mensual_data["gastos_total"],
            total_color=ROJO,
            quantity_suffix=" gasto(s)",
        )

        actividad = ctk.CTkFrame(content, fg_color=GRIS_DARK, corner_radius=22, border_width=1, border_color=BORDER_SOFT)
        actividad.pack(fill="x", padx=8, pady=(4, 12))
        ctk.CTkLabel(actividad, text="Actividad de socios", font=font_title(24), text_color=BLANCO).pack(anchor="w", padx=18, pady=(18, 10))
        for label, value in [
            ("Socios nuevos", self._reporte_mensual_data["socios_nuevos"]),
            ("Renovaciones", ingresos["renovaciones"]["cantidad"]),
        ]:
            fila = ctk.CTkFrame(actividad, fg_color="transparent")
            fila.pack(fill="x", padx=18, pady=4)
            ctk.CTkLabel(fila, text=label, font=font_body(13), text_color=BLANCO).pack(side="left")
            ctk.CTkLabel(fila, text=str(value), font=font_body(13, "bold"), text_color=BLANCO).pack(side="right")

        ctk.CTkFrame(content, fg_color="transparent", height=36).pack(fill="x")

    def _render_reporte_section(self, parent, title, rows, empty_text="", total_label=None, total_value=None, total_color=BLANCO, quantity_suffix=" movimiento(s)"):
        card = ctk.CTkFrame(parent, fg_color=GRIS_DARK, corner_radius=22, border_width=1, border_color=BORDER_SOFT)
        card.pack(fill="x", padx=8, pady=(4, 12))
        ctk.CTkLabel(card, text=title, font=font_title(24), text_color=BLANCO).pack(anchor="w", padx=18, pady=(18, 10))
        if not rows:
            ctk.CTkLabel(card, text=empty_text or "Sin datos.", text_color=TEXTO_GRIS, font=font_body(13)).pack(anchor="w", padx=18, pady=(0, 16))
            return
        for nombre, cantidad, monto in rows:
            fila = ctk.CTkFrame(card, fg_color="transparent")
            fila.pack(fill="x", padx=18, pady=4)
            ctk.CTkLabel(fila, text=nombre, font=font_body(13), text_color=BLANCO).pack(side="left")
            ctk.CTkLabel(fila, text=f"{cantidad}{quantity_suffix}", font=font_body(12), text_color=TEXTO_GRIS).pack(side="left", padx=10)
            ctk.CTkLabel(fila, text=f"${monto:,.2f}", font=font_body(13, "bold"), text_color=BLANCO if total_color != ROJO else ROJO).pack(side="right")
        if total_label is not None and total_value is not None:
            total = ctk.CTkFrame(card, fg_color=PANEL_ALT, corner_radius=12)
            total.pack(fill="x", padx=18, pady=(10, 14))
            ctk.CTkLabel(total, text=total_label, font=font_body(13, "bold"), text_color=BLANCO).pack(side="left", padx=14, pady=12)
            ctk.CTkLabel(total, text=f"${total_value:,.2f}", font=font_body(15, "bold"), text_color=total_color).pack(side="right", padx=14, pady=12)

    def exportar_reporte_mensual(self):
        reporte = getattr(self, "_reporte_mensual_data", None) or obtener_reporte_mensual()
        default_name = f"reporte_mensual_{reporte['periodo']}.pdf"
        ruta = fd.asksaveasfilename(defaultextension=".pdf", initialfile=default_name, filetypes=[("Archivos PDF", "*.pdf")], title="Guardar reporte mensual")
        if not ruta:
            return
        try:
            export_reporte_mensual_pdf(reporte, ruta)
            mb.showinfo("Exportación lista", "El reporte mensual se exportó correctamente en PDF.")
        except OSError as exc:
            mb.showerror("Error", f"No se pudo exportar el reporte mensual:\n{exc}")

    def mostrar_finanzas_generico(self, titulo, tipo):
        self._limpiar_main()
        active_key = "gastos" if tipo == "Gasto" else "ventas"
        page = self._build_topbar(
            active_key,
            titulo.title(),
            f"Dashboard / {titulo.title()}",
            primary_action={
                "text": f"Nuevo {tipo.lower()}",
                "image": self.icons["usuario"] if tipo == "Gasto" else self.icons["ventas_small"],
                "command": lambda: VentanaFinanzaForm(self, tipo, self.recargar_finanzas),
            },
        )
        self.pantalla_actual = tipo
        self.tabla = ctk.CTkScrollableFrame(page, fg_color=NEGRO, scrollbar_button_color=NEGRO, scrollbar_button_hover_color=NEGRO)
        self.tabla.pack(fill="both", expand=True, padx=16, pady=(6, 12))
        self.recargar_finanzas()

    def recargar_finanzas(self):
        if not hasattr(self, "tabla") or not self.tabla.winfo_exists():
            return
        for widget in self.tabla.winfo_children():
            widget.destroy()
        if self.pantalla_actual == "Venta":
            registros, borrar_func = obtener_ventas(), borrar_venta
        elif self.pantalla_actual == "Gasto":
            registros, borrar_func = obtener_gastos(), borrar_gasto
        else:
            return
        enc = ctk.CTkFrame(self.tabla, fg_color=GRIS_DARK, corner_radius=16, border_width=1, border_color=BORDER_SOFT)
        enc.pack(fill="x", pady=(0, 8))
        columnas = [("Fecha", 120)]
        if self.pantalla_actual == "Gasto":
            columnas.append(("Categoría", 140))
        columnas.extend([("Concepto", 320 if self.pantalla_actual == "Gasto" else 350), ("Monto", 150)])
        for txt, width in columnas:
            ctk.CTkLabel(enc, text=txt, width=width, font=font_title(17), text_color=TEXTO_GRIS, anchor="w").pack(side="left", padx=8, pady=12)
        ctk.CTkLabel(enc, text="Acciones", width=80, font=font_title(17), text_color=TEXTO_GRIS, anchor="center").pack(side="right", padx=10, pady=12)
        for registro in registros:
            fila = ctk.CTkFrame(self.tabla, fg_color=GRIS_DARK, corner_radius=16, border_width=1, border_color=BORDER_SOFT)
            fila.pack(fill="x", pady=4)
            if self.pantalla_actual == "Gasto":
                rid, fecha, categoria, concepto, monto = registro
            else:
                rid, fecha, concepto, monto = registro
                categoria = None
            ctk.CTkLabel(fila, text=fmt_date(fecha), width=120, anchor="w", text_color=BLANCO, font=font_body(12)).pack(side="left", padx=8, pady=12)
            if categoria is not None:
                ctk.CTkLabel(fila, text=categoria, width=140, anchor="w", text_color=BLANCO, font=font_body(12)).pack(side="left", padx=8, pady=12)
            ctk.CTkLabel(fila, text=concepto, width=320 if categoria is not None else 350, anchor="w", text_color=BLANCO, font=font_body(12)).pack(side="left", padx=8, pady=12)
            monto_color = VERDE if self.pantalla_actual == "Venta" else ROJO
            ctk.CTkLabel(fila, text=f"${monto:,.2f}", width=150, anchor="w", text_color=monto_color, font=font_body(13, "bold")).pack(side="left", padx=8, pady=12)
            btn_frame = ctk.CTkFrame(fila, fg_color="transparent")
            btn_frame.pack(side="right", padx=10, pady=8)
            if self.pantalla_actual == "Gasto":
                ctk.CTkButton(
                    btn_frame,
                    text="",
                    image=self.icons["lapiz"],
                    width=28,
                    height=28,
                    fg_color=GRIS_MED,
                    hover_color=GRIS_LIGHT,
                    command=lambda registro=(rid, fecha, categoria, concepto, monto): self.editar_gasto_gui(registro),
                ).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="", image=self.icons["basura"], width=28, height=28, fg_color=GRIS_MED, hover_color=GRIS_LIGHT, command=lambda item_id=rid, bfunc=borrar_func: self.borrar_finanza_gui(item_id, bfunc)).pack(side="left", padx=5)

    def borrar_finanza_gui(self, item_id, borrar_func):
        if mb.askyesno("Confirmar", "¿Estás seguro que deseas eliminar este registro?"):
            borrar_func(item_id)
            self.recargar_finanzas()

    def editar_gasto_gui(self, registro):
        VentanaFinanzaForm(self, "Gasto", self.recargar_finanzas, registro=registro)

    def mostrar_ventas(self):
        self._limpiar_main()
        page = self._build_topbar(
            "ventas",
            "Punto de Venta",
            "Dashboard / Productos",
        )
        top_frame = ctk.CTkFrame(page, fg_color=NEGRO)
        top_frame.pack(fill="x", padx=16, pady=(12, 0))
        ctk.CTkButton(top_frame, text="Historial de ventas", height=42, image=self.icons["lista"], fg_color=GRIS_MED, hover_color=GRIS_LIGHT, text_color=BLANCO, corner_radius=14, font=font_body(13, "bold"), command=lambda: VentanaHistorialVentas(self)).pack(side="right", padx=(10, 0))
        ctk.CTkButton(top_frame, text="Nueva categoría", image=self.icons["usuario"], height=42, fg_color=BLANCO, hover_color="#E9E9E9", font=font_body(13, "bold"), text_color=NEGRO, corner_radius=14, command=lambda: VentanaNuevaCategoria(self, self.cargar_pos)).pack(side="right", padx=(10, 0))
        ctk.CTkButton(top_frame, text="Nuevo producto", image=self.icons["usuario"], height=42, fg_color=BLANCO, hover_color="#E9E9E9", font=font_body(13, "bold"), text_color=NEGRO, corner_radius=14, command=lambda: VentanaNuevoProducto(self, self.cargar_pos)).pack(side="right", padx=(10, 0))
        split_frame = ctk.CTkFrame(page, fg_color=NEGRO)
        split_frame.pack(fill="both", expand=True, padx=16, pady=12)
        split_frame.grid_columnconfigure(0, weight=1)
        split_frame.grid_columnconfigure(1, weight=1)
        split_frame.grid_rowconfigure(0, weight=1)
        left_panel = ctk.CTkFrame(split_frame, fg_color=GRIS_DARK, corner_radius=20, border_width=1, border_color=BORDER_SOFT)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        header_cat = ctk.CTkFrame(left_panel, fg_color="transparent")
        header_cat.pack(fill="x", padx=18, pady=(18, 5))
        ctk.CTkLabel(header_cat, text="Catálogo de Productos", font=font_title(24), text_color=BLANCO).pack(side="left")
        
        self.filtro_cats = ctk.CTkOptionMenu(header_cat, values=["Todas las categorías"], fg_color=GRIS_MED, button_color=ROJO, button_hover_color=ROJO_DARK, text_color=BLANCO, corner_radius=8, command=lambda _: self.cargar_pos())
        self.filtro_cats.pack(side="right")
        
        self.panel_catalogo = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.panel_catalogo.pack(fill="both", expand=True, padx=10, pady=10)
        right_panel = ctk.CTkFrame(split_frame, fg_color=GRIS_DARK, corner_radius=20, border_width=1, border_color=BORDER_SOFT)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(right_panel, text="Caja / Carrito actual", font=font_title(24), text_color=BLANCO).pack(anchor="w", padx=18, pady=(18, 5))
        self.panel_carrito = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        self.panel_carrito.pack(fill="both", expand=True, padx=10, pady=10)
        self.panel_total = ctk.CTkFrame(right_panel, fg_color=PANEL_ALT, corner_radius=16, height=68, border_width=1, border_color=BORDER_SOFT)
        self.panel_total.pack(fill="x", padx=10, pady=10)
        self.panel_total.pack_propagate(False)
        self.lbl_total = ctk.CTkLabel(self.panel_total, text="Total: $0.00", font=font_title(24), text_color=VERDE)
        self.lbl_total.pack(side="left", padx=20)
        self.btn_cobrar = ctk.CTkButton(self.panel_total, text="COBRAR VENTA", image=self.icons["dolar"], height=42, font=font_body(14, "bold"), fg_color=VERDE, hover_color="#2BBF6E", text_color=NEGRO, corner_radius=14, command=self.cobrar_venta)
        self.btn_cobrar.pack(side="right", padx=20)
        self.cargar_pos()

    def cargar_pos(self):
        if not hasattr(self, "panel_catalogo") or not self.panel_catalogo.winfo_exists():
            return
            
        cats = obtener_categorias()
        opciones_cats = ["Todas las categorías"] + [c[1] for c in cats]
        cur_val = self.filtro_cats.get() if hasattr(self, "filtro_cats") else "Todas las categorías"
        if cur_val not in opciones_cats:
            cur_val = "Todas las categorías"
            
        if hasattr(self, "filtro_cats"):
            self.filtro_cats.configure(values=opciones_cats)
            self.filtro_cats.set(cur_val)
            
        for widget in self.panel_catalogo.winfo_children():
            widget.destroy()
        productos = obtener_productos()
        
        if cur_val != "Todas las categorías":
            productos = [p for p in productos if p[3] == cur_val]
            
        if not productos:
            ctk.CTkLabel(self.panel_catalogo, text="No hay productos registrados.", text_color=TEXTO_GRIS).pack(pady=20)
        self.panel_catalogo.grid_columnconfigure((0, 1, 2), weight=1)
        row_idx = 0
        col_idx = 0
        for prod in productos:
            pid, nombre, costo, cat_nombre = prod
            card = ctk.CTkFrame(self.panel_catalogo, fg_color=GRIS_MED, border_color=ROJO, border_width=1, corner_radius=18, width=160, height=152)
            card.grid(row=row_idx, column=col_idx, padx=5, pady=15)
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=nombre, font=font_body(13, "bold"), text_color=BLANCO, wraplength=120, justify="center").place(relx=0.5, rely=0.34, anchor="center")
            ctk.CTkLabel(card, text=f"${costo:,.2f}", font=font_title(22), text_color=VERDE).place(relx=0.5, rely=0.62, anchor="center")
            ctk.CTkButton(card, text="+ Añadir", width=94, height=30, corner_radius=10, fg_color=ROJO, hover_color=ROJO_DARK, font=font_body(12, "bold"), text_color="#FFF", command=lambda data=prod: self.agregar_al_carrito(data)).place(relx=0.5, rely=0.84, anchor="center")
            ctk.CTkButton(card, text="x", width=22, height=22, corner_radius=11, fg_color="transparent", hover_color=ROJO, text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12, weight="bold"), command=lambda prod_id=pid: self.eliminar_producto_catalogo(prod_id)).place(relx=0.76, rely=0.12, anchor="center")
            col_idx += 1
            if col_idx > 2:
                col_idx = 0
                row_idx += 1
        self.actualizar_carrito()

    def eliminar_producto_catalogo(self, prod_id):
        if mb.askyesno("Confirmar", "¿Eliminar este producto del catálogo?"):
            borrar_producto(prod_id)
            self.cargar_pos()

    def agregar_al_carrito(self, prod):
        pid, nombre, costo, cat_nombre = prod
        if pid in self.carrito_ventas:
            self.carrito_ventas[pid]["cantidad"] += 1
        else:
            self.carrito_ventas[pid] = {"nombre": nombre, "costo": costo, "cantidad": 1}
        self.actualizar_carrito()

    def quitar_del_carrito(self, pid):
        if pid in self.carrito_ventas:
            del self.carrito_ventas[pid]
        self.actualizar_carrito()

    def incrementar_carrito(self, pid):
        if pid in self.carrito_ventas:
            self.carrito_ventas[pid]["cantidad"] += 1
            self.actualizar_carrito()

    def decrementar_carrito(self, pid):
        if pid in self.carrito_ventas:
            if self.carrito_ventas[pid]["cantidad"] > 1:
                self.carrito_ventas[pid]["cantidad"] -= 1
            else:
                del self.carrito_ventas[pid]
            self.actualizar_carrito()

    def actualizar_carrito(self):
        if not hasattr(self, "panel_carrito") or not self.panel_carrito.winfo_exists():
            return
        for widget in self.panel_carrito.winfo_children():
            widget.destroy()
        total = 0.0
        if not self.carrito_ventas:
            ctk.CTkLabel(self.panel_carrito, text="El carrito está vacío.", text_color=TEXTO_GRIS).pack(pady=20)
            self.btn_cobrar.configure(state="disabled")
        else:
            self.btn_cobrar.configure(state="normal")
        for pid, data in self.carrito_ventas.items():
            cant = data["cantidad"]
            subtotal = data["costo"] * cant
            total += subtotal
            fila = ctk.CTkFrame(self.panel_carrito, fg_color=PANEL_ALT, corner_radius=14, border_width=1, border_color=BORDER_SOFT)
            fila.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(fila, text=data["nombre"], font=font_body(13, "bold"), text_color=BLANCO).pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(fila, text=f"${subtotal:,.2f}", font=font_body(13, "bold"), text_color=VERDE).pack(side="left", padx=(5, 10))
            ctk.CTkButton(fila, text="X", width=26, height=26, fg_color=GRIS_MED, hover_color=ROJO, text_color=BLANCO, command=lambda item_id=pid: self.quitar_del_carrito(item_id)).pack(side="right", padx=5)
            ctk.CTkButton(fila, text="+", width=26, height=26, fg_color=GRIS_MED, hover_color=ROJO, text_color=BLANCO, font=ctk.CTkFont(size=13, weight="bold"), command=lambda item_id=pid: self.incrementar_carrito(item_id)).pack(side="right", padx=2)
            ctk.CTkLabel(fila, text=str(cant), font=font_body(13, "bold"), text_color=BLANCO, width=20).pack(side="right", padx=2)
            ctk.CTkButton(fila, text="-", width=26, height=26, fg_color=GRIS_MED, hover_color="#2ecc71", text_color=BLANCO, font=ctk.CTkFont(size=13, weight="bold"), command=lambda item_id=pid: self.decrementar_carrito(item_id)).pack(side="right", padx=2)
        self.lbl_total.configure(text=f"Total: ${total:,.2f}")

    def cobrar_venta(self):
        if not self.carrito_ventas:
            return
        total = sum(d["costo"] * d["cantidad"] for d in self.carrito_ventas.values())
        concepto = ", ".join([f'{d["nombre"]} (${d["costo"]:,.2f} x {d["cantidad"]})' for d in self.carrito_ventas.values()])
        if mb.askyesno("Confirmar Cobro", f"¿Cobrar venta por un total de ${total:,.2f}?"):
            registrar_venta(concepto, total)
            self.carrito_ventas.clear()
            self.actualizar_carrito()
            mb.showinfo("Éxito", "Venta registrada exitosamente.")

    def mostrar_gastos(self):
        self.mostrar_finanzas_generico("GESTIÓN DE GASTOS", "Gasto")
