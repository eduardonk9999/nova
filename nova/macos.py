from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import quote_plus


class MacOSController:
    def __init__(self, aliases: dict[str, str]) -> None:
        self.aliases = aliases

    def app_name(self, spoken_name: str) -> str:
        return self.aliases.get(spoken_name, spoken_name)

    def open_app(self, spoken_name: str) -> str:
        app = self.app_name(spoken_name)
        result = subprocess.run(
            ["open", "-a", app], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise RuntimeError(f"Não encontrei o aplicativo {app}.")
        return f"Abrindo {app}."

    def close_app(self, spoken_name: str) -> str:
        app = self.app_name(spoken_name)
        script = 'on run argv\ntell application (item 1 of argv) to quit\nend run'
        self._applescript(script, app)
        return f"Fechando {app}."

    def focus_app(self, spoken_name: str) -> str:
        app = self.app_name(spoken_name)
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

    def send_to_app(self, spoken_app: str, prompt: str) -> str:
        app = self.app_name(spoken_app)
        script = """on run argv
set appName to item 1 of argv
set promptText to item 2 of argv
tell application appName to activate
delay 0.5
tell application "System Events"
    keystroke promptText
    key code 36
end tell
end run"""
        self._applescript(script, app, prompt)
        return f"Enviei a solicitação para {app}."

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
