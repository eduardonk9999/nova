from __future__ import annotations

from datetime import datetime
from pathlib import Path
from time import monotonic

from nova.intents import Action, contains_stop_command, has_wake_word, parse
from nova.macos import MacOSController
from nova.context import ConversationContext
from nova.projects import ProjectRegistry
from nova.router import IntentRouter
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
        self,
        controller: MacOSController,
        speaker: Speaker,
        project_path: Path | None = None,
        wake_word: str = "nova",
        dialog_window_seconds: float = 8.0,
    ) -> None:
        self.controller = controller
        self.speaker = speaker
        self.project_path = project_path or Path.cwd()
        self.projects: dict[str, dict[str, str]] = {}
        self.project_registry = ProjectRegistry({})
        self.pending_command: str | None = None
        self.pending_voice_command: str | None = None
        self.wake_word = wake_word
        self.minimum_confidence = 0.55
        self.router = IntentRouter(wake_word)
        self.context = ConversationContext()
        self.dialog_window_seconds = dialog_window_seconds
        self.awake_until = 0.0

    def set_projects(
        self, projects: dict[str, dict[str, str]], roots: list[str] | None = None
    ) -> None:
        self.projects = projects
        self.project_registry = ProjectRegistry(projects, roots)

    def handle(
        self,
        command: str,
        require_wake_word: bool = False,
        confidence: float | None = None,
    ) -> bool:
        if contains_stop_command(command, self.wake_word):
            self.speaker.stop()
            print("NOVA: escuta encerrada.")
            return False
        wake_word_present = has_wake_word(command, self.wake_word)
        if require_wake_word and not wake_word_present:
            if monotonic() > self.awake_until:
                print(f"Ignorado sem palavra de ativação: {command}")
                return True
            # A janela aberta por "NOVA" vale para apenas um comando.
            self.awake_until = 0.0
        contextual_intent = self.context.resolve(command, self.wake_word)
        route = self.router.route(command)
        intent = contextual_intent or route.intent
        if intent.action is Action.CONFIRM and self.pending_voice_command:
            pending = self.pending_voice_command
            self.pending_voice_command = None
            return self.handle(pending, require_wake_word=False, confidence=1.0)
        low_risk = {
            Action.WAKE, Action.TIME, Action.HELP, Action.GREETING, Action.THANKS,
            Action.STATUS, Action.STOP_SILENT, Action.EXIT, Action.UNKNOWN,
        }
        if (
            confidence is not None
            and confidence < self.minimum_confidence
            and intent.action not in low_risk
        ):
            self.pending_voice_command = command
            self.speaker.say(
                f"Não tenho certeza se entendi: {command}. Diga NOVA confirmar ou NOVA cancelar."
            )
            return True
        try:
            if intent.action is Action.OPEN_APP:
                response = self.controller.open_app(intent.target or "")
            elif intent.action is Action.OPEN_CLAUDE_CODE:
                response = self.controller.open_claude_code(self.project_path)
            elif intent.action is Action.OPEN_PROJECT_CLAUDE_CODE:
                response = self._open_project_in_claude_code(intent.target or "")
            elif intent.action is Action.OPEN_CLAUDE_PROJECT:
                response = self.controller.open_claude_project(intent.target or "")
            elif intent.action is Action.CREATE_CODEX_PROJECT:
                response = self.controller.create_codex_project(intent.target or "")
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
                self.pending_voice_command = None
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
            elif intent.action is Action.WAKE:
                response = "Pois não?"
                self.context.remember(intent, response)
                # Espera a confirmação terminar para não capturar a própria voz
                # como o comando que virá dentro da janela de diálogo.
                self.speaker.say(response, wait=True)
                # A contagem começa depois que a resposta terminou de tocar.
                self.awake_until = monotonic() + self.dialog_window_seconds
                return True
            elif intent.action is Action.GREETING:
                response = "Olá. Como posso ajudar?"
            elif intent.action is Action.THANKS:
                response = "Por nada."
            elif intent.action is Action.STATUS:
                response = "Estou aqui e ouvindo."
            elif intent.action is Action.REPEAT:
                response = self.context.last_response or "Ainda não há uma resposta para repetir."
            elif intent.action is Action.EXIT:
                self.speaker.say("Até logo.")
                return False
            elif intent.action is Action.STOP_SILENT:
                self.speaker.stop()
                print("NOVA: escuta encerrada.")
                return False
            else:
                response = "Ainda não entendi esse comando. Diga ajuda para ver exemplos."
        except (RuntimeError, OSError) as exc:
            response = str(exc)
        self.context.remember(intent, response)
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
