from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from datetime import datetime, timedelta
from core.models import Meetings, Services
from core.serializers.meeting_serializers.meeting_serializers import MeetingUpdateSerializer


class MeetingUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="✏️ Randevuyu güncelle (sadece admin)",
        request_body=MeetingUpdateSerializer,
        responses={
            200: "Randevu başarıyla güncellendi.",
            400: "Randevu saati başka bir randevu ile çakışıyor.",
            403: "Yetkisiz işlem.",
            404: "Randevu veya hizmet bulunamadı."
        },
        tags=["MEETINGS"]
    )
    def patch(self, request, meeting_id):
        user = request.user

        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        #Güncellenen randevuyu getir
        try:
            meeting = Meetings.objects.get(id=meeting_id, company=user.company)
        except Meetings.DoesNotExist:
            return Response(
                {"error": "Bu ID'ye ait bir randevu bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MeetingUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        #Alanları güncelle
        for field, value in data.items():
            setattr(meeting, field, value)

        #Hizmet değiştiyse süre ve fiyatı güncelle
        if "service_title" in data:
            try:
                service = Services.objects.get(
                    title=data["service_title"], company=user.company, is_active=True
                )
                meeting.service_duration = service.duration
                meeting.service_price = service.price
            except Services.DoesNotExist:
                return Response(
                    {"error": f"{data['service_title']} adlı aktif bir hizmet bulunamadı."},
                    status=status.HTTP_404_NOT_FOUND
                )

        #Yeni bitiş zamanı hesapla
        start_datetime = datetime.combine(meeting.date, meeting.time)
        end_datetime = start_datetime + timedelta(minutes=meeting.service_duration)
        meeting.end_time = end_datetime.time()

        #ÇAKIŞMA KONTROLÜ
        overlap_qs = Meetings.objects.filter(
            company=user.company,
            date=meeting.date,
            time__lt=meeting.end_time,   # mevcut randevular bitmeden başlamış mı?
            end_time__gt=meeting.time,   # mevcut randevular başladıktan sonra mı bitiyor?
        ).exclude(id=meeting.id)  # kendisini hariç tut!
        if meeting.staff_id:
            # çalışanı olan randevu sadece kendi çalışanının takvimiyle çakışır
            overlap_qs = overlap_qs.filter(staff_id=meeting.staff_id)
        overlap_exists = overlap_qs.exists()

        if overlap_exists:
            return Response(
                {"error": "Bu saat aralığında başka bir randevu zaten mevcut."},
                status=status.HTTP_400_BAD_REQUEST
            )

        meeting.save()

        return Response(
            {
                "message": "Randevu başarıyla güncellendi.",
                "updated_fields": list(data.keys()),
                "new_end_time": meeting.end_time.strftime("%H:%M:%S"),
            },
            status=status.HTTP_200_OK
        )
