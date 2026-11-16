"""Tests for the immutable user coin ledger."""

import pytest
from django.contrib.auth import get_user_model

from coins.models import CoinLedgerEntry, CoinReason
from coins.services import award_coins, coin_balance


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
    first_entry, created = award_coins(
        user, 12, reason=CoinReason.LEVEL_UP, event_key="level:1"
    )
    second_entry, duplicate = award_coins(
        user, 12, reason=CoinReason.LEVEL_UP, event_key="level:1"
    )

    assert created is True
    assert duplicate is False
    assert second_entry.pk == first_entry.pk
    assert coin_balance(user) == 12


@pytest.mark.django_db
def test_coin_awards_must_be_positive(user):
    with pytest.raises(ValueError, match="positive"):
        award_coins(user, 0, reason=CoinReason.DEMO_GRANT, event_key="demo:empty")
