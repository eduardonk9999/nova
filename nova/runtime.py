from __future__ import annotations

import signal
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import IO


class RuntimeState(str, Enum):
    STOPPED = "Parada"
    RUNNING = "Ouvindo"
    FAILED = "Falhou"


class VoiceProcessManager:
    def __init__(self, root: Path, python: str | None = None) -> None:
        self.root = root
        self.python = python or sys.executable
        self.process: subprocess.Popen | None = None
        self._log_handle: IO[str] | None = None
        self.log_path = root / ".nova" / "nova.log"

    @property
    def state(self) -> RuntimeState:
        if self.process is None:
            return RuntimeState.STOPPED
        code = self.process.poll()
        if code is None:
            return RuntimeState.RUNNING
        return RuntimeState.STOPPED if code == 0 else RuntimeState.FAILED

    def start(self) -> bool:
        if self.state is RuntimeState.RUNNING:
            return False
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_handle = self.log_path.open("a", encoding="utf-8")
        self.process = subprocess.Popen(
            [self.python, "-m", "nova.main", "--voice"],
            cwd=self.root,
            stdout=self._log_handle,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        return True

    def stop(self) -> bool:
        if self.process is None or self.process.poll() is not None:
            self._close_log()
            return False
        self.process.send_signal(signal.SIGINT)
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=2)
        self.process = None
        self._close_log()
        return True

    def _close_log(self) -> None:
        if self._log_handle:
            self._log_handle.close()
            self._log_handle = None

