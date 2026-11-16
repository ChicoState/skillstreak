"""Immutable user-owned coin ledger entries."""

from django.conf import settings
from django.db import models


class CoinReason(models.TextChoices):
    LEVEL_UP = "LEVEL_UP", "Level up"
    SKILL_STREAK = "SKILL_STREAK", "Skill streak"
    OVERALL_STREAK = "OVERALL_STREAK", "Overall streak"
    DEMO_GRANT = "DEMO_GRANT", "Demo grant"


class CoinLedgerEntry(models.Model):
    """One permanent, positive coin award for an account."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coin_ledger"
    )
    amount = models.PositiveIntegerField()
    reason = models.CharField(max_length=24, choices=CoinReason.choices)
    event_key = models.CharField(max_length=200, unique=True)
    user_skill = models.ForeignKey(
        "tracking.UserSkill",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="coin_awards",
    )
    milestone_weeks = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="coins_amount_positive"),
        ]
