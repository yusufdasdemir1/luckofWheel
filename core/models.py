import secrets

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class Companies(models.Model):
    STATUS_CHOICES = (
        ('active', 'Aktif'),
        ('passive', 'Pasif'),
    )

    WHEEL_BEFORE = 'before'
    WHEEL_AFTER = 'after'
    WHEEL_NONE = 'none'
    WHEEL_MODE_CHOICES = (
        (WHEEL_BEFORE, 'Randevudan önce'),
        (WHEEL_AFTER, 'Randevudan sonra'),
        (WHEEL_NONE, 'Çark yok'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20,unique=True)
    email = models.EmailField(unique=True)
    logo = models.CharField(max_length=255, blank=True, default="")
    thumbnail = models.CharField(max_length=255, blank=True, default="")
    slug = models.SlugField(unique=True)
    wheel_mode = models.CharField(
        max_length=10,
        choices=WHEEL_MODE_CHOICES,
        default=WHEEL_BEFORE,
        help_text="before: çark randevudan önce, after: randevudan sonra, none: çark yok",
    )
    spin_cooldown_hours=models.PositiveIntegerField(default=48)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    address_text = models.TextField(blank=True, null=False, default='')
    embed_address = models.TextField(blank=True, null=False,default='')
    city=models.TextField(blank=True, null=False, default='')
    district=models.TextField(blank=True, null=False, default='')

    youtube_url=models.TextField(blank=True, null=False, default='')
    instagram_url = models.TextField(blank=True, null=False, default='')
    facebook_url = models.TextField(blank=True, null=False, default='')

    # onaylı yorumlardan hesaplanan önbellek (bkz. core/services/review_service.py)
    rating_avg = models.FloatField(default=0)
    rating_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    @property
    def is_show_wheel(self):
        return self.wheel_mode != self.WHEEL_NONE

    def __str__(self):
        return self.title

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Normal kullanıcı oluşturur.
        """
        if not email:
            raise ValueError("Email alanı zorunludur.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Sadece admin (is_admin=True) kullanıcı oluşturur.
        """
        extra_fields.setdefault('is_admin', True)
        return self.create_user(email, password, **extra_fields)

class Users(AbstractBaseUser, PermissionsMixin):
    """
    Sade kullanıcı modeli — sadece senin belirlediğin alanlarla.
    Django'nun is_staff, is_superuser gibi alanları yok.
    """
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    email = models.EmailField()
    password = models.CharField(max_length=255)
    phone=models.CharField(max_length=20)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='users', null=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'id'
    REQUIRED_FIELDS = ['name', 'surname']

    objects = BaseUserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["email", "company"], name="unique_email_per_company")
        ]

    def __str__(self):
        return f"{self.name} {self.surname}"

    @property
    def is_company_staff(self):
        """Bir firmanın çalışanı (kuaför) mı? Çalışanlar is_admin olmaz, staff_profile'ları vardır."""
        return hasattr(self, "staff_profile")

    @property
    def is_staff(self):
        """
        Django admin uyumluluğu için zorunlu.
        is_admin True olanları staff gibi gösterir ama DB'de kolon oluşturmaz.
        """
        return self.is_admin


class Gifts(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    chance = models.FloatField(help_text="Ödülün çıkma olasılığı (0-1 arası değer)")
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='gifts')
    is_active = models.BooleanField(default=True, help_text="Bu hediye şu anda aktif mi?")
    gift_color=models.CharField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({'Aktif' if self.is_active else 'Pasif'})"


class EarnedWins(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='wins')

    gift_title = models.CharField(max_length=255, help_text="Kazanılan hediyenin adı")
    gift_description = models.TextField(blank=True, null=True, help_text="Kazanılan hediyenin açıklaması")
    gift_chance = models.FloatField(blank=True, null=True, help_text="Kazanılan hediyenin şans oranı")
    note = models.TextField(blank=True, null=True, help_text="Opsiyonel admin notu")

    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='earned_wins')
    is_used = models.BooleanField(default=False)
    meeting = models.ForeignKey(
        "Meetings",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wins",
        help_text="Hediyenin bağlı olduğu randevu (eski kayıtlarda boş olabilir)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.user.name} - {self.gift_title}"


class MeetingStatus(models.TextChoices):
    WAITING = "waiting", "Bekliyor"
    ARRIVED = "arrived", "Geldi"
    CANCELED = "canceled", "İptal"


def generate_review_token():
    return secrets.token_urlsafe(24)


class Meetings(models.Model):
    # müşteriye giden maildeki "randevuyu değerlendir" linkinin anahtarı
    review_token = models.CharField(
        max_length=64,
        unique=True,
        default=generate_review_token,
        editable=False,
    )
    date = models.DateField()
    time = models.TimeField()
    end_time = models.TimeField()

    status=models.CharField(
        max_length=20,
        choices=MeetingStatus.choices,
        default=MeetingStatus.WAITING,
    )

    service_title = models.CharField(max_length=255)
    service_duration = models.PositiveIntegerField()
    service_price = models.CharField(max_length=100)
    note = models.TextField(blank=True, null=True)

    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='meetings')
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='meetings')
    staff = models.ForeignKey(
        "Staff",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meetings",
        help_text="Randevuyu verecek çalışan (eski randevularda boş olabilir)",
    )


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.company.title} - {self.date} {self.time}"


