import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_voice_profile_tolerates_natural_pauses() -> None:
    settings = json.loads((ROOT / "config" / "settings.json").read_text(encoding="utf-8"))
    whisper = settings["whisper"]
    assert whisper["speech_threshold"] <= 200
    assert whisper["silence_seconds"] >= 2.0
