from rest_framework import serializers

from core.models import Users, Services, Gifts, Meetings


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


class MeetingOccupiedSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format="%Y-%m-%d")
    time = serializers.TimeField(format="%H:%M")
    end_time = serializers.TimeField(format="%H:%M")

    class Meta:
        model = Meetings
        fields = ["date", "time", "end_time"]