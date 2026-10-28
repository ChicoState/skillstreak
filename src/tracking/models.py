"""Django representation of the approved SkillStreak relational schema."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class UserPreference(models.Model):
    class Theme(models.TextChoices):
        GREEN = "green", "Green"
        BLUE = "blue", "Blue"
        PURPLE = "purple", "Purple"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timezone = models.CharField(max_length=63, default="UTC")
    reminders_enabled = models.BooleanField(default=False)
    reminders_started_on = models.DateField(null=True, blank=True)
    reminders_checked_through = models.DateField(null=True, blank=True)
    theme = models.CharField(max_length=16, choices=Theme.choices, default=Theme.GREEN)

    class Meta:
        db_table = "user_preferences"


class Skill(models.Model):
    class Visibility(models.TextChoices):
        SYSTEM = "SYSTEM"
        PUBLIC = "PUBLIC"
        PRIVATE = "PRIVATE"

    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.RESTRICT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    slug = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=16, choices=Visibility.choices, default=Visibility.SYSTEM
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField("Tag", through="SkillTag", related_name="skills")

    class Meta:
        db_table = "skills"
        constraints = [
            models.CheckConstraint(condition=~Q(slug=""), name="skills_nonempty_slug"),
            models.CheckConstraint(condition=~Q(name=""), name="skills_nonempty_name"),
        ]


class Tag(models.Model):
    """A curated, reusable category for system and personal skills."""

    slug = models.CharField(max_length=48, unique=True)
    name = models.CharField(max_length=48, unique=True)

    class Meta:
        db_table = "tags"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(condition=~Q(slug=""), name="tags_nonempty_slug"),
            models.CheckConstraint(condition=~Q(name=""), name="tags_nonempty_name"),
        ]


class TagAlias(models.Model):
    """A searchable synonym for one curated tag."""

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    term = models.CharField(max_length=48)

    class Meta:
        db_table = "tag_aliases"
        constraints = [
            models.UniqueConstraint(fields=["tag", "term"], name="tag_aliases_tag_term_unique"),
            models.CheckConstraint(condition=~Q(term=""), name="tag_aliases_nonempty_term"),
        ]
        indexes = [models.Index(fields=["term"], name="tag_aliases_term_idx")]


class SkillTag(models.Model):
    """A many-to-many assignment from a skill to a curated tag."""

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        db_table = "skill_tags"
        constraints = [
            models.UniqueConstraint(fields=["skill", "tag"], name="skill_tags_skill_tag_unique")
        ]
        indexes = [models.Index(fields=["tag", "skill"], name="skill_tags_tag_skill_idx")]


class MetricDefinition(models.Model):
    class ValueType(models.TextChoices):
        NUMBER = "NUMBER"
        TEXT = "TEXT"
        BOOLEAN = "BOOLEAN"

    class Aggregation(models.TextChoices):
        LATEST = "LATEST"
        SUM = "SUM"
        MAX = "MAX"
        MIN = "MIN"
        AVERAGE = "AVERAGE"

    skill = models.ForeignKey(Skill, on_delete=models.RESTRICT)
    key = models.CharField(max_length=64)
    label = models.CharField(max_length=100)
    value_type = models.CharField(max_length=16, choices=ValueType.choices)
    canonical_unit = models.CharField(max_length=32, null=True, blank=True)
    aggregation = models.CharField(
        max_length=16, choices=Aggregation.choices, default=Aggregation.LATEST
    )
    minimum_value = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    maximum_value = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    allows_multiple_values = models.BooleanField(default=False)
    display_order = models.SmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "metric_definitions"
        constraints = [
            models.UniqueConstraint(
                fields=["skill", "key"], name="metric_definitions_skill_key_unique"
            ),
            models.CheckConstraint(condition=~Q(key=""), name="metric_definitions_nonempty_key"),
            models.CheckConstraint(
                condition=~Q(label=""), name="metric_definitions_nonempty_label"
            ),
            models.CheckConstraint(
                condition=Q(display_order__gte=0), name="metric_definitions_display_order_check"
            ),
            models.CheckConstraint(
                condition=Q(minimum_value__isnull=True)
                | Q(maximum_value__isnull=True)
                | Q(minimum_value__lte=models.F("maximum_value")),
                name="metric_definitions_range_check",
            ),
        ]


class UserSkill(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.RESTRICT)
    started_on = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_skills"
        constraints = [
            models.UniqueConstraint(fields=["user", "skill"], name="user_skills_user_skill_unique")
        ]
        indexes = [models.Index(fields=["skill", "is_active"], name="user_skills_skill_active_idx")]


class DailyCompletion(models.Model):
    user_skill = models.ForeignKey(UserSkill, on_delete=models.CASCADE)
    completed_on = models.DateField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "daily_completions"
        constraints = [
            models.UniqueConstraint(
                fields=["user_skill", "completed_on"],
                name="daily_completions_user_skill_date_unique",
            )
        ]


class MissedSkillEpisode(models.Model):
    """An unresolved run of missed expected dates for one selected skill."""

    user_skill = models.ForeignKey(UserSkill, on_delete=models.CASCADE)
    first_missed_on = models.DateField()
    last_missed_on = models.DateField()
    consecutive_misses = models.PositiveSmallIntegerField(default=1)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "missed_skill_episodes"
        constraints = [
            models.UniqueConstraint(
                fields=["user_skill"],
                condition=Q(closed_at__isnull=True),
                name="missed_skill_episode_one_active",
            ),
            models.CheckConstraint(
                condition=Q(consecutive_misses__gte=1),
                name="missed_skill_episode_count_check",
            ),
            models.CheckConstraint(
                condition=Q(last_missed_on__gte=models.F("first_missed_on")),
                name="missed_skill_episode_dates_check",
            ),
        ]


class ProfileReminderDigestDismissal(models.Model):
    """The latest acknowledgement of a user's profile missed-skills digest."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    dismissed_at = models.DateTimeField()

    class Meta:
        db_table = "profile_reminder_digest_dismissals"


