from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from core.serializers import LoginSerializer
from core.models import Companies,Users


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

        company_email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        try:
            company = Companies.objects.get(email=company_email)
        except Companies.DoesNotExist:
            return Response(
                {"error": "Bu e-posta adresine ait bir firma bulunamadı."},
                status=status.HTTP_401_UNAUTHORIZED
            )


        try:
            user = Users.objects.get(company=company, is_admin=True)
        except Users.DoesNotExist:
            return Response(
                {"error": "Bu firmaya ait admin kullanıcısı bulunamadı."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 🔐 3️⃣ Şifre kontrolü
        if not user.check_password(password):
            return Response(
                {"error": "E-posta veya şifre hatalı."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 🔑 Token üretimi
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Giriş başarılı.",
            "user": {
                "id": user.id,
                "name": user.name,
                "surname": user.surname,
                "email": company.email,
                "is_admin": user.is_admin,
                "company": user.company.title if user.company else None,
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
