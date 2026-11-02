from datetime import datetime

from django.db.models import Avg, Count

from core.models import MeetingStatus, ReviewStatus
from core.services.working_hours import salon_now

# GET /public/review/<token> yanıtındaki durum değerleri
STATE_OPEN = "open"            # yorum yazılabilir
STATE_TOO_EARLY = "too_early"  # randevu henüz bitmedi
STATE_CANCELED = "canceled"    # randevu iptal edildi
STATE_DONE = "done"            # bu randevu için zaten yorum yapıldı


def review_state(meeting):
    """Randevunun yorum durumu: yapılmış > iptal > erken > açık."""
    if hasattr(meeting, "review"):
        return STATE_DONE
    if meeting.status == MeetingStatus.CANCELED:
        return STATE_CANCELED
    if datetime.combine(meeting.date, meeting.end_time) > salon_now():
        return STATE_TOO_EARLY
    return STATE_OPEN


def display_name(user):
    """Public'te soyadın sadece baş harfi gösterilir: 'Ayşe K.'"""
    surname = (user.surname or "").strip()
    return f"{user.name} {surname[:1]}.".strip() if surname else user.name


def recalculate_rating(company):
    """Onaylı yorumlardan ortalama/adet önbelleğini yeniden hesaplar."""
    stats = company.reviews.filter(status=ReviewStatus.APPROVED).aggregate(
        avg=Avg("rating"), count=Count("id")
    )
    company.rating_avg = round(stats["avg"] or 0, 1)
    company.rating_count = stats["count"]
    company.save(update_fields=["rating_avg", "rating_count"])
