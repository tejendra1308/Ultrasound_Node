"""
MicrUs Command Receiver.

Just wiring: commands.json (data) -> CommandDispatcher (logic) ->
InputBackend (delivery). To add a command, edit config/commands.json.
To change delivery mechanism, edit config/settings.json's
`command.input_backend`, or write a new backend in core/input_backend.py.
"""

from config.settings import SETTINGS, load_command_map
from core.command_dispatch import CommandDispatcher
from core.input_backend import build_input_backend


def main():
    print("=" * 50)
    print("   MicrUs Command Receiver")
    print("=" * 50)

    cfg = SETTINGS
    print(f"Window target : {cfg.window.title_hint}")
    print(f"UDP port      : {cfg.command.port}")
    print(f"Input backend : {cfg.command.input_backend}")
    print("Press Ctrl+C to stop.\n")

    dispatcher = CommandDispatcher(
        command_map=load_command_map(),
        window_title=cfg.window.title_hint,
        input_backend=build_input_backend(cfg.command.input_backend),
        key_delay=cfg.command.key_delay,
    )
    dispatcher.serve_udp_forever(cfg.command.port)


if __name__ == "__main__":
    main()
