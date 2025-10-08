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
            "**chance:** 0-1 arası oran (%25 için 0.25 yazılır)"
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
                            "company": "Yusuf's Kuaför"
                        }
                    }
                },
            ),
            400: openapi.Response(
                description="Eksik veya geçersiz veri gönderildi.",
                examples={"application/json": {"error": "chance 0 ile 1 arasında olmalı."}},
            ),
            403: openapi.Response(
                description="Yalnızca admin kullanıcılar hediye oluşturabilir.",
                examples={"application/json": {"error": "Bu işlem sadece admin kullanıcılar içindir."}},
            ),
        },
    )
    def post(self, request):
        user = request.user

        # 🔐 Kullanıcı admin mi?
        if not getattr(user, "is_admin", False):
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 🏢 Kullanıcının firması var mı kontrol et
        if not user.company:
            return Response(
                {"error": "Kullanıcının bağlı olduğu bir firma bulunamadı."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🧾 Veri doğrulama
        serializer = GiftSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        chance = serializer.validated_data.get("chance")
        if not (0 <= chance <= 1):
            return Response(
                {"error": "chance 0 ile 1 arasında olmalı."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🎁 Hediye oluştur
        gift = Gifts.objects.create(
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
            chance=chance,
            company=user.company
        )

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
