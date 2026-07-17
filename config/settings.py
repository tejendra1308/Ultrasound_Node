"""
Central configuration for Ultrasound_Node.

Defaults live here. To change anything for your setup, DO NOT edit this
file — instead create `config/settings.local.json` (git-ignored) with only
the keys you want to override, e.g.:

    {
      "window": { "title_hint": "MicrUs" },
      "video":  { "port": 6000, "fps": 20 }
    }

This file is loaded once at import time and merged over the defaults below.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

_CONFIG_DIR = Path(__file__).parent
_LOCAL_OVERRIDE_FILE = _CONFIG_DIR / "settings.local.json"
_COMMANDS_FILE = _CONFIG_DIR / "commands.json"


@dataclass
class WindowConfig:
    # Partial title of the target app window. Run feeder.py once with no
    # match to print all visible window titles and copy the right hint.
    title_hint: str = "Echo Wave II"
    # Crop box as fractions of the captured window (trims app toolbars).
    # (left, right, top, bottom) — e.g. left=0.22 trims the left 22%.
    crop_left: float = 0.22
    crop_right: float = 0.78
    crop_top: float = 0.04
    crop_bottom: float = 0.92


@dataclass
class VideoConfig:
    port: int = 5000
    jpeg_quality: int = 90
    fps: int = 30
    output_width: int = 1707
    output_height: int = 1067


@dataclass
class CommandConfig:
    port: int = 5001
    # Seconds to pause between individual keypresses in a command sequence.
    key_delay: float = 0.15
    # Seconds to wait after focusing the target window before sending keys.
    focus_delay: float = 0.15
    # "windows"  -> real pyautogui/win32 keypresses (requires Windows)
    # "dummy"    -> just logs what it would have done (for testing/dev on non-Windows)
    input_backend: str = "dummy"


@dataclass
class DiscoveryConfig:
    enabled: bool = True
    service_name: str = "ultrasound"
    multicast_group: str = "239.255.42.42"
    broadcast_port: int = 5003
    interval_seconds: float = 2.0


@dataclass
class Settings:
    window: WindowConfig = field(default_factory=WindowConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    command: CommandConfig = field(default_factory=CommandConfig)
    discovery: DiscoveryConfig = field(default_factory=DiscoveryConfig)


def _merge_dataclass(instance, overrides: dict):
    for key, value in overrides.items():
        if not hasattr(instance, key):
            continue
        current = getattr(instance, key)
        if isinstance(value, dict) and hasattr(current, "__dataclass_fields__"):
            _merge_dataclass(current, value)
        else:
            setattr(instance, key, value)
    return instance


def load_settings() -> Settings:
    settings = Settings()
    if _LOCAL_OVERRIDE_FILE.exists():
        overrides = json.loads(_LOCAL_OVERRIDE_FILE.read_text())
        _merge_dataclass(settings, overrides)
    return settings


def load_command_map() -> dict:
    """Command name -> list of key names, loaded from config/commands.json.

    To add a new command: edit commands.json, no Python changes needed.
    """
    return json.loads(_COMMANDS_FILE.read_text())


SETTINGS = load_settings()

if __name__ == "__main__":
    print(json.dumps(asdict(SETTINGS), indent=2))
