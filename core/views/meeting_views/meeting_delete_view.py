from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.models import Meetings
from core.serializers import MeetingDeleteSerializer


class MeetingDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🗑️ Randevuyu tamamen sil (sadece admin)",
        responses={
            200: MeetingDeleteSerializer,
            403: "Yetkisiz kullanıcı.",
            404: "Randevu bulunamadı."
        },
        tags=["MEETINGS"]
    )
    def delete(self, request, meeting_id):
        user = request.user

        #Sadece admin erişebilir
        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        #Randevuyu bul
        try:
            meeting = Meetings.objects.get(id=meeting_id, company=user.company)
        except Meetings.DoesNotExist:
            return Response(
                {"error": "Bu ID'ye ait bir randevu bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        #Silinmeden önce bilgileri serialize et
        serializer = MeetingDeleteSerializer(meeting)

        meeting.delete()

        return Response(
            {
                "message": "Randevu başarıyla silindi.",
                "deleted_meeting": serializer.data
            },
            status=status.HTTP_200_OK
        )
