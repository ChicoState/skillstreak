"""Tests for XP, level, timezone, and completion progression rules."""

from datetime import UTC, date, datetime

import pytest
from django.contrib.auth import get_user_model

from skills.models import Completion, Skill, SkillSchedule
from skills.progression import (
    TimezoneNotConfigured,
    is_completion_eligible,
    level_for_xp,
    level_threshold,
    local_date_for_user,
    progression_for_user,
    toggle_completion,
)


def create_user(email: str, timezone_name: str | None = "UTC") -> object:
    return get_user_model().objects.create_user(
        email=email,
        password="Secure skillstreak password 2026!",
        timezone=timezone_name,
    )


@pytest.mark.parametrize(
    ("level", "threshold"),
    [
        (0, 0),
        (1, 10),
        (2, 20),
        (3, 40),
        (4, 70),
        (5, 110),
        (6, 160),
        (7, 220),
        (99, 48_520),
    ],
)
def test_level_thresholds_follow_the_approved_formula(level: int, threshold: int) -> None:
    assert level_threshold(level) == threshold


def test_level_caps_at_99_while_xp_continues_to_accumulate() -> None:
    assert level_for_xp(level_threshold(99)) == 99
    assert level_for_xp(level_threshold(99) + 10) == 99


@pytest.mark.django_db
def test_new_account_progression_starts_at_level_zero() -> None:
    user = create_user("learner@csuchico.edu")

    progression = progression_for_user(user)

    assert progression.total_xp == 0
    assert progression.level == 0
    assert progression.level_start_xp == 0
    assert progression.next_level_xp == 10
    assert progression.progress_percent == 0


@pytest.mark.django_db
def test_progression_is_derived_from_completion_history() -> None:
    user = create_user("learner@csuchico.edu")
    skill = Skill.objects.create(owner=user, name="Practice Spanish")
    Completion.objects.create(skill=skill, completed_on=date(2026, 10, 21))
    Completion.objects.create(skill=skill, completed_on=date(2026, 10, 22))

    progression = progression_for_user(user)

    assert progression.total_xp == 20
    assert progression.level == 2
    assert progression.level_start_xp == 20
    assert progression.next_level_xp == 40
    assert progression.progress_percent == 0


@pytest.mark.django_db
def test_local_date_uses_the_account_timezone() -> None:
    user = create_user("learner@csuchico.edu", "America/Los_Angeles")
    moment = datetime(2026, 10, 21, 1, 30, tzinfo=UTC)

    assert local_date_for_user(user, moment) == date(2026, 10, 20)


@pytest.mark.django_db
def test_missing_timezone_cannot_determine_a_completion_date() -> None:
    user = create_user("learner@csuchico.edu", None)

    with pytest.raises(TimezoneNotConfigured):
        local_date_for_user(user, datetime(2026, 10, 21, tzinfo=UTC))


@pytest.mark.django_db
def test_completion_eligibility_includes_today_and_the_previous_seven_days() -> None:
    user = create_user("learner@csuchico.edu")
    skill = Skill.objects.create(owner=user, name="Practice Spanish")
    SkillSchedule.objects.create(skill=skill, weekday=2)
    moment = datetime(2026, 10, 21, 12, tzinfo=UTC)

    assert is_completion_eligible(skill, date(2026, 10, 21), reference_moment=moment)
    assert is_completion_eligible(skill, date(2026, 10, 14), reference_moment=moment)
    assert not is_completion_eligible(skill, date(2026, 10, 13), reference_moment=moment)


@pytest.mark.django_db
def test_completion_eligibility_rejects_an_unscheduled_date() -> None:
    user = create_user("learner@csuchico.edu")
    skill = Skill.objects.create(owner=user, name="Practice Spanish")
    SkillSchedule.objects.create(skill=skill, weekday=2)
    moment = datetime(2026, 10, 21, 12, tzinfo=UTC)

    assert not is_completion_eligible(skill, date(2026, 10, 20), reference_moment=moment)


@pytest.mark.django_db
def test_toggle_completion_awards_and_undoes_one_completion() -> None:
    user = create_user("learner@csuchico.edu")
    skill = Skill.objects.create(owner=user, name="Practice Spanish")
    SkillSchedule.objects.create(skill=skill, weekday=2)
    moment = datetime(2026, 10, 21, 12, tzinfo=UTC)

    assert toggle_completion(skill, date(2026, 10, 21), reference_moment=moment) is True
    assert Completion.objects.filter(skill=skill).count() == 1
    assert toggle_completion(skill, date(2026, 10, 21), reference_moment=moment) is False
    assert Completion.objects.filter(skill=skill).count() == 0
