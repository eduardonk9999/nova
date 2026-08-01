from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import quote_plus


class MacOSController:
    PROCESS_NAMES = {
        "Codex": "ChatGPT",
        "Claude": "Claude",
    }

    def __init__(self, aliases: dict[str, str]) -> None:
        self.aliases = aliases

    def app_name(self, spoken_name: str) -> str:
        return self.aliases.get(spoken_name, spoken_name)

    def open_app(self, spoken_name: str) -> str:
        app = self.app_name(spoken_name)
        self._ensure_app(app)
        result = subprocess.run(
            ["open", "-a", app], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise RuntimeError(f"Não encontrei o aplicativo {app}.")
        return f"Abrindo {app}."

    def close_app(self, spoken_name: str) -> str:
        app = self.app_name(spoken_name)
        self._ensure_app(app)
        script = 'on run argv\ntell application (item 1 of argv) to quit\nend run'
        self._applescript(script, app)
        return f"Fechando {app}."

    def focus_app(self, spoken_name: str) -> str:
        app = self.app_name(spoken_name)
        self._ensure_app(app)
        script = 'on run argv\ntell application (item 1 of argv) to activate\nend run'
        self._applescript(script, app)
        return f"Mostrando {app}."

    def set_volume(self, value: int) -> str:
        self._applescript(f"set volume output muted false\nset volume output volume {value}")
        return f"Volume ajustado para {value} por cento."

    def set_muted(self, muted: bool) -> str:
        self._applescript(f"set volume output muted {str(muted).lower()}")
        return "Som desativado." if muted else "Som ativado."

    def screenshot(self) -> str:
        destination = Path.home() / "Desktop" / "NOVA-captura.png"
        result = subprocess.run(
            ["screencapture", "-x", str(destination)], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise RuntimeError("Não consegui capturar a tela.")
        return "Captura de tela salva na Mesa."

    def open_claude_code(self, project_path: Path) -> str:
        script = """on run argv
set projectPath to item 1 of argv
tell application "Terminal"
    activate
    do script "cd " & quoted form of projectPath & " && /opt/homebrew/bin/claude"
end tell
end run"""
        self._applescript(script, str(project_path))
        return "Abrindo o Claude Code no Terminal."

    def open_claude_project(self, project_name: str) -> str:
        """Abre um Project pelo nome usando a árvore de Acessibilidade do Claude."""
        self._ensure_app("Claude")
        self._ensure_accessibility()
        script = """on run argv
set projectName to item 1 of argv
tell application "Claude" to activate
delay 1
tell application "System Events"
    tell process "Claude"
        set frontmost to true
        try
            set allItems to entire contents of window 1
            repeat with currentItem in allItems
                try
                    set itemName to name of currentItem as text
                    ignoring case
                        if itemName contains projectName then
                            perform action "AXPress" of currentItem
                            return "opened"
                        end if
                    end ignoring
                end try
            end repeat
        end try
    end tell
end tell
return "not-found"
end run"""
        result = subprocess.run(
            ["osascript", "-e", script, project_name],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            if "not allowed assistive access" in result.stderr.lower() or "-1719" in result.stderr:
                raise RuntimeError(
                    "O Claude foi aberto, mas preciso de permissão de Acessibilidade para clicar no projeto."
                )
            raise RuntimeError(result.stderr.strip() or "Não consegui controlar o Claude.")
        if result.stdout.strip() != "opened":
            return f"Abri o Claude, mas não encontrei o projeto {project_name} na tela atual."
        return f"Abrindo o projeto {project_name} no aplicativo Claude."

    def search_web(self, query: str) -> str:
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        result = subprocess.run(["open", url], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise RuntimeError("Não consegui abrir a pesquisa no navegador.")
        return f"Pesquisando por {query}."

    def run_in_terminal(self, command: str, working_directory: Path) -> str:
        script = """on run argv
set projectPath to item 1 of argv
set terminalCommand to item 2 of argv
tell application "Terminal"
    activate
    do script "cd " & quoted form of projectPath & " && " & terminalCommand
end tell
end run"""
        self._applescript(script, str(working_directory), command)
        return f"Executando no Terminal: {command}."

    def send_to_app(
        self, spoken_app: str, prompt: str, new_conversation: bool = False
    ) -> str:
        app = self.app_name(spoken_app)
        process_name = self.PROCESS_NAMES.get(app, app)
        self._ensure_app(app)
        self._ensure_accessibility()
        launch = subprocess.run(
            ["open", "-a", app], capture_output=True, text=True, timeout=10
        )
        if launch.returncode != 0:
            raise RuntimeError(f"Não consegui abrir {app}.")
        script = """on run argv
set appName to item 1 of argv
set promptText to item 2 of argv
set processName to item 3 of argv
set startNewConversation to (item 4 of argv is "true")
set previousClipboard to the clipboard
try
    set the clipboard to promptText
    tell application "System Events"
        repeat 20 times
            if exists process processName then exit repeat
            delay 0.25
        end repeat
        if not (exists process processName) then error "Processo do aplicativo não iniciou."
        tell process processName
            set frontmost to true
            delay 0.5
            if startNewConversation then
                keystroke "n" using command down
                delay 0.7
            end if
            keystroke "v" using command down
            key code 36
        end tell
    end tell
    delay 0.2
    set the clipboard to previousClipboard
on error errorMessage number errorNumber
    set the clipboard to previousClipboard
    error errorMessage number errorNumber
end try
end run"""
        self._applescript(
            script, app, prompt, process_name, str(new_conversation).lower()
        )
        return f"Enviei a solicitação para {app}."

    def create_codex_project(self, project_name: str) -> str:
        prompt = (
            f"Quero iniciar um novo projeto chamado {project_name}. "
            "Comece perguntando objetivo, stack, requisitos e diretório desejado. "
            "Não crie nem altere arquivos até eu confirmar o planejamento."
        )
        self.send_to_app("codex", prompt, new_conversation=True)
        return f"Iniciei uma nova tarefa no Codex para o projeto {project_name}."

    @staticmethod
    def _ensure_app(app: str) -> None:
        result = subprocess.run(
            ["open", "-Ra", app], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise RuntimeError(f"Não encontrei o aplicativo {app} instalado no macOS.")

    @staticmethod
    def _ensure_accessibility() -> None:
        result = subprocess.run(
            [
                "osascript", "-e",
                'tell application "System Events" to return UI elements enabled',
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0 or result.stdout.strip().lower() != "true":
            raise RuntimeError(
                "Permita Acessibilidade para o Terminal/Codex em Ajustes do Sistema, "
                "Privacidade e Segurança, Acessibilidade."
            )

    @staticmethod
    def _applescript(script: str, *args: str) -> None:
        result = subprocess.run(
            ["osascript", "-e", script, *args],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or "Falha ao controlar o macOS."
            raise RuntimeError(detail)
