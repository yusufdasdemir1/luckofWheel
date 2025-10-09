from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.models import Gifts
from core.serializers import GiftUpdateSerializer


class GiftUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🎁 Hediye düzenle (sadece admin)",
        tags=["gift"],
        operation_description=(
            "Admin, kendi şirketine ait bir hediyenin başlık, açıklama veya oranını güncelleyebilir.\n\n"
            "- Sadece `title`, `description` ve `chance` alanları düzenlenebilir.\n"
            "- Güncelleme işlemi `PATCH` metodu ile yapılır."
        ),
        request_body=GiftUpdateSerializer,
        manual_parameters=[
            openapi.Parameter(
                "gift_id",
                openapi.IN_PATH,
                description="Düzenlenecek hediyenin ID’si",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Hediye başarıyla güncellendi.",
                examples={
                    "application/json": {
                        "message": "Hediye başarıyla güncellendi.",
                        "gift": {
                            "id": 3,
                            "title": "Yeni %20 İndirim",
                            "description": "Sadece bu hafta geçerli",
                            "chance": 0.25,
                        },
                    }
                },
            ),
            403: openapi.Response(
                description="Yetkisiz işlem.",
                examples={
                    "application/json": {"error": "Bu işlem sadece admin kullanıcılar içindir."}
                },
            ),
            404: openapi.Response(
                description="Hediye bulunamadı.",
                examples={
                    "application/json": {"error": "Bu ID'ye ait hediye bulunamadı veya size ait değil."}
                },
            ),
        },
    )
    def patch(self, request, gift_id):
        user = request.user

        # 🧱 Sadece admin erişebilir
        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 🎯 Kendi şirketine ait hediye olmalı
        try:
            gift = Gifts.objects.get(id=gift_id, company=user.company)
        except Gifts.DoesNotExist:
            return Response(
                {"error": "Bu ID'ye ait hediye bulunamadı veya size ait değil."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 🔧 Serializer doğrulama ve güncelleme
        serializer = GiftUpdateSerializer(gift, data=request.data, partial=True,context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Hediye başarıyla güncellendi.",
                "gift": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
