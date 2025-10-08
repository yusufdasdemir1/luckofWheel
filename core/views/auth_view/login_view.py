from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from core.serializers import LoginSerializer
from core.models import Users


class LoginView(APIView):
    @swagger_auto_schema(
        operation_summary="Admin login (JWT token döner)",
        request_body=LoginSerializer,
        responses={
            200: "Giriş başarılı",
            401: "Geçersiz kimlik bilgileri veya yetkisiz kullanıcı"
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return Response(
                {"error": "Bu e-posta adresine ait kullanıcı bulunamadı."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 🔐 Şifre kontrolü: check_password() artık model metodundan yapılır
        if not user.check_password(password):
            return Response(
                {"error": "E-posta veya şifre hatalı."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 🔐 Sadece admin kullanıcılar giriş yapabilir
        if not user.is_admin:
            return Response(
                {"error": "Bu işlem sadece admin kullanıcılar içindir."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 🔑 Token üretimi
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Giriş başarılı.",
            "user": {
                "id": user.id,
                "name": user.name,
                "surname": user.surname,
                "email": user.email,
                "is_admin": user.is_admin,
                "company": user.company.title if user.company else None,
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
