import customtkinter as ctk

from database import (
    marcar_alerta_sistema_atendida,
    marcar_notificado,
    obtener_alertas_sistema_pendientes,
    socios_por_vencer,
)
from notificaciones import abrir_whatsapp
from power_gym_app.dialogs import VentanaAlerta
from power_gym_app.theme import BLANCO, BORDER_SOFT, GRIS_DARK, GRIS_MED, NEGRO, ROJO, ROJO_DARK, TEXTO_GRIS, fmt_date, font_body, font_title


class AlertasMixin:
    def mostrar_alertas(self):
        self._limpiar_main()
        page = self._build_topbar("alertas", "Notificaciones", "Dashboard / Alertas")

        self.msg_alertas_lbl = ctk.CTkLabel(page, text="", font=font_body(14), text_color=TEXTO_GRIS)
        self.msg_alertas_lbl.pack(padx=40, pady=(20, 8), anchor="w")

        self.alertas_container = ctk.CTkScrollableFrame(
            page,
            fg_color=GRIS_DARK,
            scrollbar_button_color=GRIS_DARK,
            scrollbar_button_hover_color=GRIS_DARK,
        )
        self.alertas_container.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        self.cargar_alertas()

    def cargar_alertas(self):
        for widget in self.alertas_container.winfo_children():
            widget.destroy()

        alertas_sistema = obtener_alertas_sistema_pendientes()
        socios = socios_por_vencer(dias=7, unnotified_only=True)
        total = len(alertas_sistema) + len(socios)
        self.msg_alertas_lbl.configure(text=f"{total} notificación(es) pendiente(s)")

        if not total:
            ctk.CTkLabel(
                self.alertas_container,
                text="No hay notificaciones pendientes.",
                font=font_body(14),
                text_color=TEXTO_GRIS,
            ).pack(pady=24)
            return

        for alerta in alertas_sistema:
            fila = ctk.CTkFrame(self.alertas_container, fg_color=GRIS_MED, corner_radius=16, height=78, border_width=1, border_color=BORDER_SOFT)
            fila.pack(fill="x", pady=5, padx=10)
            fila.pack_propagate(False)
            fila.grid_columnconfigure(1, weight=1)

            ctk.CTkFrame(fila, fg_color=ROJO, width=6, corner_radius=0).grid(row=0, column=0, sticky="ns", padx=(0, 15))

            info_frame = ctk.CTkFrame(fila, fg_color="transparent")
            info_frame.grid(row=0, column=1, sticky="w", pady=(10, 0))
            ctk.CTkLabel(info_frame, text=alerta["titulo"], font=font_body(15, "bold"), text_color=BLANCO).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=alerta["descripcion"], font=font_body(12), text_color=TEXTO_GRIS).pack(anchor="w")

            ctk.CTkButton(
                fila,
                text="Abrir",
                image=self.icons["ojo"],
                width=110,
                height=36,
                fg_color=ROJO,
                hover_color=ROJO_DARK,
                font=font_body(13, "bold"),
                text_color="#FFFFFF",
                corner_radius=12,
                command=lambda a=alerta: self.abrir_alerta_sistema(a),
            ).grid(row=0, column=2, padx=5)
            ctk.CTkButton(
                fila,
                text="Marcar visto",
                image=self.icons["check"],
                width=130,
                height=36,
                fg_color=ROJO,
                hover_color=ROJO_DARK,
                font=font_body(13, "bold"),
                text_color="#FFFFFF",
                corner_radius=12,
                command=lambda a_id=alerta["id"]: self.marcar_alerta_sistema(a_id),
            ).grid(row=0, column=3, padx=(0, 15))

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

            ctk.CTkLabel(
                fila,
                text=f"Vence el: {fmt_date(fecha_fin)}",
                font=font_body(13, "bold"),
                text_color="#F39C12",
            ).grid(row=0, column=2, padx=20)
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
                command=lambda m=mem_id, s=socio_id: self.marcar_alerta(m, s),
            ).grid(row=0, column=4, padx=(0, 15))

    def enviar_ws_alerta(self, nombre, telefono, fecha_fin, mem_id, socio_id):
        abrir_whatsapp(telefono, nombre, fecha_fin)
        marcar_notificado(mem_id, socio_id, "whatsapp")
        self.cargar_alertas()
        self.cargar_socios()

    def marcar_alerta(self, mem_id, socio_id):
        marcar_notificado(mem_id, socio_id, "manual")
        self.cargar_alertas()
        self.cargar_socios()

    def abrir_alerta_sistema(self, alerta):
        if alerta["tipo"] == "corte_semanal":
            self.mostrar_corte_semanal()
        elif alerta["tipo"] == "reporte_mensual":
            self.mostrar_reporte_mensual()

    def marcar_alerta_sistema(self, alerta_id):
        marcar_alerta_sistema_atendida(alerta_id)
        self.cargar_alertas()

    def revisar_vencimientos(self):
        socios = socios_por_vencer(dias=7, unnotified_only=True)
        if socios:
            self.ventana_alerta_instance = VentanaAlerta(self, socios)
