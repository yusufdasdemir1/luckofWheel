from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.models import Meetings
from core.serializers.meeting_serializers.meeting_serializers import MeetingCancelSerializer


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

        # 🔒 Sadece admin girebilsin
        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 🔍 Randevuyu getir
        try:
            meeting = Meetings.objects.get(id=meeting_id, company=user.company)
        except Meetings.DoesNotExist:
            return Response(
                {"error": f"{meeting_id} ID'sine ait bir randevu bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        # ✅ Serializer doğrulama
        serializer = MeetingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        is_active = serializer.validated_data["is_active"]

        # 🔁 Durumu güncelle
        meeting.is_active = is_active
        meeting.save()

        return Response(
            {
                "message": f"Randevu durumu başarıyla {'aktif' if is_active else 'iptal'} olarak güncellendi.",
                "meeting_id": meeting.id,
                "is_active": meeting.is_active,
            },
            status=status.HTTP_200_OK
        )

