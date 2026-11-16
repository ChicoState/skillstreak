"""Transactional coin ledger operations."""

from django.db import transaction
from django.db.models import Sum

from .models import CoinLedgerEntry, CoinReason


@transaction.atomic
def award_coins(
    user,
    amount: int,
    *,
    reason: CoinReason,
    event_key: str,
    user_skill=None,
    milestone_weeks: int | None = None,
) -> tuple[CoinLedgerEntry, bool]:
    """Create one idempotent positive award and report whether it was new."""
    if amount <= 0:
        raise ValueError("Coin awards must be positive.")

    entry, created = CoinLedgerEntry.objects.get_or_create(
        event_key=event_key,
        defaults={
            "user": user,
            "amount": amount,
            "reason": reason,
            "user_skill": user_skill,
            "milestone_weeks": milestone_weeks,
        },
    )
    return entry, created


def coin_balance(user) -> int:
    """Return the account's current balance derived from its ledger."""
    return CoinLedgerEntry.objects.filter(user=user).aggregate(total=Sum("amount"))["total"] or 0
