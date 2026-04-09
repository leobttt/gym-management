import customtkinter as ctk
import os
import tkinter.messagebox as mb

from power_gym_app.receipts import PHOTOS_DIR, delete_photo_path, delete_receipt_file
from power_gym_app.theme import (
    BLANCO,
    GRIS_DARK,
    GRIS_LIGHT,
    GRIS_MED,
    NEGRO,
    PANEL_ALT,
    ROJO,
    ROJO_DARK,
    ROOT_DIR,
    TEXTO_GRIS,
    fmt_date,
    font_body,
    font_title,
)
from power_gym_app.validation import (
    construir_nombre,
    normalizar_telefono_whatsapp,
    parse_fecha_ddmmyyyy,
    parse_monto,
    validar_telefono,
)

from database import (
    actualizar_fecha_alta,
    actualizar_socio,
    actualizar_membresia,
    actualizar_gasto,
    agregar_membresia,
    agregar_producto,
    agregar_socio,
    borrar_producto,
    borrar_venta,
    obtener_ventas,
    registrar_gasto,
    registrar_venta,
    agregar_categoria,
    obtener_categorias,
    requiere_reinscripcion,
)
from notificaciones import abrir_whatsapp

ICONS = {}
GASTO_CATEGORIAS = ["General", "Renta", "Servicios", "Nómina", "Mantenimiento", "Insumos", "Marketing", "Otros"]


def _add_scroll_end_spacer(container, height=28):
    ctk.CTkFrame(container, fg_color="transparent", height=height).pack(fill="x")


def _add_header_close_button(header, command):
    btn = ctk.CTkButton(
        header,
        text="",
        image=ICONS.get("regreso"),
        width=40,
        height=40,
        corner_radius=10,
        fg_color="transparent",
        hover_color=ROJO_DARK,
        command=command,
    )
    btn.place(x=8, rely=0.5, anchor="w")


class VentanaAlerta(ctk.CTkToplevel):
    def __init__(self, parent, socios):
        super().__init__()  # type: ignore
        self.title("Membresías por vencer")
        ww, wh = 600, 480
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = int((sw / 2) - (ww / 2))
        y = int((sh / 2) - (wh / 2))
        self.geometry(f"{ww}x{wh}+{x}+{y}")
        self.resizable(False, False)
        self.configure(fg_color=NEGRO)
        self.grab_set()

        header = ctk.CTkFrame(self, fg_color=ROJO, corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="  MEMBRESÍAS POR VENCER",
            image=ICONS["alerta"],
            compound="left",
            font=ctk.CTkFont(family="Arial", size=13, weight="bold"),
            text_color="#FFFFFF",
        ).pack(expand=True)
        _add_header_close_button(header, self.destroy)

        ctk.CTkLabel(
            self,
            text=f"{len(socios)} socio(s) vencen en los próximos 7 días",
            font=ctk.CTkFont(size=12),
            text_color=TEXTO_GRIS,
        ).pack(pady=(14, 6))

        frame = ctk.CTkScrollableFrame(
            self,
            fg_color=GRIS_DARK,
            scrollbar_button_color=GRIS_DARK,
            scrollbar_button_hover_color=GRIS_DARK,
            width=540,
            height=260,
        )
        frame.pack(padx=24, pady=6)

        for socio_id, nombre, telefono, fecha_fin, mem_id in socios:
            fila = ctk.CTkFrame(frame, fg_color=GRIS_MED, corner_radius=8)
            fila.pack(fill="x", pady=5, padx=4)
            fila.grid_columnconfigure(1, weight=1)

            ctk.CTkFrame(fila, fg_color=ROJO, width=4, corner_radius=0).grid(
                row=0, column=0, sticky="ns", padx=(0, 10)
            )

            info_frame = ctk.CTkFrame(fila, fg_color="transparent")
            info_frame.grid(row=0, column=1, sticky="w", pady=(8, 0))
            ctk.CTkLabel(
                info_frame, text=nombre, font=ctk.CTkFont(size=14, weight="bold"), text_color=BLANCO
            ).pack(anchor="w")
            ctk.CTkLabel(
                info_frame, text=telefono, font=ctk.CTkFont(size=11), text_color=TEXTO_GRIS
            ).pack(anchor="w")

            ctk.CTkLabel(
                fila,
                text=f"Vence: {fmt_date(fecha_fin)}",
                font=ctk.CTkFont(size=11),
                text_color=TEXTO_GRIS,
            ).grid(row=0, column=2, padx=10)

            ctk.CTkButton(
                fila,
                text="WhatsApp",
                image=ICONS["telefono"],
                width=100,
                height=30,
                fg_color=ROJO,
                hover_color=ROJO_DARK,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#FFFFFF",
                corner_radius=6,
                command=lambda n=nombre, t=telefono, f=fecha_fin, m=mem_id, s=socio_id: self.enviar_ws(
                    n, t, f, m, s
                ),
            ).grid(row=0, column=3, padx=4)

            ctk.CTkButton(
                fila,
                text="Marcar visto",
                image=ICONS["ojo"],
                width=100,
                height=30,
                fg_color=ROJO,
                hover_color=ROJO_DARK,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#FFFFFF",
                corner_radius=6,
                command=lambda m=mem_id, s=socio_id, fi=fila: self.marcar(m, s, fi),
            ).grid(row=0, column=4, padx=(0, 8))

        _add_scroll_end_spacer(frame)

        ctk.CTkButton(
            self,
            text="CERRAR",
            height=42,
            corner_radius=8,
            fg_color=ROJO,
            hover_color=ROJO_DARK,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FFFFFF",
            command=self.destroy,
        ).pack(pady=(10, 20), padx=24, fill="x")

    def enviar_ws(self, nombre, telefono, fecha_fin, mem_id, socio_id):
        from database import marcar_notificado

        abrir_whatsapp(telefono, nombre, fecha_fin)
        marcar_notificado(mem_id, socio_id, "whatsapp")

    def marcar(self, mem_id, socio_id, fila):
        from database import marcar_notificado

        marcar_notificado(mem_id, socio_id, "manual")
        fila.destroy()


