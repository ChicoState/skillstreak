"""Validated input for a member-created private skill."""

from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class CustomSkillForm(forms.Form):
    """Collect one custom skill and its recurring completion target."""

    class Frequency(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    name = forms.CharField(
        max_length=100,
        strip=True,
        error_messages={"required": "Enter a skill name."},
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
    started_on = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date", "autocomplete": "off"}),
    )
    description = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "autocomplete": "off"}),
    )
    frequency = forms.ChoiceField(choices=Frequency.choices, initial=Frequency.DAILY)
    target_days = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(attrs={"autocomplete": "off"}),
    )

    def clean_name(self) -> str:
        name = self.cleaned_data["name"]
        if not name:
            raise ValidationError("Enter a skill name.")
        return name

    def clean_started_on(self):
        started_on = self.cleaned_data["started_on"]
        if started_on > timezone.localdate():
            raise ValidationError("Start date cannot be in the future.")
        return started_on

    def clean(self):
        cleaned_data = super().clean()
        frequency = cleaned_data.get("frequency")
        target_days = cleaned_data.get("target_days")

        if frequency == self.Frequency.DAILY:
            cleaned_data["target_days"] = None
        elif target_days is None:
            self.add_error("target_days", "Enter the number of days you want to complete.")
        elif frequency == self.Frequency.WEEKLY and target_days > 7:
            self.add_error("target_days", "A weekly goal cannot exceed 7 days.")

        return cleaned_data
