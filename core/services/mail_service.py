from django.template import Template, Context
from django.conf import settings
from core.models import MailTemplate, MailLog
from core.services.mail_template_service import create_default_mail_templates
import logging
import threading
import requests

logger = logging.getLogger(__name__)


class MailService:

    BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

    SUCCESS_STATUS_CODES = (200, 201, 202)

    @staticmethod
    def send(company, key, to_email, context_data):

        template = MailTemplate.objects.filter(
            company=company,
            key=key,
            is_active=True
        ).first()

        if not template:
            create_default_mail_templates(company)
            template = MailTemplate.objects.filter(
                company=company,
                key=key,
                is_active=True
            ).first()
            if not template:
                return

        subject = Template(template.subject).render(Context(context_data))
        body = Template(template.body).render(Context(context_data))

        html_body = f"""
        <div style="
            font-family: Arial, Helvetica, sans-serif;
            font-size: 14px;
            line-height: 1.7;
            white-space: pre-line;
        ">
        {body}
        </div>
        """

        sender_email = settings.BREVO_SENDER_EMAIL
        sender_name = f"{company.title} | CevirKazan"

        log = MailLog.objects.create(
            company=company,
            to_email=to_email,
            key=key,
            is_sent=False
        )

        payload = {
            "sender": {
                "email": sender_email,
                "name": sender_name
            },
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_body,
            "replyTo": {
                "email": company.email,
                "name": company.title
            }
        }

        headers = {
            "api-key": settings.BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = requests.post(
                MailService.BREVO_API_URL,
                json=payload,
                headers=headers,
                timeout=10
            )

            data = {}
            try:
                if response.content:
                    data = response.json()
            except ValueError:
                data = {}

            if response.status_code in MailService.SUCCESS_STATUS_CODES:
                a=response.status_code
                log.is_sent = True
                log.provider_message_id = data.get("messageId")
                log.error_message = None
            else:
                log.error_message = response.text

            log.save(update_fields=["is_sent", "provider_message_id", "error_message"])

        except Exception as e:
            log.error_message = str(e)
            log.save(update_fields=["error_message"])

    @staticmethod
    def send_plain(to_email, subject, html_content, reply_to=None):
        """
        Firmaya bağlı olmayan tek seferlik mail (örn. salon başvurusu).
        Gönderildiyse True döner. Şablon ve MailLog kullanmaz.
        """
        if not settings.BREVO_API_KEY and settings.DEBUG:
            # local'de anahtar yoksa maili göndermek yerine log'a yaz
            logger.warning("[MAIL local] to=%s subject=%s\n%s", to_email, subject, html_content)
            return True

        payload = {
            "sender": {
                "email": settings.BREVO_SENDER_EMAIL,
                "name": settings.BREVO_SENDER_NAME,
            },
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content,
        }
        if reply_to:
            payload["replyTo"] = reply_to

        headers = {
            "api-key": settings.BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.post(
                MailService.BREVO_API_URL,
                json=payload,
                headers=headers,
                timeout=10,
            )
        except Exception:
            logger.exception("Brevo isteği başarısız")
            return False

        if response.status_code in MailService.SUCCESS_STATUS_CODES:
            return True

        logger.error("Brevo mail hatası %s: %s", response.status_code, response.text)
        return False

    @staticmethod
    def send_async(*args, **kwargs):
        threading.Thread(
            target=MailService.send,
            args=args,
            kwargs=kwargs,
            daemon=True
        ).start()
