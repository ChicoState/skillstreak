import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_python_tooling_configuration_loads() -> None:
    with (ROOT / "pyproject.toml").open("rb") as configuration:
        parsed = tomllib.load(configuration)

    assert "ruff" in parsed["tool"]
    assert "pytest" in parsed["tool"]
    assert "coverage" in parsed["tool"]


def test_required_infrastructure_files_are_present() -> None:
    required_files = (
        ".dockerignore",
        ".env.example",
        ".gitleaks.toml",
        "Dockerfile",
        "compose.yml",
        "requirements.in",
        "requirements.txt",
    )

    assert all((ROOT / path).is_file() for path in required_files)


def test_compose_exposes_the_web_service_without_exposing_postgresql() -> None:
    configuration = (ROOT / "compose.yml").read_text()

    assert '      - "${APP_PORT:-8000}:8000"' in configuration
    assert "internal: true" not in configuration
    assert '      - "5432:5432"' not in configuration


def test_pull_request_quality_job_has_a_postgresql_service_for_django() -> None:
    workflow = (ROOT / ".github/workflows/pr-checks.yml").read_text()

    assert "name: Python quality and infrastructure harness" in workflow
    assert "postgres:17.7-bookworm" in workflow
    assert (
        "DATABASE_URL: postgresql://skillstreak:ci-test-password@localhost:5432/skillstreak"
        in workflow
    )
    assert "DJANGO_SETTINGS_MODULE: skillstreak.settings.production" in workflow
