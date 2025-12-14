from django.template import Template, Context
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from core.models import MailTemplate, MailLog
from core.services.mail_template_service import create_default_mail_templates
import threading



class MailService:

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

        text_body = body

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

        # 🔹 Gönderen: CevirKazan hesabı ama kuaför adı görünür
        from_email = f"{company.title} | CevirKazan <{settings.DEFAULT_FROM_EMAIL}>"

        log = MailLog.objects.create(
            company=company,
            to_email=to_email,
            key=key,
            is_sent=False
        )

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,  # text/plain → satırlar düzgün
                from_email=from_email,
                to=[to_email],
            )

            msg.reply_to = [company.email]
            msg.attach_alternative(html_body, "text/html")
            sent_count = msg.send(fail_silently=True)

            if sent_count > 0:
                log.is_sent = True
            else:
                log.error_message = "SMTP send failed (fail_silently=True)"

            log.save(update_fields=["is_sent", "error_message"])

        except Exception as e:
        # Safety net – normalde düşmez
            log.error_message = str(e)
            log.save(update_fields=["error_message"])

    @staticmethod
    def send_async(*args, **kwargs):
        threading.Thread(
            target=MailService.send,
            args=args,
            kwargs=kwargs,
        ).start()