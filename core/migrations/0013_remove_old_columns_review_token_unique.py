from django.db import migrations, models

import core.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_migrate_existing_data'),
    ]

    operations = [
        # veri 0012'de wheel_mode'a taşındı; artık eski kolonlar silinebilir
        migrations.RemoveField(model_name='companies', name='is_show_wheel'),
        migrations.RemoveField(model_name='companies', name='show_before_meeting'),
        # firma rengi artık kullanılmıyor (yerelde de bilerek kaldırıldı)
        migrations.RemoveField(model_name='companies', name='company_color'),
        # 0012'de her randevuya benzersiz token yazıldı; şimdi unique + default yapılır
        migrations.AlterField(
            model_name='meetings',
            name='review_token',
            field=models.CharField(
                default=core.models.generate_review_token,
                editable=False,
                max_length=64,
                unique=True,
            ),
        ),
    ]
