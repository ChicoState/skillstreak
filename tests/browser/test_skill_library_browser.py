"""Browser coverage for searching, selecting, and completing a system skill."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright

from tracking.models import MissedSkillEpisode, Skill, UserPreference, UserSkill


@pytest.mark.django_db(transaction=True)
def test_member_can_find_select_and_complete_a_skill_in_the_browser(live_server) -> None:
    user = get_user_model().objects.create_user(
        email="browser-user@csuchico.edu",
        password="A safe browser test password 2026",
    )
    Skill.objects.create(
        slug="read-fiction",
        name="Read Fiction",
        description="Spend time reading fiction.",
        visibility=Skill.Visibility.SYSTEM,
    )
    Skill.objects.create(slug="exercise", name="Exercise", visibility=Skill.Visibility.SYSTEM)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server.url}/sign-in")
        page.get_by_label("Email").fill(user.email)
        page.get_by_label("Password").fill("A safe browser test password 2026")
        page.get_by_role("button", name="Sign in").click()

        page.get_by_label("Find a skill").fill("fiction")
        page.get_by_role("button", name="Search").click()
        expect(page.get_by_role("heading", name="Read Fiction")).to_be_visible()
        expect(page.get_by_role("heading", name="Exercise")).not_to_be_visible()

        page.locator(".library-card", has_text="Read Fiction").get_by_role(
            "button", name="Add skill"
        ).click()
        card = page.locator(".skill-card", has_text="Read Fiction")
        card.get_by_role("button", name="Mark complete today").click()
        page.reload()
        expect(card.get_by_role("button", name="Completed today — undo")).to_be_visible()
        browser.close()


@pytest.mark.django_db(transaction=True)
def test_member_can_see_a_missed_indicator_on_an_active_skill_in_the_browser(live_server) -> None:
    user = get_user_model().objects.create_user(
        email="missed-browser-user@csuchico.edu",
        password="A safe browser test password 2026",
    )
    skill = Skill.objects.create(
        slug="missed-browser-skill",
        name="Missed browser skill",
        visibility=Skill.Visibility.SYSTEM,
    )
    user_skill = UserSkill.objects.create(
        user=user,
        skill=skill,
        started_on=timezone.localdate(),
    )
    UserPreference.objects.create(user=user, reminders_enabled=True)
    MissedSkillEpisode.objects.create(
        user_skill=user_skill,
        first_missed_on=timezone.localdate() - timedelta(days=1),
        last_missed_on=timezone.localdate() - timedelta(days=1),
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server.url}/sign-in")
        page.get_by_label("Email").fill(user.email)
        page.get_by_label("Password").fill("A safe browser test password 2026")
        page.get_by_role("button", name="Sign in").click()

        card = page.locator(".skill-card", has_text="Missed browser skill")
        expect(card.get_by_role("img", name="Missed scheduled skill")).to_be_visible()
        expect(card.locator(".skill-icon.missed")).to_have_text("!")
        card.get_by_role("button", name="Mark complete today").click()
        expect(card.get_by_role("img", name="Missed scheduled skill")).not_to_be_visible()
        browser.close()


@pytest.mark.django_db(transaction=True)
def test_member_can_dismiss_the_profile_missed_skills_digest_in_the_browser(live_server) -> None:
    user = get_user_model().objects.create_user(
        email="digest-browser-user@csuchico.edu",
        password="A safe browser test password 2026",
    )
    skill = Skill.objects.create(
        slug="digest-browser-skill",
        name="Digest browser skill",
        visibility=Skill.Visibility.SYSTEM,
    )
    user_skill = UserSkill.objects.create(
        user=user,
        skill=skill,
        started_on=timezone.localdate(),
    )
    UserPreference.objects.create(user=user, reminders_enabled=True)
    MissedSkillEpisode.objects.create(
        user_skill=user_skill,
        first_missed_on=timezone.localdate() - timedelta(days=1),
        last_missed_on=timezone.localdate() - timedelta(days=1),
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server.url}/sign-in")
        page.get_by_label("Email").fill(user.email)
        page.get_by_label("Password").fill("A safe browser test password 2026")
        page.get_by_role("button", name="Sign in").click()
        page.locator("summary.profile").click()
        page.get_by_role("link", name="Profile & settings").click()

        expect(page.get_by_role("heading", name="Missed skills")).to_be_visible()
        expect(page.get_by_text("Digest browser skill")).to_be_visible()
        page.get_by_role("button", name="Dismiss reminder").click()
        expect(page.get_by_role("heading", name="Missed skills")).not_to_be_visible()
        page.goto(f"{live_server.url}/")
        expect(page.get_by_role("img", name="Missed scheduled skill")).to_be_visible()
        browser.close()
