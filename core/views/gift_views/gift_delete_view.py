from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.models import Gifts
from core.serializers import GiftDeleteSerializer

class GiftDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🎁 Hediye sil (sadece admin)",
        tags=["gift"],
        operation_description=(
            "Admin kendi şirketine ait bir hediyeyi silebilir.\n\n"
            "Yalnızca `company` ile ilişkili hediyeler silinebilir."
        ),
        manual_parameters=[
            openapi.Parameter(
                "gift_id",
                openapi.IN_PATH,
                description="Silinecek hediye ID'si",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Silme işlemi başarılı",
                examples={
                    "application/json": {"message": "Hediye başarıyla silindi."}
                },
            ),
            403: openapi.Response(
                description="Yetkisiz işlem",
                examples={
                    "application/json": {"error": "Bu işlem sadece admin kullanıcılar içindir."}
                },
            ),
            404: openapi.Response(
                description="Hediye bulunamadı",
                examples={
                    "application/json": {"error": "Bu ID'ye ait hediye bulunamadı."}
                },
            ),
        },
    )
    def delete(self, request, gift_id):
        user = request.user

        # 🧱 Sadece adminler erişebilir
        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            gift=Gifts.objects.get(id=gift_id,company=user.company)

        except Gifts.DoesNotExist:
            return Response(
                {"error": "Bu ID'ye ait hediye bulunamadı veya size ait değil."},
                status=status.HTTP_404_NOT_FOUND,
            )

        gift.delete()

        #silinen hediyenin serializer edilmiş hali
        serializer=GiftDeleteSerializer(gift)

        return Response(
            {"message": "Hediye başarıyla silindi.",
                    "deleted_gift":serializer.data
             },
            status=status.HTTP_200_OK,
        )