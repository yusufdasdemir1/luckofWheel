from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.models import Services
from core.serializers import ServiceListSerializer


class ServiceFilterView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="💈 Hizmetleri filtrele/sırala (fiyat, süre, aktiflik, sadece admin)",
        operation_description=(
                "Admin kendi şirketine ait hizmetleri filtreleyip sıralar.\n\n"
                "Kullanılabilir parametreler:\n"
                "🔹 `min_price`, `max_price` → Fiyat aralığı\n"
                "🔹 `min_duration`, `max_duration` → Süre aralığı (dakika)\n"
                "🔹 `is_active` → true / false (aktiflik durumu)\n"
                "🔹 `order` → asc / desc (süreye göre sıralama)\n\n"
                "Parametrelerin hiçbiri zorunlu değildir — hepsi birlikte veya ayrı ayrı kullanılabilir."
        ),
        manual_parameters=[
            openapi.Parameter("min_price", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, description="Minimum fiyat"),
            openapi.Parameter("max_price", openapi.IN_QUERY, type=openapi.TYPE_NUMBER, description="Maksimum fiyat"),
            openapi.Parameter("min_duration", openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description="Minimum süre (dk)"),
            openapi.Parameter("max_duration", openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description="Maksimum süre (dk)"),
            openapi.Parameter("is_active", openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN,
                              description="Aktiflik durumu (true / false)"),
            openapi.Parameter("order", openapi.IN_QUERY, type=openapi.TYPE_STRING,
                              description="Sıralama yönü duration(asc / desc)"),
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

        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        min_duration = request.query_params.get("min_duration")
        max_duration = request.query_params.get("max_duration")
        is_active = request.query_params.get("is_active")
        order = request.query_params.get("order")

        queryset = Services.objects.filter(company=user.company)

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        if min_duration:
            queryset = queryset.filter(duration__gte=min_duration)
        if max_duration:
            queryset = queryset.filter(duration__lte=max_duration)

        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(is_active=False)

        if order == "desc":
            queryset = queryset.order_by("-duration")
        else:
            queryset = queryset.order_by("duration")

        if not queryset.exists():
            return Response(
                {"message": "Belirtilen filtrelere uygun hizmet bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ServiceListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)