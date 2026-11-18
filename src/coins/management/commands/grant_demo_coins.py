"""Grant a temporary demo balance to one local account."""

from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from coins.models import CoinReason
from coins.services import award_coins


class Command(BaseCommand):
    help = "Grant demo-only coins to one account."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--amount", type=int, default=100)

    def handle(self, *args, **options):
        user = get_user_model().objects.filter(email=options["email"]).first()
        if user is None:
            raise CommandError("No account exists with that email.")
        if options["amount"] <= 0:
            raise CommandError("The demo amount must be positive.")
        award_coins(
            user,
            options["amount"],
            reason=CoinReason.DEMO_GRANT,
            event_key=f"demo:{user.pk}:{uuid4()}",
        )
        self.stdout.write(self.style.SUCCESS(f"Granted {options['amount']} coins to {user.email}."))
