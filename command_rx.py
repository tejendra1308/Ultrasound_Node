import socket
import threading
import pyautogui
import win32gui
import win32con
import win32api
import ctypes
import time

# ═══════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════
COMMAND_PORT  = 5001
WINDOW_TITLE  = "Echo Wave II"

COMMAND_MAP = {
    "focus_dec"    : ["f", "left"],
    "focus_inc"    : ["f", "right"],
    "depth_dec"    : ["d", "left"],
    "depth_inc"    : ["d", "right"],
    "gain_dec"     : ["g", "left"],
    "gain_inc"     : ["g", "right"],
    "dynrange_dec" : ["y", "left"],
    "dynrange_inc" : ["y", "right"],
    "power_dec"    : ["p", "left"],
    "power_inc"    : ["p", "right"],
    "freq_dec"     : ["n", "left"],
    "freq_inc"     : ["n", "right"],
    "angle_dec"    : ["a", "left"],
    "angle_inc"    : ["a", "right"],
    "scan_dir"     : ["s"],
    "freeze"       : ["space"],
    "f1"           : ["f1"],
    "f2"           : ["f2"],
    "f3"           : ["f3"],
    "f4"           : ["f4"],
    "f5"           : ["f5"],
    "f6"           : ["f6"],
    "f7"           : ["f7"],
    "f8"           : ["f8"],
    "f9"           : ["f9"],
    "f10"          : ["f10"],
    "f11"          : ["f11"],
    "f12"          : ["f12"],
    "distance"     : ["f8"],
    "length"       : ["f8"],
    "area"         : ["f8"],
    "angle"        : ["f8"],
    "angle2"       : ["f8"],
    "volume"       : ["f8"],
    "volume2"      : ["f8"],
    "stenosis"     : ["f8"],
    "stenosis2"    : ["f8"],
    "ab_ratio"     : ["f8"],
    "ab_ratio2"    : ["f8"],
    "trace"        : ["f8"],
    "mode1"        : ["1"],
    "mode2"        : ["2"],
    "mode3"        : ["3"],
    "mode4"        : ["4"],
    "mode5"        : ["5"],
    "mode6"        : ["6"],
    "mode7"        : ["7"],
    "mode8"        : ["8"],
    "mode9"        : ["9"],
}


def focus_window_by_click():
    """
    Click the center of Echo Wave II window to give it focus.
    This is the most reliable way — simulates a real user click.
    """
    hwnd = win32gui.FindWindow(None, WINDOW_TITLE)
    if not hwnd:
        print(f"[CommandReceiver] Window '{WINDOW_TITLE}' not found!")
        return False

    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    cx = (left + right)  // 2
    cy = (top  + bottom) // 2

    # Save current mouse position
    old_x, old_y = pyautogui.position()

    # Click center of Echo Wave II to focus it
    pyautogui.click(cx, cy)
    time.sleep(0.15)

    # Restore mouse position
    pyautogui.moveTo(old_x, old_y)
    time.sleep(0.05)

    return True


def handle_command(command):
    command = command.strip().lower()

    if command not in COMMAND_MAP:
        print(f"[CommandReceiver] Unknown command: '{command}'")
        return

    # Focus Echo Wave II by clicking it
    if not focus_window_by_click():
        return

    # Send key sequence
    keys = COMMAND_MAP[command]
    for key in keys:
        pyautogui.press(key)
        time.sleep(0.15)

    print(f"[CommandReceiver] '{command}' → pressed {keys}")


def start_udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", COMMAND_PORT))
    print(f"Listening for commands on UDP port {COMMAND_PORT}...\n")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            command = data.decode("utf-8").strip()
            print(f"Received '{command}' from {addr}")
            threading.Thread(
                target=handle_command,
                args=(command,),
                daemon=True
            ).start()
        except Exception as e:
            print(f"[CommandReceiver] Error: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("   MicrUs Command Receiver")
    print("=" * 50)
    print(f"Window target : {WINDOW_TITLE}")
    print(f"UDP port      : {COMMAND_PORT}")
    print("Press Ctrl+C to stop.\n")
    start_udp_listener()