from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.models import EarnedWins
from core.serializers import EarnedWinsSerializer
from drf_yasg.utils import swagger_auto_schema


class CompanySpinHistoryView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🏢 Şirkete ait tüm spin geçmişlerini listele (JWT gerektirir)",
        operation_description=(
                "Bu endpoint, giriş yapmış firma yöneticisinin şirketine ait tüm spin geçmişlerini döner.\n\n"
                "**Not:** Sadece `is_admin=True` kullanıcılar erişebilir.\n\n"
                "**Response**:\n"
                "- Firma adı\n"
                "- Toplam spin sayısı\n"
                "- Kullanıcı, hediye ve tarih bilgilerini içeren kayıt listesi"
        ))
    def get(self, request):
        user=request.user

        if not user.is_admin:
            return Response({"error": "Bu işlem için yetkiniz yok."},status=status.HTTP_403_FORBIDDEN)

        spins=EarnedWins.objects.filter(company=user.company).select_related("user","gift")
        data=EarnedWinsSerializer(spins,many=True).data

        return Response({
            "company": user.company.title,
            "total_spins": len(data),
            "spins": data
        }, status=status.HTTP_200_OK)




