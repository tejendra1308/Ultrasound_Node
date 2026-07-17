"""
Input backends: anything that can "focus a window, then press some keys".

Swapping HOW commands get delivered to the target app (keyboard simulation
today, maybe a native API tomorrow) means writing a new backend class here
and pointing config.command.input_backend at it — nothing else changes.
"""

import time


class InputBackend:
    """Interface every backend implements."""
    def focus_window(self, title_hint) -> bool:
        raise NotImplementedError

    def press_keys(self, keys, delay_seconds):
        raise NotImplementedError


class DummyInputBackend(InputBackend):
    """Logs what it would do. Safe on any OS — used for dev/testing."""
    def focus_window(self, title_hint):
        print(f"[DummyInput] would focus window '{title_hint}'")
        return True

    def press_keys(self, keys, delay_seconds):
        for key in keys:
            print(f"[DummyInput] would press '{key}'")
            time.sleep(0)  # no real delay needed in dummy mode


class WindowsInputBackend(InputBackend):
    """Real keypresses via pyautogui, focusing the target window by clicking it."""
    def __init__(self):
        import pyautogui
        import win32gui
        self._pyautogui = pyautogui
        self._win32gui = win32gui

    def focus_window(self, title_hint):
        hwnd = self._win32gui.FindWindow(None, title_hint)
        if not hwnd:
            print(f"[WindowsInput] window '{title_hint}' not found!")
            return False

        left, top, right, bottom = self._win32gui.GetWindowRect(hwnd)
        cx, cy = (left + right) // 2, (top + bottom) // 2

        old_x, old_y = self._pyautogui.position()
        self._pyautogui.click(cx, cy)
        time.sleep(0.15)
        self._pyautogui.moveTo(old_x, old_y)
        time.sleep(0.05)
        return True

    def press_keys(self, keys, delay_seconds):
        for key in keys:
            self._pyautogui.press(key)
            time.sleep(delay_seconds)


def build_input_backend(name: str) -> InputBackend:
    if name == "windows":
        return WindowsInputBackend()
    if name == "dummy":
        return DummyInputBackend()
    raise ValueError(f"Unknown input_backend '{name}' (expected 'windows' or 'dummy')")
