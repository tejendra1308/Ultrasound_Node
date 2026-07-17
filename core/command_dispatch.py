"""
CommandDispatcher: UDP command name -> key sequence -> input backend.

Adding a new command requires editing config/commands.json only.
Changing HOW keys get delivered requires swapping the input backend only.
Neither requires touching this file.
"""

import socket
import threading

from core.input_backend import InputBackend


class CommandDispatcher:
    def __init__(self, command_map: dict, window_title: str,
                 input_backend: InputBackend, key_delay: float = 0.15):
        self.command_map = command_map
        self.window_title = window_title
        self.input_backend = input_backend
        self.key_delay = key_delay

    def handle(self, command: str):
        command = command.strip().lower()
        keys = self.command_map.get(command)
        if keys is None:
            print(f"[CommandDispatcher] Unknown command: '{command}'")
            return

        if not self.input_backend.focus_window(self.window_title):
            return

        self.input_backend.press_keys(keys, self.key_delay)
        print(f"[CommandDispatcher] '{command}' -> pressed {keys}")

    def serve_udp_forever(self, port: int):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", port))
        print(f"Listening for commands on UDP port {port}...\n")

        while True:
            try:
                data, addr = sock.recvfrom(1024)
                command = data.decode("utf-8").strip()
                print(f"Received '{command}' from {addr}")
                threading.Thread(target=self.handle, args=(command,), daemon=True).start()
            except Exception as e:
                print(f"[CommandDispatcher] Error: {e}")
