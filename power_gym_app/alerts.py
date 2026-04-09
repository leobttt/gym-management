import customtkinter as ctk

from database import marcar_notificado, socios_por_vencer
from notificaciones import abrir_whatsapp
from power_gym_app.dialogs import VentanaAlerta
from power_gym_app.theme import BLANCO, BORDER_SOFT, GRIS_DARK, GRIS_MED, NEGRO, ROJO, ROJO_DARK, TEXTO_GRIS, fmt_date, font_body, font_title


class AlertasMixin:
    def mostrar_alertas(self):
        self._limpiar_main()
        page = self._build_topbar("alertas", "Notificaciones", "Dashboard / Alertas")

        filtro_frame = ctk.CTkFrame(page, fg_color=NEGRO)
        filtro_frame.pack(fill="x", padx=40, pady=(20, 0))

        ctk.CTkLabel(
            filtro_frame,
            text="Filtrar estado:",
            font=font_body(14, "bold"),
            text_color=TEXTO_GRIS,
        ).pack(side="left", padx=(0, 10))

        self.filtro_alertas_var = ctk.StringVar(value="Por Vencer")
        opciones = ctk.CTkOptionMenu(
            filtro_frame,
            values=["Por Vencer", "Vencidos", "Activos"],
            variable=self.filtro_alertas_var,
            command=self.cargar_alertas,
            fg_color=GRIS_MED,
            button_color=ROJO,
            button_hover_color=ROJO_DARK,
            dropdown_fg_color=GRIS_DARK,
            corner_radius=12,
            font=font_body(13, "bold"),
        )
        opciones.pack(side="left")

        self.msg_alertas_lbl = ctk.CTkLabel(page, text="", font=font_body(14), text_color=TEXTO_GRIS)
        self.msg_alertas_lbl.pack(pady=(10, 5))

        self.alertas_container = ctk.CTkScrollableFrame(
            page,
            fg_color=GRIS_DARK,
            scrollbar_button_color=GRIS_DARK,
            scrollbar_button_hover_color=GRIS_DARK,
        )
        self.alertas_container.pack(fill="both", expand=True, padx=40, pady=(5, 20))

        self.cargar_alertas("Por Vencer")

    def cargar_alertas(self, estado=None):
        from database import obtener_socios_por_estado_notificacion

        if not estado:
            estado = self.filtro_alertas_var.get()

        for widget in self.alertas_container.winfo_children():
            widget.destroy()

        socios = obtener_socios_por_estado_notificacion(estado, unnotified_only=False)
        if estado == "Por Vencer":
            msg = f"{len(socios)} socio(s) vencen en los próximos 7 días"
        elif estado == "Vencidos":
            msg = f"{len(socios)} socio(s) con membresía vencida"
        elif estado == "Activos":
            msg = f"{len(socios)} socio(s) actualmente activos"
        else:
            msg = ""
        self.msg_alertas_lbl.configure(text=msg)

        for socio_id, nombre, telefono, fecha_fin, mem_id in socios:
            fila = ctk.CTkFrame(self.alertas_container, fg_color=GRIS_MED, corner_radius=16, height=72, border_width=1, border_color=BORDER_SOFT)
            fila.pack(fill="x", pady=5, padx=10)
            fila.pack_propagate(False)
            fila.grid_columnconfigure(1, weight=1)

            ctk.CTkFrame(fila, fg_color=ROJO, width=6, corner_radius=0).grid(row=0, column=0, sticky="ns", padx=(0, 15))

            info_frame = ctk.CTkFrame(fila, fg_color="transparent")
            info_frame.grid(row=0, column=1, sticky="w", pady=(8, 0))
            ctk.CTkLabel(info_frame, text=nombre, font=font_body(15, "bold"), text_color=BLANCO).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=telefono, font=font_body(12), text_color=TEXTO_GRIS).pack(anchor="w")

            if estado == "Activos":
                txt_estado = f"Activo hasta: {fmt_date(fecha_fin)}"
                color_estado = "#2ecc71"
            elif estado == "Vencidos":
                txt_estado = f"Vencido el: {fmt_date(fecha_fin)}"
                color_estado = ROJO
            else:
                txt_estado = f"Vence el: {fmt_date(fecha_fin)}"
                color_estado = "#F39C12"

            ctk.CTkLabel(fila, text=txt_estado, font=font_body(13, "bold"), text_color=color_estado).grid(row=0, column=2, padx=20)
            ctk.CTkButton(
                fila,
                text="WhatsApp",
                image=self.icons["telefono"],
                width=110,
                height=36,
                fg_color=ROJO,
                hover_color=ROJO_DARK,
                font=font_body(13, "bold"),
                text_color="#FFFFFF",
                corner_radius=12,
                command=lambda n=nombre, t=telefono, f=fecha_fin, m=mem_id, s=socio_id: self.enviar_ws_alerta(n, t, f, m, s),
            ).grid(row=0, column=3, padx=5)
            ctk.CTkButton(
                fila,
                text="Marcar visto",
                image=self.icons["ojo"],
                width=110,
                height=36,
                fg_color=ROJO,
                hover_color=ROJO_DARK,
                font=font_body(13, "bold"),
                text_color="#FFFFFF",
                corner_radius=12,
                command=lambda m=mem_id, s=socio_id, fi=fila: self.marcar_alerta(m, s, fi),
            ).grid(row=0, column=4, padx=(0, 15))

    def enviar_ws_alerta(self, nombre, telefono, fecha_fin, mem_id, socio_id):
        abrir_whatsapp(telefono, nombre, fecha_fin)
        marcar_notificado(mem_id, socio_id, "whatsapp")

    def marcar_alerta(self, mem_id, socio_id, fila):
        marcar_notificado(mem_id, socio_id, "manual")
        fila.destroy()

    def revisar_vencimientos(self):
        socios = socios_por_vencer(dias=7, unnotified_only=True)
        if socios:
            self.ventana_alerta_instance = VentanaAlerta(self, socios)