class VentanaSocio(ctk.CTkToplevel):
    def __init__(self, parent, callback, socio=None):
        super().__init__()  # type: ignore
        self.callback = callback
        self.socio = socio
        es_edicion = socio is not None

        self.title("Editar socio" if es_edicion else "Nuevo socio")
        self.geometry("500x750" if es_edicion else "500x850")
        self.resizable(False, False)
        self.configure(fg_color=NEGRO)
        self.grab_set()

        self.vid = None
        self.after_id = None
        self.ruta_foto = socio[3] if socio and socio[3] else ""
        self.ruta_foto_original = self.ruta_foto
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        header = ctk.CTkFrame(self, fg_color=ROJO, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="EDITAR SOCIO" if es_edicion else "NUEVO SOCIO",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BLANCO,
        ).pack(expand=True)
        _add_header_close_button(header, self.on_close)

        form = ctk.CTkScrollableFrame(
            self, fg_color=NEGRO, scrollbar_button_color=NEGRO, scrollbar_button_hover_color=NEGRO
        )
        form.pack(padx=20, pady=10, fill="both", expand=True)
        form.grid_columnconfigure(0, weight=1)

        self.cam_frame = ctk.CTkFrame(form, height=180, fg_color=GRIS_DARK)
        self.cam_frame.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        self.lbl_video = ctk.CTkLabel(self.cam_frame, text="", height=180)
        self.lbl_video.pack(pady=5)

        default_avatar = ROOT_DIR / "icons" / "usuario.png"
        img_a_cargar = self.ruta_foto if self.ruta_foto and os.path.exists(self.ruta_foto) else str(default_avatar)
        if os.path.exists(img_a_cargar):
            from PIL import Image

            img = Image.open(img_a_cargar)
            img.thumbnail((240, 180))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.lbl_video.configure(text="", image=ctk_img)
            self.lbl_video.image = ctk_img
        else:
            self.lbl_video.configure(text="Cámara apagada")

        btn_cam_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_cam_frame.grid(row=1, column=0, pady=(0, 10))
        self.btn_cam = ctk.CTkButton(
            btn_cam_frame,
            text=" Prender Cámara",
            image=ICONS["camara"],
            command=self.toggle_cam,
            width=120,
            fg_color=ROJO,
            hover_color=ROJO_DARK,
            text_color=BLANCO,
            text_color_disabled=BLANCO,
        )
        self.btn_cam.pack(side="left", padx=5)
        self.btn_foto = ctk.CTkButton(
            btn_cam_frame,
            text=" Tomar Foto",
            image=ICONS["rayo"],
            command=self.tomar_foto,
            width=120,
            state="disabled",
            fg_color=ROJO,
            hover_color=ROJO_DARK,
            text_color=BLANCO,
            text_color_disabled=BLANCO,
        )
        self.btn_foto.pack(side="left", padx=5)

        def campo(label, row_index, valor=""):
            ctk.CTkLabel(
                form, text=label, text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w"
            ).grid(row=row_index * 2, column=0, sticky="w", pady=(10, 2))
            entry = ctk.CTkEntry(
                form,
                height=38,
                corner_radius=8,
                fg_color=GRIS_MED,
                border_color=GRIS_LIGHT,
                text_color=BLANCO,
                font=ctk.CTkFont(size=13),
            )
            entry.grid(row=row_index * 2 + 1, column=0, sticky="ew", pady=(0, 4))
            entry.insert(0, valor)
            return entry

        nombre_val = socio[1] if socio else ""
        partes = nombre_val.split(" ", 1) if nombre_val else ["", ""]

        self.e_nombre = campo("Nombre(s)", 2, partes[0])
        self.e_apellido = campo("Apellido(s)", 3, partes[1] if len(partes) > 1 else "")
        self.e_telefono = campo("Teléfono (10 dígitos)", 4, socio[2] if socio else "")

        if not es_edicion:
            from datetime import date

            ctk.CTkLabel(form, text="Tipo de membresía", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").grid(row=10, column=0, sticky="w", pady=(10, 2))
            self.tipo_mem = ctk.CTkOptionMenu(form, values=["Mensual", "Bimestral", "Trimestral", "Semestral", "Anual"], fg_color=GRIS_MED, button_color=ROJO, button_hover_color=ROJO_DARK, text_color=BLANCO, corner_radius=8, height=38)
            self.tipo_mem.grid(row=11, column=0, sticky="ew")

            ctk.CTkLabel(form, text="Fecha inicio (DD-MM-YYYY)", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").grid(row=12, column=0, sticky="w", pady=(10, 2))
            self.e_inicio = ctk.CTkEntry(form, height=38, corner_radius=8, fg_color=GRIS_MED, border_color=GRIS_LIGHT, text_color=BLANCO, font=ctk.CTkFont(size=13))
            self.e_inicio.grid(row=13, column=0, sticky="ew")
            self.e_inicio.insert(0, date.today().strftime("%d-%m-%Y"))

            ctk.CTkLabel(form, text="Pago Inicial ($)", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").grid(row=14, column=0, sticky="w", pady=(10, 2))
            self.e_monto = ctk.CTkEntry(form, height=38, corner_radius=8, fg_color=GRIS_MED, border_color=GRIS_LIGHT, text_color=BLANCO, font=ctk.CTkFont(size=13))
            self.e_monto.grid(row=15, column=0, sticky="ew")

            ctk.CTkLabel(form, text="Método de pago", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").grid(row=16, column=0, sticky="w", pady=(10, 2))
            self.metodo_pago = ctk.CTkOptionMenu(form, values=["Efectivo", "Transferencia", "Tarjeta"], fg_color=GRIS_MED, button_color=ROJO, button_hover_color=ROJO_DARK, text_color=BLANCO, corner_radius=8, height=38)
            self.metodo_pago.grid(row=17, column=0, sticky="ew")

        ctk.CTkButton(form, text="GUARDAR", height=42, corner_radius=8, fg_color=ROJO, hover_color=ROJO_DARK, font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF", command=self.guardar).grid(row=18, column=0, sticky="ew", pady=(20, 10))
        form.grid_rowconfigure(19, minsize=24)

    def on_close(self):
        if self.vid is not None:
            self.vid.release()
            self.vid = None
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        if self.ruta_foto and self.ruta_foto != self.ruta_foto_original:
            delete_photo_path(self.ruta_foto)
            self.ruta_foto = self.ruta_foto_original
        self.destroy()

    def _descartar_foto_temporal_actual(self):
        if self.ruta_foto and self.ruta_foto != self.ruta_foto_original:
            delete_photo_path(self.ruta_foto)

    def toggle_cam(self):
        import cv2
        from PIL import Image

        if self.vid is None:
            self.vid = cv2.VideoCapture(0)
            self.btn_cam.configure(text=" Prender Cámara")
            self.btn_foto.configure(state="normal")
            self.update_frame()
            return

        self.vid.release()
        self.vid = None
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.btn_cam.configure(text="Prender Cámara")
        self.btn_foto.configure(state="disabled")
        if not self.ruta_foto:
            default_ico = ROOT_DIR / "icons" / "usuario.png"
            if os.path.exists(default_ico):
                img = Image.open(default_ico)
                img.thumbnail((240, 180))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                self.lbl_video.configure(image=ctk_img, text="")
                self.lbl_video.image = ctk_img
            else:
                self.lbl_video.configure(image=None, text="Cámara apagada")

    def update_frame(self):
        import cv2
        from PIL import Image

        if self.vid is not None:
            ret, frame = self.vid.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.thumbnail((240, 180))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                self.lbl_video.configure(image=ctk_img, text="")
                self.lbl_video.image = ctk_img
            self.after_id = self.after(15, self.update_frame)

    def tomar_foto(self):
        import cv2
        from PIL import Image
        import uuid

        if self.vid is None:
            return
        ret, frame = self.vid.read()
        if not ret:
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        self.vid.release()
        self.vid = None
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.btn_cam.configure(text=" Prender Cámara")
        self.btn_foto.configure(state="disabled")

        self._descartar_foto_temporal_actual()
        PHOTOS_DIR.mkdir(exist_ok=True)
        filename = PHOTOS_DIR / f"socio_{uuid.uuid4().hex[:8]}.jpg"
        img.save(filename, "JPEG")
        self.ruta_foto = str(filename)

        img.thumbnail((240, 180))
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self.lbl_video.configure(image=ctk_img, text="")
        self.lbl_video.image = ctk_img

    def guardar(self):
        from datetime import timedelta
        from database import registrar_pago
        from generador_recibos import generar_recibo_jpg

        try:
            nombre = construir_nombre(self.e_nombre.get(), self.e_apellido.get())
            telefono = validar_telefono(self.e_telefono.get())
        except ValueError as exc:
            mb.showerror("Datos incompletos", str(exc))
            return

        if self.socio is not None:
            actualizar_socio(self.socio[0], nombre, telefono, self.ruta_foto)
            self.ruta_foto_original = self.ruta_foto
        else:
            dias = {"Mensual": 30, "Bimestral": 60, "Trimestral": 90, "Semestral": 180, "Anual": 365}
            try:
                fecha_inicio = parse_fecha_ddmmyyyy(self.e_inicio.get(), "Fecha de inicio")
                monto = parse_monto(self.e_monto.get(), "Pago inicial")
            except ValueError as exc:
                mb.showerror("Datos inválidos", str(exc))
                return

            fecha_fin = fecha_inicio + timedelta(days=dias[self.tipo_mem.get()])
            metodo = self.metodo_pago.get()
            socio_id = agregar_socio(nombre, telefono, self.ruta_foto, fecha_inicio.isoformat())
            self.ruta_foto_original = self.ruta_foto
            agregar_membresia(socio_id, fecha_inicio.isoformat(), fecha_fin.isoformat(), self.tipo_mem.get())
            registrar_pago(socio_id, monto, metodo, "Inscripción")
            VentanaRecibo(
                self,
                generar_recibo_jpg(nombre, monto, metodo, "Inscripción", None, socio_id, temporal=True),
                telefono,
                auto_delete=True,
            )

        if self.vid is not None:
            self.vid.release()
            self.vid = None
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.destroy()
        self.callback()


class VentanaRenovar(ctk.CTkToplevel):
    def __init__(self, parent, callback, socio):
        super().__init__()  # type: ignore
        self.callback = callback
        self.socio = socio
        self.reinscripcion_requerida = requiere_reinscripcion(socio[4])

        self.title("Reinscribir socio" if self.reinscripcion_requerida else "Renovar Membresía")
        self.geometry("380x600" if self.reinscripcion_requerida else "380x540")
        self.resizable(False, False)
        self.configure(fg_color=NEGRO)
        self.grab_set()

        header = ctk.CTkFrame(self, fg_color=ROJO, corner_radius=0, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text=f"{'REINSCRIBIR' if self.reinscripcion_requerida else 'RENOVAR'} A {socio[1].split()[0].upper()}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FFFFFF",
        ).pack(expand=True)
        _add_header_close_button(header, self.destroy)

        form = ctk.CTkFrame(self, fg_color=NEGRO)
        form.pack(padx=30, pady=20, fill="both", expand=True)
        if self.reinscripcion_requerida:
            ctk.CTkLabel(
                form,
                text="La inscripción anterior ya cumplió un año. Este cobro se registrará como reinscripción.",
                text_color=TEXTO_GRIS,
                font=ctk.CTkFont(size=12),
                wraplength=300,
                justify="left",
            ).pack(anchor="w", pady=(0, 12))
        ctk.CTkLabel(form, text="Tipo de membresía", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(10, 2))
        self.tipo_mem = ctk.CTkOptionMenu(form, values=["Mensual", "Bimestral", "Trimestral", "Semestral", "Anual"], fg_color=GRIS_MED, button_color=ROJO, button_hover_color=ROJO_DARK, text_color=BLANCO, corner_radius=8, height=38)
        self.tipo_mem.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Fecha inicio (DD-MM-YYYY)", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(10, 2))
        self.e_inicio = ctk.CTkEntry(form, height=38, corner_radius=8, fg_color=GRIS_MED, border_color=GRIS_LIGHT, text_color=BLANCO, font=ctk.CTkFont(size=13))
        self.e_inicio.pack(fill="x", pady=(0, 10))
        from datetime import date
        self.e_inicio.insert(0, date.today().strftime("%d-%m-%Y"))

        ctk.CTkLabel(form, text="Monto pagado ($)", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(10, 2))
        self.e_monto = ctk.CTkEntry(form, height=38, corner_radius=8, fg_color=GRIS_MED, border_color=GRIS_LIGHT, text_color=BLANCO, font=ctk.CTkFont(size=13))
        self.e_monto.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Método de pago", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(10, 2))
        self.metodo_pago = ctk.CTkOptionMenu(form, values=["Efectivo", "Transferencia", "Tarjeta"], fg_color=GRIS_MED, button_color=ROJO, button_hover_color=ROJO_DARK, text_color=BLANCO, corner_radius=8, height=38)
        self.metodo_pago.pack(fill="x", pady=(0, 20))
        ctk.CTkButton(
            form,
            text="GUARDAR REINSCRIPCIÓN" if self.reinscripcion_requerida else "GUARDAR RENOVACIÓN",
            height=50,
            corner_radius=8,
            fg_color=ROJO,
            text_color="#FFFFFF",
            hover_color=ROJO_DARK,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.guardar,
        ).pack(fill="x", pady=(15, 20))

    def guardar(self):
        from datetime import timedelta
        from database import registrar_pago
        from generador_recibos import generar_recibo_jpg

        dias = {"Mensual": 30, "Bimestral": 60, "Trimestral": 90, "Semestral": 180, "Anual": 365}
        try:
            fecha_inicio = parse_fecha_ddmmyyyy(self.e_inicio.get(), "Fecha de inicio")
            monto = parse_monto(self.e_monto.get(), "Monto pagado")
        except ValueError as exc:
            mb.showerror("Datos inválidos", str(exc))
            return

        fecha_fin = fecha_inicio + timedelta(days=dias[self.tipo_mem.get()])
        metodo = self.metodo_pago.get()
        actualizar_membresia(self.socio[0], fecha_inicio.isoformat(), fecha_fin.isoformat(), self.tipo_mem.get())
        concepto_pago = "Reinscripción" if self.reinscripcion_requerida else "Renovación"
        if self.reinscripcion_requerida:
            actualizar_fecha_alta(self.socio[0], fecha_inicio.isoformat())
        registrar_pago(self.socio[0], monto, metodo, concepto_pago)
        VentanaRecibo(
            self,
            generar_recibo_jpg(self.socio[1], monto, metodo, concepto_pago, None, self.socio[0], temporal=True),
            self.socio[2],
            auto_delete=True,
        )
        self.callback()
        self.destroy()


class VentanaPerfil(ctk.CTkToplevel):
    def __init__(self, parent, socio):
        super().__init__()  # type: ignore
        self.title("Perfil del Socio")
        self.geometry("450x550")
        self.resizable(False, False)
        self.configure(fg_color=NEGRO)
        self.grab_set()

        _, nombre, telefono, foto, _, _, fecha_fin, tipo, estado_txt = socio

        header = ctk.CTkFrame(self, fg_color=ROJO, corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="FICHA DE CLIENTE", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF").pack(expand=True)
        _add_header_close_button(header, self.destroy)

        card = ctk.CTkFrame(self, fg_color=GRIS_DARK, corner_radius=12)
        card.pack(padx=20, pady=20, fill="both", expand=True)

        self.img_frame = ctk.CTkFrame(card, fg_color=NEGRO, width=160, height=160, corner_radius=80)
        self.img_frame.pack(pady=20)
        self.img_frame.pack_propagate(False)
        self.lbl_foto = ctk.CTkLabel(self.img_frame, text="")
        self.lbl_foto.pack(expand=True, fill="both")

        img_a_cargar = foto if foto and os.path.exists(foto) else str(ROOT_DIR / "icons" / "usuario.png")
        if os.path.exists(img_a_cargar):
            from PIL import Image

            img = Image.open(img_a_cargar)
            img.thumbnail((160, 160))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.lbl_foto.configure(image=ctk_img)
            self.lbl_foto.image = ctk_img
        else:
            self.lbl_foto.configure(text="Sin foto")

        ctk.CTkLabel(card, text=nombre.upper(), font=ctk.CTkFont(size=22, weight="bold"), text_color=BLANCO).pack(pady=(0, 5))
        ctk.CTkLabel(card, text=f" {telefono}", image=ICONS["telefono"], compound="left", font=ctk.CTkFont(size=14), text_color=TEXTO_GRIS).pack()

        stats = ctk.CTkFrame(card, fg_color=GRIS_MED, corner_radius=8)
        stats.pack(fill="x", padx=30, pady=20)
        stats.grid_columnconfigure((0, 1), weight=1)

        def add_stat(label, value, row_index):
            ctk.CTkLabel(stats, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXTO_GRIS).grid(row=row_index, column=0, sticky="w", padx=20, pady=10)
            ctk.CTkLabel(stats, text=value, font=ctk.CTkFont(size=14, weight="bold"), text_color=BLANCO).grid(row=row_index, column=1, sticky="e", padx=20, pady=10)

        add_stat("Membresía", tipo if tipo else "Ninguna", 0)
        add_stat("Vencimiento", fmt_date(fecha_fin) if fecha_fin else "—", 1)
        add_stat("Estado", estado_txt, 2)


class VentanaHistorial(ctk.CTkToplevel):
    def __init__(self, parent, socio):
        super().__init__()  # type: ignore
        self.title("Historial de Pagos")
        self.geometry("600x400")
        self.resizable(False, False)
        self.configure(fg_color=NEGRO)
        self.grab_set()

        nombre = socio[1].upper()
        header = ctk.CTkFrame(self, fg_color=ROJO, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=f"HISTORIAL: {nombre}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").pack(expand=True)
        _add_header_close_button(header, self.destroy)

        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkButton(top_frame, text="Limpiar historial", image=ICONS["basura"], fg_color="#000000", hover_color="#222222", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"), command=lambda s=socio[0]: self.limpiar_todo(s)).pack(side="right")

        self.tabla = ctk.CTkScrollableFrame(self, fg_color=GRIS_DARK, scrollbar_button_color=GRIS_DARK, scrollbar_button_hover_color=GRIS_DARK)
        self.tabla.pack(fill="both", expand=True, padx=20, pady=20)

        enc = ctk.CTkFrame(self.tabla, fg_color=GRIS_MED, corner_radius=4)
        enc.pack(fill="x", pady=(0, 4))
        for txt, width in [("Fecha", 100), ("Concepto", 120), ("Monto", 100), ("Método", 100)]:
            ctk.CTkLabel(enc, text=txt, width=width, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXTO_GRIS, anchor="w").pack(side="left", padx=5, pady=5)

        from database import obtener_historial_pagos
        pagos = obtener_historial_pagos(socio[0])
        if not pagos:
            ctk.CTkLabel(self.tabla, text="No hay pagos registrados aún.", text_color=TEXTO_GRIS, pady=20).pack()

        for pago_id, fecha, concepto, monto, metodo in pagos:
            fila = ctk.CTkFrame(self.tabla, fg_color=NEGRO, corner_radius=4)
            fila.pack(fill="x", pady=2)
            for val, width in [(fmt_date(fecha), 100), (concepto, 120), (f"${monto:,.2f}", 100), (metodo, 100)]:
                ctk.CTkLabel(fila, text=str(val), width=width, font=ctk.CTkFont(size=12), text_color=BLANCO, anchor="w").pack(side="left", padx=5, pady=5)

            ctk.CTkButton(fila, text="", image=ICONS["basura"], width=32, height=32, fg_color=GRIS_MED, hover=False, command=lambda p_id=pago_id, m=monto, c=concepto, f=fecha, s_id=socio[0], row=fila: self.borrar_recibo_gui(p_id, m, c, f, s_id, row)).pack(side="right", padx=(5, 10), pady=0)

        _add_scroll_end_spacer(self.tabla)

    def borrar_recibo_gui(self, pago_id, monto, concepto, fecha, socio_id, fila):
        from database import borrar_pago

        if mb.askyesno("Confirmar", "¿Estás seguro que deseas eliminar este recibo y su historial de pago?"):
            borrar_pago(pago_id)
            try:
                delete_receipt_file(socio_id, monto, concepto, fecha)
            except OSError as exc:
                mb.showerror("Error", f"No se pudo eliminar el archivo del recibo:\n{exc}")
            fila.destroy()

    def limpiar_todo(self, socio_id):
        from database import borrar_todos_pagos_socio

        if mb.askyesno("Confirmar", "¿Eliminar TODOS los recibos e historial de pagos de este socio?\n\nEsta acción es permanente."):
            borrar_todos_pagos_socio(socio_id)
            for widget in self.tabla.winfo_children():
                widget.destroy()
            ctk.CTkLabel(self.tabla, text="Historial limpiado. No hay pagos.", text_color=TEXTO_GRIS, pady=20).pack()
            _add_scroll_end_spacer(self.tabla)


class VentanaFinanzaForm(ctk.CTkToplevel):
    def __init__(self, parent, tipo, callback, registro=None):
        super().__init__()
        self.tipo = tipo
        self.callback = callback
        self.registro = registro

        es_edicion = registro is not None
        self.title(f"{'Editar' if es_edicion else 'Nuevo'} {self.tipo}")
        self.geometry("380x380")
        self.resizable(False, False)
        self.configure(fg_color=NEGRO)
        self.grab_set()

        header = ctk.CTkFrame(self, fg_color=ROJO, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text=f"{'EDITAR' if es_edicion else 'REGISTRAR'} {self.tipo.upper()}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FFFFFF",
        ).pack(expand=True)
        _add_header_close_button(header, self.destroy)

        form = ctk.CTkFrame(self, fg_color=NEGRO)
        form.pack(padx=30, pady=20, fill="both", expand=True)
        self.categoria_var = None
        ctk.CTkLabel(form, text="Concepto/Descripción", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(10, 2))
        self.e_concepto = ctk.CTkEntry(form, height=38, corner_radius=8, fg_color=GRIS_MED, border_color=GRIS_LIGHT, text_color=BLANCO, font=ctk.CTkFont(size=13))
        self.e_concepto.pack(fill="x", pady=(0, 10))
        if self.tipo == "Gasto":
            ctk.CTkLabel(form, text="Categoría", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(10, 2))
            categoria_default = registro[2] if registro is not None and len(registro) >= 5 else "General"
            self.categoria_var = ctk.StringVar(value=categoria_default if categoria_default in GASTO_CATEGORIAS else "General")
            self.e_categoria = ctk.CTkOptionMenu(
                form,
                values=GASTO_CATEGORIAS,
                variable=self.categoria_var,
                fg_color=GRIS_MED,
                button_color=ROJO,
                button_hover_color=ROJO_DARK,
                text_color=BLANCO,
                corner_radius=8,
                height=38,
            )
            self.e_categoria.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(form, text="Monto ($)", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(10, 2))
        self.e_monto = ctk.CTkEntry(form, height=38, corner_radius=8, fg_color=GRIS_MED, border_color=GRIS_LIGHT, text_color=BLANCO, font=ctk.CTkFont(size=13))
        self.e_monto.pack(fill="x", pady=(0, 20))
        if registro is not None:
            if self.tipo == "Gasto":
                _, _, _, concepto, monto = registro
            else:
                _, _, concepto, monto = registro
            self.e_concepto.insert(0, concepto)
            self.e_monto.insert(0, f"{monto:.2f}")
        ctk.CTkButton(form, text="GUARDAR", height=50, corner_radius=8, fg_color=ROJO, text_color="#FFFFFF", hover_color=ROJO_DARK, font=ctk.CTkFont(size=16, weight="bold"), command=self.guardar).pack(fill="x", pady=(15, 20))

    def guardar(self):
        concepto = self.e_concepto.get().strip()
        monto_str = self.e_monto.get().strip()
        if not concepto or not monto_str:
            mb.showerror("Datos incompletos", "Concepto y monto son obligatorios.")
            return
        try:
            monto = parse_monto(monto_str, "Monto", required=True)
        except ValueError as exc:
            mb.showerror("Dato inválido", str(exc))
            return
        categoria = self.categoria_var.get() if self.categoria_var is not None else "General"

        if self.tipo == "Gasto" and self.registro is not None:
            actualizar_gasto(self.registro[0], concepto, monto, categoria)
        elif self.tipo == "Gasto":
            registrar_gasto(concepto, monto, categoria)
        else:
            registrar_venta(concepto, monto)
        self.callback()
        self.destroy()

class VentanaNuevaCategoria(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__()
        self.callback = callback
        self.title("Nueva Categoría")
        self.geometry("380x280")
        self.resizable(False, False)
        self.configure(fg_color=NEGRO)
        self.grab_set()

        header = ctk.CTkFrame(self, fg_color=ROJO, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="AGREGAR CATEGORÍA", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").pack(expand=True)
        _add_header_close_button(header, self.destroy)

        form = ctk.CTkFrame(self, fg_color=NEGRO)
        form.pack(padx=30, pady=20, fill="both", expand=True)
        ctk.CTkLabel(form, text="Nombre de la categoría", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(10, 2))
        self.e_nombre = ctk.CTkEntry(form, height=38, corner_radius=8, fg_color=GRIS_MED, border_color=GRIS_LIGHT, text_color=BLANCO, font=ctk.CTkFont(size=13))
        self.e_nombre.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(form, text="GUARDAR", height=50, corner_radius=8, fg_color=ROJO, text_color="#FFFFFF", hover_color=ROJO_DARK, font=ctk.CTkFont(size=16, weight="bold"), command=self.guardar).pack(fill="x", pady=(10, 20))

    def guardar(self):
        nombre = self.e_nombre.get().strip()
        if not nombre:
            mb.showerror("Datos incompletos", "El nombre es obligatorio.")
            return
            
        agregar_categoria(nombre)
        self.callback()
        self.destroy()


class VentanaNuevoProducto(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__()
        self.callback = callback
        self.title("Nuevo Producto")
        self.geometry("380x480")
        self.resizable(False, False)
        self.configure(fg_color=NEGRO)
        self.grab_set()

        header = ctk.CTkFrame(self, fg_color=ROJO, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="AGREGAR PRODUCTO", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").pack(expand=True)
        _add_header_close_button(header, self.destroy)

        form = ctk.CTkFrame(self, fg_color=NEGRO)
        form.pack(padx=30, pady=20, fill="both", expand=True)
        ctk.CTkLabel(form, text="Nombre del producto", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(10, 2))
        self.e_nombre = ctk.CTkEntry(form, height=38, corner_radius=8, fg_color=GRIS_MED, border_color=GRIS_LIGHT, text_color=BLANCO, font=ctk.CTkFont(size=13))
        self.e_nombre.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(form, text="Costo ($)", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(10, 2))
        self.e_costo = ctk.CTkEntry(form, height=38, corner_radius=8, fg_color=GRIS_MED, border_color=GRIS_LIGHT, text_color=BLANCO, font=ctk.CTkFont(size=13))
        self.e_costo.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(form, text="Categoría", text_color=TEXTO_GRIS, font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(10, 2))
        
        cats = obtener_categorias()
        self.mapa_categorias = {c[1]: c[0] for c in cats}
        nombres_cats = list(self.mapa_categorias.keys())
        
        if not nombres_cats:
            self.e_categoria = ctk.CTkOptionMenu(form, values=["Sin categoría"], state="disabled", fg_color=GRIS_MED, button_color=ROJO, button_hover_color=ROJO_DARK, text_color=BLANCO, corner_radius=8, height=38)
        else:
            self.e_categoria = ctk.CTkOptionMenu(form, values=nombres_cats, fg_color=GRIS_MED, button_color=ROJO, button_hover_color=ROJO_DARK, text_color=BLANCO, corner_radius=8, height=38)
        self.e_categoria.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(form, text="GUARDAR", height=50, corner_radius=8, fg_color=ROJO, text_color="#FFFFFF", hover_color=ROJO_DARK, font=ctk.CTkFont(size=16, weight="bold"), command=self.guardar).pack(fill="x", pady=(15, 20))

    def guardar(self):
        nombre = self.e_nombre.get().strip()
        costo_str = self.e_costo.get().strip()
        cat_seleccionada = self.e_categoria.get()
        
        if not nombre or not costo_str:
            mb.showerror("Datos incompletos", "Nombre y costo son obligatorios.")
            return
            
        if cat_seleccionada == "Sin categoría" or cat_seleccionada not in self.mapa_categorias:
            mb.showerror("Categoría Faltante", "Debe crear una categoría antes de añadir productos.")
            return
        try:
            costo = parse_monto(costo_str, "Costo", required=True)
        except ValueError as exc:
            mb.showerror("Dato inválido", str(exc))
            return
            
        cat_id = self.mapa_categorias[cat_seleccionada]
        agregar_producto(nombre, costo, cat_id)
        self.callback()
        self.destroy()


class VentanaHistorialVentas(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__()
        self.title("Historial de Ventas")
        self.geometry("650x500")
        self.resizable(False, False)
        self.configure(fg_color=NEGRO)
        self.grab_set()

        header = ctk.CTkFrame(self, fg_color=ROJO, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="HISTORIAL DE VENTAS", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").pack(expand=True)
        _add_header_close_button(header, self.destroy)

        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkButton(
            top_frame,
            text="Limpiar historial",
            image=ICONS["basura"],
            fg_color="#000000",
            hover_color="#222222",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.limpiar_todo,
        ).pack(side="right")

        self.tabla = ctk.CTkScrollableFrame(self, fg_color=GRIS_DARK, scrollbar_button_color=GRIS_DARK, scrollbar_button_hover_color=GRIS_DARK)
        self.tabla.pack(fill="both", expand=True, padx=20, pady=20)
        self.cargar()

    def cargar(self):
        for widget in self.tabla.winfo_children():
            widget.destroy()
        registros = obtener_ventas()

        enc = ctk.CTkFrame(self.tabla, fg_color=GRIS_MED, corner_radius=6)
        enc.pack(fill="x", pady=(0, 4))
        for txt, width in [("Fecha", 100), ("Concepto", 280), ("Monto", 100)]:
            ctk.CTkLabel(enc, text=txt, width=width, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXTO_GRIS, anchor="w").pack(side="left", padx=5, pady=5)

        for rid, fecha, concepto, monto in registros:
            fila = ctk.CTkFrame(self.tabla, fg_color=NEGRO, corner_radius=4)
            fila.pack(fill="x", pady=2)
            ctk.CTkLabel(fila, text=fmt_date(fecha), width=100, anchor="w", text_color=BLANCO, font=ctk.CTkFont(size=12)).pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(fila, text=concepto.replace(", ", "\n"), width=280, anchor="w", justify="left", wraplength=270, text_color=BLANCO, font=ctk.CTkFont(size=12)).pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(fila, text=f"${monto:,.2f}", width=100, anchor="w", text_color=BLANCO, font=ctk.CTkFont(size=12)).pack(side="left", padx=5, pady=5)
            btn_frame = ctk.CTkFrame(fila, fg_color="transparent")
            btn_frame.pack(side="right", padx=10, pady=5)
            ctk.CTkButton(btn_frame, text="", image=ICONS["basura"], width=28, height=28, fg_color=GRIS_MED, hover_color=GRIS_LIGHT, command=lambda item_id=rid: self.borrar_venta_gui(item_id)).pack(side="left")

        _add_scroll_end_spacer(self.tabla)

    def borrar_venta_gui(self, item_id):
        if mb.askyesno("Confirmar", "¿Eliminar registro?"):
            borrar_venta(item_id)
            self.cargar()

    def limpiar_todo(self):
        from database import borrar_todas_ventas

        if mb.askyesno("Confirmar", "¿Estás seguro de eliminar TODAS las ventas registradas del historial?"):
            borrar_todas_ventas()
            self.cargar()


class VentanaRecibo(ctk.CTkToplevel):
    def __init__(self, parent, ruta_jpg, telefono="", auto_delete=False):
        super().__init__()  # type: ignore
        self.title("Recibo de Pago")
        self.resizable(False, False)
        self.configure(fg_color=NEGRO)
        self.grab_set()
        self.lift()
        self.focus_force()

        self._telefono = telefono
        self._ruta_jpg = ruta_jpg
        self._auto_delete = auto_delete
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

        from PIL import Image as PILImage

        try:
            img = PILImage.open(ruta_jpg)
        except Exception:
            img = PILImage.new("RGB", (600, 400), (255, 255, 255))

        max_w, max_h = 600, 700
        img.thumbnail((max_w, max_h), PILImage.LANCZOS)
        img_w, img_h = img.size

        win_w = img_w + 40
        win_h = img_h + 140
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = int((sw - win_w) / 2)
        y = int((sh - win_h) / 2)
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")

        header = ctk.CTkFrame(self, fg_color=ROJO, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="RECIBO DE PAGO", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").pack(expand=True)
        _add_header_close_button(header, self._cerrar)

        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img_w, img_h))
        lbl = ctk.CTkLabel(self, image=ctk_img, text="")
        lbl.image = ctk_img
        lbl.pack(padx=20, pady=(16, 10))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 16))
        fila1 = ctk.CTkFrame(btn_frame, fg_color="transparent")
        fila1.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(fila1, text="Compartir por WhatsApp", image=ICONS["telefono"], height=42, corner_radius=8, fg_color="#25D366", hover_color="#1ebe57", text_color="#FFFFFF", font=ctk.CTkFont(size=14, weight="bold"), command=self._compartir_whatsapp).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(fila1, text="Copiar imagen", height=42, corner_radius=8, fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF", font=ctk.CTkFont(size=14, weight="bold"), command=self._copiar_imagen).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(btn_frame, text="Cerrar", image=ICONS["basura"], height=38, corner_radius=8, fg_color=GRIS_MED, hover_color=GRIS_LIGHT, text_color=BLANCO, font=ctk.CTkFont(size=13), command=self._cerrar).pack(fill="x")

    def _cerrar(self):
        if self._auto_delete and self._ruta_jpg:
            try:
                os.remove(self._ruta_jpg)
            except FileNotFoundError:
                pass
            except OSError as exc:
                mb.showerror("Error", f"No se pudo eliminar el recibo temporal:\n{exc}")
                return
        self.destroy()

    def _compartir_whatsapp(self):
        import webbrowser

        try:
            digitos = normalizar_telefono_whatsapp(self._telefono)
        except ValueError as exc:
            mb.showwarning("Sin número", str(exc))
            return
        webbrowser.open(f"https://wa.me/{digitos}")

    def _copiar_imagen(self):
        import platform
        import subprocess

        ruta = os.path.abspath(self._ruta_jpg)
        sistema = platform.system()
        try:
            if sistema == "Darwin":
                script = f'set the clipboard to (read (POSIX file "{ruta}") as JPEG picture)'
                subprocess.run(["osascript", "-e", script], check=True)
            elif sistema == "Windows":
                from PIL import Image as PILImage
                import io
                import win32clipboard  # type: ignore

                img = PILImage.open(ruta).convert("RGB")
                output = io.BytesIO()
                img.save(output, "BMP")
                data = output.getvalue()[14:]
                output.close()
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
            else:
                subprocess.run(f'xclip -selection clipboard -t image/png -i "{ruta}"', shell=True, check=True)
            mb.showinfo("Imagen copiada", "Imagen copiada al portapapeles.\nPega directamente en WhatsApp con Cmd+V.")
        except Exception as exc:
            mb.showerror("Error", f"No se pudo copiar la imagen:\n{exc}")
