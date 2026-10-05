"""Tests for the fixed-demo dashboard sign-in."""

from django.test import Client, override_settings


def test_home_page_shows_a_sign_in_prompt_when_session_is_not_authenticated(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Welcome to SkillStreak" in response.content.decode()
    assert "Sign in" in response.content.decode()
    assert "Your skills" not in response.content.decode()


@override_settings(
    DEMO_LOGIN_EMAIL="demo@skillstreak.test", DEMO_LOGIN_PASSWORD="test-demo-password"
)
def test_valid_demo_credentials_create_a_session_and_show_the_dashboard(client) -> None:
    response = client.post(
        "/sign-in",
        {"email": "demo@skillstreak.test", "password": "test-demo-password"},
    )

    assert response.status_code == 302
    assert response.url == "/"

    dashboard_response = client.get("/")

    assert "Your skills" in dashboard_response.content.decode()
    assert "Welcome to SkillStreak" not in dashboard_response.content.decode()


@override_settings(
    DEMO_LOGIN_EMAIL="demo@skillstreak.test", DEMO_LOGIN_PASSWORD="test-demo-password"
)
def test_invalid_demo_credentials_remain_blocked_with_a_generic_error(client) -> None:
    response = client.post(
        "/sign-in",
        {"email": "demo@skillstreak.test", "password": "wrong-password"},
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert "The email or password is incorrect." in content
    assert "Your skills" not in content
    assert "demo@skillstreak.test" not in content


def test_sign_in_rejects_a_request_without_a_csrf_token() -> None:
    csrf_client = Client(enforce_csrf_checks=True)

    response = csrf_client.post("/sign-in", {"email": "any", "password": "value"})

    assert response.status_code == 403


@override_settings(
    DEMO_LOGIN_EMAIL="demo@skillstreak.test", DEMO_LOGIN_PASSWORD="test-demo-password"
)
def test_logout_clears_the_demo_session(client) -> None:
    client.post(
        "/sign-in",
        {"email": "demo@skillstreak.test", "password": "test-demo-password"},
    )
    response = client.post("/logout")

    assert response.status_code == 302
    assert response.url == "/"
    assert "Welcome to SkillStreak" in client.get("/").content.decode()
