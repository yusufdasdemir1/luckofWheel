from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.models import Gifts
from core.serializers import GiftSerializer


class GiftCreateView(APIView):
    """
    Admin kullanıcı kendi firmasına hediye ekleyebilir.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Yeni hediye oluştur (sadece admin kullanıcılar)",
        operation_description=(
            "JWT ile giriş yapmış admin kullanıcının firmasına yeni bir ödül ekler.\n\n"
            "**chance:** 0-1 arası oran (%25 için 0.25 yazılır). "
            "Toplam oran hiçbir zaman 1.0'ı geçemez."
        ),
        request_body=GiftSerializer,
        responses={
            201: openapi.Response(
                description="Hediye başarıyla oluşturuldu.",
                examples={
                    "application/json": {
                        "message": "Hediye oluşturuldu.",
                        "gift": {
                            "id": 5,
                            "title": "%10 indirim",
                            "description": "Sonraki hizmette geçerli",
                            "chance": 0.2,
                            "company": "Beauty of Yusuf"
                        }
                    }
                },
            ),
            400: openapi.Response(
                description="Eksik veya geçersiz veri gönderildi.",
                examples={"application/json": {"error": "Toplam olasılık 1'i geçemez (şu an: 1.05)."}},
            ),
            403: openapi.Response(
                description="Yalnızca admin kullanıcılar hediye oluşturabilir.",
                examples={"application/json": {"error": "Bu işlem sadece admin kullanıcılar içindir."}},
            ),
        },
    )
    def post(self, request):
        user = request.user

        # 👮 Sadece admin kullanıcılar
        if not getattr(user, "is_admin", False):
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 🏢 Firma kontrolü
        if not user.company:
            return Response(
                {"error": "Kullanıcının bağlı olduğu bir firma bulunamadı."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🧾 Serializer (context ile!)
        serializer = GiftSerializer(data=request.data, context={"request": request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 🎁 Hediye oluştur
        gift = serializer.save(company=user.company)

        return Response({
            "message": "Hediye oluşturuldu.",
            "gift": {
                "id": gift.id,
                "title": gift.title,
                "description": gift.description,
                "chance": gift.chance,
                "company": gift.company.title,
            }
        }, status=status.HTTP_201_CREATED)
