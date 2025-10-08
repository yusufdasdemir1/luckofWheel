from rest_framework import serializers

from core.models import Users,Gifts
from django.db.models import Sum

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


class PublicRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ('name', 'surname', 'email','phone')


class GiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gifts
        fields = ["id", "title", "description", "chance", "company"]
        read_only_fields = ["company"]

    def validate(self, data):
        """Toplam chance hiçbir zaman 1'i geçemez."""
        request = self.context.get("request")
        user = getattr(request, "user", None)
        company = getattr(user, "company", None)

        if company:
            total_chance = (
                Gifts.objects.filter(company=company)
                .aggregate(total=Sum("chance"))["total"]
                or 0
            )

            new_total = total_chance + data.get("chance", 0)

            # 1.0'dan büyük olamaz
            if new_total > 1.0:
                raise serializers.ValidationError(
                    f"Toplam olasılık 1'i geçemez (şu an: {round(new_total, 2)})."
                )

        return data