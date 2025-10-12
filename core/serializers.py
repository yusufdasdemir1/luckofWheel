from rest_framework import serializers

from core.models import Users, Gifts, EarnedWins, Services
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
    is_show_wheel = serializers.BooleanField(default=True)


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

class EarnedWinsSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    user_surname = serializers.CharField(source="user.surname", read_only=True)
    gift_title = serializers.CharField(source="gift.title", read_only=True)

    class Meta:
        model = EarnedWins
        fields = ["id", "user_name", "user_surname", "gift_title", "is_used", "created_at"]


class CompanyUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    show_before_meeting = serializers.BooleanField(required=False)
    is_show_wheel = serializers.BooleanField(required=False)
    spin_cooldown_hours=serializers.IntegerField(required=False,min_value=1)


class EarnedWinStatusSerializer(serializers.Serializer):
    is_used = serializers.BooleanField(required=True, help_text="Ödül kullanıldı mı (true/false)")


class GiftListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.title", read_only=True)

    class Meta:
        model = Gifts
        fields = ["id", "title", "description", "chance", "company_name","is_active"]


class GiftDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gifts
        fields = ["title", "chance"]


class GiftUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gifts
        fields = ["title", "description", "chance","is_active"]
        extra_kwargs = {
            "title": {"required": False},
            "description": {"required": False},
            "chance": {"required": False},
            "is_active":{"required": False},
        }

    def validate(self, data):
        """Toplam chance 1.0'ı geçemez."""
        instance = self.instance  # mevcut hediye
        user = self.context["request"].user
        company = getattr(user, "company", None)

        # Eğer chance güncellenmiyorsa kontrol gerekmez
        if "chance" not in data or not company:
            return data

        new_chance = data["chance"]

        # Şirketin diğer hediyelerinin toplamını al (bu hediyeyi hariç tut)
        total_chance = (
            Gifts.objects.filter(company=company)
            .exclude(id=instance.id)
            .aggregate(total=Sum("chance"))["total"]
            or 0
        )

        # Yeni total hesapla
        updated_total = total_chance + new_chance

        if updated_total > 1.0:
            raise serializers.ValidationError(
                f"Toplam olasılık 1'i geçemez. (Şu anki toplam: {round(updated_total, 2)})"
            )

        return data


class ServiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields=["title", "description", "duration", "price"]


class ServiceListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.title", read_only=True)

    class Meta:
        model = Services
        fields = ["title", "description", "duration", "price","is_active","company_name"]


class PublicServiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = ["title", "description", "duration", "price"]


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
