"""Tests for schema guarantees and repeatable local demo setup."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import override_settings
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


@pytest.mark.django_db
@override_settings(
    DEMO_ACCOUNT_1_EMAIL="student-one@example.com",
    DEMO_ACCOUNT_1_PASSWORD="student-one-password",
    DEMO_ACCOUNT_2_EMAIL="student-two@example.com",
    DEMO_ACCOUNT_2_PASSWORD="student-two-password",
)
def test_provisioning_is_idempotent_and_defaults_both_accounts_to_touch_grass() -> None:
    call_command("seed_system_skills")
    call_command("provision_demo_users")
    call_command("provision_demo_users")

    users = get_user_model().objects.order_by("username")
    assert users.count() == 2
    assert all(user.check_password(f"{user.username.split('@')[0]}-password") for user in users)
    assert UserSkill.objects.count() == 2
    assert set(UserSkill.objects.values_list("skill__slug", flat=True)) == {"touch-grass"}
    assert all(UserSkill.objects.values_list("is_active", flat=True))


@pytest.mark.django_db(transaction=True)
def test_schedule_periods_for_one_skill_cannot_overlap() -> None:
    user = get_user_model().objects.create_user(username="schedule-user")
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
