"""Transactional coin ledger operations."""

from django.db import transaction
from django.db.models import Sum

from skills.progression import progression_for_user

from .models import CoinLedgerEntry, CoinReason
from .rewards import INDIVIDUAL_MILESTONES, LEVEL_UP_REWARD, OVERALL_MILESTONES
from .streaks import milestone_occurrences, skill_streak


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


@transaction.atomic
def award_progression_rewards(user, user_skill=None, *, as_of=None) -> None:
    """Award newly reached level and streak milestones without duplicates."""
    from django.utils import timezone

    from tracking.models import UserSkill

    reward_date = as_of or timezone.localdate()
    progression = progression_for_user(user)
    for level in range(1, progression.level + 1):
        award_coins(
            user,
            LEVEL_UP_REWARD,
            reason=CoinReason.LEVEL_UP,
            event_key=f"{user.pk}:level:{level}",
        )

    if user_skill is None:
        return

    summary = skill_streak(user_skill, as_of=reward_date)
    for milestone, amount in INDIVIDUAL_MILESTONES.items():
        if summary.cycle_start is None or summary.current_occurrences < milestone_occurrences(
            user_skill, milestone, cycle_start=summary.cycle_start
        ):
            continue
        if milestone % 2:
            event_key = f"{user.pk}:skill:{user_skill.pk}:once:{milestone}"
        else:
            event_key = (
                f"{user.pk}:skill:{user_skill.pk}:cycle:{summary.cycle_start}:milestone:{milestone}"
            )
        award_coins(
            user,
            amount,
            reason=CoinReason.SKILL_STREAK,
            event_key=event_key,
            user_skill=user_skill,
            milestone_weeks=milestone,
        )

    active_skills = list(UserSkill.objects.filter(user=user, is_active=True))
    current_overall_skill = max(
        active_skills,
        key=lambda item: skill_streak(item, as_of=reward_date).current_occurrences,
        default=None,
    )
    if current_overall_skill is None:
        return
    current_overall_summary = skill_streak(current_overall_skill, as_of=reward_date)
    current_overall = current_overall_summary.current_occurrences
    if current_overall_summary.cycle_start is None:
        return
    for milestone, amount in OVERALL_MILESTONES.items():
        if current_overall >= milestone_occurrences(
            current_overall_skill,
            milestone,
            cycle_start=current_overall_summary.cycle_start,
        ):
            award_coins(
                user,
                amount,
                reason=CoinReason.OVERALL_STREAK,
                event_key=f"{user.pk}:overall:{milestone}",
                milestone_weeks=milestone,
            )
