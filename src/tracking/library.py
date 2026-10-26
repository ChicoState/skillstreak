"""Shared visibility and query rules for the authenticated skill library."""

from django.db.models import Q, QuerySet

from .models import Skill

MAX_LIBRARY_QUERY_LENGTH = 100


def available_library_skills(user) -> QuerySet[Skill]:
    """Return active system skills and active private skills owned by ``user``."""
    return Skill.objects.filter(is_active=True).filter(
        Q(visibility=Skill.Visibility.SYSTEM)
        | Q(visibility=Skill.Visibility.PRIVATE, created_by=user)
    )


def normalize_library_query(value: str) -> str:
    """Bound a user-supplied library search query before querying or redirecting."""
    return value.strip()[:MAX_LIBRARY_QUERY_LENGTH]
