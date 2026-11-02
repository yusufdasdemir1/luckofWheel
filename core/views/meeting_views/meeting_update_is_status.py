from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.models import Meetings,MeetingStatus,MailTemplate
from core.permissions import scope_for, NO_ACCESS_MESSAGE
from core.serializers.meeting_serializers.meeting_serializers import MeetingCancelSerializer
from core.services.mail_service import MailService
from django.db import transaction


class MeetingCancelView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🔄 Randevunun aktiflik durumunu değiştir (is_active True/False)",
        request_body=MeetingCancelSerializer,
        responses={
            200: "Durum başarıyla güncellendi.",
            403: "Bu işlem sadece admin kullanıcılar içindir.",
            404: "Randevu bulunamadı."
        },
        tags=["MEETINGS"]
    )
    def patch(self, request, meeting_id):
        user = request.user

        # 🔒 Firma sahibi ya da (kendi randevusu için) çalışan
        role, staff = scope_for(user)
        if role is None:
            return Response(
                {"error": NO_ACCESS_MESSAGE},
                status=status.HTTP_403_FORBIDDEN
            )

        lookup = {"id": meeting_id, "company": user.company}
        if role == "staff":
            lookup["staff"] = staff

        # 🔍 Randevuyu getir
        try:
            meeting = Meetings.objects.get(**lookup)
        except Meetings.DoesNotExist:
            return Response(
                {"error": f"{meeting_id} ID'sine ait bir randevu bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        old_status = meeting.status

        # ✅ Serializer doğrulama
        serializer = MeetingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]

        # 🔁 Durumu güncelle
        meeting.status = new_status
        meeting.save()

        if old_status != MeetingStatus.CANCELED and new_status == MeetingStatus.CANCELED:

            customer = meeting.user
            company = meeting.company

            if customer.email:
                transaction.on_commit(lambda: MailService.send_async(
                    company=company,
                    key=MailTemplate.APPOINTMENT_CANCELLED,
                    to_email=customer.email,
                    context_data={
                        "user_name": customer.name,
                        "company_name": company.title,
                        "meeting_date": meeting.date.strftime("%d.%m.%Y"),
                        "meeting_time": meeting.time.strftime("%H:%M"),
                        "service_title": meeting.service_title,
                        "company_phone": company.phone
                    }
                ))

        readable_status = dict(MeetingStatus.choices).get(new_status)

        return Response(
            {
                "message": f"Randevu durumu başarıyla '{readable_status}' olarak güncellendi.",
                "meeting_id": meeting.id,
                "status": meeting.status,
            },
            status=status.HTTP_200_OK
        )

