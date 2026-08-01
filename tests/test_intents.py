from nova.intents import Action, parse


def test_open_app_with_wake_word() -> None:
    intent = parse("NOVA, abra o Safari")
    assert intent.action is Action.OPEN_APP
    assert intent.target == "safari"


def test_close_app_without_wake_word() -> None:
    intent = parse("feche o Spotify")
    assert intent.action is Action.CLOSE_APP
    assert intent.target == "spotify"


def test_volume_is_capped() -> None:
    intent = parse("coloque o volume em 150")
    assert intent.action is Action.SET_VOLUME
    assert intent.value == 100


def test_unknown_command() -> None:
    assert parse("faça um café").action is Action.UNKNOWN


def test_open_claude_code() -> None:
    assert parse("NOVA, abra o Claude Code").action is Action.OPEN_CLAUDE_CODE


def test_open_claude_code_with_offline_transcription() -> None:
    assert parse("nova a obra claudio coutinho").action is Action.OPEN_CLAUDE_CODE


def test_search_web() -> None:
    intent = parse("NOVA pesquise na internet Python 3.14")
    assert intent.action is Action.SEARCH_WEB
    assert intent.target == "python 3 14"


def test_start_project() -> None:
    intent = parse("inicie o projeto NOVA")
    assert intent.action is Action.START_PROJECT
    assert intent.target == "nova"


def test_terminal_command() -> None:
    intent = parse("execute no terminal git status")
    assert intent.action is Action.RUN_TERMINAL
    assert intent.target == "git status"
