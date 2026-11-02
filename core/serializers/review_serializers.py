from rest_framework import serializers

from core.models import Review, ReviewStatus
from core.services.review_service import display_name


class ReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(
        min_value=1,
        max_value=5,
        error_messages={
            "min_value": "Puan 1 ile 5 arasında olmalı.",
            "max_value": "Puan 1 ile 5 arasında olmalı.",
            "invalid": "Puan 1 ile 5 arasında olmalı.",
            "required": "Lütfen puan verin.",
        },
    )
    comment = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")

    def validate_comment(self, value):
        return value.strip()


class PublicReviewSerializer(serializers.ModelSerializer):
    """Salon sayfasında görünen onaylı yorum."""
    customer = serializers.SerializerMethodField()
    service_title = serializers.CharField(source="meeting.service_title", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "rating", "comment", "customer", "service_title", "reply", "replied_at", "created_at"]

    def get_customer(self, obj):
        return display_name(obj.meeting.user)


class PanelReviewSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    service_title = serializers.CharField(source="meeting.service_title", read_only=True)
    meeting_date = serializers.DateField(source="meeting.date", read_only=True)
    staff = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id", "rating", "comment", "status", "reply", "replied_at", "created_at",
            "customer", "service_title", "meeting_date", "staff",
        ]

    def get_customer(self, obj):
        user = obj.meeting.user
        return f"{user.name} {user.surname}".strip()

    def get_staff(self, obj):
        staff = obj.meeting.staff
        return f"{staff.user.name} {staff.user.surname}".strip() if staff else None


class ReviewUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ReviewStatus.choices, required=False)
    reply = serializers.CharField(max_length=1000, required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Güncellenecek alan gönderilmedi.")
        return attrs
