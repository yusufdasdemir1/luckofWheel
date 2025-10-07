from django.db import models

# Create your models here.
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True



class Company(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True)
    show_before_meeting = models.BooleanField(default=False)

    def __str__(self):
        return self.title