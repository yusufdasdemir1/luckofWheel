from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.serializers.company_serializers.auth_serializers import UserSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(tags=["ADMIN AUTHENTICATION"])
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)





