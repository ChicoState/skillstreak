"""XP, level, timezone, and scheduled-completion domain rules."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db import transaction
from django.utils import timezone

from .models import Completion, Skill, SkillSchedule

XP_PER_COMPLETION = 10
MAX_LEVEL = 99
MAX_COMPLETION_AGE_DAYS = 7


class TimezoneNotConfigured(ValueError):
    """Raised when an account cannot provide a valid timezone."""


class CompletionEligibilityError(ValueError):
    """Raised when a completion date is not valid for its skill schedule."""


@dataclass(frozen=True)
class Progression:
    """Derived XP and level values for one account."""

    total_xp: int
    level: int
    level_start_xp: int
    next_level_xp: int | None

    @property
    def progress_percent(self) -> int:
        """Return whole-number progress through the current level."""
        if self.next_level_xp is None:
            return 100

        level_span = self.next_level_xp - self.level_start_xp
        return int((self.total_xp - self.level_start_xp) * 100 / level_span)


def level_threshold(level: int) -> int:
    """Return the cumulative XP required to reach a level."""
    if not 0 <= level <= MAX_LEVEL:
        raise ValueError(f"Level must be between 0 and {MAX_LEVEL}.")
    if level == 0:
        return 0
    return 10 + 10 * (level - 1) * level // 2


def level_for_xp(total_xp: int) -> int:
    """Return the account level for total XP, capped at the maximum level."""
    if total_xp < 0:
        raise ValueError("Total XP cannot be negative.")

    for level in range(1, MAX_LEVEL + 1):
        if total_xp < level_threshold(level):
            return level - 1
    return MAX_LEVEL


def progression_for_user(user) -> Progression:
    """Derive progression from the account's completion history."""
    completion_count = Completion.objects.filter(skill__owner=user).count()
    total_xp = completion_count * XP_PER_COMPLETION
    level = level_for_xp(total_xp)
    next_level = level + 1 if level < MAX_LEVEL else None

    return Progression(
        total_xp=total_xp,
        level=level,
        level_start_xp=level_threshold(level),
        next_level_xp=level_threshold(next_level) if next_level else None,
    )


def _account_timezone(user) -> ZoneInfo:
    if not user.timezone:
        raise TimezoneNotConfigured("Set an IANA timezone before completing a skill.")

    try:
        return ZoneInfo(user.timezone)
    except ZoneInfoNotFoundError as error:
        raise TimezoneNotConfigured("The account timezone is not valid.") from error


def local_date_for_user(user, moment: datetime | None = None) -> date:
    """Convert an instant to the account's local calendar date."""
    current_moment = moment or timezone.now()
    if timezone.is_naive(current_moment):
        current_moment = timezone.make_aware(current_moment, timezone=UTC)
    return current_moment.astimezone(_account_timezone(user)).date()


def is_completion_eligible(
    skill: Skill, completed_on: date, *, reference_moment: datetime | None = None
) -> bool:
    """Return whether a date is scheduled and within the allowed local window."""
    local_today = local_date_for_user(skill.owner, reference_moment)
    earliest_date = local_today - timedelta(days=MAX_COMPLETION_AGE_DAYS)
    if not earliest_date <= completed_on <= local_today:
        return False

    return SkillSchedule.objects.filter(skill=skill, weekday=completed_on.weekday()).exists()


@transaction.atomic
def toggle_completion(
    skill: Skill, completed_on: date, *, reference_moment: datetime | None = None
) -> bool:
    """Create or remove one eligible completion while serializing the skill."""
    locked_skill = Skill.objects.select_for_update().select_related("owner").get(pk=skill.pk)
    if not is_completion_eligible(locked_skill, completed_on, reference_moment=reference_moment):
        raise CompletionEligibilityError("The selected date is not eligible for this skill.")

    completion = Completion.objects.filter(skill=locked_skill, completed_on=completed_on).first()
    if completion:
        completion.delete()
        return False

    Completion.objects.create(skill=locked_skill, completed_on=completed_on)
    return True
