from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.models import Companies, Services
from core.serializers.public_serializers.public_serializers import PublicServiceListSerializer


class PublicServiceListView(APIView):
    @swagger_auto_schema(
        operation_summary="🌐 Public: Şirkete ait aktif hizmetleri listele",
        operation_description=(
            "Bu endpoint JWT gerektirmez. Ziyaretçi, firma slug’ı üzerinden "
            "aktif (is_active=True) hizmetleri görüntüleyebilir.\n\n"
            "**Örnek:** `/api/public/services/beauty-of-yusuf/`\n\n"
            "**Dönen bilgiler:**\n"
            "- Hizmet adı\n"
            "- Açıklama\n"
            "- Süre (dakika)\n"
            "- Fiyat\n"
            "- Aktiflik durumu"
        ),
        responses={
            200: openapi.Response(description="Aktif hizmet listesi başarıyla döndü."),
            404: openapi.Response(description="Firma bulunamadı."),
        },
        tags=["PUBLIC"]
    )
    def get(self, request, slug):
        try:
            company = Companies.objects.get(slug=slug)
        except Companies.DoesNotExist:
            return Response(
                {"error": "Firma bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔎 Aktif hizmetleri al
        services = Services.objects.filter(company=company, is_active=True)

        if not services.exists():
            return Response(
                {"message": "Bu firmaya ait aktif hizmet bulunamadı."},
                status=status.HTTP_200_OK
            )

        serializer = PublicServiceListSerializer(services, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
