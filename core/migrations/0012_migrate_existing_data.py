import datetime
import secrets

from django.db import migrations

# Panelden değiştirilemeyen mevcut randevu mailine değerlendirme linki eklenir.
# Metin core/services/mail_template_service.py içindeki REVIEW_LINK_SNIPPET ile aynı olmalı.
REVIEW_LINK_SNIPPET = (
    "\n"
    "⭐ Randevunuzdan sonra deneyiminizi paylaşmak isterseniz:\n"
    '<a href="{{ review_url }}">Randevuyu değerlendir</a>\n'
)


def create_default_working_hours(apps, schema_editor):
    """Mevcut firmalara eski koddaki sabit saatleri yazar: Pzt-Cmt 09:00-17:30, Pazar 10:00-17:30."""
    Companies = apps.get_model('core', 'Companies')
    WorkingHours = apps.get_model('core', 'WorkingHours')

    for company in Companies.objects.all():
        for weekday in range(7):
            WorkingHours.objects.get_or_create(
                company=company,
                weekday=weekday,
                defaults={
                    'is_closed': False,
                    'opens': datetime.time(10, 0) if weekday == 6 else datetime.time(9, 0),
                    'closes': datetime.time(17, 30),
                },
            )


def migrate_wheel_mode(apps, schema_editor):
    """Eski iki bayrağı tek moda çevirir: çark kapalıysa none, diğerleri bugünkü akış olan before."""
    Companies = apps.get_model('core', 'Companies')
    Companies.objects.filter(is_show_wheel=False).update(wheel_mode='none')
    Companies.objects.filter(is_show_wheel=True).update(wheel_mode='before')


def link_existing_wins(apps, schema_editor):
    """Eski kullanılmamış hediyeleri, müşterinin kazandıktan sonraki ilk randevusuna bağlar."""
    EarnedWins = apps.get_model('core', 'EarnedWins')
    Meetings = apps.get_model('core', 'Meetings')

    for win in EarnedWins.objects.filter(is_used=False, meeting__isnull=True):
        meeting = (
            Meetings.objects
            .filter(user_id=win.user_id, company_id=win.company_id, created_at__gte=win.created_at)
            .order_by('created_at')
            .first()
        )
        if meeting:
            win.meeting = meeting
            win.save(update_fields=['meeting'])


def fill_review_tokens(apps, schema_editor):
    """Mevcut randevulara tek tek benzersiz token yazar (callable default hepsine aynı değeri verirdi)."""
    Meetings = apps.get_model("core", "Meetings")
    used = set()
    for meeting in Meetings.objects.filter(review_token__isnull=True).iterator():
        token = secrets.token_urlsafe(24)
        while token in used:
            token = secrets.token_urlsafe(24)
        used.add(token)
        Meetings.objects.filter(pk=meeting.pk).update(review_token=token)


def add_review_link(apps, schema_editor):
    MailTemplate = apps.get_model("core", "MailTemplate")
    for template in MailTemplate.objects.filter(key="appointment_created"):
        if "review_url" in template.body:
            continue  # tekrar çalışırsa ikinci kez eklenmez
        template.body = template.body.rstrip() + "\n" + REVIEW_LINK_SNIPPET
        template.save(update_fields=["body"])


def restore_wheel_flags(apps, schema_editor):
    Companies = apps.get_model('core', 'Companies')
    Companies.objects.filter(wheel_mode='none').update(is_show_wheel=False)
    Companies.objects.exclude(wheel_mode='none').update(is_show_wheel=True)
    Companies.objects.filter(wheel_mode='before').update(show_before_meeting=True)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_reviews_staff_wheel_mode'),
    ]

    operations = [
        migrations.RunPython(create_default_working_hours, migrations.RunPython.noop),
        migrations.RunPython(migrate_wheel_mode, restore_wheel_flags),
        migrations.RunPython(link_existing_wins, migrations.RunPython.noop),
        migrations.RunPython(fill_review_tokens, migrations.RunPython.noop),
        migrations.RunPython(add_review_link, migrations.RunPython.noop),
    ]
