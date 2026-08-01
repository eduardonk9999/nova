from pathlib import Path
from unittest.mock import Mock, patch

from nova.runtime import RuntimeState, VoiceProcessManager


def test_manager_starts_voice_process(tmp_path: Path) -> None:
    process = Mock()
    process.poll.return_value = None
    with patch("nova.runtime.subprocess.Popen", return_value=process) as popen:
        manager = VoiceProcessManager(tmp_path, python="python-test")
        assert manager.start()
        assert manager.state is RuntimeState.RUNNING
        command = popen.call_args.args[0]
        assert command == ["python-test", "-m", "nova.main", "--voice"]
        manager._close_log()


def test_manager_does_not_start_twice(tmp_path: Path) -> None:
    process = Mock()
    process.poll.return_value = None
    with patch("nova.runtime.subprocess.Popen", return_value=process):
        manager = VoiceProcessManager(tmp_path)
        assert manager.start()
        assert not manager.start()
        manager._close_log()


def test_manager_stops_with_interrupt(tmp_path: Path) -> None:
    process = Mock()
    process.poll.return_value = None
    with patch("nova.runtime.subprocess.Popen", return_value=process):
        manager = VoiceProcessManager(tmp_path)
        manager.start()
        assert manager.stop()
        process.send_signal.assert_called_once()
        assert manager.state is RuntimeState.STOPPED
