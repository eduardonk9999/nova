from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum


class Action(str, Enum):
    OPEN_APP = "open_app"
    CLOSE_APP = "close_app"
    FOCUS_APP = "focus_app"
    OPEN_CLAUDE_CODE = "open_claude_code"
    SEARCH_WEB = "search_web"
    START_PROJECT = "start_project"
    RUN_TERMINAL = "run_terminal"
    SEND_TO_APP = "send_to_app"
    MUTE = "mute"
    UNMUTE = "unmute"
    SCREENSHOT = "screenshot"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    SET_VOLUME = "set_volume"
    TIME = "time"
    HELP = "help"
    EXIT = "exit"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Intent:
    action: Action
    target: str | None = None
    value: int | None = None


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[,.!?;:]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse(text: str, wake_word: str = "nova") -> Intent:
    command = normalize(text)
    if command.startswith(f"{wake_word} "):
        command = command[len(wake_word) + 1 :].strip()
    elif command == wake_word:
        return Intent(Action.HELP)

    if command in {"sair", "encerrar", "desligar", "tchau"}:
        return Intent(Action.EXIT)
    if command in {"confirmar", "confirmo", "pode executar", "sim execute"}:
        return Intent(Action.CONFIRM)
    if command in {"cancelar", "cancele", "nao execute"}:
        return Intent(Action.CANCEL)
    if command in {"ajuda", "o que voce faz", "comandos"}:
        return Intent(Action.HELP)
    if command in {"que horas sao", "horas", "me diga as horas"}:
        return Intent(Action.TIME)
    if command in {"silencio", "mudo", "ative o mudo", "tire o som"}:
        return Intent(Action.MUTE)
    if command in {"ative o som", "remova o mudo", "volte o som"}:
        return Intent(Action.UNMUTE)
    if command in {"tire uma captura de tela", "tire um print", "captura de tela"}:
        return Intent(Action.SCREENSHOT)

    match = re.fullmatch(
        r"(?:envie|enviar|mande|mandar|pergunte|perguntar) (?:para|ao|a)(?: o)? (codex|codax|codigo x|claude|claudio) (.+)",
        command,
    )
    if match:
        spoken_app = match.group(1)
        app = "codex" if spoken_app in {"codex", "codax", "codigo x"} else "claude"
        return Intent(Action.SEND_TO_APP, target=f"{app}\n{match.group(2)}")

    # Modelos offline em português costumam aproximar o nome estrangeiro
    # "Claude Code" para "Cláudio Code/Coutinho". Aceitamos essas formas.
    claude_names = (
        "claude code", "claudio", "claudio code", "claudio coutinho", "claudio couto"
    )
    open_words = ("abra", "abrir", "obra", "inicie", "iniciar")
    if any(word in command.split() for word in open_words) and any(
        name in command for name in claude_names
    ):
        return Intent(Action.OPEN_CLAUDE_CODE)

    match = re.fullmatch(
        r"(?:pesquise|pesquisar|busque|buscar|procure|procurar)(?: na internet| no google)? (.+)",
        command,
    )
    if match:
        return Intent(Action.SEARCH_WEB, target=match.group(1))

    match = re.fullmatch(
        r"(?:inicie|iniciar|suba|subir|starte|startar|rode) (?:o )?projeto (.+)", command
    )
    if match:
        return Intent(Action.START_PROJECT, target=match.group(1))

    match = re.fullmatch(
        r"(?:execute|executar|rode|rodar)(?: no terminal)? (?:o comando )?(.+)", command
    )
    if match:
        return Intent(Action.RUN_TERMINAL, target=match.group(1))

    match = re.fullmatch(r"(?:abra|abrir|inicie|iniciar) (?:o |a )?(.+)", command)
    if match:
        return Intent(Action.OPEN_APP, target=match.group(1))

    match = re.fullmatch(r"(?:feche|fechar|encerre) (?:o |a )?(.+)", command)
    if match:
        return Intent(Action.CLOSE_APP, target=match.group(1))

    match = re.fullmatch(r"(?:foque|mostrar|mostre|va para) (?:o |a )?(.+)", command)
    if match:
        return Intent(Action.FOCUS_APP, target=match.group(1))

    match = re.fullmatch(r"(?:volume|defina o volume(?: para)?|coloque o volume(?: em)?) (\d{1,3})", command)
    if match:
        return Intent(Action.SET_VOLUME, value=min(100, int(match.group(1))))

    return Intent(Action.UNKNOWN)
