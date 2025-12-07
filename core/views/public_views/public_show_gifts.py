from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from core.models import Companies, Gifts
from core.serializers.public_serializers.public_serializers import GiftPublicListSerializer


class PublicGiftView(APIView):
    @swagger_auto_schema(
        operation_summary="🎁 Çarkta gösterilecek aktif hediyeleri listele (public)",
        operation_description=(
            "Firma slug'ına göre, çarkta yer alacak **aktif** hediyeleri döner.\n\n"
            "Bu endpoint herkese açıktır, giriş gerekmez."
        ),
        tags=["PUBLIC"],
        responses={
            200: "Aktif hediyeler başarıyla listelendi.",
            404: "Firma veya aktif hediye bulunamadı."
        },
    )
    def get(self, request, slug):
        try:
            company = Companies.objects.get(slug=slug)
        except Companies.DoesNotExist:
            return Response(
                {"error": "Firma bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        gifts = Gifts.objects.filter(company=company, is_active=True)

        if not gifts.exists():
            return Response(
                {"message": "Bu firmaya ait aktif hediye bulunmamaktadır."},
                status=status.HTTP_200_OK
            )

        serializer = GiftPublicListSerializer(gifts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
