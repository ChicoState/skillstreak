"""Create repeatable local data for manually testing in-app reminders."""

from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from tracking.models import (
    DailyCompletion,
    MissedSkillEpisode,
    Skill,
    UserPreference,
    UserSkill,
    UserSkillSchedule,
)


class Command(BaseCommand):
    help = "Create repeatable local reminder demo data for an existing account."
    demo_skills = (
        ("exercise", "Reminder Demo: Exercise", "A missed daily demo skill."),
        ("read", "Reminder Demo: Read", "A missed daily demo skill."),
        ("meditate", "Reminder Demo: Meditate", "A completed daily demo skill."),
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("--email", required=True, help="Existing local account email address.")

    def handle(self, *args, **options) -> None:
        email = options["email"].strip().casefold()
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=email)
        except user_model.DoesNotExist as error:
            raise CommandError(f"No account exists for {email}.") from error

        with transaction.atomic():
            preference, _ = UserPreference.objects.get_or_create(
                user=user,
                defaults={"timezone": "UTC", "reminders_enabled": True},
            )
            if not preference.reminders_enabled:
                preference.reminders_enabled = True
                preference.save(update_fields=["reminders_enabled"])

            try:
                local_today = timezone.now().astimezone(ZoneInfo(preference.timezone)).date()
            except ZoneInfoNotFoundError as error:
                raise CommandError(
                    f"The account timezone {preference.timezone!r} is invalid."
                ) from error

            user_skills = {
                key: self._ensure_daily_skill(user, key, name, description, local_today)
                for key, name, description in self.demo_skills
            }
            for slug in ("exercise", "read"):
                MissedSkillEpisode.objects.update_or_create(
                    user_skill=user_skills[slug],
                    closed_at__isnull=True,
                    defaults={
                        "first_missed_on": local_today - timedelta(days=2),
                        "last_missed_on": local_today - timedelta(days=1),
                        "consecutive_misses": 2,
                    },
                )
            DailyCompletion.objects.get_or_create(
                user_skill=user_skills["meditate"],
                completed_on=local_today,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Reminder demo data is ready for {user.email}: Exercise and Read are missed."
            )
        )

    @staticmethod
    def _ensure_daily_skill(
        user,
        key: str,
        name: str,
        description: str,
        local_today,
    ) -> UserSkill:
        skill, _ = Skill.objects.get_or_create(
            slug=f"reminder-demo-{user.pk}-{key}",
            defaults={
                "name": name,
                "description": description,
                "visibility": Skill.Visibility.PRIVATE,
                "created_by": user,
            },
        )
        user_skill, _ = UserSkill.objects.get_or_create(
            user=user,
            skill=skill,
            defaults={"started_on": local_today - timedelta(days=3), "is_active": True},
        )
        if not user_skill.is_active:
            user_skill.is_active = True
            user_skill.save(update_fields=["is_active"])
        UserSkillSchedule.objects.get_or_create(
            user_skill=user_skill,
            defaults={
                "rule_type": UserSkillSchedule.RuleType.DAILY,
                "effective_from": user_skill.started_on,
            },
        )
        return user_skill
