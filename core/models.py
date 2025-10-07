from django.db import models

# Create your models here.
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Companies(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20,unique=True)
    email = models.EmailField(unique=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True)
    show_before_meeting = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Users(BaseModel):
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE,related_name='users')
    is_admin = models.BooleanField(default=False)
    is_show_wheel= models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} {self.surname}"


class Gifts(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    chance = models.FloatField(help_text="Ödülün çıkma olasılığı (0-1 arası değer)")
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='gifts')

    def __str__(self):
        return f"{self.title} ({self.company.title})"


class EarnedWins(BaseModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='wins')
    gift = models.ForeignKey(Gifts, on_delete=models.CASCADE, related_name='earned_wins')
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.name} - {self.gift.title}"


class Meetings(BaseModel):
    date = models.DateField()
    time = models.TimeField()
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='meetings')
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='meetings')

    def __str__(self):
        return f"{self.company.title} - {self.date} {self.time}"