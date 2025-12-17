from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.models import Users,Companies
import re


PHONE_RE = re.compile(r'^\+90\d{10}$')
class RegisterSerializer(serializers.Serializer):
    # USER fields
    name = serializers.CharField(max_length=255,required=True)
    surname = serializers.CharField(max_length=255,required=True)
    password = serializers.CharField(write_only=True,required=True)

    # COMPANY fields
    company_title = serializers.CharField(max_length=255,required=True)
    company_description = serializers.CharField(required=False, allow_blank=True)
    company_email = serializers.EmailField(required=True,
                                           error_messages={"invalid": "Geçerli bir email adresi giriniz."}
                                           )
    company_phone = serializers.CharField(required=True)
    show_before_meeting = serializers.BooleanField(default=False)
    is_show_wheel = serializers.BooleanField(default=True)

    def validate_company_phone(self, value):
        value = value.strip()
        if not PHONE_RE.match(value):
            raise serializers.ValidationError(
                "Telefon numarası +90XXXXXXXXXX formatında olmalıdır."
            )
        return value


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
        fields = ["id", "title", "description", "phone", "email", "slug","is_show_wheel","show_before_meeting","spin_cooldown_hours",
                  "logo", "thumbnail","embed_address","address_text","status","company_color","city","district","instagram_url","youtube_url","facebook_url"]


class UserSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)  # 🔹 company bilgilerini iç içe dahil ediyoruz

    class Meta:
        model = Users
        fields = ["id", "name", "surname","company"]