"""Email-only account model for SkillStreak team members."""

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

TEAM_EMAIL_DOMAIN = "csuchico.edu"


def normalize_email(email: str) -> str:
    """Return the canonical email stored and used for authentication."""
    return email.strip().casefold()


def is_team_email(email: str) -> bool:
    """Return whether an email belongs to the approved project-team domain."""
    local_part, separator, domain = normalize_email(email).rpartition("@")
    return bool(local_part and separator and domain == TEAM_EMAIL_DOMAIN)


class UserManager(BaseUserManager):
    """Create users whose email address is their only login identifier."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("The email address must be set.")
        if not is_team_email(email):
            raise ValueError("Use a @csuchico.edu email address.")

        user = self.model(email=normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """A user authenticated by their normalized Chico State email address."""

    username = None
    email = models.EmailField("email address", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def clean(self) -> None:
        super().clean()
        self.email = normalize_email(self.email)
        if not is_team_email(self.email):
            raise ValidationError({"email": "Use your @csuchico.edu email address."})

    def save(self, *args, **kwargs) -> None:
        self.email = normalize_email(self.email)
        super().save(*args, **kwargs)
