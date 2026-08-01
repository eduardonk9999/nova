import json

from nova.projects import ProjectRegistry


def test_detects_npm_dev_project(tmp_path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"dev": "vite"}}), encoding="utf-8"
    )
    assert ProjectRegistry.detect_command(tmp_path) == "npm run dev"


def test_detects_django_project(tmp_path) -> None:
    (tmp_path / "manage.py").touch()
    assert ProjectRegistry.detect_command(tmp_path) == "python3 manage.py runserver"


def test_configured_project_wins(tmp_path) -> None:
    registry = ProjectRegistry({"meu app": {"path": str(tmp_path), "command": "make dev"}})
    project = registry.find("meu app")
    assert project is not None
    assert project.command == "make dev"
