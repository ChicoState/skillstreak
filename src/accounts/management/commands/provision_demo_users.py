"""Provision the two configured local demonstration accounts."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from tracking.models import Skill, UserSkill


class Command(BaseCommand):
    help = "Create or update the two local demo users and their Touch Grass default."

    def handle(self, *args, **options) -> None:
        credentials = (
            (settings.DEMO_ACCOUNT_1_EMAIL, settings.DEMO_ACCOUNT_1_PASSWORD),
            (settings.DEMO_ACCOUNT_2_EMAIL, settings.DEMO_ACCOUNT_2_PASSWORD),
        )
        if any(not email or not password for email, password in credentials):
            raise CommandError("Set both demo account email and password pairs in the environment.")
        try:
            touch_grass = Skill.objects.get(slug="touch-grass", visibility=Skill.Visibility.SYSTEM)
        except Skill.DoesNotExist as error:
            raise CommandError("Run seed_system_skills before provisioning demo users.") from error
        user_model = get_user_model()
        for email, password in credentials:
            user, _ = user_model.objects.get_or_create(username=email, defaults={"email": email})
            user.email = email
            user.set_password(password)
            user.save()
            selection, _ = UserSkill.objects.get_or_create(
                user=user,
                skill=touch_grass,
                defaults={"started_on": timezone.localdate(), "is_active": True},
            )
            if not selection.is_active:
                selection.is_active = True
                selection.save(update_fields=["is_active"])
        self.stdout.write(self.style.SUCCESS("Demo users are ready."))
