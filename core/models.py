from django.db import models

# Create your models here.

class Companies(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20,unique=True)
    email = models.EmailField(unique=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True)
    show_before_meeting = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.title


class Users(models.Model):
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE,related_name='users')
    is_admin = models.BooleanField(default=False)
    is_show_wheel= models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.name} {self.surname}"


class Gifts(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    chance = models.FloatField(help_text="Ödülün çıkma olasılığı (0-1 arası değer)")
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='gifts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.title} ({self.company.title})"


class EarnedWins(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='wins')
    gift = models.ForeignKey(Gifts, on_delete=models.CASCADE, related_name='earned_wins')
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.user.name} - {self.gift.title}"


class Meetings(models.Model):
    date = models.DateField()
    time = models.TimeField()
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='meetings')
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, related_name='meetings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.company.title} - {self.date} {self.time}"