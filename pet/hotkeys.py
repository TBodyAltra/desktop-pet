"""Global hotkey support on Windows."""

from __future__ import annotations

import sys
from typing import Callable

from PySide6.QtCore import QAbstractNativeEventFilter, QByteArray


class GlobalHotkeyFilter(QAbstractNativeEventFilter):
    WM_HOTKEY = 0x0312
    HOTKEY_ID = 0xC47

    def __init__(self, on_toggle: Callable[[], None]) -> None:
        super().__init__()
        self._on_toggle = on_toggle
        self._registered = False

    def register(self, window_id: int) -> bool:
        if sys.platform != "win32" or self._registered:
            return False

        import ctypes

        user32 = ctypes.windll.user32
        ok = user32.RegisterHotKey(window_id, self.HOTKEY_ID, 0x0001 | 0x0002, ord("P"))
        self._registered = bool(ok)
        return self._registered

    def unregister(self, window_id: int) -> None:
        if sys.platform != "win32" or not self._registered:
            return

        import ctypes

        ctypes.windll.user32.UnregisterHotKey(window_id, self.HOTKEY_ID)
        self._registered = False

    def nativeEventFilter(self, event_type: QByteArray, message: int) -> tuple[bool, int]:
        if sys.platform != "win32" or event_type != b"windows_generic_MSG":
            return False, 0

        import ctypes
        from ctypes import wintypes

        msg = ctypes.cast(message, ctypes.POINTER(wintypes.MSG)).contents
        if msg.message == self.WM_HOTKEY and msg.wParam == self.HOTKEY_ID:
            self._on_toggle()
            return True, 0
        return False, 0
