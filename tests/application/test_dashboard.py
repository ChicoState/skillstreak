"""Selected-skill dashboard behavior for registered team accounts."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from tracking.models import (
    DailyCompletion,
    Skill,
    SkillTag,
    Tag,
    TagAlias,
    UserSkill,
    UserSkillSchedule,
)


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        email="student@csuchico.edu", password="Secure skillstreak password 2026!"
    )


@pytest.fixture
def system_skill(db):
    return Skill.objects.create(
        slug="touch-grass",
        name="Touch Grass",
        description="Spend time outdoors.",
        visibility=Skill.Visibility.SYSTEM,
    )


@pytest.mark.django_db
def test_anonymous_dashboard_request_redirects_to_registered_member_sign_in(client) -> None:
    response = client.get(reverse("dashboard-preview"))
    assert response.status_code == 302
    assert response.url == "/sign-in?next=/"


@pytest.mark.django_db
def test_registered_member_can_select_and_complete_a_system_skill(
    client, user, system_skill
) -> None:
    client.force_login(user)
    selected = client.post(reverse("toggle-selection", args=[system_skill.id]))
    user_skill = UserSkill.objects.get(user=user, skill=system_skill)
    completed = client.post(reverse("toggle-completion", args=[user_skill.id]))

    assert selected.status_code == 302
    assert selected.url == f"/?skill={user_skill.id}"
    assert completed.status_code == 302
    assert completed.url == f"/?skill={user_skill.id}"
    assert DailyCompletion.objects.filter(
        user_skill=user_skill, completed_on=timezone.localdate()
    ).exists()
    dashboard = client.get(reverse("dashboard-preview"), {"skill": user_skill.id}).content.decode()
    assert user.email in dashboard
    assert "Touch Grass" in dashboard
    assert "Spend time outdoors." in dashboard
    assert '<span class="detail-label">Progress</span>' in dashboard
    assert "1 day completed this week" in dashboard
    assert "Your check-ins" in dashboard
    assert "Completion history" in dashboard
    assert "Completed today — undo" in dashboard


@pytest.mark.django_db
def test_skill_actions_are_isolated_to_the_signed_in_account(client, user, system_skill) -> None:
    other_user = get_user_model().objects.create_user(
        email="other@csuchico.edu", password="Secure skillstreak password 2026!"
    )
    other_selection = UserSkill.objects.create(
        user=other_user, skill=system_skill, started_on=timezone.localdate()
    )
    client.force_login(user)

    response = client.post(reverse("toggle-completion", args=[other_selection.id]))

    assert response.status_code == 404
    assert not DailyCompletion.objects.exists()


@pytest.mark.django_db
def test_only_active_system_skills_can_be_selected(client, user) -> None:
    private_skill = Skill.objects.create(
        slug="private-skill", name="Private Skill", visibility=Skill.Visibility.PRIVATE
    )
    client.force_login(user)

    response = client.post(reverse("toggle-selection", args=[private_skill.id]))

    assert response.status_code == 404
    assert not UserSkill.objects.exists()


@pytest.mark.django_db
def test_skill_library_can_filter_active_system_skills_by_name(client, user) -> None:
    matching_skill = Skill.objects.create(
        slug="read-fiction", name="Read Fiction", visibility=Skill.Visibility.SYSTEM
    )
    Skill.objects.create(slug="exercise", name="Exercise", visibility=Skill.Visibility.SYSTEM)
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"), {"view": "library", "q": "fiction"})

    assert response.status_code == 200
    assert list(response.context["library_results"]) == [matching_skill]
    assert 'value="fiction"' in response.content.decode()


@pytest.mark.django_db
def test_library_combines_owned_private_skills_and_hides_other_members_skills(client, user) -> None:
    own_skill = Skill.objects.create(
        slug="private-sketch",
        name="Sketch",
        description="Make a quick drawing.",
        visibility=Skill.Visibility.PRIVATE,
        created_by=user,
    )
    other_user = get_user_model().objects.create_user(
        email="other-library@csuchico.edu", password="Secure skillstreak password 2026!"
    )
    Skill.objects.create(
        slug="private-other",
        name="Other Member Skill",
        visibility=Skill.Visibility.PRIVATE,
        created_by=other_user,
    )
    Skill.objects.create(
        slug="read-fiction", name="Read Fiction", visibility=Skill.Visibility.SYSTEM
    )
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"), {"view": "library"})
    content = response.content.decode()

    assert response.status_code == 200
    assert own_skill.name in content
    assert content.count("data-library-item") == 2
    assert "My skill" in content
    assert "Other Member Skill" not in content


@pytest.mark.django_db
def test_library_keeps_all_authorized_skills_for_live_filtering(client, user) -> None:
    private_skill = Skill.objects.create(
        slug="private-oldest",
        name="Oldest personal skill",
        visibility=Skill.Visibility.PRIVATE,
        created_by=user,
    )
    system_skill = Skill.objects.create(
        slug="read-fiction", name="Read Fiction", visibility=Skill.Visibility.SYSTEM
    )
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"), {"view": "library", "q": "oldest"})

    assert list(response.context["library"]) == [private_skill, system_skill]
    assert list(response.context["library_results"]) == [private_skill]


@pytest.mark.django_db
def test_library_search_matches_descriptions_and_only_the_members_private_skills(
    client, user
) -> None:
    Skill.objects.create(
        slug="read-fiction",
        name="Read Fiction",
        description="Explore imaginative stories.",
        visibility=Skill.Visibility.SYSTEM,
    )
    Skill.objects.create(
        slug="private-sketch",
        name="Sketch",
        description="Practice imaginative drawing.",
        visibility=Skill.Visibility.PRIVATE,
        created_by=user,
    )
    other_user = get_user_model().objects.create_user(
        email="other-search@csuchico.edu", password="Secure skillstreak password 2026!"
    )
    Skill.objects.create(
        slug="private-other-search",
        name="Secret Skill",
        description="An imaginative private activity.",
        visibility=Skill.Visibility.PRIVATE,
        created_by=other_user,
    )
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"), {"view": "library", "q": "imaginative"})
    content = response.content.decode()

    assert "Read Fiction" in content
    assert "Sketch" in content
    assert "Secret Skill" not in content
    assert "2 skills found" in content


@pytest.mark.django_db
def test_library_search_and_tag_filter_match_a_tag_alias(client, user) -> None:
    pets = Tag.objects.create(slug="pets", name="Pets")
    TagAlias.objects.create(tag=pets, term="dog")
    pet_skill = Skill.objects.create(
        slug="care-for-a-pet", name="Care for a Pet", visibility=Skill.Visibility.SYSTEM
    )
    SkillTag.objects.create(skill=pet_skill, tag=pets)
    other_skill = Skill.objects.create(
        slug="take-a-walk", name="Take a Walk", visibility=Skill.Visibility.SYSTEM
    )
    client.force_login(user)

    response = client.get(
        reverse("dashboard-preview"), {"view": "library", "q": "dog", "tag": "pets"}
    )

    assert list(response.context["library_results"]) == [pet_skill]
    assert response.context["library_tag"] == "pets"
    assert other_skill not in response.context["library_results"]


@pytest.mark.django_db
def test_member_can_reactivate_their_private_skill_and_open_its_dashboard_tracker(
    client, user
) -> None:
    skill = Skill.objects.create(
        slug="private-sketch",
        name="Sketch",
        visibility=Skill.Visibility.PRIVATE,
        created_by=user,
    )
    user_skill = UserSkill.objects.create(
        user=user, skill=skill, started_on=timezone.localdate(), is_active=False
    )
    client.force_login(user)

    response = client.post(reverse("toggle-selection", args=[skill.id]), {"q": "sketch"})

    user_skill.refresh_from_db()
    assert response.status_code == 302
    assert response.url == f"/?skill={user_skill.id}"
    assert user_skill.is_active is True


@pytest.mark.django_db
def test_member_cannot_select_another_members_private_skill(client, user) -> None:
    owner = get_user_model().objects.create_user(
        email="private-owner@csuchico.edu", password="Secure skillstreak password 2026!"
    )
    skill = Skill.objects.create(
        slug="private-owner-skill",
        name="Owner skill",
        visibility=Skill.Visibility.PRIVATE,
        created_by=owner,
    )
    client.force_login(user)

    response = client.post(reverse("toggle-selection", args=[skill.id]))

    assert response.status_code == 404
    assert not UserSkill.objects.filter(user=user, skill=skill).exists()


def test_skill_actions_reject_requests_without_a_csrf_token() -> None:
    response = Client(enforce_csrf_checks=True).post(reverse("toggle-selection", args=[1]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_dashboard_card_does_not_expose_a_weekly_completed_value(
    client, user, system_skill
) -> None:
    UserSkill.objects.create(user=user, skill=system_skill, started_on=timezone.localdate())
    client.force_login(user)

    user_skill = UserSkill.objects.get(user=user, skill=system_skill)
    response = client.get(reverse("dashboard-preview"), {"skill": user_skill.id})

    assert "weekly_completed" not in response.context["selected_card"]
    assert response.context["selected_card"]["days"]


@pytest.mark.django_db
def test_dashboard_omits_the_secondary_line_when_a_skill_has_no_description(client, user) -> None:
    skill = Skill.objects.create(
        slug="private-no-description",
        name="Private Skill",
        visibility=Skill.Visibility.PRIVATE,
        created_by=user,
    )
    UserSkill.objects.create(user=user, skill=skill, started_on=timezone.localdate())
    client.force_login(user)

    user_skill = UserSkill.objects.get(user=user, skill=skill)
    response = client.get(reverse("dashboard-preview"), {"skill": user_skill.id})

    content = response.content.decode()
    assert "<h2>Private Skill</h2>" in content
    assert 'class="detail-description"' not in content


@pytest.mark.django_db
def test_dashboard_shows_only_the_requested_active_skill_and_lists_all_active_skills(
    client, user
) -> None:
    first_skill = Skill.objects.create(
        slug="first-skill", name="First skill", visibility=Skill.Visibility.SYSTEM
    )
    second_skill = Skill.objects.create(
        slug="second-skill", name="Second skill", visibility=Skill.Visibility.SYSTEM
    )
    first_user_skill = UserSkill.objects.create(
        user=user, skill=first_skill, started_on=timezone.localdate()
    )
    second_user_skill = UserSkill.objects.create(
        user=user, skill=second_skill, started_on=timezone.localdate()
    )
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"), {"skill": second_user_skill.id})
    content = response.content.decode()

    assert response.context["selected_card"]["user_skill"] == second_user_skill
    assert list(response.context["active_skills"]) == [first_user_skill, second_user_skill]
    assert content.count('class="skill-detail"') == 1
    assert f'href="/?skill={first_user_skill.id}#skills"' in content
    assert f'href="/?skill={second_user_skill.id}#skills"' in content
    assert "First skill" in content
    assert "Second skill" in content


@pytest.mark.django_db
@pytest.mark.parametrize("skill_parameter", ["not-a-number", "0"])
def test_dashboard_shows_the_landing_page_for_an_invalid_selection(
    client, user, skill_parameter
) -> None:
    skill = Skill.objects.create(slug="touch-grass", name="Touch Grass")
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=timezone.localdate())
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"), {"skill": skill_parameter})

    assert response.status_code == 200
    assert response.context["selected_card"] is None
    assert response.context["landing_cards"][0]["user_skill"] == user_skill


@pytest.mark.django_db
def test_dashboard_does_not_select_another_members_skill(client, user) -> None:
    own_skill = Skill.objects.create(slug="own-skill", name="Own skill")
    other_skill = Skill.objects.create(slug="other-skill", name="Other skill")
    own_user_skill = UserSkill.objects.create(
        user=user, skill=own_skill, started_on=timezone.localdate()
    )
    other_user = get_user_model().objects.create_user(
        email="selection-owner@csuchico.edu", password="Secure skillstreak password 2026!"
    )
    other_user_skill = UserSkill.objects.create(
        user=other_user, skill=other_skill, started_on=timezone.localdate()
    )
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"), {"skill": other_user_skill.id})

    assert response.context["selected_card"] is None
    assert response.context["landing_cards"][0]["user_skill"] == own_user_skill


@pytest.mark.django_db
def test_removing_the_selected_skill_falls_back_to_another_active_skill(client, user) -> None:
    first_skill = Skill.objects.create(slug="first-skill", name="First skill")
    second_skill = Skill.objects.create(slug="second-skill", name="Second skill")
    first_user_skill = UserSkill.objects.create(
        user=user, skill=first_skill, started_on=timezone.localdate()
    )
    second_user_skill = UserSkill.objects.create(
        user=user, skill=second_skill, started_on=timezone.localdate()
    )
    client.force_login(user)

    response = client.post(
        reverse("toggle-selection", args=[first_skill.id]), {"skill": first_user_skill.id}
    )

    assert response.url == "/"
    follow_up = client.get(response.url)
    assert follow_up.context["selected_card"] is None
    assert follow_up.context["landing_cards"][0]["user_skill"] == second_user_skill


@pytest.mark.django_db
def test_dashboard_landing_lists_all_active_skills_and_dashboard_link_returns_there(
    client, user
) -> None:
    first_skill = Skill.objects.create(slug="first-skill", name="First skill")
    second_skill = Skill.objects.create(slug="second-skill", name="Second skill")
    UserSkill.objects.create(user=user, skill=first_skill, started_on=timezone.localdate())
    UserSkill.objects.create(user=user, skill=second_skill, started_on=timezone.localdate())
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"))
    content = response.content.decode()

    assert response.context["selected_card"] is None
    assert [card["user_skill"].skill for card in response.context["landing_cards"]] == [
        first_skill,
        second_skill,
    ]
    assert 'href="/#skills"' in content
    assert content.count('class="landing-skill-card"') == 2


@pytest.mark.django_db
def test_dashboard_landing_can_toggle_only_its_own_skill_and_stay_on_the_landing_page(
    client, user
) -> None:
    skill = Skill.objects.create(slug="first-skill", name="First skill")
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=timezone.localdate())
    other_user = get_user_model().objects.create_user(
        email="other-landing@csuchico.edu", password="Secure skillstreak password 2026!"
    )
    other_user_skill = UserSkill.objects.create(
        user=other_user, skill=skill, started_on=timezone.localdate()
    )
    DailyCompletion.objects.create(user_skill=other_user_skill, completed_on=timezone.localdate())
    client.force_login(user)

    completed = client.post(
        reverse("toggle-completion", args=[user_skill.id]), {"return_view": "dashboard"}
    )

    assert completed.url == "/"
    assert DailyCompletion.objects.filter(
        user_skill=user_skill, completed_on=timezone.localdate()
    ).exists()
    assert DailyCompletion.objects.filter(
        user_skill=other_user_skill, completed_on=timezone.localdate()
    ).exists()

    undone = client.post(
        reverse("toggle-completion", args=[user_skill.id]), {"return_view": "dashboard"}
    )

    assert undone.url == "/"
    assert not DailyCompletion.objects.filter(
        user_skill=user_skill, completed_on=timezone.localdate()
    ).exists()
    assert DailyCompletion.objects.filter(
        user_skill=other_user_skill, completed_on=timezone.localdate()
    ).exists()


@pytest.mark.django_db
def test_skill_detail_shows_real_weekly_schedule_and_current_month_history(client, user) -> None:
    skill = Skill.objects.create(
        slug="practice-guitar",
        name="Practice guitar",
        visibility=Skill.Visibility.PRIVATE,
        created_by=user,
    )
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=timezone.localdate())
    UserSkillSchedule.objects.create(
        user_skill=user_skill,
        rule_type=UserSkillSchedule.RuleType.DAYS_PER_WEEK,
        effective_from=timezone.localdate(),
        target_days_per_week=3,
        week_starts_on=1,
    )
    DailyCompletion.objects.create(user_skill=user_skill, completed_on=timezone.localdate())
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"), {"skill": user_skill.id})
    content = response.content.decode()

    assert response.context["selected_card"]["frequency"] == "3 days per week"
    assert response.context["selected_card"]["deadline_label"] == "Weekly goal ends"
    assert len(response.context["selected_card"]["calendar_weeks"]) >= 4
    assert "3 days per week" in content
    assert "Weekly goal ends" in content
    assert "This month" in content


@pytest.mark.django_db
def test_library_tab_hides_tracker_content_and_marks_its_navigation_active(
    client, user, system_skill
) -> None:
    UserSkill.objects.create(user=user, skill=system_skill, started_on=timezone.localdate())
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"), {"view": "library"})
    content = response.content.decode()

    assert response.context["active_view"] == "library"
    assert response.context["selected_card"] is None
    assert 'class="nav-item active"' in content
    assert "Skill library" in content
    assert 'class="skill-card"' not in content


@pytest.mark.django_db
def test_invalid_dashboard_view_falls_back_to_dashboard(client, user, system_skill) -> None:
    user_skill = UserSkill.objects.create(
        user=user, skill=system_skill, started_on=timezone.localdate()
    )
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"), {"view": "unknown", "skill": user_skill.id})

    assert response.context["active_view"] == "dashboard"
    assert response.context["selected_card"]["user_skill"] == user_skill


@pytest.mark.django_db
def test_removing_a_skill_from_the_library_returns_to_the_library_tab(
    client, user, system_skill
) -> None:
    user_skill = UserSkill.objects.create(
        user=user, skill=system_skill, started_on=timezone.localdate()
    )
    client.force_login(user)

    response = client.post(
        reverse("toggle-selection", args=[system_skill.id]),
        {"return_view": "library", "q": "grass", "skill": user_skill.id},
    )

    assert response.url == "/?view=library&q=grass"
