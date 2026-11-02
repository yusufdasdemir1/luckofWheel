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
    wheel_mode = serializers.ChoiceField(choices=Companies.WHEEL_MODE_CHOICES, default=Companies.WHEEL_BEFORE)

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
    is_show_wheel = serializers.BooleanField(read_only=True)

    class Meta:
        model = Companies
        fields = ["id", "title", "description", "phone", "email", "slug","is_show_wheel","wheel_mode","spin_cooldown_hours",
                  "logo", "thumbnail","embed_address","address_text","status","city","district","instagram_url","youtube_url","facebook_url"]


class UserSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)  # 🔹 company bilgilerini iç içe dahil ediyoruz
    role = serializers.SerializerMethodField()
    staff_id = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ["id", "name", "surname", "email", "role", "staff_id", "company"]

    def get_role(self, obj):
        # owner: firma sahibi, staff: çalışan (kuaför), customer: müşteri
        if obj.is_admin:
            return "owner"
        if obj.is_company_staff:
            return "staff"
        return "customer"

    def get_staff_id(self, obj):
        return obj.staff_profile.id if obj.is_company_staff else None