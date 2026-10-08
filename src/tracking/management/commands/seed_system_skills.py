"""Seed the system skill catalog defined in initial_data.sql."""

from django.core.management.base import BaseCommand

from tracking.models import Skill

SYSTEM_SKILLS = (
    ("exercise", "Exercise", "Complete any exercise activity."),
    ("eat-healthy", "Eat Healthy", "Make a healthy eating choice."),
    ("read", "Read", "Spend time reading."),
    ("learn", "Learn", "Spend time learning something new."),
    ("touch-grass", "Touch Grass", "Spend time outdoors."),
    ("go-to-gym", "Go to Gym", "Visit the gym."),
    ("hobby", "Hobby", "Spend time on a hobby."),
    ("drink-water", "Drink Water", "Meet your hydration intention."),
    ("sleep", "Sleep", "Meet your sleep intention."),
)


class Command(BaseCommand):
    help = "Create the idempotent system skill catalog."

    def handle(self, *args, **options) -> None:
        for slug, name, description in SYSTEM_SKILLS:
            Skill.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": description,
                    "visibility": Skill.Visibility.SYSTEM,
                },
            )
        self.stdout.write(self.style.SUCCESS("System skills are ready."))
