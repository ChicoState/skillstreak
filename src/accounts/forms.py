"""Forms for creating and authenticating internal team accounts."""

from django import forms
from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError

from .models import User, is_team_email, normalize_email

ACCOUNT_CREATION_ERROR = "We couldn't create an account with those details."


class RegistrationForm(forms.Form):
    """Validate a new self-service account without exposing duplicate emails."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_email(self) -> str:
        email = normalize_email(self.cleaned_data["email"])
        if not is_team_email(email):
            raise ValidationError("Use your @csuchico.edu email address.")
        if User.objects.filter(email=email).exists():
            raise ValidationError(ACCOUNT_CREATION_ERROR)
        return email

    def clean(self) -> dict[str, str]:
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The two password fields didn't match.")
        elif password1:
            user = User(email=cleaned_data.get("email", ""))
            try:
                password_validation.validate_password(password1, user)
            except ValidationError as error:
                self.add_error("password1", error)

        return cleaned_data

    def save(self) -> User:
        """Create the validated account with Django-managed password hashing."""
        return User.objects.create_user(
            email=self.cleaned_data["email"], password=self.cleaned_data["password1"]
        )


class SignInForm(forms.Form):
    """Authenticate a registered team member by email and password."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"})
    )

    def __init__(self, request=None, *args, **kwargs) -> None:
        self.request = request
        self.user_cache: User | None = None
        super().__init__(*args, **kwargs)

    def clean(self) -> dict[str, str]:
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            self.user_cache = authenticate(
                self.request, email=normalize_email(email), password=password
            )
            if self.user_cache is None:
                raise ValidationError("The email or password is incorrect.")

        return cleaned_data

    def get_user(self) -> User | None:
        """Return the authenticated user after successful form validation."""
        return self.user_cache
