from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tracking", "0011_userpreference_reminders_checked_through")]

    operations = [
        migrations.AddField(
            model_name="skill",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="skill",
            index=models.Index(
                fields=["visibility", "created_by", "archived_at"],
                name="skills_private_archive_idx",
            ),
        ),
    ]
