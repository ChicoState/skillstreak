"""Forms for authenticated profile settings."""

from zoneinfo import available_timezones

from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from tracking.models import UserPreference

TIMEZONE_CHOICES = [(name, name) for name in sorted(available_timezones())]


class ProfileSettingsForm(forms.ModelForm):
    """Validate the settings a user may change on their profile."""

    timezone = forms.ChoiceField(choices=TIMEZONE_CHOICES)
    theme = forms.ChoiceField(choices=UserPreference.Theme.choices, required=False)

    class Meta:
        model = UserPreference
        fields = ["timezone", "reminders_enabled", "theme"]
        labels = {
            "reminders_enabled": "Enable in-app reminders",
            "theme": "Color palette",
        }

    def clean_theme(self) -> str:
        """Keep an existing palette when older form posts omit the new field."""
        return self.cleaned_data["theme"] or self.instance.theme


class ChangePasswordForm(PasswordChangeForm):
    """Validate a signed-in user's current and new passwords."""

    def __init__(self, user, *args, **kwargs) -> None:
        super().__init__(user, *args, **kwargs)
        self.fields["old_password"].label = "Current password"
        self.fields["old_password"].widget.attrs.update({"autocomplete": "current-password"})
        self.fields["new_password1"].label = "New password"
        self.fields["new_password1"].widget.attrs.update({"autocomplete": "new-password"})
        self.fields["new_password2"].label = "Confirm new password"
        self.fields["new_password2"].widget.attrs.update({"autocomplete": "new-password"})
