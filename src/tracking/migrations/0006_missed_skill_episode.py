from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [("tracking", "0005_merge_20261019_1913")]

    operations = [
        migrations.CreateModel(
            name="MissedSkillEpisode",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("first_missed_on", models.DateField()),
                ("last_missed_on", models.DateField()),
                ("consecutive_misses", models.PositiveSmallIntegerField(default=1)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user_skill",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, to="tracking.userskill"),
                ),
            ],
            options={"db_table": "missed_skill_episodes"},
        ),
        migrations.AddConstraint(
            model_name="missedskillepisode",
            constraint=models.UniqueConstraint(
                condition=Q(("closed_at__isnull", True)),
                fields=("user_skill",),
                name="missed_skill_episode_one_active",
            ),
        ),
        migrations.AddConstraint(
            model_name="missedskillepisode",
            constraint=models.CheckConstraint(
                condition=Q(("consecutive_misses__gte", 1)),
                name="missed_skill_episode_count_check",
            ),
        ),
        migrations.AddConstraint(
            model_name="missedskillepisode",
            constraint=models.CheckConstraint(
                condition=Q(("last_missed_on__gte", models.F("first_missed_on"))),
                name="missed_skill_episode_dates_check",
            ),
        ),
    ]
