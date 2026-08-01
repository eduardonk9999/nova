from __future__ import annotations

import argparse
import json
from pathlib import Path

from nova.assistant import NovaAssistant
from nova.macos import MacOSController
from nova.speech import Speaker, VoskListener


ROOT = Path(__file__).resolve().parent.parent


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NOVA, sua assistente local")
    parser.add_argument("--voice", action="store_true", help="usar microfone com Vosk")
    parser.add_argument("--silent", action="store_true", help="não responder em voz alta")
    parser.add_argument(
        "--model", type=Path, default=ROOT / "models" / "vosk-pt", help="modelo Vosk"
    )
    return parser.parse_args()


def main() -> None:
    args = arguments()
    config = json.loads((ROOT / "config" / "apps.json").read_text(encoding="utf-8"))
    assistant = NovaAssistant(
        MacOSController(config["aliases"]), Speaker(not args.silent), ROOT
    )
    projects_file = ROOT / "config" / "projects.json"
    if projects_file.exists():
        assistant.set_projects(
            json.loads(projects_file.read_text(encoding="utf-8"))["projects"]
        )

    listener = None
    if args.voice:
        try:
            listener = VoskListener(args.model)
        except RuntimeError as exc:
            print(f"Voz indisponível: {exc}\nUsando modo texto.")

    assistant.speaker.say("NOVA iniciada. Como posso ajudar?")
    running = True
    while running:
        try:
            command = listener.listen() if listener else input("Você: ").strip()
            if command:
                print(f"Você: {command}" if listener else "", end="\n" if listener else "")
                running = assistant.handle(command)
        except (EOFError, KeyboardInterrupt):
            print()
            assistant.speaker.say("Até logo.")
            break


if __name__ == "__main__":
    main()
