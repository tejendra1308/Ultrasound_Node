"""
Windows-only window capture.

WindowCapture knows how to find a window by (partial) title, grab its pixels,
and hand back a cropped/resized BGR numpy frame. It doesn't know or care
what happens to that frame afterwards — that's the caller's job (stream it,
save it, run CV on it, whatever).
"""

import sys
import ctypes

import cv2
import numpy as np
import win32gui
import win32ui
import win32con


class WindowNotFoundError(RuntimeError):
    pass


class WindowCapture:
    def __init__(self, title_hint, crop=(0.22, 0.78, 0.04, 0.92), output_size=(1707, 1067)):
        """
        title_hint : substring to match against visible window titles
        crop       : (left, right, top, bottom) fractions to trim from the raw capture
        output_size: (width, height) the final frame is resized to
        """
        self.title_hint = title_hint
        self.crop_left, self.crop_right, self.crop_top, self.crop_bottom = crop
        self.output_size = output_size
        self.hwnd = None

    @staticmethod
    def list_all_windows():
        titles = []
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title.strip():
                    titles.append((hwnd, title))
        win32gui.EnumWindows(callback, None)
        return titles

    def find(self):
        """Locate and cache the window handle. Raises WindowNotFoundError if not found."""
        matches = [
            (hwnd, title) for hwnd, title in self.list_all_windows()
            if self.title_hint.lower() in title.lower()
        ]
        if not matches:
            available = "\n".join(f"  [{h}] '{t}'" for h, t in self.list_all_windows())
            raise WindowNotFoundError(
                f"No window found containing '{self.title_hint}'.\n"
                f"Make sure the app is open and not minimized.\n"
                f"All visible windows:\n{available}"
            )
        self.hwnd, title = matches[0]
        print(f"Found window: '{title}'  [hwnd={self.hwnd}]")
        return self.hwnd

    def is_valid(self):
        return self.hwnd is not None and win32gui.IsWindow(self.hwnd)

    def capture(self):
        """Return a cropped/resized BGR frame, or None if capture failed."""
        if not self.is_valid():
            return None

        left, top, right, bottom = win32gui.GetClientRect(self.hwnd)
        w, h = right - left, bottom - top
        if w <= 0 or h <= 0:
            return None

        hwnd_dc = win32gui.GetWindowDC(self.hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
        save_dc.SelectObject(bitmap)

        # PrintWindow works with hardware-accelerated windows; BitBlt is the fallback.
        ok = ctypes.windll.user32.PrintWindow(self.hwnd, save_dc.GetSafeHdc(), 3)
        if not ok:
            save_dc.BitBlt((0, 0), (w, h), mfc_dc, (0, 0), win32con.SRCCOPY)

        bmp_info = bitmap.GetInfo()
        bmp_str = bitmap.GetBitmapBits(True)
        img = np.frombuffer(bmp_str, dtype=np.uint8)
        img = img.reshape((bmp_info["bmHeight"], bmp_info["bmWidth"], 4))  # BGRA

        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwnd_dc)

        return self._postprocess(img)

    def _postprocess(self, bgra_frame):
        frame = cv2.cvtColor(bgra_frame, cv2.COLOR_BGRA2BGR)
        h_full, w_full = frame.shape[:2]
        x1 = int(w_full * self.crop_left)
        x2 = int(w_full * self.crop_right)
        y1 = int(h_full * self.crop_top)
        y2 = int(h_full * self.crop_bottom)
        frame = frame[y1:y2, x1:x2]
        frame = cv2.resize(frame, self.output_size, interpolation=cv2.INTER_AREA)
        return frame
