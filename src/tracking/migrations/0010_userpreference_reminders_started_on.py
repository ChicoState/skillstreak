from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tracking", "0009_userpreference_theme")]

    operations = [
        migrations.AddField(
            model_name="userpreference",
            name="reminders_started_on",
            field=models.DateField(blank=True, null=True),
        )
    ]
