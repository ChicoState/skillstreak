"""Database invariants for per-skill missed reminder episodes."""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from tracking.models import MissedSkillEpisode, Skill, UserSkill


@pytest.mark.django_db(transaction=True)
def test_only_one_active_missed_episode_is_allowed_per_user_skill() -> None:
    user = get_user_model().objects.create_user(
        email="episode-test@csuchico.edu",
        password="A safe local test password 2026",
    )
    skill = Skill.objects.create(slug="episode-test-skill", name="Episode test skill")
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=date(2026, 10, 1))
    episode = MissedSkillEpisode.objects.create(
        user_skill=user_skill,
        first_missed_on=date(2026, 10, 2),
        last_missed_on=date(2026, 10, 2),
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        MissedSkillEpisode.objects.create(
            user_skill=user_skill,
            first_missed_on=date(2026, 10, 3),
            last_missed_on=date(2026, 10, 3),
        )

    episode.closed_at = timezone.now()
    episode.save(update_fields=["closed_at"])
    MissedSkillEpisode.objects.create(
        user_skill=user_skill,
        first_missed_on=date(2026, 10, 3),
        last_missed_on=date(2026, 10, 3),
    )
