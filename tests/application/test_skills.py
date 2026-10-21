"""Tests for owned skills, weekly schedules, and dated completions."""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import Client

from skills.models import Completion, Skill, SkillSchedule


def create_user(email: str, timezone_name: str | None = None) -> object:
    return get_user_model().objects.create_user(
        email=email,
        password="Secure skillstreak password 2026!",
        timezone=timezone_name,
    )


@pytest.mark.django_db
def test_skill_belongs_to_one_account() -> None:
    user = create_user("learner@csuchico.edu")

    skill = Skill.objects.create(owner=user, name="Practice Spanish")

    assert skill.owner == user
    assert list(user.skills.all()) == [skill]


@pytest.mark.django_db
def test_skill_schedule_rejects_duplicate_weekdays() -> None:
    user = create_user("learner@csuchico.edu")
    skill = Skill.objects.create(owner=user, name="Practice Spanish")
    SkillSchedule.objects.create(skill=skill, weekday=0)

    with pytest.raises(IntegrityError):
        SkillSchedule.objects.create(skill=skill, weekday=0)


@pytest.mark.django_db
def test_skill_schedule_rejects_weekdays_outside_the_calendar_range() -> None:
    user = create_user("learner@csuchico.edu")
    skill = Skill.objects.create(owner=user, name="Practice Spanish")
    schedule = SkillSchedule(skill=skill, weekday=7)

    with pytest.raises(ValidationError):
        schedule.full_clean()


@pytest.mark.django_db
def test_completion_rejects_duplicate_skill_dates() -> None:
    user = create_user("learner@csuchico.edu")
    skill = Skill.objects.create(owner=user, name="Practice Spanish")
    Completion.objects.create(skill=skill, completed_on=date(2026, 10, 21))

    with pytest.raises(IntegrityError):
        Completion.objects.create(skill=skill, completed_on=date(2026, 10, 21))


@pytest.mark.django_db
def test_authenticated_member_can_create_a_skill_and_weekly_schedule(client) -> None:
    user = create_user("learner@csuchico.edu")
    client.force_login(user)

    response = client.post(
        "/skills/create",
        {"name": "Practice Spanish", "weekdays": ["0", "2"]},
    )

    skill = Skill.objects.get(owner=user)
    assert response.status_code == 302
    assert response.url == "/"
    assert skill.name == "Practice Spanish"
    assert set(skill.schedules.values_list("weekday", flat=True)) == {0, 2}


@pytest.mark.django_db
def test_skill_creation_requires_at_least_one_weekday(client) -> None:
    user = create_user("learner@csuchico.edu")
    client.force_login(user)

    response = client.post("/skills/create", {"name": "Practice Spanish"})

    assert response.status_code == 200
    assert response.context["skill_form"].errors["weekdays"] == ["This field is required."]
    assert not Skill.objects.filter(owner=user).exists()


@pytest.mark.django_db
def test_anonymous_member_cannot_create_a_skill(client) -> None:
    response = client.post("/skills/create", {"name": "Practice Spanish", "weekdays": ["0"]})

    assert response.status_code == 302
    assert response.url == "/sign-in?next=/skills/create"


@pytest.mark.django_db
def test_authenticated_member_can_sync_a_valid_timezone(client) -> None:
    user = create_user("learner@csuchico.edu", timezone_name=None)
    client.force_login(user)

    response = client.post("/account/timezone", {"timezone": "America/Los_Angeles"})

    assert response.status_code == 302
    assert response.url == "/"
    assert get_user_model().objects.get(pk=user.pk).timezone == "America/Los_Angeles"


@pytest.mark.django_db
def test_timezone_sync_rejects_invalid_values(client) -> None:
    user = create_user("learner@csuchico.edu", timezone_name=None)
    client.force_login(user)

    response = client.post("/account/timezone", {"timezone": "Not/A_Timezone"})

    assert response.status_code == 400
    assert "valid IANA timezone" in response.context["timezone_form"].errors.as_text()
    assert get_user_model().objects.get(pk=user.pk).timezone is None


@pytest.mark.django_db
def test_member_can_toggle_an_eligible_completion(client) -> None:
    user = create_user("learner@csuchico.edu", timezone_name="UTC")
    client.force_login(user)
    skill = Skill.objects.create(owner=user, name="Practice Spanish")
    today = date.today()
    SkillSchedule.objects.create(skill=skill, weekday=today.weekday())

    response = client.post(f"/skills/{skill.pk}/completion", {"completed_on": today.isoformat()})

    assert response.status_code == 302
    assert response.url == "/"
    assert Completion.objects.filter(skill=skill, completed_on=today).exists()


@pytest.mark.django_db
def test_completion_rejects_an_out_of_window_or_unscheduled_date(client) -> None:
    user = create_user("learner@csuchico.edu", timezone_name="UTC")
    client.force_login(user)
    skill = Skill.objects.create(owner=user, name="Practice Spanish")
    SkillSchedule.objects.create(skill=skill, weekday=date.today().weekday())

    response = client.post(f"/skills/{skill.pk}/completion", {"completed_on": "1900-01-01"})

    assert response.status_code == 400
    assert not Completion.objects.filter(skill=skill).exists()


@pytest.mark.django_db
def test_completion_requires_a_configured_timezone(client) -> None:
    user = create_user("learner@csuchico.edu", timezone_name=None)
    client.force_login(user)
    skill = Skill.objects.create(owner=user, name="Practice Spanish")
    today = date.today()
    SkillSchedule.objects.create(skill=skill, weekday=today.weekday())

    response = client.post(f"/skills/{skill.pk}/completion", {"completed_on": today.isoformat()})

    assert response.status_code == 400
    assert not Completion.objects.filter(skill=skill).exists()


@pytest.mark.django_db
def test_member_cannot_toggle_another_members_skill(client) -> None:
    owner = create_user("owner@csuchico.edu", timezone_name="UTC")
    attacker = create_user("attacker@csuchico.edu", timezone_name="UTC")
    skill = Skill.objects.create(owner=owner, name="Practice Spanish")
    SkillSchedule.objects.create(skill=skill, weekday=date.today().weekday())
    client.force_login(attacker)

    response = client.post(
        f"/skills/{skill.pk}/completion", {"completed_on": date.today().isoformat()}
    )

    assert response.status_code == 404
    assert not Completion.objects.filter(skill=skill).exists()


@pytest.mark.django_db
def test_state_changing_skill_request_requires_csrf() -> None:
    user = create_user("learner@csuchico.edu")
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(user)

    response = csrf_client.post("/skills/create", {"name": "Practice Spanish", "weekdays": ["0"]})

    assert response.status_code == 403
    assert not Skill.objects.filter(owner=user).exists()
