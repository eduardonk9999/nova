from nova.intents import Action
from nova.router import IntentRouter


def test_natural_research_request_is_rewritten() -> None:
    route = IntentRouter().route("NOVA, faça uma pesquisa sobre restaurantes inteligentes")
    assert route.corrected
    assert route.intent.action is Action.SEARCH_WEB
    assert route.intent.target == "restaurantes inteligentes"


def test_colloquial_open_is_rewritten() -> None:
    route = IntentRouter().route("NOVA, abre o Safari")
    assert route.intent.action is Action.OPEN_APP
    assert route.intent.target == "safari"


def test_unknown_text_remains_unknown() -> None:
    route = IntentRouter().route("NOVA, transforme o mundo")
    assert route.intent.action is Action.UNKNOWN
