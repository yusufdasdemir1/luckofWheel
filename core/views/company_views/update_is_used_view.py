from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.models import EarnedWins
from core.serializers import EarnedWinStatusSerializer


class EarnedWinStatusUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🎁 Ödül kullanım durumunu güncelle (sadece admin)",
        tags=["Admin Actions"],
        operation_description=(
            "Admin, kendi şirketine ait bir ödül kaydının `is_used` durumunu değiştirebilir.\n"
            "Yalnızca `is_used` (True/False) alanı güncellenir."
        ),
        request_body=EarnedWinStatusSerializer,
        responses={
            200: openapi.Response(
                description="Durum başarıyla güncellendi.",
                examples={
                    "application/json": {
                        "message": "Ödül durumu güncellendi.",
                        "earned_win_id": 12,
                        "is_used": True
                    }
                }
            ),
            403: "Yetkisiz erişim",
            404: "Kayıt bulunamadı"
        }
    )
    def patch(self, request, earned_win_id):
        user = request.user

        # 🔒 Sadece adminler erişebilir
        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 🎯 Güncellenecek kayıt: sadece kendi şirketine ait olmalı
        try:
            earned_win = EarnedWins.objects.get(id=earned_win_id, company=user.company)
        except EarnedWins.DoesNotExist:
            return Response(
                {"error": "Bu ödül kaydı bulunamadı veya size ait değil."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🧾 Veriyi doğrula
        serializer = EarnedWinStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ⚙️ Güncelle
        earned_win.is_used = serializer.validated_data["is_used"]
        earned_win.save()

        return Response(
            {
                "message": "Ödül durumu güncellendi.",
                "earned_win_id": earned_win.id,
                "is_used": earned_win.is_used
            },
            status=status.HTTP_200_OK
        )
