from nova.context import ConversationContext
from nova.intents import Action, Intent


def test_switches_previous_research_to_claude() -> None:
    context = ConversationContext(last_query="dispositivos para restaurantes")
    intent = context.resolve("NOVA, agora no Claude")
    assert intent is not None
    assert intent.action is Action.SEND_TO_APP
    assert intent.target and intent.target.startswith("claude\nPesquise")


def test_repeat_without_response_is_safe() -> None:
    intent = ConversationContext().resolve("NOVA, repita")
    assert intent is not None and intent.action is Action.REPEAT


def test_remembers_browser_query() -> None:
    context = ConversationContext()
    context.remember(Intent(Action.SEARCH_WEB, target="H2O"), "Pesquisando")
    assert context.last_query == "H2O"
    assert context.last_provider == "browser"
