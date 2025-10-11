from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.models import Services
from core.serializers import ServiceUpdateSerializer


class ServiceUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="✏️ Hizmet güncelle (sadece admin)",
        operation_description=(
            "Admin kendi şirketine ait bir hizmeti günceller.\n\n"
            "Gönderilmeyen alanlar değiştirilmez.\n\n"
            "Örnek: sadece `price` veya sadece `is_active` gönderilebilir."
        ),
        request_body=ServiceUpdateSerializer,
        responses={
            200: "Hizmet başarıyla güncellendi.",
            403: "Yetkisiz kullanıcı",
            404: "Hizmet bulunamadı"
        },
        tags=["SERVICES"]
    )
    def patch(self, request, service_id):
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
                {"error": "Bu ID'ye sahip bir hizmet bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ServiceUpdateSerializer(service, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # 🎯 Chance kontrolü gerekmez (burada probability yok)
        serializer.save()

        return Response(
            {
                "message": "Hizmet başarıyla güncellendi.",
                "service": serializer.data
            },
            status=status.HTTP_200_OK
        )
