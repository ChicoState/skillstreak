"""Models for account-owned skills, schedules, and completions."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Skill(models.Model):
    """A named routine owned by one authenticated account."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="skills"
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "pk"]

    def __str__(self) -> str:
        return self.name


class SkillSchedule(models.Model):
    """One weekday on which an owned skill is scheduled."""

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="schedules")
    weekday = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["skill", "weekday"], name="unique_skill_schedule_weekday"
            ),
            models.CheckConstraint(
                condition=models.Q(weekday__gte=0) & models.Q(weekday__lte=6),
                name="skill_schedule_weekday_range",
            ),
        ]


class Completion(models.Model):
    """A skill completed once on a local calendar date."""

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="completions")
    completed_on = models.DateField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["skill", "completed_on"], name="unique_skill_completion_date"
            )
        ]
