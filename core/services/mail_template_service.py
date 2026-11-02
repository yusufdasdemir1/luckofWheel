from core.models import MailTemplate

# Randevu mailinin altındaki "değerlendir" linki. Migration 0026 mevcut şablonlara aynı metni ekler.
REVIEW_LINK_SNIPPET = (
    "\n"
    "⭐ Randevunuzdan sonra deneyiminizi paylaşmak isterseniz:\n"
    '<a href="{{ review_url }}">Randevuyu değerlendir</a>\n'
)


def create_default_mail_templates(company):
    """
    Firma ilk kez oluşturulduğunda
    default mail şablonlarını ekler.
    """

    MailTemplate.objects.get_or_create(
        company=company,
        key=MailTemplate.APPOINTMENT_CREATED,
        defaults={
            "subject": "🎁 {{ company_name }} | Randevunuz Oluşturuldu",
            "body": """
Merhaba {{ user_name }},

{{ company_name }} için randevunuz başarıyla oluşturulmuştur.

📅 Randevu Tarihi: {{ meeting_date }}
⏰ Randevu Saati: {{ meeting_time }}
💇‍♂️ Hizmet: {{ service_title }}

🎁 Kazanılan Hediye:
{{ gift_title }}

Randevu saatinden birkaç dakika önce gelmenizi rica ederiz.
Herhangi bir değişiklik veya iptal durumunda bizimle iletişime geçebilirsiniz.

Saygılarımızla,
{{ company_name }}

📞 İletişim:
{{ company_phone }}
""" + REVIEW_LINK_SNIPPET
        }
    )

    MailTemplate.objects.get_or_create(
        company=company,
        key=MailTemplate.APPOINTMENT_CANCELLED,
        defaults={
            "subject": "{{ company_name }} | Randevu İptali",
            "body": """
            Merhaba {{ user_name }},
        
            {{ company_name }} için oluşturmuş olduğunuz randevu iptal edilmiştir.
        
            📅 Randevu Tarihi: {{ meeting_date }}
            ⏰ Randevu Saati: {{ meeting_time }}
            💇‍♂️ Hizmet: {{ service_title }}
        
            Anlayışınız için teşekkür ederiz.
            Dilerseniz uygun bir tarih için yeniden randevu oluşturabilirsiniz.
        
            Saygılarımızla,
            {{ company_name }}
        
            📞 İletişim:
            {{ company_phone }}
            """
        }
    )
