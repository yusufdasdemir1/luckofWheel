from datetime import time
from zoneinfo import ZoneInfo

from django.utils import timezone

# Randevu saatleri salonun yerel saatidir (sunucu UTC'de çalışır)
SALON_TZ = ZoneInfo("Europe/Istanbul")

# weekday: 0=Pazartesi ... 6=Pazar (Python'un date.weekday() değeriyle aynı)
DEFAULT_OPENS = time(9, 0)
DEFAULT_SUNDAY_OPENS = time(10, 0)
DEFAULT_CLOSES = time(17, 30)


def salon_now():
    """Şu an, salonun yerel saatiyle (timezone bilgisi olmadan, randevu saatleriyle kıyaslanabilir)."""
    return timezone.now().astimezone(SALON_TZ).replace(tzinfo=None)


def _default_for(weekday):
    opens = DEFAULT_SUNDAY_OPENS if weekday == 6 else DEFAULT_OPENS
    return {"weekday": weekday, "is_closed": False, "opens": opens, "closes": DEFAULT_CLOSES}


def hours_for_company(company):
    """Her zaman 7 günlük liste döner; kaydı olmayan günler için varsayılan saatler kullanılır."""
    saved = {h.weekday: h for h in company.working_hours.all()}
    result = []
    for weekday in range(7):
        row = saved.get(weekday)
        if row:
            result.append(
                {
                    "weekday": weekday,
                    "is_closed": row.is_closed,
                    "opens": row.opens,
                    "closes": row.closes,
                }
            )
        else:
            result.append(_default_for(weekday))
    return result


def hours_for_day(company, weekday):
    return hours_for_company(company)[weekday]


def ensure_default_working_hours(company):
    """Yeni firmaya varsayılan çalışma saatlerini yazar (var olanlara dokunmaz)."""
    from core.models import WorkingHours

    for weekday in range(7):
        default = _default_for(weekday)
        WorkingHours.objects.get_or_create(
            company=company,
            weekday=weekday,
            defaults={
                "is_closed": default["is_closed"],
                "opens": default["opens"],
                "closes": default["closes"],
            },
        )
