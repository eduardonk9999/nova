from nova.terminal import TerminalPolicy


def test_safe_read_only_command() -> None:
    assert TerminalPolicy.classify("git status") == "safe"


def test_unknown_command_needs_confirmation() -> None:
    assert TerminalPolicy.classify("npm install") == "confirm"


def test_destructive_command_is_blocked() -> None:
    assert TerminalPolicy.classify("rm -rf projeto") == "blocked"


def test_shell_chaining_is_blocked() -> None:
    assert TerminalPolicy.classify("git status && rm arquivo") == "blocked"
