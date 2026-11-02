import random

from django.utils import timezone

from core.models import EarnedWins, Gifts


def spin_status(user, company):
    """Müşterinin çark hakkı: {can_spin, remaining_seconds}. Bekleme süresi dolmadıysa hak yoktur."""
    last_spin = EarnedWins.objects.filter(user=user).order_by("-created_at").first()
    if not last_spin:
        return {"can_spin": True, "remaining_seconds": 0}

    elapsed = (timezone.now() - last_spin.created_at).total_seconds()
    remaining = int(company.spin_cooldown_hours * 3600 - elapsed)
    if remaining <= 0:
        return {"can_spin": True, "remaining_seconds": 0}
    return {"can_spin": False, "remaining_seconds": remaining}


def cooldown_message(remaining_seconds):
    """Kalan süreyi kullanıcıya gösterilecek cümleye çevirir."""
    remaining_hours = remaining_seconds / 3600
    days = int(remaining_hours // 24)
    hours = int(remaining_hours % 24)
    if days > 0 and hours > 0:
        return f"Henüz spin hakkınız yenilenmedi. {days} gün {hours} saat sonra tekrar deneyin."
    if days > 0:
        return f"Henüz spin hakkınız yenilenmedi. {days} gün sonra tekrar deneyin."
    return f"Henüz spin hakkınız yenilenmedi. {hours} saat sonra tekrar deneyin."


def spin_wheel(user, company, meeting=None):
    """Firmanın aktif hediyelerinden şansa göre birini seçip EarnedWins'e yazar. Hediye yoksa None döner."""
    gifts = list(Gifts.objects.filter(company=company, is_active=True))
    if not gifts:
        return None

    total_chance = sum(g.chance for g in gifts)
    rand = random.uniform(0, total_chance)
    cumulative = 0
    selected_gift = None
    for gift in gifts:
        cumulative += gift.chance
        if rand <= cumulative:
            selected_gift = gift
            break

    if not selected_gift:
        selected_gift = random.choice(gifts)

    return EarnedWins.objects.create(
        user=user,
        company=company,
        meeting=meeting,
        gift_title=selected_gift.title,
        gift_description=selected_gift.description,
        gift_chance=selected_gift.chance,
    )
