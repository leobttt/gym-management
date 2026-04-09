from pathlib import Path
import hashlib

ROOT_DIR = Path(__file__).resolve().parent.parent
RECEIPTS_DIR = ROOT_DIR / "recibos_socios"
PHOTOS_DIR = ROOT_DIR / "fotos_socios"


def ensure_asset_dirs():
    RECEIPTS_DIR.mkdir(exist_ok=True)
    PHOTOS_DIR.mkdir(exist_ok=True)


def _fecha_para_hash(fecha):
    fs = fecha or ""
    if len(fs) < 10:
        return fs
    if len(fs) >= 10 and fs[4:5] == "-" and fs[7:8] == "-":
        if " " in fs:
            return f"{fs[8:10]}-{fs[5:7]}-{fs[0:4]} {fs[11:16]}"
        return f"{fs[8:10]}-{fs[5:7]}-{fs[0:4]}"
    if len(fs) >= 10 and fs[2:3] == "-" and fs[5:6] == "-":
        return fs[:16] if " " in fs else fs[:10]
    return fs


def build_receipt_path(socio_id, monto, concepto, fecha):
    ensure_asset_dirs()
    fecha_str = _fecha_para_hash(fecha)
    hash_date = fecha_str[:10]
    unique_id = hashlib.md5(
        f"{hash_date}_{monto}_{concepto}".encode("utf-8")
    ).hexdigest()[:8]
    return RECEIPTS_DIR / f"recibo_socio{socio_id}_{unique_id}.jpg"


def delete_receipt_file(socio_id, monto, concepto, fecha):
    path = build_receipt_path(socio_id, monto, concepto, fecha)
    if path.exists():
        path.unlink()


def delete_member_receipts(socio_id):
    ensure_asset_dirs()
    for path in RECEIPTS_DIR.glob(f"recibo_socio{socio_id}_*.jpg"):
        path.unlink(missing_ok=True)


def delete_member_photo(photo_path, socio_id):
    if photo_path:
        delete_photo_path(photo_path)
    ensure_asset_dirs()
    for path in PHOTOS_DIR.glob(f"socio_{socio_id}_*.jpg"):
        path.unlink(missing_ok=True)


def delete_photo_path(photo_path):
    if not photo_path:
        return
    path = Path(photo_path)
    if not path.is_absolute():
        path = ROOT_DIR / path
    path.unlink(missing_ok=True)
