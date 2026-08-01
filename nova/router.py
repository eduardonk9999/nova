from __future__ import annotations

import re
from dataclasses import dataclass

from nova.intents import Action, Intent, normalize, parse


@dataclass(frozen=True)
class Route:
    intent: Intent
    understood_text: str
    corrected: bool = False


class IntentRouter:
    """Aplica variações naturais antes do parser determinístico e seguro."""

    REWRITES = (
        # Fallback observado quando o antigo prompt do Whisper confundiu
        # "crie um" com "H2O" antes de "novo projeto".
        (r"^h2o novo projeto ", "crie um novo projeto "),
        (r"^(?:faca|faz) uma pesquisa(?: na internet)? sobre ", "pesquise "),
        (r"^quero que (?:voce )?(?:pesquise|busque) ", "pesquise "),
        (r"^(?:me diga|me fala|diga) que horas sao(?: agora)?$", "que horas sao"),
        (r"^qual e a hora(?: agora)?$", "que horas sao"),
        (r"^abre (?:o |a )?", "abra "),
        (r"^fecha (?:o |a )?", "feche "),
        (r"^vai para (?:o |a )?", "mostre "),
    )

    def __init__(self, wake_word: str = "nova") -> None:
        self.wake_word = wake_word

    def route(self, text: str) -> Route:
        direct = parse(text, self.wake_word)
        if direct.action is not Action.UNKNOWN:
            return Route(direct, text)

        command = normalize(text)
        prefix = f"{self.wake_word} "
        had_wake_word = command.startswith(prefix)
        if had_wake_word:
            command = command[len(prefix) :]

        rewritten = command
        for pattern, replacement in self.REWRITES:
            rewritten = re.sub(pattern, replacement, rewritten)
        if rewritten == command:
            return Route(direct, text)

        candidate = f"{self.wake_word} {rewritten}" if had_wake_word else rewritten
        intent = parse(candidate, self.wake_word)
        return Route(intent, candidate, corrected=intent.action is not Action.UNKNOWN)
