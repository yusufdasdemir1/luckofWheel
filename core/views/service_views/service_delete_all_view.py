from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.models import Services


class ServiceDeleteAllView(APIView):
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
    def delete(self, request):
        user=request.user

        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            services = Services.objects.filter(company=user.company)
        except Services.DoesNotExist:
            return Response(
                {"error": f"Bu şirkete ait hizmet bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        deleted_count = services.count()
        deleted_titles = list(services.values_list("title", flat=True))

        services.delete()

        return Response(
            {
                "message": f"{deleted_count} hizmet başarıyla silindi.",
                "deleted_services": deleted_titles
            },
            status=status.HTTP_200_OK
        )
