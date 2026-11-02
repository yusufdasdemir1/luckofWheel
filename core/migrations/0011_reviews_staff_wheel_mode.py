# Sunucudaki 0010 geçmişinin üstüne: sadece EKLEMELER. Veri taşıma 0012'de, eski kolonların
# silinmesi 0013'te (canlı veri kaybolmasın diye ayrı adımlar).

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_alter_meetings_service_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='companies',
            name='rating_avg',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='companies',
            name='rating_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='companies',
            name='wheel_mode',
            field=models.CharField(choices=[('before', 'Randevudan önce'), ('after', 'Randevudan sonra'), ('none', 'Çark yok')], default='before', help_text='before: çark randevudan önce, after: randevudan sonra, none: çark yok', max_length=10),
        ),
        migrations.AddField(
            model_name='earnedwins',
            name='meeting',
            field=models.ForeignKey(blank=True, help_text='Hediyenin bağlı olduğu randevu (eski kayıtlarda boş olabilir)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wins', to='core.meetings'),
        ),
        migrations.AddField(
            model_name='meetings',
            name='review_token',
            field=models.CharField(editable=False, max_length=64, null=True),
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('comment', models.TextField(blank=True, default='')),
                ('status', models.CharField(choices=[('pending', 'Beklemede'), ('approved', 'Onaylı'), ('hidden', 'Gizli')], default='pending', max_length=10)),
                ('reply', models.TextField(blank=True, default='')),
                ('replied_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='core.companies')),
                ('meeting', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='review', to='core.meetings')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, help_text='Pasif çalışan randevuda seçilemez ve panele giremez')),
                ('photo', models.CharField(blank=True, default='', help_text='Çalışan fotoğrafı: public/images altındaki dosya yolu (ör. staff/ab12.webp)', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff', to='core.companies')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='staff_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='meetings',
            name='staff',
            field=models.ForeignKey(blank=True, help_text='Randevuyu verecek çalışan (eski randevularda boş olabilir)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='meetings', to='core.staff'),
        ),
        migrations.CreateModel(
            name='WorkingHours',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.PositiveSmallIntegerField()),
                ('is_closed', models.BooleanField(default=False)),
                ('opens', models.TimeField()),
                ('closes', models.TimeField()),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='working_hours', to='core.companies')),
            ],
            options={
                'ordering': ['weekday'],
                'unique_together': {('company', 'weekday')},
            },
        ),
    ]
