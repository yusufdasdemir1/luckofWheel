from rest_framework import serializers
from core.models import EarnedWins


class EarnedWinsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EarnedWins
        fields = ["id","user","gift_title","is_used", "created_at"]


class EarnedWinStatusSerializer(serializers.Serializer):
    is_used = serializers.BooleanField(required=True, help_text="Ödül kullanıldı mı (true/false)")


class CompanyUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    show_before_meeting = serializers.BooleanField(required=False)
    is_show_wheel = serializers.BooleanField(required=False)
    spin_cooldown_hours=serializers.IntegerField(required=False,min_value=1)