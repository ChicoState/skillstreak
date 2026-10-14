from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tracking", "0003_user_skill_schedule_date_exclusion")]

    operations = [
        migrations.AddField(
            model_name="userpreference",
            name="reminders_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
