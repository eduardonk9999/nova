from nova.intents import Action, contains_stop_command, has_wake_word, parse


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


def test_nova_stop_is_silent_stop() -> None:
    assert parse("NOVA, parar").action is Action.STOP_SILENT


def test_nova_stop_in_english_is_silent_stop() -> None:
    assert parse("NOVA, stop").action is Action.STOP_SILENT


def test_wake_word_must_be_at_start() -> None:
    assert has_wake_word("NOVA, abra o Safari")
    assert not has_wake_word("conversando sobre a nova versão")


def test_wake_word_alone_is_not_full_help() -> None:
    assert parse("NOVA").action is Action.WAKE


def test_natural_acknowledgement() -> None:
    assert parse("NOVA, beleza").action is Action.THANKS


def test_spoken_volume_number() -> None:
    intent = parse("NOVA, volume dez")
    assert intent.action is Action.SET_VOLUME
    assert intent.value == 10


def test_stop_is_detected_inside_captured_speech() -> None:
    assert contains_stop_command("Esta é uma resposta longa. NOVA, stop")


def test_open_claude_code() -> None:
    assert parse("NOVA, abra o Claude Code").action is Action.OPEN_CLAUDE_CODE


def test_open_claude_desktop_app() -> None:
    intent = parse("NOVA, abra o Claude")
    assert intent.action is Action.OPEN_APP
    assert intent.target == "claude"


def test_open_claude_desktop_app_with_explicit_wording() -> None:
    intent = parse("NOVA, abra o aplicativo Cláudio")
    assert intent.action is Action.OPEN_APP
    assert intent.target == "claude"


def test_open_project_in_claude_code() -> None:
    intent = parse("abra o projeto NOVA no Claude Code")
    assert intent.action is Action.OPEN_PROJECT_CLAUDE_CODE
    assert intent.target == "nova"


def test_open_project_in_claude_desktop() -> None:
    intent = parse("abra o projeto Meu Produto no Claude")
    assert intent.action is Action.OPEN_CLAUDE_PROJECT
    assert intent.target == "meu produto"


def test_create_new_codex_project_from_real_transcription() -> None:
    intent = parse("NOVA, iniciou um novo projeto no Codex chamado GV")
    assert intent.action is Action.CREATE_CODEX_PROJECT
    assert intent.target == "gv"


def test_create_codex_project_from_whisper_audio_transcription() -> None:
    intent = parse("NOVA, Cri um novo projeto no Codex chamado GV")
    assert intent.action is Action.CREATE_CODEX_PROJECT
    assert intent.target == "gv"


def test_create_project_with_article_from_live_transcription() -> None:
    intent = parse("Cri o novo projeto no Codex, chamado GV")
    assert intent.action is Action.CREATE_CODEX_PROJECT
    assert intent.target == "gv"


def test_create_project_semantics_tolerate_wording() -> None:
    intent = parse("NOVA, comece para mim um projeto no código X com o nome de Loja")
    assert intent.action is Action.CREATE_CODEX_PROJECT
    assert intent.target == "loja"


def test_open_project_inside_claude_app() -> None:
    intent = parse("mostre o projeto Site dentro do aplicativo Cláudio")
    assert intent.action is Action.OPEN_CLAUDE_PROJECT
    assert intent.target == "site"


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


def test_send_prompt_to_codex() -> None:
    intent = parse("pergunte ao Codex como corrigir este teste")
    assert intent.action is Action.SEND_TO_APP
    assert intent.target == "codex\ncomo corrigir este teste"


def test_send_prompt_to_codex_with_offline_transcription() -> None:
    intent = parse("mande para o codigo x rode os testes")
    assert intent.action is Action.SEND_TO_APP
    assert intent.target == "codex\nrode os testes"


def test_research_using_codex() -> None:
    intent = parse("NOVA, pesquise novidades do Python no Codex")
    assert intent.action is Action.SEND_TO_APP
    assert intent.target == (
        "codex\nPesquise na internet sobre novidades do python e apresente um resumo com as fontes."
    )


def test_research_using_codex_offline_name() -> None:
    intent = parse("busque arquitetura de agentes usando o código X")
    assert intent.action is Action.SEND_TO_APP
    assert intent.target.startswith("codex\nPesquise na internet sobre arquitetura de agentes")


def test_research_codex_before_topic() -> None:
    intent = parse("pesquise no Codex H dois O")
    assert intent.action is Action.SEND_TO_APP
    assert intent.target == (
        "codex\nPesquise na internet sobre H2O e apresente um resumo com as fontes."
    )


def test_research_with_codex_destination_first() -> None:
    intent = parse("NOVA, no Codex, busque sobre dispositivos de restaurante")
    assert intent.action is Action.SEND_TO_APP
    assert intent.target == (
        "codex\nPesquise na internet sobre dispositivos de restaurante "
        "e apresente um resumo com as fontes."
    )


def test_research_with_indicative_transcription() -> None:
    intent = parse("NOVA, pesquisa sobre dispositivos de restaurante")
    assert intent.action is Action.SEARCH_WEB
    assert intent.target == "dispositivos de restaurante"


def test_research_h20_spoken_form() -> None:
    intent = parse("pesquise agá vinte no código X")
    assert intent.action is Action.SEND_TO_APP
    assert "sobre H20" in (intent.target or "")


def test_mute_and_screenshot() -> None:
    assert parse("NOVA, tire o som").action is Action.MUTE
    assert parse("NOVA, tire um print").action is Action.SCREENSHOT
