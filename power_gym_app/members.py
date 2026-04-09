import csv
from datetime import date

import customtkinter as ctk
import tkinter.filedialog as fd
import tkinter.messagebox as mb

from database import borrar_socio, obtener_socios, requiere_reinscripcion
from power_gym_app.dialogs import VentanaHistorial, VentanaPerfil, VentanaRenovar, VentanaSocio
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


class SociosMixin:
    def mostrar_socios(self):
        self._limpiar_main()
        page = self._build_topbar(
            "socios",
            "Gestión de Socios",
            "Dashboard / Socios",
            primary_action={"text": "Nuevo socio", "image": self.icons["usuario"], "command": self.nuevo_socio},
        )

        search_frame = ctk.CTkFrame(page, fg_color=NEGRO)
        search_frame.pack(fill="x", padx=16, pady=(12, 0))
        self.e_busqueda = ctk.CTkEntry(
            search_frame,
            placeholder_text="Buscar por nombre o teléfono...",
            height=42,
            corner_radius=14,
            fg_color=GRIS_MED,
            border_color=BORDER_SOFT,
            text_color=BLANCO,
            font=font_body(13),
        )
        self.e_busqueda.pack(side="left", fill="x", expand=True)
        self.e_busqueda.bind("<KeyRelease>", lambda e: self.cargar_socios())
        self.filtro_estado_var = ctk.StringVar(value="Todos")
        self.opciones_estado = ctk.CTkOptionMenu(
            search_frame,
            values=["Todos", "Activos", "Por Vencer", "Vencidos"],
            variable=self.filtro_estado_var,
            command=lambda e: self.cargar_socios(),
            fg_color=GRIS_MED,
            button_color=ROJO,
            button_hover_color=ROJO_DARK,
            dropdown_fg_color=GRIS_DARK,
            height=42,
            corner_radius=14,
            font=font_body(13, "bold"),
        )
        self.opciones_estado.pack(side="left", padx=(10, 0))
        ctk.CTkButton(search_frame, text="Exportar CSV", image=self.icons["exportar"], height=42, fg_color=GRIS_MED, hover_color=GRIS_LIGHT, text_color=BLANCO, corner_radius=14, font=font_body(13, "bold"), command=self.exportar_csv).pack(side="right", padx=(10, 0))
        self.tabla = ctk.CTkScrollableFrame(page, fg_color=NEGRO, scrollbar_button_color=NEGRO, scrollbar_button_hover_color=NEGRO)
        self.tabla.pack(fill="both", expand=True, padx=16, pady=12)
        self.cargar_socios()

    def exportar_csv(self):
        ruta = fd.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivos CSV", "*.csv")], title="Guardar Socios")
        if not ruta:
            return
        try:
            socios = obtener_socios()
            with open(ruta, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Nombre", "Teléfono", "Foto", "Fecha Alta", "Inicio Membresía", "Fin Membresía", "Tipo"])
                for socio in socios:
                    writer.writerow(socio)
            mb.showinfo("Exportación exitosa", "La base de datos se exportó correctamente.")
        except Exception as exc:
            mb.showerror("Error", f"No se pudo exportar: {exc}")

    def cargar_socios(self):
        self.actualizar_badges_sidebar()
        if not hasattr(self, "tabla") or not self.tabla.winfo_exists():
            return
        for widget in self.tabla.winfo_children():
            widget.destroy()
        filtro = self.e_busqueda.get().strip().lower() if hasattr(self, "e_busqueda") and self.e_busqueda.winfo_exists() else ""

        hoy = date.today()
        socios = []
        for socio in obtener_socios():
            sid, nombre, telefono, foto, alta, fecha_inicio, fecha_fin, tipo = socio
            estado_txt = "Sin membresía"
            if fecha_fin:
                try:
                    diff = (date.fromisoformat(fecha_fin) - hoy).days
                    if diff < 0 and requiere_reinscripcion(alta, hoy):
                        estado_txt = "Reinscripción requerida"
                    elif diff < 0:
                        estado_txt = "Vencido ❌"
                    elif 0 <= diff <= 5:
                        estado_txt = "Por vencer ⚠️"
                    else:
                        estado_txt = "Activo ✅"
                except ValueError:
                    estado_txt = "Inválido"
            if hasattr(self, "filtro_estado_var"):
                selected = self.filtro_estado_var.get()
                if selected == "Activos" and estado_txt != "Activo ✅":
                    continue
                if selected == "Por Vencer" and estado_txt != "Por vencer ⚠️":
                    continue
                if selected == "Vencidos" and estado_txt not in {"Vencido ❌", "Reinscripción requerida"}:
                    continue
            if filtro and filtro not in f"{nombre} {telefono} {tipo} {estado_txt}".lower():
                continue
            socios.append((*socio, estado_txt))

        enc = ctk.CTkFrame(self.tabla, fg_color=GRIS_DARK, corner_radius=16, border_width=1, border_color=BORDER_SOFT)
        enc.pack(fill="x", pady=(0, 8), padx=2)
        for txt, width in [("Socio", 250), ("Contacto", 120), ("Membresía", 130), ("Vencimiento", 120), ("Estado", 120)]:
            ctk.CTkLabel(enc, text=txt, width=width, font=font_title(17), text_color=TEXTO_GRIS, anchor="w").pack(side="left", padx=8, pady=10)
        ctk.CTkLabel(enc, text="Acciones", width=190, font=font_title(17), text_color=TEXTO_GRIS, anchor="center").pack(side="right", padx=10, pady=10)

        for socio in socios:
            fila = ctk.CTkFrame(self.tabla, fg_color=GRIS_DARK, corner_radius=18, border_width=1, border_color=BORDER_SOFT)
            fila.pack(fill="x", pady=2, padx=2)
            sid, nombre_completo, telefono, foto, alta, fecha_inicio, fecha_fin, tipo, estado_txt = socio
            persona = ctk.CTkFrame(fila, fg_color="transparent", width=250)
            persona.pack(side="left", padx=8, pady=4)
            persona.pack_propagate(False)
            avatar = ctk.CTkFrame(persona, fg_color=ROJO_SUAVE, border_width=2, border_color=ROJO, width=40, height=40, corner_radius=20)
            avatar.pack(side="left", padx=(6, 10))
            avatar.pack_propagate(False)
            iniciales = "".join([w[0].upper() for w in nombre_completo.split()[:2]]) if nombre_completo else "?"
            ctk.CTkLabel(
                avatar,
                text=iniciales,
                font=font_body(13, "bold"),
                text_color=ROJO,
                anchor="center",
                justify="center",
            ).place(relx=0.5, rely=0.5, anchor="center")
            text_info = ctk.CTkFrame(persona, fg_color="transparent")
            text_info.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(text_info, text=nombre_completo, anchor="w", text_color=BLANCO, font=font_body(13, "bold")).pack(anchor="w")
            ctk.CTkLabel(text_info, text=f"Alta: {fmt_date(alta)}", anchor="w", text_color=TEXTO_GRIS, font=font_body(11)).pack(anchor="w")

            ctk.CTkLabel(fila, text=telefono, width=120, anchor="w", text_color=BLANCO, font=font_body(12)).pack(side="left", padx=8)
            self._plan_badge(fila, tipo or "Sin plan").pack(side="left", padx=8)
            ctk.CTkLabel(fila, text=fmt_date(fecha_fin) or "—", width=120, anchor="w", text_color=BLANCO, font=font_body(12)).pack(side="left", padx=8)
            ctk.CTkLabel(fila, text=estado_txt, width=120, anchor="w", text_color=self._estado_color(estado_txt), font=font_body(12, "bold")).pack(side="left", padx=8)
            btn_frame = ctk.CTkFrame(fila, fg_color="transparent")
            btn_frame.pack(side="right", padx=12, pady=4)
            ctk.CTkButton(btn_frame, text="", image=self.icons["ojo"], width=34, height=34, fg_color=GRIS_MED, hover_color=GRIS_LIGHT, text_color=BLANCO, command=lambda data=socio: self.perfil_socio(data)).pack(side="left", padx=3)
            ctk.CTkButton(btn_frame, text="", image=self.icons["lista"], width=34, height=34, fg_color=GRIS_MED, hover_color=GRIS_LIGHT, command=lambda data=socio[:8]: self.historial_socio(data)).pack(side="left", padx=3)
            ctk.CTkButton(btn_frame, text="", image=self.icons["lapiz"], width=34, height=34, fg_color=GRIS_MED, hover_color=GRIS_LIGHT, command=lambda data=socio[:8]: self.editar_socio(data)).pack(side="left", padx=3)
            ctk.CTkButton(btn_frame, text="", image=self.icons["renovar"], width=34, height=34, fg_color=GRIS_MED, hover_color=GRIS_LIGHT, text_color="#000", command=lambda data=socio[:8]: self.renovar_socio(data)).pack(side="left", padx=3)
            ctk.CTkButton(btn_frame, text="", image=self.icons["eliminar"], width=34, height=34, fg_color=GRIS_MED, hover_color=GRIS_LIGHT, command=lambda socio_id=sid: self.borrar_socio_gui(socio_id)).pack(side="left", padx=6)

    def _plan_badge(self, parent, plan):
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
            width=130,
            height=28,
            corner_radius=14,
            fg_color=colors.get(plan, PANEL_ALT),
            text_color=BLANCO,
            font=font_body(11, "bold"),
        )

    def _estado_color(self, estado_txt):
        if "Vencido" in estado_txt:
            return ROJO
        if "Reinscripción" in estado_txt:
            return ROJO
        if "Por vencer" in estado_txt:
            return AMBAR
        if "Activo" in estado_txt:
            return VERDE
        return TEXTO_GRIS

    def perfil_socio(self, socio):
        VentanaPerfil(self, socio)

    def historial_socio(self, socio):
        VentanaHistorial(self, socio)

    def nuevo_socio(self):
        VentanaSocio(self, self.cargar_socios)

    def editar_socio(self, socio):
        VentanaSocio(self, self.cargar_socios, socio=socio)

    def renovar_socio(self, socio):
        VentanaRenovar(self, self.cargar_socios, socio)

    def borrar_socio_gui(self, socio_id):
        borrar_socio(socio_id)
        self.cargar_socios()
