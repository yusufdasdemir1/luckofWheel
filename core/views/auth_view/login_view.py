from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from core.serializers import LoginSerializer
from core.models import Users


class LoginView(APIView):
    @swagger_auto_schema(
        operation_summary="Admin login (JWT token döner)",
        request_body=LoginSerializer,
        responses={200: "Giriş başarılı", 401: "Geçersiz kimlik bilgileri"},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        try:
            user = Users.objects.get(email=email, is_admin=True)
        except Users.DoesNotExist:
            return Response(
                {"error": "bu maile ait kullanıcı bulunamadı."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not check_password(password, user.password):
            return Response(
                {"error": "E-posta veya şifre hatalı."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Giriş başarılı.",
            "user": {
                "id": user.id,
                "name": user.name,
                "surname": user.surname,
                "email": user.email,
                "is_admin": user.is_admin,
                "company": user.company.title,
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
