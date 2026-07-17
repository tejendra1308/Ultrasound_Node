"""
Generic TCP frame streamer.

VideoStreamServer doesn't know anything about window capture or ultrasound —
it just accepts a `frame_provider` callable (anything that returns a BGR
numpy frame or None) and streams JPEG-encoded frames to whoever connects.

This means the same server can later stream any other frame source (a
camera, a different app window, a synthetic test pattern) with zero changes
to this file.
"""

import socket
import struct
import time

import cv2


class VideoStreamServer:
    def __init__(self, frame_provider, port, fps=30, jpeg_quality=90,
                 is_source_alive=lambda: True):
        """
        frame_provider  : callable() -> BGR numpy frame or None
        is_source_alive : callable() -> bool, checked each loop to decide
                           whether to keep streaming (e.g. "is the window
                           still open"). Defaults to always-alive.
        """
        self.frame_provider = frame_provider
        self.is_source_alive = is_source_alive
        self.port = port
        self.fps = fps
        self.jpeg_quality = jpeg_quality

    def serve_forever(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self.port))
        server.listen(1)
        print(f"Waiting for client on port {self.port}. Press Ctrl+C to stop.\n")

        try:
            while True:
                conn, addr = server.accept()
                self._handle_client(conn, addr)
                print("\nWaiting for client to reconnect...")
        except KeyboardInterrupt:
            print("\nServer stopped.")
        finally:
            server.close()

    def _handle_client(self, conn, addr):
        print(f"Client connected from {addr}")
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
        frame_delay = 1.0 / self.fps
        frames_sent = 0
        start_time = time.time()

        try:
            while True:
                t_start = time.time()

                if not self.is_source_alive():
                    print("Frame source no longer available — stopping stream.")
                    break

                frame = self.frame_provider()
                if frame is None:
                    time.sleep(0.05)
                    continue

                ok, buffer = cv2.imencode(".jpg", frame, encode_params)
                if not ok:
                    continue

                data = buffer.tobytes()
                header = struct.pack(">I", len(data))
                conn.sendall(header + data)
                frames_sent += 1

                elapsed = time.time() - start_time
                if elapsed >= 5.0:
                    print(f"Streaming — {frames_sent / elapsed:.1f} FPS  |  "
                          f"Frame size: {len(data) / 1024:.1f} KB")
                    frames_sent = 0
                    start_time = time.time()

                sleep_for = frame_delay - (time.time() - t_start)
                if sleep_for > 0:
                    time.sleep(sleep_for)

        except (BrokenPipeError, ConnectionResetError, OSError):
            print(f"Client at {addr} disconnected")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            conn.close()
