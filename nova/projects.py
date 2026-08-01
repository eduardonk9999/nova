from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Project:
    name: str
    path: Path
    command: str


class ProjectRegistry:
    IGNORED = {".git", ".venv", "node_modules", "vendor", "dist", "build"}

    def __init__(self, configured: dict, roots: list[str] | None = None) -> None:
        self.configured = configured
        self.roots = [Path(root).expanduser() for root in (roots or [])]

    def find(self, spoken_name: str) -> Project | None:
        entry = self.configured.get(spoken_name)
        if entry:
            path = Path(entry["path"]).expanduser()
            command = entry.get("command") or self.detect_command(path)
            return Project(spoken_name, path, command)

        wanted = self._key(spoken_name)
        for root in self.roots:
            for path in self._project_directories(root, max_depth=3):
                if self._key(path.name) == wanted:
                    return Project(path.name, path, self.detect_command(path))
        return None

    @classmethod
    def detect_command(cls, path: Path) -> str:
        package_file = path / "package.json"
        if package_file.exists():
            try:
                scripts = json.loads(package_file.read_text(encoding="utf-8")).get("scripts", {})
                package_manager = "pnpm" if (path / "pnpm-lock.yaml").exists() else "npm"
                if "dev" in scripts:
                    return f"{package_manager} run dev"
                if "start" in scripts:
                    return f"{package_manager} start"
            except (OSError, json.JSONDecodeError):
                pass
        if (path / "manage.py").exists():
            return "python3 manage.py runserver"
        if (path / "docker-compose.yml").exists() or (path / "compose.yml").exists():
            return "docker compose up"
        return "code ."

    @classmethod
    def _project_directories(cls, root: Path, max_depth: int):
        if not root.is_dir():
            return
        root_depth = len(root.parts)
        markers = {".git", "package.json", "pyproject.toml", "composer.json", "Cargo.toml"}
        for current, directories, files in os.walk(root):
            path = Path(current)
            depth = len(path.parts) - root_depth
            directories[:] = [item for item in directories if item not in cls.IGNORED]
            if depth > max_depth:
                directories[:] = []
                continue
            if markers.intersection(set(files) | set(directories)):
                yield path
                directories[:] = []

    @staticmethod
    def _key(value: str) -> str:
        return "".join(character for character in value.lower() if character.isalnum())

