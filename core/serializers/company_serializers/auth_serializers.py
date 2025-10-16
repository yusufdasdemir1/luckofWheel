from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

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