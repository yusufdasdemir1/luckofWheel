from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.serializers.gift_serializers.gift_serializers import GiftListSerializer
from core.models import Gifts


class GiftListView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🎁 Firma hediyelerini listele (sadece admin)",
        tags=["GIFT"],
        operation_description=(
            "Admin kendi şirketine ait tüm hediyeleri görüntüler.\n\n"
            "- JWT token gereklidir.\n"
            "- Sadece admin kullanıcılar erişebilir.\n"
            "- Eğer hediye tanımlı değilse bilgi mesajı döner."
        ),
        responses={
            200: openapi.Response(
                description="Hediyeler başarıyla listelendi.",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "title": "%10 İndirim",
                            "description": "Tüm hizmetlerde geçerli.",
                            "chance": 0.3,
                            "company": 4,
                            "company_name": "Yusuf Hair Studio"
                        },
                        {
                            "id": 2,
                            "title": "Ücretsiz Saç Bakımı",
                            "description": "Sadece yeni müşteriler için.",
                            "chance": 0.1,
                            "company": 4,
                            "company_name": "Yusuf Hair Studio"
                        }
                    ]
                },
            ),
            403: openapi.Response(
                description="Yetkisiz işlem.",
                examples={
                    "application/json": {"error": "Bu işlem sadece admin kullanıcılar içindir."}
                },
            ),
            200: openapi.Response(
                description="Hediye bulunamadı.",
                examples={
                    "application/json": {"message": "Sisteminize ait herhangi bir hediye bulunamadı."}
                },
            ),
        },
    )
    def get(self,request):
        user = request.user

        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        gift_list=Gifts.objects.filter(company=user.company).select_related("company")

        if not gift_list.exists():
            return Response(
                {"message":"Sisteminize ait herhangi bir hediye bulunamadı."},
                status=status.HTTP_200_OK
            )

        serializer = GiftListSerializer(gift_list, many=True)

        return Response(serializer.data,status=status.HTTP_200_OK)