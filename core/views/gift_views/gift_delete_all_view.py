from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.models import Gifts


class GiftDeleteAllView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🗑️ Tüm hediyeleri sil (sadece admin)",
        tags=["GIFT"],
        operation_description=(
            "Admin, kendi şirketine ait **tüm hediye kayıtlarını** silebilir.\n\n"
            "- JWT doğrulaması gereklidir.\n"
            "- Sadece admin kullanıcılar erişebilir.\n"
            "- İşlem sadece adminin ait olduğu firmadaki hediyeleri etkiler."
        ),
        responses={
            200: openapi.Response(
                description="Tüm hediyeler silindi.",
                examples={
                    "application/json": {
                        "message": "Tüm hediyeler başarıyla silindi.",
                        "deleted_count": 5
                    }
                },
            ),
            403: openapi.Response(
                description="Yetkisiz işlem.",
                examples={
                    "application/json": {
                        "error": "Bu işlem sadece admin kullanıcılar içindir."
                    }
                },
            ),
            200: openapi.Response(
                description="Silinecek hediye yok.",
                examples={
                    "application/json": {
                        "message": "Sistemde silinecek hediye bulunamadı."
                    }
                },
            ),
        },
    )
    def delete(self, request):
        user = request.user

        # ❌ Sadece admin erişebilir
        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 🎯 Adminin şirketine ait hediyeleri getir
        gifts = Gifts.objects.filter(company=user.company)

        if not gifts.exists():
            return Response(
                {"message": "Sistemde silinecek hediye bulunamadı."},
                status=status.HTTP_200_OK,
            )

        # 🔥 Silme işlemi
        deleted_count = gifts.count()
        gifts.delete()

        return Response(
            {
                "message": "Tüm hediyeler başarıyla silindi.",
                "deleted_count": deleted_count,
            },
            status=status.HTTP_200_OK,
        )
