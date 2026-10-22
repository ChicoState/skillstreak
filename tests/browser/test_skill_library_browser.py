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
