from rest_framework import serializers
from core.models import Gifts
from django.db.models import Sum


class GiftCreateSerializer(serializers.ModelSerializer):
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


class GiftListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gifts
        fields = ["id", "title", "description", "chance", "is_active","gift_color"]


class GiftDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gifts
        fields = ["title", "chance"]


class GiftUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gifts
        fields = ["title", "description", "chance","is_active","gift_color"]
        extra_kwargs = {
            "title": {"required": False},
            "description": {"required": False},
            "chance": {"required": False},
            "is_active":{"required": False},
            "gift_color": {"required": False}
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