class ReviewStatus(models.TextChoices):
    PENDING = "pending", "Beklemede"
    APPROVED = "approved", "Onaylı"
    HIDDEN = "hidden", "Gizli"


class Review(models.Model):
    """Müşterinin randevusu için bıraktığı yorum. Randevu başına en fazla bir tane."""
    meeting = models.OneToOneField(Meetings, on_delete=models.CASCADE, related_name="review")
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, default="")
    status = models.CharField(max_length=10, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    reply = models.TextField(blank=True, default="")
    replied_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company.title} | {self.rating}★ | {self.status}"


class Services(models.Model):
    company = models.ForeignKey("Companies", on_delete=models.CASCADE, related_name="services")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    duration = models.PositiveIntegerField(help_text="Hizmet süresi (dakika)")
    price = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, help_text="Hizmet şu anda aktif mi?")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({'Aktif' if self.is_active else 'Pasif'})"


LOG_LEVELS = (
    ("INFO", "INFO"),
    ("WARNING", "WARNING"),
    ("ERROR", "ERROR"),
)


class APILog(models.Model):
    log_level = models.CharField(max_length=20, choices=LOG_LEVELS, default="INFO")

    path = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    status = models.IntegerField()
    ip = models.CharField(max_length=100)
    duration = models.FloatField()

    request_body = models.TextField(null=True, blank=True)
    response_body = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method} {self.path} [{self.status}]"


class MailTemplate(models.Model):
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_CANCELLED = "appointment_cancelled"

    TEMPLATE_KEYS = (
        (APPOINTMENT_CREATED, "Randevu Oluşturuldu"),
        (APPOINTMENT_CANCELLED, "Randevu İptal Edildi"),
    )

    company = models.ForeignKey(
        Companies,
        on_delete=models.CASCADE,
        related_name="mail_templates"
    )
    key = models.CharField(max_length=50, choices=TEMPLATE_KEYS)
    subject = models.CharField(max_length=255)
    body = models.TextField(
        help_text="HTML destekler. {{ user_name }}, {{ meeting_date }} gibi değişkenler kullanılabilir."
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("company", "key")

    def __str__(self):
        return f"{self.company.title} - {self.key}"



class MailLog(models.Model):
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    to_email = models.EmailField()
    key = models.CharField(max_length=50)

    is_sent = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    provider_message_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.title} | {self.key} | {self.to_email}"


class Staff(models.Model):
    """Bir firmanın çalışanı (kuaför). Panelde kendi e-posta ve şifresiyle giriş yapar."""
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name="staff")
    user = models.OneToOneField(Users, on_delete=models.CASCADE, related_name="staff_profile")
    is_active = models.BooleanField(default=True, help_text="Pasif çalışan randevuda seçilemez ve panele giremez")
    photo = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Çalışan fotoğrafı: public/images altındaki dosya yolu (ör. staff/ab12.webp)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.name} {self.user.surname} ({self.company.title})"


class WorkingHours(models.Model):
    """Firmanın haftalık çalışma saatleri. weekday: 0=Pazartesi ... 6=Pazar."""
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name="working_hours")
    weekday = models.PositiveSmallIntegerField()
    is_closed = models.BooleanField(default=False)
    opens = models.TimeField()
    closes = models.TimeField()

    class Meta:
        unique_together = ("company", "weekday")
        ordering = ["weekday"]

    def __str__(self):
        state = "Kapalı" if self.is_closed else f"{self.opens:%H:%M}-{self.closes:%H:%M}"
        return f"{self.company.title} | {self.weekday} | {state}"
