from django.conf import settings
from django.utils.html import escape
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from core.serializers.public_serializers.public_serializers import SalonApplicationSerializer
from core.services.mail_service import MailService


class PublicSalonApplicationView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "salon_application"

    @swagger_auto_schema(
        operation_summary="📩 Public: Salon başvurusu (yönetici e-postasına iletilir)",
        operation_description=(
            "Salon eklemek isteyen kuaförün formunu alır ve `SUPPORT_EMAIL` adresine e-posta olarak iletir.\n\n"
            "`website` alanı bot tuzağıdır (honeypot): doluysa başvuru sessizce yok sayılır.\n"
            "IP başına saatlik istek sınırı vardır."
        ),
        request_body=SalonApplicationSerializer,
        responses={
            201: "Başvuru alındı",
            400: "Geçersiz veri",
            429: "Çok fazla istek",
            503: "Başvuru iletilemedi",
        },
        tags=["PUBLIC"],
    )
    def post(self, request):
        serializer = SalonApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Bot tuzağı: insanlar bu alanı görmez, doldurmaz
        if data.get("website"):
            return Response({"message": "Başvurunuz alındı."}, status=status.HTTP_201_CREATED)

        to_email = settings.SUPPORT_EMAIL
        if not to_email:
            return Response(
                {"error": "Başvuru şu anda alınamıyor. Lütfen daha sonra tekrar deneyin."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        rows = [
            ("Salon adı", data["salon_name"]),
            ("Yetkili", data["owner_name"]),
            ("Telefon", data["phone"]),
            ("E-posta", data["email"]),
            ("Şehir", data["city"]),
            ("İlçe", data.get("district", "")),
            ("Instagram", data.get("instagram", "")),
            ("Not", data.get("note", "")),
        ]
        html_rows = "".join(
            f"<tr><td style='padding:6px 14px 6px 0;font-weight:bold;vertical-align:top'>{escape(label)}</td>"
            f"<td style='padding:6px 0;white-space:pre-line'>{escape(value)}</td></tr>"
            for label, value in rows
            if value
        )
        html = (
            "<div style='font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.6'>"
            "<p>Yeni salon başvurusu geldi:</p>"
            f"<table>{html_rows}</table>"
            "</div>"
        )

        sent = MailService.send_plain(
            to_email=to_email,
            subject=f"{settings.MAIL_SUBJECT_PREFIX}Yeni salon başvurusu: {data['salon_name']}",
            html_content=html,
            reply_to={"email": data["email"], "name": data["owner_name"]},
        )
        if not sent:
            return Response(
                {"error": "Başvurunuz iletilemedi. Lütfen daha sonra tekrar deneyin."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"message": "Başvurunuz alındı."}, status=status.HTTP_201_CREATED)
