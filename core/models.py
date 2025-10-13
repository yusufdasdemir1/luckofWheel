from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class Companies(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20,unique=True)
    email = models.EmailField(unique=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True)
    is_show_wheel = models.BooleanField(default=True)
    show_before_meeting = models.BooleanField(default=False)
    spin_cooldown_hours=models.PositiveIntegerField(default=48)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.user.name} - {self.gift.title}"


class Meetings(models.Model):
    date = models.DateField()
    time = models.TimeField()
    end_time = models.TimeField()

    service_title = models.CharField(max_length=255)
    service_duration = models.PositiveIntegerField()
    service_price = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField(blank=True, null=True)

    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='meetings')
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='meetings')

    is_active = models.BooleanField(default=True, help_text="Randevu geçerli mi?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.company.title} - {self.date} {self.time}"


class Services(models.Model):
    company = models.ForeignKey("Companies", on_delete=models.CASCADE, related_name="services")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    duration = models.PositiveIntegerField(help_text="Hizmet süresi (dakika)")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True, help_text="Hizmet şu anda aktif mi?")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({'Aktif' if self.is_active else 'Pasif'})"