from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.serializers.service_serializers.service_serializers import ServiceListSerializer


class ServiceCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="💈 Yeni hizmet oluştur (sadece admin)",
        operation_description="Admin kendi şirketine ait yeni bir hizmet ekler.",
        request_body=ServiceListSerializer,
        responses={
            201: "Hizmet başarıyla oluşturuldu.",
            403: "Yalnızca admin kullanıcılar işlem yapabilir.",
        },
        tags=["SERVICES"]
    )
    def post(self, request):
        user=request.user
        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ServiceListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(company=user.company)

        return Response(
            {
                "message": "Hizmet başarıyla oluşturuldu.",
                "service": serializer.data
            },
            status=status.HTTP_201_CREATED
        )