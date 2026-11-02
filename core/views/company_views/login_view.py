from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from core.serializers.company_serializers.auth_serializers import LoginSerializer
from core.models import Companies, Users

INACTIVE_COMPANY_MESSAGE = (
    "Firmanız ödeme yapılmadığı için pasif durumdadır."
    " Hesabınızı yeniden aktif etmek için lütfen cevirkazan360@gmail.com adresine e-posta gönderin."
)


def _token_response(user, email, role):
    refresh = RefreshToken.for_user(user)
    return Response({
        "message": "Giriş başarılı.",
        "user": {
            "id": user.id,
            "name": user.name,
            "surname": user.surname,
            "email": email,
            "is_admin": user.is_admin,
            "role": role,
            "company": user.company.title if user.company else None,
        },
        "tokens": {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
    }, status=status.HTTP_200_OK)


class LoginView(APIView):
    @swagger_auto_schema(
        operation_summary="Panel girişi: firma sahibi (firma e-postası) veya çalışan (kendi e-postası) — JWT token döner",
        tags=["ADMIN AUTHENTICATION"],
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

        email = serializer.validated_data.get("email").strip().lower()
        password = serializer.validated_data.get("password")

        # 1) Firma sahibi: firma e-postası + şifre
        company = Companies.objects.filter(email=email).first()
        if company:
            return self._owner_login(company, password)

        # 2) Çalışan (kuaför): kendi e-postası + şifre
        staff_user = (
            Users.objects.filter(email__iexact=email, staff_profile__isnull=False)
            .select_related("company", "staff_profile")
            .first()
        )
        if staff_user:
            return self._staff_login(staff_user, email, password)

        return Response(
            {"error": "E-posta veya şifre hatalı."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    def _owner_login(self, company, password):
        if company.status != 'active':
            return Response(
                {"error": INACTIVE_COMPANY_MESSAGE},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            user = Users.objects.get(company=company, is_admin=True)
        except Users.DoesNotExist:
            return Response(
                {"error": "Bu firmaya ait admin kullanıcısı bulunamadı."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 🔐 Şifre kontrolü
        if not user.check_password(password):
            return Response(
                {"error": "E-posta veya şifre hatalı."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return _token_response(user, company.email, "owner")

    def _staff_login(self, user, email, password):
        if not user.check_password(password):
            return Response(
                {"error": "E-posta veya şifre hatalı."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if user.company.status != 'active':
            return Response(
                {"error": INACTIVE_COMPANY_MESSAGE},
                status=status.HTTP_403_FORBIDDEN
            )

        if not user.staff_profile.is_active:
            return Response(
                {"error": "Hesabınız pasif durumdadır. Lütfen salon yöneticinizle görüşün."},
                status=status.HTTP_403_FORBIDDEN
            )

        return _token_response(user, user.email, "staff")
