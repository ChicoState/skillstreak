from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tracking", "0010_userpreference_reminders_started_on")]

    operations = [
        migrations.AddField(
            model_name="userpreference",
            name="reminders_checked_through",
            field=models.DateField(blank=True, null=True),
        )
    ]
