"""Add count-based calendar-month goals for custom skills."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tracking", "0003_user_skill_schedule_date_exclusion")]

    operations = [
        migrations.AddField(
            model_name="userskillschedule",
            name="target_days_per_month",
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="userskillschedule",
            name="rule_type",
            field=models.CharField(
                choices=[
                    ("DAILY", "Daily"),
                    ("EVERY_N_DAYS", "Every N Days"),
                    ("DAYS_PER_WEEK", "Days Per Week"),
                    ("DAYS_PER_MONTH", "Days Per Month"),
                    ("DAYS_OF_WEEK", "Days Of Week"),
                    ("DAYS_OF_MONTH", "Days Of Month"),
                ],
                max_length=16,
            ),
        ),
        migrations.RemoveConstraint(
            model_name="userskillschedule",
            name="user_skill_schedules_rule_check",
        ),
        migrations.AddConstraint(
            model_name="userskillschedule",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        rule_type="DAILY",
                        interval_days__isnull=True,
                        target_days_per_week__isnull=True,
                        target_days_per_month__isnull=True,
                        week_starts_on__isnull=True,
                        short_month_policy__isnull=True,
                    )
                    | models.Q(
                        rule_type="EVERY_N_DAYS",
                        interval_days__gte=2,
                        target_days_per_week__isnull=True,
                        target_days_per_month__isnull=True,
                        week_starts_on__isnull=True,
                        short_month_policy__isnull=True,
                    )
                    | models.Q(
                        rule_type="DAYS_PER_WEEK",
                        interval_days__isnull=True,
                        target_days_per_week__gte=1,
                        target_days_per_week__lte=7,
                        target_days_per_month__isnull=True,
                        week_starts_on__gte=1,
                        week_starts_on__lte=7,
                        short_month_policy__isnull=True,
                    )
                    | models.Q(
                        rule_type="DAYS_PER_MONTH",
                        interval_days__isnull=True,
                        target_days_per_week__isnull=True,
                        target_days_per_month__gte=1,
                        target_days_per_month__lte=31,
                        week_starts_on__isnull=True,
                        short_month_policy__isnull=True,
                    )
                    | models.Q(
                        rule_type="DAYS_OF_WEEK",
                        interval_days__isnull=True,
                        target_days_per_week__isnull=True,
                        target_days_per_month__isnull=True,
                        week_starts_on__isnull=True,
                        short_month_policy__isnull=True,
                    )
                    | models.Q(
                        rule_type="DAYS_OF_MONTH",
                        interval_days__isnull=True,
                        target_days_per_week__isnull=True,
                        target_days_per_month__isnull=True,
                        week_starts_on__isnull=True,
                        short_month_policy__in=["SKIP", "LAST_DAY"],
                    )
                ),
                name="user_skill_schedules_rule_check",
            ),
        ),
    ]
