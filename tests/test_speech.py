from array import array

from nova.speech import VoskListener, WhisperListener


def test_research_ending_in_letter_waits_for_continuation() -> None:
    assert VoskListener._research_needs_continuation("pesquise no codex h")


def test_complete_research_does_not_wait() -> None:
    assert not VoskListener._research_needs_continuation("pesquise no codex h dois o")


def test_whisper_rms_detects_silence() -> None:
    assert WhisperListener._rms(bytes(3200)) == 0


def test_whisper_rms_detects_speech() -> None:
    samples = array("h", [1000, -1000] * 800)
    assert WhisperListener._rms(samples.tobytes()) == 1000


def test_feminine_voice_is_default() -> None:
    from nova.speech import Speaker

    assert Speaker(enabled=False).voice == "Luciana"