class UserSkillSchedule(models.Model):
    class RuleType(models.TextChoices):
        DAILY = "DAILY"
        EVERY_N_DAYS = "EVERY_N_DAYS"
        DAYS_PER_WEEK = "DAYS_PER_WEEK"
        DAYS_PER_MONTH = "DAYS_PER_MONTH"
        DAYS_OF_WEEK = "DAYS_OF_WEEK"
        DAYS_OF_MONTH = "DAYS_OF_MONTH"

    user_skill = models.ForeignKey(UserSkill, on_delete=models.CASCADE)
    rule_type = models.CharField(max_length=16, choices=RuleType.choices)
    effective_from = models.DateField()
    effective_through = models.DateField(null=True, blank=True)
    interval_days = models.SmallIntegerField(null=True, blank=True)
    target_days_per_week = models.SmallIntegerField(null=True, blank=True)
    target_days_per_month = models.SmallIntegerField(null=True, blank=True)
    week_starts_on = models.SmallIntegerField(null=True, blank=True)
    short_month_policy = models.CharField(max_length=16, null=True, blank=True)

    class Meta:
        db_table = "user_skill_schedules"
        constraints = [
            models.CheckConstraint(
                condition=Q(effective_through__isnull=True)
                | Q(effective_through__gte=models.F("effective_from")),
                name="user_skill_schedules_dates_check",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        rule_type="DAILY",
                        interval_days__isnull=True,
                        target_days_per_week__isnull=True,
                        target_days_per_month__isnull=True,
                        week_starts_on__isnull=True,
                        short_month_policy__isnull=True,
                    )
                    | Q(
                        rule_type="EVERY_N_DAYS",
                        interval_days__gte=2,
                        target_days_per_week__isnull=True,
                        target_days_per_month__isnull=True,
                        week_starts_on__isnull=True,
                        short_month_policy__isnull=True,
                    )
                    | Q(
                        rule_type="DAYS_PER_WEEK",
                        interval_days__isnull=True,
                        target_days_per_week__gte=1,
                        target_days_per_week__lte=7,
                        target_days_per_month__isnull=True,
                        week_starts_on__gte=1,
                        week_starts_on__lte=7,
                        short_month_policy__isnull=True,
                    )
                    | Q(
                        rule_type="DAYS_PER_MONTH",
                        interval_days__isnull=True,
                        target_days_per_week__isnull=True,
                        target_days_per_month__gte=1,
                        target_days_per_month__lte=31,
                        week_starts_on__isnull=True,
                        short_month_policy__isnull=True,
                    )
                    | Q(
                        rule_type="DAYS_OF_WEEK",
                        interval_days__isnull=True,
                        target_days_per_week__isnull=True,
                        target_days_per_month__isnull=True,
                        week_starts_on__isnull=True,
                        short_month_policy__isnull=True,
                    )
                    | Q(
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
        ]


class ScheduleWeekday(models.Model):
    schedule = models.ForeignKey(UserSkillSchedule, on_delete=models.CASCADE)
    weekday = models.SmallIntegerField()

    class Meta:
        db_table = "schedule_weekdays"
        constraints = [
            models.UniqueConstraint(
                fields=["schedule", "weekday"], name="schedule_weekdays_primary_key"
            ),
            models.CheckConstraint(
                condition=Q(weekday__gte=1, weekday__lte=7), name="schedule_weekdays_weekday_check"
            ),
        ]


class ScheduleMonthDay(models.Model):
    schedule = models.ForeignKey(UserSkillSchedule, on_delete=models.CASCADE)
    day_of_month = models.SmallIntegerField()

    class Meta:
        db_table = "schedule_month_days"
        constraints = [
            models.UniqueConstraint(
                fields=["schedule", "day_of_month"], name="schedule_month_days_primary_key"
            ),
            models.CheckConstraint(
                condition=Q(day_of_month__gte=1, day_of_month__lte=31),
                name="schedule_month_days_day_check",
            ),
        ]


class MetricMeasurement(models.Model):
    daily_completion = models.ForeignKey(DailyCompletion, on_delete=models.CASCADE)
    metric_definition = models.ForeignKey(MetricDefinition, on_delete=models.RESTRICT)
    series_index = models.SmallIntegerField(default=0)
    numeric_value = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    text_value = models.TextField(null=True, blank=True)
    boolean_value = models.BooleanField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "metric_measurements"
        constraints = [
            models.UniqueConstraint(
                fields=["daily_completion", "metric_definition", "series_index"],
                name="metric_measurements_completion_metric_series_unique",
            ),
            models.CheckConstraint(
                condition=Q(series_index__gte=0), name="metric_measurements_series_index_check"
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        numeric_value__isnull=False,
                        text_value__isnull=True,
                        boolean_value__isnull=True,
                    )
                    | Q(
                        numeric_value__isnull=True,
                        text_value__isnull=False,
                        boolean_value__isnull=True,
                    )
                    | Q(
                        numeric_value__isnull=True,
                        text_value__isnull=True,
                        boolean_value__isnull=False,
                    )
                ),
                name="metric_measurements_exactly_one_value_check",
            ),
        ]
        indexes = [models.Index(fields=["metric_definition"], name="metric_measurement_def_idx")]

    def clean(self) -> None:
        values = [
            self.numeric_value is not None,
            self.text_value is not None,
            self.boolean_value is not None,
        ]
        if sum(values) != 1:
            raise ValidationError("Exactly one metric value must be supplied.")
        if (
            self.daily_completion_id
            and self.metric_definition_id
            and self.daily_completion.user_skill.skill_id != self.metric_definition.skill_id
        ):
            raise ValidationError("The metric must belong to the completed skill.")
