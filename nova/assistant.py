from __future__ import annotations

from datetime import datetime
from pathlib import Path

from nova.intents import Action, parse
from nova.macos import MacOSController
from nova.projects import ProjectRegistry
from nova.speech import Speaker
from nova.terminal import TerminalPolicy


HELP = (
    "Você pode dizer: abra o Safari, feche o Spotify, mostre o Finder, "
    "abra o Claude Code, pesquise na internet, inicie o projeto NOVA, "
    "execute no terminal git status, pesquise inteligência artificial no Codex, "
    "pergunte ao Codex, tire um print, "
    "volume 40, ou sair."
)


class NovaAssistant:
    def __init__(
        self, controller: MacOSController, speaker: Speaker, project_path: Path | None = None
    ) -> None:
        self.controller = controller
        self.speaker = speaker
        self.project_path = project_path or Path.cwd()
        self.projects: dict[str, dict[str, str]] = {}
        self.project_registry = ProjectRegistry({})
        self.pending_command: str | None = None

    def set_projects(
        self, projects: dict[str, dict[str, str]], roots: list[str] | None = None
    ) -> None:
        self.projects = projects
        self.project_registry = ProjectRegistry(projects, roots)

    def handle(self, command: str) -> bool:
        intent = parse(command)
        try:
            if intent.action is Action.OPEN_APP:
                response = self.controller.open_app(intent.target or "")
            elif intent.action is Action.OPEN_CLAUDE_CODE:
                response = self.controller.open_claude_code(self.project_path)
            elif intent.action is Action.OPEN_PROJECT_CLAUDE_CODE:
                response = self._open_project_in_claude_code(intent.target or "")
            elif intent.action is Action.OPEN_CLAUDE_PROJECT:
                response = self.controller.open_claude_project(intent.target or "")
            elif intent.action is Action.SEARCH_WEB:
                response = self.controller.search_web(intent.target or "")
            elif intent.action is Action.START_PROJECT:
                response = self._start_project(intent.target or "")
            elif intent.action is Action.RUN_TERMINAL:
                response = self._terminal_command(intent.target or "")
            elif intent.action is Action.SEND_TO_APP:
                app, prompt = (intent.target or "\n").split("\n", 1)
                response = self.controller.send_to_app(app, prompt)
            elif intent.action is Action.MUTE:
                response = self.controller.set_muted(True)
            elif intent.action is Action.UNMUTE:
                response = self.controller.set_muted(False)
            elif intent.action is Action.SCREENSHOT:
                response = self.controller.screenshot()
            elif intent.action is Action.CONFIRM:
                response = self._confirm_terminal()
            elif intent.action is Action.CANCEL:
                self.pending_command = None
                response = "Comando cancelado."
            elif intent.action is Action.CLOSE_APP:
                response = self.controller.close_app(intent.target or "")
            elif intent.action is Action.FOCUS_APP:
                response = self.controller.focus_app(intent.target or "")
            elif intent.action is Action.SET_VOLUME:
                response = self.controller.set_volume(intent.value or 0)
            elif intent.action is Action.TIME:
                response = f"Agora são {datetime.now():%H:%M}."
            elif intent.action is Action.HELP:
                response = HELP
            elif intent.action is Action.EXIT:
                self.speaker.say("Até logo.")
                return False
            else:
                response = "Ainda não entendi esse comando. Diga ajuda para ver exemplos."
        except (RuntimeError, OSError) as exc:
            response = str(exc)
        self.speaker.say(response)
        return True

    def _start_project(self, name: str) -> str:
        project = self.project_registry.find(name)
        if not project:
            return f"O projeto {name} ainda não está cadastrado."
        return self.controller.run_in_terminal(
            project.command, project.path
        )

    def _open_project_in_claude_code(self, name: str) -> str:
        project = self.project_registry.find(name)
        if not project:
            return f"O projeto {name} ainda não foi encontrado."
        return self.controller.open_claude_code(project.path)

    def _terminal_command(self, command: str) -> str:
        classification = TerminalPolicy.classify(command)
        if classification == "blocked":
            return "Bloqueei esse comando por segurança. Digite comandos destrutivos manualmente."
        if classification == "confirm":
            self.pending_command = command
            return f"O comando {command} precisa de confirmação. Diga confirmar ou cancelar."
        return self.controller.run_in_terminal(command, self.project_path)

    def _confirm_terminal(self) -> str:
        if not self.pending_command:
            return "Não há comando pendente."
        command = self.pending_command
        self.pending_command = None
        return self.controller.run_in_terminal(command, self.project_path)
