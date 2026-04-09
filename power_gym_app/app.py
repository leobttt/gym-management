import customtkinter as ctk

import power_gym_app.dialogs as dialogs
from database import socios_por_vencer
from power_gym_app.alerts import AlertasMixin
from power_gym_app.dashboard import DashboardMixin
from power_gym_app.members import SociosMixin
from power_gym_app.sales import VentasMixin
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
    font_body,
    font_title,
    cargar_iconos_globales,
)

ICONS = {}


class App(AlertasMixin, DashboardMixin, SociosMixin, VentasMixin, ctk.CTk):
    def __init__(self):
        super().__init__()
        global ICONS
        ICONS = cargar_iconos_globales()
        dialogs.ICONS = ICONS
        self.icons = ICONS
        self.rojo_dark = ROJO_DARK
        self.title("Power Gym")
        self.geometry("1050x700")
        self.configure(fg_color=GRIS_DARK)
        self.resizable(True, True)
        self.nav_buttons = {}
        self.sidebar_badges = {}
        self.carrito_ventas = {}
        self.topbar_container = None
        self.content_container = None

        self.after(0, self._maximizar_ventana)
        self._build_sidebar()
        self._build_main()
        self.after(600, self.revisar_vencimientos)
        self.cargar_socios()

    def _maximizar_ventana(self):
        try:
            self.state("zoomed")
        except Exception:
            try:
                w = self.winfo_screenwidth()
                h = self.winfo_screenheight()
                self.geometry(f"{w}x{h}+0+0")
            except Exception:
                pass

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=GRIS_DARK, width=272, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = ctk.CTkFrame(self.sidebar, fg_color=GRIS_DARK, corner_radius=0, height=120)
        brand.pack(fill="x", padx=0, pady=0)
        brand.pack_propagate(False)
        ctk.CTkLabel(brand, text="POWER", font=font_title(30), text_color=BLANCO).pack(anchor="w", padx=24, pady=(24, 0))
        ctk.CTkLabel(brand, text="GYM", font=font_title(44), text_color=ROJO).pack(anchor="w", padx=24)
        ctk.CTkLabel(brand, text="Premium fitness management", font=font_body(12), text_color=TEXTO_GRIS).pack(anchor="w", padx=24, pady=(0, 12))

        footer_wrap = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_wrap.pack(side="bottom", fill="x", padx=18, pady=(0, 18))

        nav = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav.pack(fill="both", expand=True, padx=18, pady=(18, 10))

        self._sidebar_section(nav, "PANEL")
        self._sidebar_item(nav, "inicio", "Dashboard", self.mostrar_inicio, icon=self.icons.get("dashboard"))
        self._sidebar_item(nav, "alertas", "Notificaciones", self.mostrar_alertas, icon=self.icons.get("alerta"))

        self._sidebar_separator(nav)
        self._sidebar_section(nav, "SOCIOS")
        self._sidebar_item(nav, "socios", "Gestión de socios", self.mostrar_socios, icon=self.icons.get("usuarios"))

        self._sidebar_separator(nav)
        self._sidebar_section(nav, "OPERACIÓN")
        self._sidebar_item(nav, "ventas", "Ventas productos", self.mostrar_ventas, icon=self.icons.get("ventas_small"))
        self._sidebar_item(nav, "gastos", "Gastos", self.mostrar_gastos, icon=self.icons.get("gastos_small"))

        footer = ctk.CTkFrame(footer_wrap, fg_color=PANEL_ALT, corner_radius=16, border_width=0, border_color=BORDER_SOFT, height=76)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        ctk.CTkFrame(footer, fg_color=ROJO_SUAVE, width=42, height=42, corner_radius=21).pack(side="left", padx=14, pady=16)
        footer.winfo_children()[-1].pack_propagate(False)
        ctk.CTkLabel(footer.winfo_children()[-1], text="PG", font=font_title(18), text_color=ROJO).pack(expand=True)
        footer_text = ctk.CTkFrame(footer, fg_color="transparent")
        footer_text.pack(side="left", fill="x", expand=True, pady=12)
        ctk.CTkLabel(footer_text, text="Power Gym", font=font_body(13, "bold"), text_color=BLANCO).pack(anchor="w")
        ctk.CTkLabel(footer_text, text="Administración", font=font_body(11), text_color=TEXTO_GRIS).pack(anchor="w")

    def _sidebar_section(self, parent, text):
        ctk.CTkFrame(parent, fg_color=BORDER_SOFT, height=1).pack(fill="x", pady=(2, 10))
        ctk.CTkLabel(parent, text=text, font=font_title(14), text_color=TEXTO_GRIS).pack(anchor="w", pady=(0, 8), padx=6)

    def _sidebar_separator(self, parent):
        ctk.CTkFrame(parent, fg_color=BORDER_SOFT, height=1).pack(fill="x", pady=14)

    def _sidebar_item(self, parent, key, text, command, badge=None, icon=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        btn = ctk.CTkButton(
            row,
            text=text,
            image=icon,
            compound="left",
            height=44,
            anchor="w",
            fg_color=GRIS_MED,
            hover_color=ROJO_DARK,
            text_color=BLANCO,
            border_width=1,
            border_color=BORDER_SOFT,
            font=font_body(14, "bold"),
            corner_radius=14,
            command=command,
        )
        btn.pack(side="left", fill="x", expand=True)
        self.nav_buttons[key] = btn
        if badge is not None:
            badge_lbl = ctk.CTkLabel(
                row,
                text=badge,
                width=28,
                height=28,
                corner_radius=14,
                fg_color=ROJO,
                text_color=BLANCO,
                font=font_body(12, "bold"),
            )
            badge_lbl.place(relx=0.9, rely=0.5, anchor="center")
            self.sidebar_badges[key] = badge_lbl

    def _build_main(self):
        self.main = ctk.CTkFrame(self, fg_color=NEGRO, corner_radius=0)
        self.main.pack(side="right", fill="both", expand=True)
        self.mostrar_inicio()

    def _limpiar_main(self):
        for w in self.main.winfo_children():
            w.destroy()
        self.topbar_container = None
        self.content_container = None

    def _set_active_nav(self, active_key):
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.configure(fg_color=ROJO, hover_color=ROJO_DARK, border_color=ROJO)
            else:
                btn.configure(fg_color=GRIS_MED, hover_color=ROJO_DARK, border_color=BORDER_SOFT)

    def _notificaciones_pendientes(self):
        try:
            return len(socios_por_vencer(dias=7, unnotified_only=True))
        except Exception:
            return 0

    def _build_topbar(self, active_key, title, subtitle, primary_action=None, show_notifications=False):
        self._set_active_nav(active_key)
        wrapper = ctk.CTkFrame(self.main, fg_color=NEGRO, corner_radius=0)
        wrapper.pack(fill="both", expand=True)

        topbar = ctk.CTkFrame(wrapper, fg_color=ROJO, corner_radius=0, height=88)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        left = ctk.CTkFrame(topbar, fg_color="transparent")
        left.pack(side="left", fill="y", padx=24, pady=10)
        ctk.CTkLabel(left, text=subtitle.upper(), font=font_title(16), text_color="#FFD7DA").pack(anchor="w")
        ctk.CTkLabel(left, text=title, font=font_title(28), text_color=BLANCO).pack(anchor="w")

        right = ctk.CTkFrame(topbar, fg_color="transparent")
        right.pack(side="right", padx=24, pady=18)

        if show_notifications:
            notif_wrap = ctk.CTkFrame(right, fg_color="transparent", width=48, height=48)
            notif_wrap.pack(side="left", padx=(0, 12))
            notif_wrap.pack_propagate(False)
            notif_btn = ctk.CTkButton(
                notif_wrap,
                text="",
                image=self.icons.get("alerta"),
                width=48,
                height=48,
                corner_radius=16,
                fg_color=NEGRO,
                hover_color=GRIS_DARK,
                command=self.mostrar_alertas,
            )
            notif_btn.pack(fill="both", expand=True)
            if self._notificaciones_pendientes():
                dot = ctk.CTkFrame(notif_wrap, fg_color=BLANCO, width=10, height=10, corner_radius=5)
                dot.place(relx=0.8, rely=0.2, anchor="center")

        if primary_action:
            ctk.CTkButton(
                right,
                text=primary_action.get("text", "Acción"),
                image=primary_action.get("image"),
                height=48,
                corner_radius=16,
                fg_color=BLANCO,
                hover_color="#E9E9E9",
                text_color=ROJO,
                font=font_body(14, "bold"),
                command=primary_action.get("command"),
            ).pack(side="left")

        content = ctk.CTkFrame(wrapper, fg_color=NEGRO, corner_radius=0)
        content.pack(fill="both", expand=True)
        self.topbar_container = topbar
        self.content_container = content
        return content

    def _update_sidebar_badge(self, key, value):
        badge = self.sidebar_badges.get(key)
        if badge is not None and badge.winfo_exists():
            badge.configure(text=str(value))

    def actualizar_badges_sidebar(self):
        return
