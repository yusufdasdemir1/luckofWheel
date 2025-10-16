from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.models import Services
from core.serializers.service_serializers.service_serializers import ServiceDeleteSerializer


class ServiceDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🗑️ Hizmet sil (sadece admin)",
        operation_description="Admin kendi şirketine ait bir hizmeti tamamen siler.",
        responses={
            200: ServiceDeleteSerializer,
            403: "Yetkisiz kullanıcı.",
            404: "Hizmet bulunamadı."
        },
        tags=["SERVICES"]
    )
    def delete(self, request, service_id):
        user = request.user

        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            service = Services.objects.get(id=service_id, company=user.company)
        except Services.DoesNotExist:
            return Response(
                {"error": f"Bu şirketin {service_id} ID'ye sahip bir hizmeti bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🧾 Serialize etmeden önce bilgileri al
        serializer = ServiceDeleteSerializer(service)
        deleted_data = serializer.data

        # 🗑️ Sil
        service.delete()

        return Response(
            {
                "message": f"{deleted_data['title']} adlı hizmet başarıyla silindi.",
                "deleted_service": deleted_data
            },
            status=status.HTTP_200_OK
        )
