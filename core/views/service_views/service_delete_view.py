from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.models import Services


class ServiceDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🗑️ Hizmet sil (sadece admin)",
        operation_description="Admin kendi şirketine ait bir hizmeti tamamen siler.",
        responses={
            200: "Hizmet başarıyla silindi.",
            403: "Yetkisiz kullanıcı.",
            404: "Hizmet bulunamadı."
        },
        tags=["SERVICES"]
    )
    def delete(self, request, service_id):
        user=request.user

        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            service = Services.objects.get(id=service_id,company=user.company)
        except Services.DoesNotExist:
            return Response(
                {"error": f"Bu şirketin {service_id} ID'ye sahip bir hizmeti bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        service.delete()

        return Response(
            {"message": f"{service.title} adlı hizmet başarıyla silindi."},
            status=status.HTTP_200_OK
        )
