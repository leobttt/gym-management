import customtkinter as ctk
import tkinter.messagebox as mb

from database import borrar_gasto, borrar_producto, borrar_venta, obtener_gastos, obtener_productos, obtener_ventas, registrar_venta
from power_gym_app.dialogs import VentanaFinanzaForm, VentanaHistorialVentas, VentanaNuevoProducto
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
        for txt, width in [("Fecha", 120), ("Concepto", 350), ("Monto", 150)]:
            ctk.CTkLabel(enc, text=txt, width=width, font=font_title(17), text_color=TEXTO_GRIS, anchor="w").pack(side="left", padx=8, pady=12)
        ctk.CTkLabel(enc, text="Acciones", width=80, font=font_title(17), text_color=TEXTO_GRIS, anchor="center").pack(side="right", padx=10, pady=12)
        for rid, fecha, concepto, monto in registros:
            fila = ctk.CTkFrame(self.tabla, fg_color=GRIS_DARK, corner_radius=16, border_width=1, border_color=BORDER_SOFT)
            fila.pack(fill="x", pady=4)
            ctk.CTkLabel(fila, text=fmt_date(fecha), width=120, anchor="w", text_color=BLANCO, font=font_body(12)).pack(side="left", padx=8, pady=12)
            ctk.CTkLabel(fila, text=concepto, width=350, anchor="w", text_color=BLANCO, font=font_body(12)).pack(side="left", padx=8, pady=12)
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
                    command=lambda registro=(rid, fecha, concepto, monto): self.editar_gasto_gui(registro),
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
        ctk.CTkButton(top_frame, text="Nuevo producto", image=self.icons["usuario"], height=42, fg_color=BLANCO, hover_color="#E9E9E9", font=font_body(13, "bold"), text_color=ROJO, corner_radius=14, command=lambda: VentanaNuevoProducto(self, self.cargar_pos)).pack(side="right", padx=(10, 0))
        split_frame = ctk.CTkFrame(page, fg_color=NEGRO)
        split_frame.pack(fill="both", expand=True, padx=16, pady=12)
        split_frame.grid_columnconfigure(0, weight=1)
        split_frame.grid_columnconfigure(1, weight=1)
        split_frame.grid_rowconfigure(0, weight=1)
        left_panel = ctk.CTkFrame(split_frame, fg_color=GRIS_DARK, corner_radius=20, border_width=1, border_color=BORDER_SOFT)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(left_panel, text="Catálogo de Productos", font=font_title(24), text_color=BLANCO).pack(anchor="w", padx=18, pady=(18, 5))
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
        for widget in self.panel_catalogo.winfo_children():
            widget.destroy()
        productos = obtener_productos()
        if not productos:
            ctk.CTkLabel(self.panel_catalogo, text="No hay productos registrados.", text_color=TEXTO_GRIS).pack(pady=20)
        self.panel_catalogo.grid_columnconfigure((0, 1, 2), weight=1)
        row_idx = 0
        col_idx = 0
        for prod in productos:
            pid, nombre, costo = prod
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
        pid, nombre, costo = prod
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
