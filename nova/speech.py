from __future__ import annotations

import json
import queue
import re
import subprocess
from pathlib import Path


class Speaker:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def say(self, message: str) -> None:
        print(f"NOVA: {message}")
        if self.enabled:
            subprocess.run(["say", "-v", "Luciana", message], check=False)


class VoskListener:
    """Captura uma frase usando reconhecimento local/offline."""

    def __init__(self, model_path: Path, sample_rate: int = 16_000) -> None:
        try:
            import sounddevice as sd
            from vosk import KaldiRecognizer, Model
        except ImportError as exc:
            raise RuntimeError(
                "Dependências de voz ausentes. Instale com: pip install -e '.[voice]'"
            ) from exc

        if not model_path.exists():
            raise RuntimeError(f"Modelo Vosk não encontrado em {model_path}")
        self.sd = sd
        self.recognizer = KaldiRecognizer(Model(str(model_path)), sample_rate)
        self.sample_rate = sample_rate
        self.audio: queue.Queue[bytes] = queue.Queue()

    def listen(self) -> str:
        def callback(indata, frames, time, status) -> None:  # noqa: ANN001
            self.audio.put(bytes(indata))

        print("Ouvindo...")
        phrases: list[str] = []
        with self.sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            while True:
                if self.recognizer.AcceptWaveform(self.audio.get()):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        phrases.append(text)
                        combined = " ".join(phrases)
                        # O modelo pode encerrar na pausa entre "H" e "dois O".
                        # Mantemos a escuta se uma pesquisa no Codex termina em letra isolada.
                        if self._research_needs_continuation(combined):
                            print("Continue o termo...")
                            continue
                        return combined

    @staticmethod
    def _research_needs_continuation(text: str) -> bool:
        normalized = text.lower().strip()
        is_research = any(word in normalized for word in ("pesquise", "busque", "procure"))
        mentions_codex = any(word in normalized for word in ("codex", "codax", "códex"))
        return is_research and mentions_codex and bool(re.search(r"\bh$", normalized))
