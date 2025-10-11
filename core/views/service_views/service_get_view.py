from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from core.models import Services
from core.serializers import ServiceListSerializer


class ServiceDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🔍 Tek hizmet detayını görüntüle",
        responses={200: ServiceListSerializer()},
        tags=["SERVICES"]
    )
    def get(self, request, service_id):
        user = request.user
        try:
            service = Services.objects.get(id=service_id, company=user.company)
        except Services.DoesNotExist:
            return Response(
                {"error": "Hizmet bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ServiceListSerializer(service)
        return Response(serializer.data, status=status.HTTP_200_OK)
