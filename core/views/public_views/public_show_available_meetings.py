from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.models import Companies, Meetings, MeetingStatus
from core.serializers.public_serializers.public_serializers import MeetingOccupiedSerializer
from drf_yasg import openapi

class PublicOccupiedMeetingsView(APIView):
    @swagger_auto_schema(
        operation_summary="📅 Firma slug’ına göre dolu randevu saatlerini getir (public)",
        operation_description=(
                "Bu uç noktadan herhangi bir kullanıcı JWT olmadan erişebilir.\n\n"
                "Belirli bir firmanın dolu tarih ve saatlerini döner.\n\n"
                "Frontend, bu veriyi takvimde 'dolu saatleri' devre dışı bırakmak için kullanabilir."
        ),
        tags=["PUBLIC"],
        responses={
            200: openapi.Response(
                description="Başarılı listeleme",
                schema=MeetingOccupiedSerializer(many=True),
            ),
            404: "Firma bulunamadı",
        },
        manual_parameters=[
            openapi.Parameter(
                "slug",
                openapi.IN_PATH,
                description="Firmanın benzersiz slug değeri",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
    )
    def get(self, request, slug):
        try:
            company = Companies.objects.get(slug=slug)
        except Companies.DoesNotExist:
            return Response({"error": "Firma bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        # Şirkete ait aktif randevular
        meetings = Meetings.objects.filter(company=company, status__in=[MeetingStatus.WAITING, MeetingStatus.ARRIVED])

        serializer = MeetingOccupiedSerializer(meetings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
