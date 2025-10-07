from rest_framework import serializers


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


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)