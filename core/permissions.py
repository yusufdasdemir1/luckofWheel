from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response

OWNER_ONLY_MESSAGE = "Bu işlem sadece firma yöneticisi içindir."
NO_ACCESS_MESSAGE = "Bu işlem için yetkiniz yok."


def get_active_staff(user):
    """Kullanıcı aktif bir çalışansa Staff kaydını döner; değilse (sahip, müşteri, pasif çalışan) None."""
    try:
        staff = user.staff_profile
    except ObjectDoesNotExist:
        return None
    return staff if staff.is_active else None


def owner_only_response(user):
    """Firma sahibi değilse 403 yanıtı döner, sahipse None."""
    if user.is_admin:
        return None
    return Response({"error": OWNER_ONLY_MESSAGE}, status=status.HTTP_403_FORBIDDEN)


def scope_for(user):
    """
    Panel verisi için kapsam:
    - firma sahibi: ("owner", None)  -> firmanın tüm verisi
    - aktif çalışan: ("staff", Staff) -> sadece kendi randevuları
    - diğer: (None, None)            -> erişim yok
    """
    if user.is_admin:
        return "owner", None
    staff = get_active_staff(user)
    if staff:
        return "staff", staff
    return None, None
