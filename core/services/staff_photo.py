import os
import uuid

from django.conf import settings
from PIL import Image, ImageOps, UnidentifiedImageError

PHOTO_DIR = "staff"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 25_000_000
OUTPUT_SIZE = 600


class PhotoError(Exception):
    """Kullanıcıya gösterilecek fotoğraf hatası."""


def save_staff_photo(uploaded):
    """
    Yüklenen görseli doğrular, kareye kırpıp küçültür ve webp olarak kaydeder.
    Dosya adı kullanıcıdan gelmez (rastgele üretilir), geriye `staff/<uuid>.webp` döner.
    """
    ext = os.path.splitext(uploaded.name or "")[1].lstrip(".").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise PhotoError(f"İzin verilen uzantılar: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    if uploaded.size > MAX_BYTES:
        raise PhotoError("Fotoğraf en fazla 5 MB olabilir.")

    try:
        image = Image.open(uploaded)
        # çok büyük çözünürlüklü dosyalar açılmadan reddedilir (bellek şişmesin)
        if image.width * image.height > MAX_PIXELS:
            raise PhotoError("Fotoğrafın çözünürlüğü çok yüksek.")
        image = ImageOps.exif_transpose(image).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise PhotoError("Geçerli bir görsel dosyası yükleyin.")

    # yüzün ortada kalması için kareye kırp
    image = ImageOps.fit(image, (OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS)

    relative = f"{PHOTO_DIR}/{uuid.uuid4().hex}.webp"
    directory = os.path.join(settings.PUBLIC_ROOT, PHOTO_DIR)
    os.makedirs(directory, exist_ok=True)
    image.save(os.path.join(settings.PUBLIC_ROOT, relative), "WEBP", quality=85)
    return relative


def delete_staff_photo(relative):
    """Çalışan fotoğrafını diskten siler (sadece staff klasöründekiler)."""
    if not relative or not relative.startswith(f"{PHOTO_DIR}/"):
        return

    root = os.path.realpath(os.path.join(settings.PUBLIC_ROOT, PHOTO_DIR))
    path = os.path.realpath(os.path.join(settings.PUBLIC_ROOT, relative))
    if not path.startswith(root + os.sep):
        return

    try:
        os.remove(path)
    except FileNotFoundError:
        pass
