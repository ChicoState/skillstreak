from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tracking", "0008_profile_reminder_digest_dismissal")]

    operations = [
        migrations.AddField(
            model_name="userpreference",
            name="theme",
            field=models.CharField(
                choices=[("green", "Green"), ("blue", "Blue"), ("purple", "Purple")],
                default="green",
                max_length=16,
            ),
        ),
    ]
