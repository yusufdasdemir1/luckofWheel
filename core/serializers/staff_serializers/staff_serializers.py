from django.db.models import Q
from rest_framework import serializers

from core.models import Companies, Staff, Users, WorkingHours


def email_in_use(email, company, exclude_user_id=None):
    """
    Çalışan e-postası, firma e-postalarıyla ve diğer çalışanlarla çakışamaz
    (giriş ekranı sadece e-posta ile hangi hesap olduğunu bulur).
    Aynı firmadaki müşteri kayıtlarıyla da çakışamaz (e-posta + firma benzersizdir).
    """
    if Companies.objects.filter(email__iexact=email).exists():
        return True

    users = Users.objects.filter(email__iexact=email)
    if exclude_user_id:
        users = users.exclude(pk=exclude_user_id)
    return users.filter(Q(staff_profile__isnull=False) | Q(company=company)).exists()


class StaffSerializer(serializers.ModelSerializer):
    """Panelde çalışan listesi (sadece firma sahibi görür)."""
    name = serializers.CharField(source="user.name")
    surname = serializers.CharField(source="user.surname")
    email = serializers.CharField(source="user.email")
    meeting_count = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = ["id", "name", "surname", "email", "is_active", "meeting_count", "photo"]

    def get_meeting_count(self, obj):
        return obj.meetings.count()


class StaffPublicSerializer(serializers.ModelSerializer):
    """Müşterinin göreceği çalışan bilgisi: ad, soyad ve fotoğraf."""
    name = serializers.CharField(source="user.name")
    surname = serializers.CharField(source="user.surname")

    class Meta:
        model = Staff
        fields = ["id", "name", "surname", "photo"]


class StaffCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    surname = serializers.CharField(max_length=255)
    email = serializers.EmailField(error_messages={"invalid": "Geçerli bir email adresi giriniz."})
    password = serializers.CharField(
        write_only=True,
        min_length=6,
        error_messages={"min_length": "Şifre en az 6 karakter olmalıdır."},
    )

    def validate_email(self, value):
        value = value.strip().lower()
        company = self.context["company"]
        if email_in_use(value, company):
            raise serializers.ValidationError("Bu e-posta adresi zaten kullanılıyor.")
        return value


class StaffUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    surname = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField(
        required=False,
        error_messages={"invalid": "Geçerli bir email adresi giriniz."},
    )
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        error_messages={"min_length": "Şifre en az 6 karakter olmalıdır."},
    )
    is_active = serializers.BooleanField(required=False)

    def validate_email(self, value):
        value = value.strip().lower()
        staff = self.context["staff"]
        if email_in_use(value, staff.company, exclude_user_id=staff.user_id):
            raise serializers.ValidationError("Bu e-posta adresi zaten kullanılıyor.")
        return value

    def validate_password(self, value):
        # boş bırakılırsa şifre değişmez
        if value and len(value) < 6:
            raise serializers.ValidationError("Şifre en az 6 karakter olmalıdır.")
        return value


class WorkingHoursSerializer(serializers.Serializer):
    """Bir günün çalışma saati. weekday: 0=Pazartesi ... 6=Pazar."""
    weekday = serializers.IntegerField(min_value=0, max_value=6)
    is_closed = serializers.BooleanField()
    opens = serializers.TimeField(format="%H:%M", input_formats=["%H:%M", "%H:%M:%S"])
    closes = serializers.TimeField(format="%H:%M", input_formats=["%H:%M", "%H:%M:%S"])

    def validate(self, attrs):
        if not attrs["is_closed"] and attrs["opens"] >= attrs["closes"]:
            raise serializers.ValidationError(
                {"closes": "Kapanış saati açılış saatinden sonra olmalıdır."}
            )
        return attrs


class WorkingHoursUpdateSerializer(serializers.Serializer):
    hours = WorkingHoursSerializer(many=True)

    def validate_hours(self, value):
        days = [item["weekday"] for item in value]
        if sorted(days) != list(range(7)):
            raise serializers.ValidationError("Haftanın 7 günü de gönderilmelidir.")
        return value
