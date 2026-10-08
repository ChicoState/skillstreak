"""Tests for schema guarantees and repeatable system-skill setup."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.utils import timezone

from tracking.models import Skill, UserSkill, UserSkillSchedule


@pytest.mark.django_db
def test_system_skill_seed_is_idempotent() -> None:
    call_command("seed_system_skills")
    call_command("seed_system_skills")

    assert Skill.objects.count() == 9
    assert set(Skill.objects.values_list("slug", flat=True)) == {
        "drink-water",
        "eat-healthy",
        "exercise",
        "go-to-gym",
        "hobby",
        "learn",
        "read",
        "sleep",
        "touch-grass",
    }


@pytest.mark.django_db(transaction=True)
def test_schedule_periods_for_one_skill_cannot_overlap() -> None:
    user = get_user_model().objects.create_user(
        email="schedule-user@csuchico.edu",
        password="A safe local test password 2026",
    )
    skill = Skill.objects.create(slug="schedule-skill", name="Schedule skill")
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=timezone.localdate())
    UserSkillSchedule.objects.create(
        user_skill=user_skill,
        rule_type=UserSkillSchedule.RuleType.DAILY,
        effective_from=timezone.localdate(),
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        UserSkillSchedule.objects.create(
            user_skill=user_skill,
            rule_type=UserSkillSchedule.RuleType.DAILY,
            effective_from=timezone.localdate(),
        )
