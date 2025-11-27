from rest_framework import serializers
from core.models import  Meetings


class MeetingListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    user_surname = serializers.CharField(source="user.surname", read_only=True)
    user_phone = serializers.CharField(source="user.phone", read_only=True)
    class Meta:
        model=Meetings
        fields=["id","user_name","user_surname","user_phone","date","time","end_time","is_active","service_title","service_price"]


class MeetingUpdateSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)
    date = serializers.DateField(required=False)
    time = serializers.TimeField(required=False)
    service_title = serializers.CharField(required=False, max_length=255)


class MeetingCancelSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=True)


class MeetingDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model=Meetings
        fields=["user","date","time","end_time","is_active","service_title","service_price"]
