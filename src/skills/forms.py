"""Forms for creating skills and validating completion inputs."""

from django import forms

from accounts.models import validate_timezone

WEEKDAY_CHOICES = (
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
)


class SkillForm(forms.Form):
    """Validate a skill name and one or more scheduled weekdays."""

    name = forms.CharField(max_length=100, strip=True)
    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )

    def clean_name(self) -> str:
        name = self.cleaned_data["name"]
        if not name:
            raise forms.ValidationError("Enter a skill name.")
        return name

    def clean_weekdays(self) -> list[int]:
        return [int(weekday) for weekday in self.cleaned_data["weekdays"]]


class TimezoneForm(forms.Form):
    """Validate a browser-provided IANA timezone name."""

    timezone = forms.CharField(max_length=64, validators=[validate_timezone])


class CompletionForm(forms.Form):
    """Parse the explicit local calendar date selected by the member."""

    completed_on = forms.DateField(
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}),
    )
