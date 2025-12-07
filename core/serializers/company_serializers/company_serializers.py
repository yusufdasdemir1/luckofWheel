from rest_framework import serializers
from core.models import EarnedWins,Companies
from core.exceptions import SimpleError

class EarnedWinsSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    user_surname = serializers.CharField(source="user.surname", read_only=True)
    class Meta:
        model = EarnedWins
        fields = ["id","user_name","user_surname","gift_title","is_used", "created_at"]


class EarnedWinStatusSerializer(serializers.Serializer):
    is_used = serializers.BooleanField(required=True, help_text="Ödül kullanıldı mı (true/false)")


class CompanyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model=Companies
        exclude=["slug","created_at","updated_at","status"]

    allowed_extensions = ["png", "jpg", "jpeg", "webp"]

    def validate(self, attrs):

        logo = attrs.get("logo")
        if logo:
            ext = logo.split(".")[-1].lower()
            if ext not in self.allowed_extensions:
                raise SimpleError(f"Logo için izin verilen uzantılar: {', '.join(self.allowed_extensions)}")

        thumbnail = attrs.get("thumbnail")
        if thumbnail:
            ext = thumbnail.split(".")[-1].lower()
            if ext not in self.allowed_extensions:
                raise SimpleError(f"Thumbnail için izin verilen uzantılar: {', '.join(self.allowed_extensions)}")

        return attrs


class CompanyResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Companies
        exclude = ["slug", "created_at", "updated_at", "status"]