from rest_framework import serializers
import re
from core.models import Users, Services, Gifts, Meetings, Companies


PHONE_RE = re.compile(r'^\+90\d{10}$')

class PublicRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        error_messages={"invalid": "Geçerli bir email adresi giriniz."}
    )
    phone = serializers.CharField()

    class Meta:
        model = Users
        fields = ('name', 'surname', 'email', 'phone')

    def validate_email(self, value):
        value = value.strip().lower()
        domain = value.split("@")[-1]

        # internet maili kuralı
        if "." not in domain:
            raise serializers.ValidationError(
                "Email adresi geçerli bir alan adı içermelidir (ör: example.com)."
            )
        return value

    def validate_phone(self, value):
        value = value.strip()
        if not PHONE_RE.match(value):
            raise serializers.ValidationError(
                "Telefon numarası +90XXXXXXXXXX formatında olmalıdır."
            )
        return value


class PublicServiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = ["title", "description", "duration", "price"]


class PublicMeetingCreateSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, help_text="Kayıtlı telefon numarası")
    service_title = serializers.CharField(max_length=255)
    date = serializers.DateField()
    time = serializers.TimeField()
    note=serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Opsiyonel müşteri notu"
    )


class GiftPublicListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gifts
        fields = ["title","chance","gift_color"]


class MeetingOccupiedSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format="%Y-%m-%d")
    time = serializers.TimeField(format="%H:%M")
    end_time = serializers.TimeField(format="%H:%M")

    class Meta:
        model = Meetings
        fields = ["date", "time", "end_time"]


class ShowCompaniesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Companies
        fields=["title","description","phone","slug","city","district","logo"]


class PublicCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Companies
        fields = [
            "title",
            "description",
            "phone",
            "email",
            "slug",
            "address_text",
            "embed_address",
            "city",
            "district",
            "logo"
        ]