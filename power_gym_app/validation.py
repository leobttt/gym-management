from datetime import datetime
import re


def construir_nombre(nombre, apellido):
    full_name = f"{nombre.strip()} {apellido.strip()}".strip()
    if not full_name:
        raise ValueError("El nombre es obligatorio.")
    return full_name


def validar_telefono(telefono):
    digits = re.sub(r"\D", "", telefono)
    if len(digits) == 12 and digits.startswith("52"):
        digits = digits[2:]
    if len(digits) != 10:
        raise ValueError("El teléfono debe contener 10 dígitos.")
    return digits


def normalizar_telefono_whatsapp(telefono):
    digits = re.sub(r"\D", "", telefono or "")
    if not digits:
        raise ValueError("Este socio no tiene teléfono registrado.")
    if len(digits) == 10:
        return "52" + digits
    if len(digits) == 12 and digits.startswith("52"):
        return digits
    raise ValueError("El teléfono no tiene un formato válido para WhatsApp.")


def parse_monto(value, field_name="Monto", required=False):
    raw_value = (value or "").strip().replace("$", "").replace(",", "")
    if not raw_value:
        if required:
            raise ValueError(f"{field_name} es obligatorio.")
        return 0.0
    try:
        amount = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{field_name} debe ser un número válido.") from exc
    if amount < 0:
        raise ValueError(f"{field_name} no puede ser negativo.")
    return amount


def parse_fecha_ddmmyyyy(value, field_name="Fecha"):
    raw_value = (value or "").strip()
    if not raw_value:
        raise ValueError(f"{field_name} es obligatoria.")
    try:
        return datetime.strptime(raw_value, "%d-%m-%Y").date()
    except ValueError as exc:
        raise ValueError(f"{field_name} debe tener formato DD-MM-YYYY.") from exc

