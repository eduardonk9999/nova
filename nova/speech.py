from __future__ import annotations

import json
import queue
import re
import subprocess
import tempfile
import wave
from array import array
from collections import deque
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Recognition:
    text: str
    confidence: float | None = None


class Speaker:
    def __init__(
        self, enabled: bool = True, blocking: bool = True, voice: str = "Luciana"
    ) -> None:
        self.enabled = enabled
        self.blocking = blocking
        self.voice = voice
        self._process: subprocess.Popen | None = None

    def say(self, message: str, wait: bool | None = None) -> None:
        print(f"NOVA: {message}")
        if not self.enabled:
            return
        self.stop()
        # Uma ação anterior pode ter colocado a saída em mudo. A assistente
        # precisa permanecer audível para confirmar comandos ao usuário.
        subprocess.run(
            ["osascript", "-e", "set volume output muted false"],
            check=False, capture_output=True,
        )
        self._process = subprocess.Popen(
            ["say", "-v", self.voice, message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        should_wait = self.blocking if wait is None else wait
        if should_wait:
            self._process.wait()
            self._process = None

    @property
    def is_speaking(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def stop(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None


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

    def listen(self) -> Recognition:
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
                        words = result.get("result", [])
                        confidence = None
                        if words:
                            confidence = sum(word.get("conf", 0.0) for word in words) / len(words)
                        return Recognition(combined, confidence)

    @staticmethod
    def _research_needs_continuation(text: str) -> bool:
        normalized = text.lower().strip()
        is_research = any(word in normalized for word in ("pesquise", "busque", "procure"))
        mentions_codex = any(word in normalized for word in ("codex", "codax", "códex"))
        return is_research and mentions_codex and bool(re.search(r"\bh$", normalized))


class WhisperListener:
    """Captura uma frase e usa whisper.cpp local para transcrevê-la."""

    PROMPT = (
        "NOVA, Codex, Claude, Claude Code, H2O, H20, GitHub, Python, terminal, "
        "projeto, pesquisar, aplicativo"
    )

    def __init__(
        self,
        model_path: Path,
        executable: str = "/opt/homebrew/bin/whisper-cli",
        sample_rate: int = 16_000,
        silence_seconds: float = 1.2,
        speech_threshold: int = 350,
        language: str = "pt",
        use_gpu: bool = False,
    ) -> None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("Dependência sounddevice ausente.") from exc
        if not model_path.exists():
            raise RuntimeError(f"Modelo Whisper não encontrado em {model_path}")
        if not Path(executable).exists():
            raise RuntimeError(f"whisper-cli não encontrado em {executable}")
        self.sd = sd
        self.model_path = model_path
        self.executable = executable
        self.sample_rate = sample_rate
        self.silence_seconds = silence_seconds
        self.speech_threshold = speech_threshold
        self.language = language
        self.use_gpu = use_gpu
        self.audio: queue.Queue[bytes] = queue.Queue()

    def listen(self) -> Recognition:
        blocksize = self.sample_rate // 10
        silence_blocks_required = round(self.silence_seconds * 10)
        pre_roll: deque[bytes] = deque(maxlen=4)
        frames: list[bytes] = []
        speaking = False
        silent_blocks = 0

        def callback(indata, frames_count, time, status) -> None:  # noqa: ANN001
            self.audio.put(bytes(indata))

        print("Ouvindo com Whisper...")
        with self.sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=blocksize,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            while True:
                chunk = self.audio.get()
                rms = self._rms(chunk)
                if not speaking:
                    pre_roll.append(chunk)
                    if rms >= self.speech_threshold:
                        speaking = True
                        frames.extend(pre_roll)
                    continue

                frames.append(chunk)
                silent_blocks = silent_blocks + 1 if rms < self.speech_threshold else 0
                if silent_blocks >= silence_blocks_required or len(frames) >= 150:
                    break

        return self._transcribe(frames)

    def _transcribe(self, frames: list[bytes]) -> Recognition:
        temporary = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temporary_path = Path(temporary.name)
        temporary.close()
        output_base = temporary_path.with_suffix("")
        output_json = output_base.with_suffix(".json")
        try:
            with wave.open(str(temporary_path), "wb") as audio_file:
                audio_file.setnchannels(1)
                audio_file.setsampwidth(2)
                audio_file.setframerate(self.sample_rate)
                audio_file.writeframes(b"".join(frames))
            command = [
                    self.executable,
                    "-m", str(self.model_path),
                    "-f", str(temporary_path),
                    "-l", self.language,
                    "-nt", "-t", "6",
                    "--output-json-full", "--output-file", str(output_base),
                    "--prompt", self.PROMPT,
                ]
            if not self.use_gpu:
                command.insert(1, "-ng")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "Falha na transcrição Whisper.")
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            segments = payload.get("transcription", [])
            text = " ".join(segment.get("text", "").strip() for segment in segments).strip(" .")
            probabilities = [
                token["p"]
                for segment in segments
                for token in segment.get("tokens", [])
                if token.get("p") is not None and not token.get("text", "").startswith("[_")
            ]
            confidence = sum(probabilities) / len(probabilities) if probabilities else None
            return Recognition(text, confidence)
        finally:
            temporary_path.unlink(missing_ok=True)
            output_json.unlink(missing_ok=True)

    @staticmethod
    def _rms(chunk: bytes) -> int:
        samples = array("h")
        samples.frombytes(chunk)
        if not samples:
            return 0
        return int((sum(sample * sample for sample in samples) / len(samples)) ** 0.5)
