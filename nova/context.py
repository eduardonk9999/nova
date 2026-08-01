from __future__ import annotations

from dataclasses import dataclass

from nova.intents import Action, Intent, normalize


@dataclass
class ConversationContext:
    last_action: Action | None = None
    last_query: str | None = None
    last_provider: str | None = None
    last_response: str | None = None

    def resolve(self, command: str, wake_word: str = "nova") -> Intent | None:
        text = normalize(command)
        if text.startswith(f"{wake_word} "):
            text = text[len(wake_word) + 1 :]

        if text in {"repita", "repete", "diga novamente"}:
            return Intent(Action.REPEAT)

        if text in {"agora no codex", "mande isso para o codex"} and self.last_query:
            prompt = self._research_prompt(self.last_query)
            return Intent(Action.SEND_TO_APP, target=f"codex\n{prompt}")

        if text in {"agora no claude", "mande isso para o claude"} and self.last_query:
            prompt = self._research_prompt(self.last_query)
            return Intent(Action.SEND_TO_APP, target=f"claude\n{prompt}")

        if text in {"pesquise mais sobre isso", "aprofunde isso", "continue a pesquisa"}:
            if not self.last_query:
                return None
            provider = self.last_provider or "codex"
            prompt = (
                f"Aprofunde a pesquisa sobre {self.last_query}. Compare perspectivas e cite fontes."
            )
            return Intent(Action.SEND_TO_APP, target=f"{provider}\n{prompt}")
        return None

    def remember(self, intent: Intent, response: str | None = None) -> None:
        self.last_action = intent.action
        if response:
            self.last_response = response
        if intent.action is Action.SEARCH_WEB and intent.target:
            self.last_query = intent.target
            self.last_provider = "browser"
        elif intent.action is Action.SEND_TO_APP and intent.target:
            provider, prompt = intent.target.split("\n", 1)
            self.last_provider = provider
            marker = "sobre "
            if marker in prompt:
                self.last_query = prompt.split(marker, 1)[1].split(" e apresente", 1)[0].rstrip(".")

    @staticmethod
    def _research_prompt(query: str) -> str:
        return f"Pesquise na internet sobre {query} e apresente um resumo com as fontes."

