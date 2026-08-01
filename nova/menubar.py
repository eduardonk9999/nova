from __future__ import annotations

import atexit
import subprocess
from pathlib import Path

from nova.runtime import RuntimeState, VoiceProcessManager


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    try:
        import rumps
    except ImportError as exc:
        raise SystemExit("Instale a interface com: pip install -e '.[desktop]'") from exc

    class NovaMenuBar(rumps.App):
        def __init__(self) -> None:
            super().__init__("NOVA", title="✦", quit_button=None)
            self.manager = VoiceProcessManager(ROOT)
            self.status_item = rumps.MenuItem("Estado: Parada")
            self.status_item.set_callback(None)
            self.start_item = rumps.MenuItem("Iniciar NOVA", callback=self.start_nova)
            self.stop_item = rumps.MenuItem("Parar NOVA", callback=self.stop_nova)
            self.menu = [
                self.status_item,
                None,
                self.start_item,
                self.stop_item,
                None,
                rumps.MenuItem("Abrir configurações", callback=self.open_settings),
                rumps.MenuItem("Abrir log", callback=self.open_log),
                rumps.MenuItem("Abrir projeto", callback=self.open_project),
                None,
                rumps.MenuItem("Sair", callback=self.quit_app),
            ]
            self.timer = rumps.Timer(self.refresh, 1)
            self.timer.start()
            atexit.register(self.manager.stop)
            self.refresh(None)

        def refresh(self, _sender) -> None:  # noqa: ANN001
            state = self.manager.state
            self.status_item.title = f"Estado: {state.value}"
            self.start_item.set_callback(None if state is RuntimeState.RUNNING else self.start_nova)
            self.stop_item.set_callback(self.stop_nova if state is RuntimeState.RUNNING else None)

        def start_nova(self, _sender) -> None:  # noqa: ANN001
            if self.manager.start():
                rumps.notification("NOVA", "Assistente iniciada", "Ouvindo a palavra NOVA")
            self.refresh(None)

        def stop_nova(self, _sender) -> None:  # noqa: ANN001
            self.manager.stop()
            self.refresh(None)

        def open_settings(self, _sender) -> None:  # noqa: ANN001
            subprocess.run(["open", str(ROOT / "config" / "settings.json")], check=False)

        def open_log(self, _sender) -> None:  # noqa: ANN001
            self.manager.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.manager.log_path.touch(exist_ok=True)
            subprocess.run(["open", str(self.manager.log_path)], check=False)

        def open_project(self, _sender) -> None:  # noqa: ANN001
            subprocess.run(["open", str(ROOT)], check=False)

        def quit_app(self, _sender) -> None:  # noqa: ANN001
            self.manager.stop()
            rumps.quit_application()

    NovaMenuBar().run()


if __name__ == "__main__":
    main()

