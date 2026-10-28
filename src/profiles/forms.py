"""Forms for authenticated profile settings."""

from zoneinfo import available_timezones

from django import forms

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
