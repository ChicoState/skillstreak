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
