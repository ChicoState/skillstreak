"""Tests for owned skills, weekly schedules, and dated completions."""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from skills.models import Completion, Skill, SkillSchedule


def create_user(email: str) -> object:
    return get_user_model().objects.create_user(
        email=email, password="Secure skillstreak password 2026!"
    )


@pytest.mark.django_db
def test_skill_belongs_to_one_account() -> None:
    user = create_user("learner@csuchico.edu")

    skill = Skill.objects.create(owner=user, name="Practice Spanish")

    assert skill.owner == user
    assert list(user.skills.all()) == [skill]


@pytest.mark.django_db
def test_skill_schedule_rejects_duplicate_weekdays() -> None:
    user = create_user("learner@csuchico.edu")
    skill = Skill.objects.create(owner=user, name="Practice Spanish")
    SkillSchedule.objects.create(skill=skill, weekday=0)

    with pytest.raises(IntegrityError):
        SkillSchedule.objects.create(skill=skill, weekday=0)


@pytest.mark.django_db
def test_skill_schedule_rejects_weekdays_outside_the_calendar_range() -> None:
    user = create_user("learner@csuchico.edu")
    skill = Skill.objects.create(owner=user, name="Practice Spanish")
    schedule = SkillSchedule(skill=skill, weekday=7)

    with pytest.raises(ValidationError):
        schedule.full_clean()


@pytest.mark.django_db
def test_completion_rejects_duplicate_skill_dates() -> None:
    from datetime import date

    user = create_user("learner@csuchico.edu")
    skill = Skill.objects.create(owner=user, name="Practice Spanish")
    Completion.objects.create(skill=skill, completed_on=date(2026, 10, 21))

    with pytest.raises(IntegrityError):
        Completion.objects.create(skill=skill, completed_on=date(2026, 10, 21))
