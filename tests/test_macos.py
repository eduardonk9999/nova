from unittest.mock import Mock, patch

import pytest

from nova.macos import MacOSController


@patch("nova.macos.subprocess.run")
def test_missing_app_has_clear_error(run: Mock) -> None:
    run.return_value = Mock(returncode=1)
    with pytest.raises(RuntimeError, match="Não encontrei o aplicativo Codex"):
        MacOSController._ensure_app("Codex")


@patch("nova.macos.subprocess.run")
def test_accessibility_permission_is_checked(run: Mock) -> None:
    run.return_value = Mock(returncode=0, stdout="false\n")
    with pytest.raises(RuntimeError, match="Acessibilidade"):
        MacOSController._ensure_accessibility()


@patch("nova.macos.subprocess.run")
def test_accessibility_permission_accepts_true(run: Mock) -> None:
    run.return_value = Mock(returncode=0, stdout="true\n")
    MacOSController._ensure_accessibility()
