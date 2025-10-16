from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.models import Services
from core.serializers.service_serializers.service_serializers import ServiceDeleteSerializer


class ServiceDeleteAllView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🗑️ Tüm hizmetleri sil (sadece admin)",
        operation_description="Admin kendi şirketine ait tüm hizmetleri tamamen siler.",
        responses={
            200: ServiceDeleteSerializer(many=True),
            403: "Yetkisiz kullanıcı.",
            404: "Hizmet bulunamadı."
        },
        tags=["SERVICES"]
    )
    def delete(self, request):
        user = request.user

        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        services = Services.objects.filter(company=user.company)

        if not services.exists():
            return Response(
                {"error": "Bu şirkete ait hiçbir hizmet bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🧾 Silinmeden önce serialize et
        serializer = ServiceDeleteSerializer(services, many=True)
        deleted_data = serializer.data
        deleted_count = len(deleted_data)


        services.delete()

        return Response(
            {
                "message": f"{deleted_count} hizmet başarıyla silindi.",
                "deleted_services": deleted_data
            },
            status=status.HTTP_200_OK
        )
