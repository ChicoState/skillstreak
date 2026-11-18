"""Tests for the immutable user coin ledger."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from coins.models import CoinLedgerEntry, CoinReason
from coins.services import award_coins, award_progression_rewards, coin_balance
from tracking.models import DailyCompletion, Skill, UserSkill, UserSkillSchedule


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        email="coins@csuchico.edu", password="Secure skillstreak password 2026!"
    )


@pytest.mark.django_db
def test_coin_balance_is_derived_from_positive_ledger_entries(user):
    award_coins(user, 12, reason=CoinReason.LEVEL_UP, event_key="level:1")
    award_coins(user, 8, reason=CoinReason.SKILL_STREAK, event_key="skill:7:week:2")

    assert coin_balance(user) == 20
    assert CoinLedgerEntry.objects.filter(user=user).count() == 2


@pytest.mark.django_db
def test_reprocessing_the_same_event_does_not_award_coins_twice(user):
    first_entry, created = award_coins(user, 12, reason=CoinReason.LEVEL_UP, event_key="level:1")
    second_entry, duplicate = award_coins(user, 12, reason=CoinReason.LEVEL_UP, event_key="level:1")

    assert created is True
    assert duplicate is False
    assert second_entry.pk == first_entry.pk
    assert coin_balance(user) == 12


@pytest.mark.django_db
def test_coin_awards_must_be_positive(user):
    with pytest.raises(ValueError, match="positive"):
        award_coins(user, 0, reason=CoinReason.DEMO_GRANT, event_key="demo:empty")


@pytest.mark.django_db
def test_completion_rewards_are_idempotent_and_include_level_and_streak_awards(user):
    skill = Skill.objects.create(slug="coins-walk", name="Walk", visibility=Skill.Visibility.SYSTEM)
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=timezone.localdate())
    UserSkillSchedule.objects.create(
        user_skill=user_skill,
        rule_type=UserSkillSchedule.RuleType.DAILY,
        effective_from=user_skill.started_on,
    )
    for offset in range(7):
        DailyCompletion.objects.create(
            user_skill=user_skill,
            completed_on=user_skill.started_on + timedelta(days=offset),
        )

    award_progression_rewards(user, user_skill, as_of=user_skill.started_on + timedelta(days=6))
    award_progression_rewards(user, user_skill, as_of=user_skill.started_on + timedelta(days=6))

    assert CoinLedgerEntry.objects.filter(user=user, reason=CoinReason.LEVEL_UP).count() == 4
    assert CoinLedgerEntry.objects.filter(user=user, reason=CoinReason.SKILL_STREAK).count() == 1
    assert CoinLedgerEntry.objects.filter(user=user, reason=CoinReason.OVERALL_STREAK).count() == 1


@pytest.mark.django_db
def test_demo_command_grants_coins_to_one_account(user):
    call_command("grant_demo_coins", email=user.email, amount=50)

    assert coin_balance(user) == 50
    assert CoinLedgerEntry.objects.get(user=user).reason == CoinReason.DEMO_GRANT
