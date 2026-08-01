from pathlib import Path

from nova.assistant import NovaAssistant


class FakeSpeaker:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.stopped = False

    def say(self, message: str, wait=None) -> None:  # noqa: ANN001
        self.messages.append(message)

    def stop(self) -> None:
        self.stopped = True


class FakeController:
    pass


def assistant() -> tuple[NovaAssistant, FakeSpeaker]:
    speaker = FakeSpeaker()
    instance = NovaAssistant(FakeController(), speaker, Path("/tmp"))  # type: ignore[arg-type]
    return instance, speaker


def test_voice_mode_ignores_command_without_wake_word() -> None:
    instance, speaker = assistant()
    assert instance.handle("que horas são", require_wake_word=True)
    assert speaker.messages == []


def test_text_mode_accepts_command_without_wake_word() -> None:
    instance, speaker = assistant()
    assert instance.handle("que horas são", require_wake_word=False)
    assert speaker.messages and speaker.messages[0].startswith("Agora são")


def test_stop_interrupts_speaker_and_session() -> None:
    instance, speaker = assistant()
    assert not instance.handle("resposta anterior NOVA stop", require_wake_word=True)
    assert speaker.stopped
