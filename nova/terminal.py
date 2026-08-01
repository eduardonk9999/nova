from __future__ import annotations

import re
import shlex


class TerminalPolicy:
    """Classifica comandos de voz antes que cheguem ao Terminal."""

    BLOCKED_PROGRAMS = {
        "rm", "rmdir", "sudo", "su", "shutdown", "reboot", "halt",
        "diskutil", "dd", "mkfs", "kill", "killall", "chmod", "chown",
    }
    SAFE_PATTERNS = (
        r"pwd$", r"ls(?:\s|$)", r"git status$", r"git log(?:\s|$)",
        r"git diff(?:\s|$)", r"pytest(?:\s|$)", r"python(?:3)? -m pytest(?:\s|$)",
        r"npm (?:run|test)(?:\s|$)", r"pnpm (?:run|test)(?:\s|$)",
        r"yarn (?:run|test)(?:\s|$)", r"docker ps(?:\s|$)",
    )

    @classmethod
    def classify(cls, command: str) -> str:
        if any(token in command for token in (";", "&&", "||", "`", "$(`", ">", "<")):
            return "blocked"
        try:
            parts = shlex.split(command)
        except ValueError:
            return "blocked"
        if not parts or parts[0] in cls.BLOCKED_PROGRAMS or ".." in parts:
            return "blocked"
        if any(re.match(pattern, command) for pattern in cls.SAFE_PATTERNS):
            return "safe"
        return "confirm"

