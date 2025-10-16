from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from core.models import Companies, Users, Meetings, Services
from core.serializers import MeetingCreateSerializer
from datetime import datetime, timedelta
from django.utils import timezone

class MeetingCreateView(APIView):
    @swagger_auto_schema(
        operation_summary="🗓️ Public: Randevu oluştur (slug bazlı, hizmet süresiyle)",
        operation_description=(
            "Müşteri, firma slug'ına göre randevu oluşturur.\n\n"
            "Hizmet süresi `Services` tablosundan otomatik alınır.\n"
            "Randevu bitiş saati (end_time) otomatik hesaplanır ve çakışmalar kontrol edilir."
        ),
        request_body=MeetingCreateSerializer,
        responses={
            201: "Randevu oluşturuldu",
            400: "Geçersiz veri, hizmet bulunamadı veya zaman çakışması var",
            404: "Firma veya kullanıcı bulunamadı",
        },
        tags=["MEETINGS"],
    )
    def post(self, request, company_slug):
        # 1️⃣ Firma kontrolü
        try:
            company = Companies.objects.get(slug=company_slug)
        except Companies.DoesNotExist:
            return Response({"error": "Firma bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        serializer = MeetingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone=serializer.validated_data["phone"]
        service_title=serializer.validated_data["service_title"]
        date=serializer.validated_data["date"]
        time=serializer.validated_data["time"]

        try:
            user = Users.objects.get(phone=phone, company=company)
        except Users.DoesNotExist:
            return Response(
                {"error": "Bu telefon numarasına ait kullanıcı bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 4️⃣ Hizmet kontrolü
        try:
            service = Services.objects.get(company=company, title=service_title, is_active=True)
        except Services.DoesNotExist:
            return Response(
                {"error": "Seçilen hizmet bulunamadı veya pasif durumda."},
                status=status.HTTP_404_NOT_FOUND
            )

        start_datetime = timezone.datetime.combine(date, time)
        end_datetime=start_datetime + timedelta(minutes=service.duration)
        end_time = end_datetime.time()

        overlap_exists=Meetings.objects.filter(
            company=company,
            date=date,
            time__lt=end_time,
            end_time__gt=time,
        ).exists()

        if overlap_exists:
            return Response(
                {"error": "Bu saat aralığında başka bir randevu zaten mevcut."},
                status=status.HTTP_400_BAD_REQUEST
            )

        Meetings.objects.create(
            user=user,
            company=company,
            service_title=service.title,
            service_duration=service.duration,
            service_price=service.price,
            date=date,
            time=time,
            end_time=end_time,
        )

        return Response(
            {
                "message": f"Randevunuz oluşturuldu: {service.title} ({date} {time} - {end_time})",
                "duration": f"{service.duration} dakika",
                "price": f"{service.price} ₺",
            },
            status=status.HTTP_201_CREATED
        )