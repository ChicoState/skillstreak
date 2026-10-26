"""Browser coverage for searching, selecting, and completing a system skill."""

import re
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright

from tracking.models import (
    MissedSkillEpisode,
    Skill,
    SkillTag,
    Tag,
    TagAlias,
    UserPreference,
    UserSkill,
)


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
    pets = Tag.objects.create(slug="pets", name="Pets")
    TagAlias.objects.create(tag=pets, term="dog")
    pet_skill = Skill.objects.create(
        slug="care-for-a-pet", name="Care for a Pet", visibility=Skill.Visibility.SYSTEM
    )
    SkillTag.objects.create(skill=pet_skill, tag=pets)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server.url}/sign-in")
        page.get_by_label("Email").fill(user.email)
        page.get_by_label("Password").fill("A safe browser test password 2026")
        page.get_by_role("button", name="Sign in").click()
        page.get_by_role("link", name="Skill library").click()

        page.get_by_label("Tag").select_option("pets")
        expect(page.get_by_role("heading", name="Care for a Pet")).to_be_visible()
        expect(page).to_have_url(f"{live_server.url}/?view=library&tag=pets")

        page.get_by_label("Tag").select_option("")
        page.get_by_label("Find a skill").fill("fiction")
        expect(page.get_by_role("heading", name="Read Fiction")).to_be_visible()
        expect(page.get_by_role("heading", name="Exercise")).not_to_be_visible()
        expect(page.get_by_role("status")).to_have_text("1 skill found for “fiction”.")
        expect(page).to_have_url(f"{live_server.url}/?view=library&q=fiction")

        page.locator(".library-card", has_text="Read Fiction").get_by_role(
            "button", name="Add skill"
        ).click()
        expect(page).to_have_url(re.compile(rf"{re.escape(live_server.url)}/\?skill=\d+$"))
        card = page.locator(".skill-detail", has_text="Read Fiction")
        card.get_by_role("button", name="Mark complete today").click()
        expect(page).to_have_url(re.compile(rf"{re.escape(live_server.url)}/\?skill=\d+$"))
        page.reload()
        expect(card.get_by_role("button", name="Completed today — undo")).to_be_visible()
        browser.close()


@pytest.mark.django_db(transaction=True)
def test_skill_library_shows_all_skills_and_live_search_filters_them(
    live_server,
) -> None:
    user = get_user_model().objects.create_user(
        email="compact-library@csuchico.edu",
        password="A safe browser test password 2026",
    )
    for index in range(20):
        Skill.objects.create(
            slug=f"private-library-{index}",
            name=f"Personal skill {index}",
            visibility=Skill.Visibility.PRIVATE,
            created_by=user,
        )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server.url}/sign-in")
        page.get_by_label("Email").fill(user.email)
        page.get_by_label("Password").fill("A safe browser test password 2026")
        page.get_by_role("button", name="Sign in").click()
        page.get_by_role("link", name="Skill library").click()

        library = page.locator("[data-library-browser]")
        expect(library.locator("[data-library-item]:visible")).to_have_count(20)
        expect(page.get_by_role("button", name="Show all 20 skills")).not_to_be_visible()

        page.get_by_label("Find a skill").fill("Personal skill 0")
        expect(page.get_by_role("heading", name="Personal skill 0")).to_be_visible()
        expect(library.locator("[data-library-item]:visible")).to_have_count(1)
        browser.close()


@pytest.mark.django_db(transaction=True)
def test_member_can_choose_one_tracker_from_the_dashboard_sidebar(live_server) -> None:
    user = get_user_model().objects.create_user(
        email="sidebar-user@csuchico.edu",
        password="A safe browser test password 2026",
    )
    first_skill = Skill.objects.create(
        slug="read-fiction", name="Read Fiction", visibility=Skill.Visibility.SYSTEM
    )
    second_skill = Skill.objects.create(
        slug="take-a-walk", name="Take a Walk", visibility=Skill.Visibility.SYSTEM
    )
    UserSkill.objects.create(user=user, skill=first_skill, started_on=timezone.localdate())
    second_user_skill = UserSkill.objects.create(
        user=user, skill=second_skill, started_on=timezone.localdate()
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server.url}/sign-in")
        page.get_by_label("Email").fill(user.email)
        page.get_by_label("Password").fill("A safe browser test password 2026")
        page.get_by_role("button", name="Sign in").click()

        expect(page.locator(".landing-skill-card")).to_have_count(2)
        walk_card = page.locator(".landing-skill-card", has_text="Take a Walk")
        walk_card.get_by_role("button", name="Mark Take a Walk complete today").click()
        expect(page).to_have_url(f"{live_server.url}/")
        expect(
            walk_card.get_by_role("button", name="Undo Take a Walk completion for today")
        ).to_be_visible()
        walk_card.get_by_role("button", name="Undo Take a Walk completion for today").click()
        expect(page).to_have_url(f"{live_server.url}/")
        expect(
            walk_card.get_by_role("button", name="Mark Take a Walk complete today")
        ).to_be_visible()

        page.get_by_role("link", name="Take a Walk").click()

        expect(page).to_have_url(f"{live_server.url}/?skill={second_user_skill.id}#skills")
        expect(page.locator(".skill-detail")).to_have_count(1)
        expect(page.locator(".skill-detail")).to_contain_text("Take a Walk")
        page.get_by_role("link", name="Dashboard", exact=True).click()
        expect(page).to_have_url(f"{live_server.url}/#skills")
        expect(page.locator(".landing-skill-card")).to_have_count(2)
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

        card = page.locator(".landing-skill-card", has_text="Missed browser skill")
        expect(card.get_by_role("img", name="Missed scheduled skill")).to_be_visible()
        expect(card.locator(".skill-reminder-icon")).to_have_text("!")
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
