from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.models import Services
from core.serializers import ServiceListSerializer


class ServiceListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="💈 Hizmetleri listele (is_active filtreli, sadece admin)",
        operation_description=(
            "Admin kendi şirketine ait hizmetleri listeler.\n\n"
            "🔹 `is_active=true` → sadece aktif hizmetler\n"
            "🔹 `is_active=false` → sadece pasif hizmetler\n"
            "🔹 parametre olmadan → tüm hizmetler"
        ),
        manual_parameters=[
            openapi.Parameter(
                "is_active",
                openapi.IN_QUERY,
                description="Aktiflik durumuna göre filtreleme (true/false)",
                type=openapi.TYPE_BOOLEAN,
                required=False,
                example=True,
            ),
        ],
        responses={200: ServiceListSerializer(many=True)},
        tags=["SERVICES"]
    )
    def get(self, request):
        user = request.user

        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        is_active_param = request.query_params.get("is_active")

        queryset=Services.objects.filter(company=user.company)

        if is_active_param is not None:
            if is_active_param.lower() == "true":
                queryset = queryset.filter(is_active=True)
            elif is_active_param.lower() == "false":
                queryset = queryset.filter(is_active=False)

        if not queryset.exists():
            return Response(
                {"message": "Belirtilen filtreye uygun hizmet bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ServiceListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)