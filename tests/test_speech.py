from nova.speech import VoskListener


def test_research_ending_in_letter_waits_for_continuation() -> None:
    assert VoskListener._research_needs_continuation("pesquise no codex h")


def test_complete_research_does_not_wait() -> None:
    assert not VoskListener._research_needs_continuation("pesquise no codex h dois o")
