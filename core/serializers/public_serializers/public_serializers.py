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
    staff_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Randevuyu verecek çalışan (firmanın aktif çalışanı varsa zorunlu)"
    )
    note=serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Opsiyonel müşteri notu"
    )

    def validate_phone(self, value):
        value = value.strip()
        if not PHONE_RE.match(value):
            raise serializers.ValidationError(
                "Telefon numarası +90XXXXXXXXXX formatında olmalıdır."
            )
        return value


class PublicSpinSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, help_text="Kayıtlı müşterinin telefonu")
    meeting_id = serializers.IntegerField(
        required=False,
        help_text="Çarkın bağlanacağı randevu (wheel_mode=after için zorunlu)",
    )

    def validate_phone(self, value):
        value = value.strip()
        if not PHONE_RE.match(value):
            raise serializers.ValidationError(
                "Telefon numarası +90XXXXXXXXXX formatında olmalıdır."
            )
        return value


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
    is_show_wheel = serializers.BooleanField(read_only=True)

    class Meta:
        model = Companies
        fields=["title","description","phone","slug","city","district","logo","is_show_wheel","rating_avg","rating_count"]


class PublicCompanySerializer(serializers.ModelSerializer):
    is_show_wheel = serializers.BooleanField(read_only=True)

    class Meta:
        model = Companies
        exclude=["created_at","updated_at","thumbnail","status"]


class SalonApplicationSerializer(serializers.Serializer):
    salon_name = serializers.CharField(max_length=255)
    owner_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=30)
    email = serializers.EmailField(
        error_messages={"invalid": "Geçerli bir email adresi giriniz."}
    )
    city = serializers.CharField(max_length=100)
    district = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    instagram = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    note = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")
    # bot tuzağı (honeypot): gerçek kullanıcılar boş bırakır
    website = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")

    def validate_phone(self, value):
        digits = re.sub(r"\D", "", value)
        if len(digits) < 10 or len(digits) > 12:
            raise serializers.ValidationError("Geçerli bir telefon numarası giriniz.")
        return value.strip()

    def validate_email(self, value):
        value = value.strip().lower()
        if "." not in value.split("@")[-1]:
            raise serializers.ValidationError(
                "Email adresi geçerli bir alan adı içermelidir (ör: example.com)."
            )
        return value
