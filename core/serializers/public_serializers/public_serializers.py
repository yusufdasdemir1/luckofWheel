from rest_framework import serializers

from core.models import Users, Services, Gifts


class PublicRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ('name', 'surname', 'email','phone')


class PublicServiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = ["title", "description", "duration", "price"]


class PublicMeetingCreateSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, help_text="Kayıtlı telefon numarası")
    service_title = serializers.CharField(max_length=255)
    date = serializers.DateField()
    time = serializers.TimeField()


class GiftPublicListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gifts
        fields = ["title"]
