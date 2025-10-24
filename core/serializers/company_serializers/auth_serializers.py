from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.models import Users,Companies

class RegisterSerializer(serializers.Serializer):
    # USER fields
    name = serializers.CharField(max_length=255,required=True)
    surname = serializers.CharField(max_length=255,required=True)
    password = serializers.CharField(write_only=True,required=True)

    # COMPANY fields
    company_title = serializers.CharField(max_length=255,required=True)
    company_description = serializers.CharField(required=False, allow_blank=True)
    company_email = serializers.EmailField(required=True)
    company_phone = serializers.CharField(required=True)
    show_before_meeting = serializers.BooleanField(default=False)
    is_show_wheel = serializers.BooleanField(default=True)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        if not user.is_admin:
            raise ValueError("Bu işlem sadece admin kullanıcılar içindir.")
        token = super().get_token(user)
        return token


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        required=True,
        help_text="Geçerli refresh token (JWT logout için zorunludur)"
    )


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Companies
        fields = ["id", "title", "description", "phone", "email", "slug", "logo", "thumbnail"]


class UserSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)  # 🔹 company bilgilerini iç içe dahil ediyoruz

    class Meta:
        model = Users
        fields = ["id", "name", "surname","company"]