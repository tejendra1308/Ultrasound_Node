import socket
import cv2
import struct
import time
import sys
import numpy as np

# Windows-specific window capture
import ctypes
import win32gui
import win32ui
import win32con

# ═══════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════
PORT              = 5000
JPEG_QUALITY      = 90
FPS               = 30
FRAME_WIDTH       = 1707
FRAME_HEIGHT      = 1067

# Partial title of the MicrUs window — run script once to see all titles
WINDOW_TITLE_HINT = "Echo Wave II"
# ═══════════════════════════════════════════


def list_all_windows():
    """Print every visible window title."""
    print("\nAll open windows:")
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title.strip():
                print(f"  [{hwnd}] '{title}'")
    win32gui.EnumWindows(callback, None)
    print()


def find_window_handle(hint):
    """Return the HWND of the first visible window whose title contains hint."""
    result = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if hint.lower() in title.lower():
                result.append((hwnd, title))
    win32gui.EnumWindows(callback, None)

    if not result:
        print(f"\nERROR: No window found containing '{hint}'")
        print("Make sure the MicrUs app is open and not minimized.")
        list_all_windows()
        sys.exit(1)

    hwnd, title = result[0]
    print(f"Found window: '{title}'  [hwnd={hwnd}]")
    return hwnd


def capture_hwnd(hwnd):
    """
    Capture ONLY the pixels of the given window using Win32 BitBlt.
    This works even if another window is partially on top.
    Returns a BGR numpy array.
    """
    # Get window dimensions
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    w = right - left
    h = bottom - top

    if w <= 0 or h <= 0:
        return None

    # Create device contexts
    hwnd_dc   = win32gui.GetWindowDC(hwnd)
    mfc_dc    = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc   = mfc_dc.CreateCompatibleDC()

    # Create bitmap
    bitmap    = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
    save_dc.SelectObject(bitmap)

    # BitBlt — copy window pixels into bitmap
    # Use PrintWindow for better compatibility (works with hardware-accelerated windows)
    result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)

    if not result:
        # Fallback to BitBlt
        save_dc.BitBlt((0, 0), (w, h), mfc_dc, (0, 0), win32con.SRCCOPY)

    # Convert bitmap to numpy array
    bmp_info = bitmap.GetInfo()
    bmp_str  = bitmap.GetBitmapBits(True)
    img = np.frombuffer(bmp_str, dtype=np.uint8)
    img = img.reshape((bmp_info['bmHeight'], bmp_info['bmWidth'], 4))  # BGRA

    # Cleanup
    win32gui.DeleteObject(bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)

    # Convert BGRA to BGR and resize to target
    # frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    # frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
    # return frame
    # Convert BGRA to BGR
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # Crop to ultrasound image only — trim Echo Wave II toolbars
    # These are percentages of window size so they adapt to any window size
    h_full, w_full = frame.shape[:2]
    x1 = int(w_full * 0.22)   # trim left toolbar  (~22%)
    x2 = int(w_full * 0.78)   # trim right toolbar (~22%)
    y1 = int(h_full * 0.04)   # trim top bar       (~4%)
    y2 = int(h_full * 0.92)   # trim bottom bar    (~8%)
    frame = frame[y1:y2, x1:x2]

    # Resize cropped region to target output size
    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
    return frame


def handle_client(conn, addr, hwnd):
    """Stream the captured window to Quest 3."""
    print(f"Quest 3 connected from {addr}")
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
    frames_sent   = 0
    start_time    = time.time()
    frame_delay   = 1.0 / FPS

    try:
        while True:
            t_start = time.time()

            # Check window still exists
            if not win32gui.IsWindow(hwnd):
                print("MicrUs window closed — stopping.")
                break

            frame = capture_hwnd(hwnd)
            if frame is None:
                time.sleep(0.05)
                continue

            success, buffer = cv2.imencode('.jpg', frame, encode_params)
            if not success:
                continue

            data   = buffer.tobytes()
            size   = len(data)
            header = struct.pack('>I', size)
            conn.sendall(header + data)
            frames_sent += 1

            elapsed = time.time() - start_time
            if elapsed >= 5.0:
                print(f"Streaming — {frames_sent / elapsed:.1f} FPS  |  "
                      f"Frame size: {size / 1024:.1f} KB")
                frames_sent = 0
                start_time  = time.time()

            t_elapsed = time.time() - t_start
            sleep_for = frame_delay - t_elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

    except (BrokenPipeError, ConnectionResetError, OSError):
        print(f"Quest 3 at {addr} disconnected")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        conn.close()


def main():
    print("=" * 50)
    print("   MicrUs Ultrasound -> Quest 3 Streaming Server")
    print("=" * 50)
    print(f"\nOutput : {FRAME_WIDTH}x{FRAME_HEIGHT} @ {FPS}FPS  JPEG={JPEG_QUALITY}")

    print("\nLooking for MicrUs window...")
    hwnd = find_window_handle(WINDOW_TITLE_HINT)

    print(f"\nPort : {PORT}")

    # Broadcast this PC's IP + ports so Unity can auto-discover it
    from shared_discovery import start_broadcaster
    start_broadcaster("ultrasound", {"video": PORT, "control": 5001}, broadcast_port=5003)

    print("Make sure Quest 3 is on the same network.\n")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen(1)

    print("Waiting for Quest 3 to connect...")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            conn, addr = server.accept()
            handle_client(conn, addr, hwnd)
            print("\nWaiting for Quest 3 to reconnect...")
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.close()


if __name__ == "__main__":
    main()