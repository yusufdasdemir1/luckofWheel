from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework import status
from core.models import Users
from core.serializers import AdminTokenObtainPairSerializer


class AdminTokenObtainPairView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            user = Users.objects.get(id=request.data.get("id"))
            if not user.is_admin:
                return Response(
                    {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Users.DoesNotExist:
            return Response(
                {"error": "Kullanıcı bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        return super().post(request, *args, **kwargs)