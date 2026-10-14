"""Forms for authenticated profile settings."""

from zoneinfo import available_timezones

from django import forms

from tracking.models import UserPreference

TIMEZONE_CHOICES = [(name, name) for name in sorted(available_timezones())]


class ProfileSettingsForm(forms.ModelForm):
    """Validate the settings a user may change on their profile."""

    timezone = forms.ChoiceField(choices=TIMEZONE_CHOICES)

    class Meta:
        model = UserPreference
        fields = ["timezone", "reminders_enabled"]
        labels = {"reminders_enabled": "Enable reminders"}
