from django.db import migrations, models

import accounts.models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="timezone",
            field=models.CharField(
                blank=True,
                max_length=64,
                null=True,
                validators=[accounts.models.validate_timezone],
            ),
        ),
    ]
