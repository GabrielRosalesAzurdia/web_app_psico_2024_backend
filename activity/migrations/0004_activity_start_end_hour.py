# RF-17: renombra "hour" a "start_hour" y agrega "end_hour" en Activity.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0003_activity_description_activity_title'),
    ]

    operations = [
        migrations.RenameField(
            model_name='activity',
            old_name='hour',
            new_name='start_hour',
        ),
        migrations.AddField(
            model_name='activity',
            name='end_hour',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
