import importlib
import sys
import types
import unittest
from unittest.mock import patch


class NotificacionesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fake_ctk = types.ModuleType("customtkinter")
        fake_ctk.set_appearance_mode = lambda *_args, **_kwargs: None
        fake_ctk.set_default_color_theme = lambda *_args, **_kwargs: None
        fake_ctk.CTkFont = lambda *args, **kwargs: (args, kwargs)
        sys.modules.setdefault("customtkinter", fake_ctk)
        cls.notificaciones = importlib.import_module("notificaciones")

    def test_generar_mensaje_formatea_fecha(self):
        mensaje = self.notificaciones.generar_mensaje("Leo", "2026-04-10")

        self.assertIn("Hola Leo", mensaje)
        self.assertIn("10-04-2026", mensaje)
        self.assertIn("vence", mensaje)

    @patch("notificaciones.webbrowser.open")
    def test_abrir_whatsapp_normaliza_numero_y_abre_url(self, mock_open):
        self.notificaciones.abrir_whatsapp("55 1234 5678", "Leo", "2026-04-10")

        mock_open.assert_called_once()
        url = mock_open.call_args[0][0]
        self.assertIn("https://wa.me/525512345678", url)
        self.assertIn("Hola%20Leo", url)
        self.assertIn("10-04-2026", url)


if __name__ == "__main__":
    unittest.main()
