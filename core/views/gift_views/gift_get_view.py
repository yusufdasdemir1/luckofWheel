from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.serializers import GiftListSerializer
from core.models import Gifts

class GiftDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🎁 Tek bir hediyeyi getir (sadece admin)",
        tags=["GIFT"],
        operation_description="Admin kendi şirketine ait belirli bir hediyeyi detaylı görüntüleyebilir.",
        responses={
            200: openapi.Response(
                description="Hediye bulundu.",
                examples={
                    "application/json": {
                        "id": 3,
                        "title": "%20 İndirim",
                        "description": "Tüm hizmetlerde geçerli.",
                        "chance": 0.25,
                        "company": 4
                    }
                },
            ),
            403: openapi.Response(
                description="Yetkisiz işlem.",
                examples={"application/json": {"error": "Bu işlem sadece admin kullanıcılar içindir."}},
            ),
            404: openapi.Response(
                description="Hediye bulunamadı.",
                examples={"application/json": {"error": "Bu ID'ye ait hediye bulunamadı veya size ait değil."}},
            ),
        },
    )
    def get(self, request, gift_id):
        user = request.user

        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            gift = Gifts.objects.get(id=gift_id, company=user.company)
        except Gifts.DoesNotExist:
            return Response(
                {"error": "Bu ID'ye ait hediye bulunamadı veya size ait değil."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GiftListSerializer(gift)
        return Response(serializer.data, status=status.HTTP_200_OK)
