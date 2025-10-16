from rest_framework import serializers
from core.models import Services


class ServiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = ["id","title", "description", "duration", "price","is_active"]


class ServiceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = ["title", "description", "duration", "price", "is_active"]
        extra_kwargs = {
            "title": {"required": False},
            "description": {"required": False},
            "duration": {"required": False},
            "price": {"required": False},
            "is_active": {"required": False},
        }


class ServiceDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = ["id", "title", "description", "duration", "price", "is_active"]