from rest_framework import serializers
from core.models import  Meetings,EarnedWins
from core.models import MeetingStatus
from core.serializers.company_serializers.company_serializers import EarnedWinSerializer


class MeetingListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    user_surname = serializers.CharField(source="user.surname", read_only=True)
    user_phone = serializers.CharField(source="user.phone", read_only=True)
    unused_gifts = serializers.SerializerMethodField()

    class Meta:
        model=Meetings
        fields=["id","user_name","user_surname","user_phone",
                "date","time","end_time","status","note",
                "service_title","service_price","unused_gifts"]


    def get_unused_gifts(self, obj):
        wins = EarnedWins.objects.filter(
            user=obj.user,
            company=obj.company,
            is_used=False
        )

        return EarnedWinSerializer(wins, many=True).data

class MeetingUpdateSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)
    date = serializers.DateField(required=False)
    time = serializers.TimeField(required=False)
    service_title = serializers.CharField(required=False, max_length=255)


class MeetingCancelSerializer(serializers.Serializer):
    status=serializers.ChoiceField(
        choices=MeetingStatus.values,
        required=True,
    )


class MeetingDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model=Meetings
        fields=["user","date","time","end_time","status","service_title","service_price"]
