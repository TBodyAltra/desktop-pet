"""Detect the foreground application context on Windows."""

from __future__ import annotations

import sys
from enum import Enum, auto


class ForegroundContext(Enum):
    CODING = auto()
    TERMINAL = auto()
    BROWSING = auto()
    MEETING = auto()
    UNKNOWN = auto()


_CODING_KEYWORDS = ("cursor", "code", "visual studio", "idea", "pycharm", "vim", "nvim", "sublime")
_TERMINAL_KEYWORDS = ("terminal", "powershell", "cmd", "windowsterminal", "wsl", "git bash")
_BROWSER_KEYWORDS = ("chrome", "edge", "firefox", "bilibili", "youtube", "browser")
_MEETING_KEYWORDS = ("zoom", "teams", "meeting", "tencent", "feishu", "lark", "discord call")


def _classify_title(title: str) -> ForegroundContext:
    lowered = title.lower()
    if any(keyword in lowered for keyword in _MEETING_KEYWORDS):
        return ForegroundContext.MEETING
    if any(keyword in lowered for keyword in _TERMINAL_KEYWORDS):
        return ForegroundContext.TERMINAL
    if any(keyword in lowered for keyword in _CODING_KEYWORDS):
        return ForegroundContext.CODING
    if any(keyword in lowered for keyword in _BROWSER_KEYWORDS):
        return ForegroundContext.BROWSING
    return ForegroundContext.UNKNOWN


def get_foreground_title() -> str:
    if sys.platform != "win32":
        return ""

    import ctypes

    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""

    length = user32.GetWindowTextLengthW(hwnd) + 1
    buffer = ctypes.create_unicode_buffer(length)
    user32.GetWindowTextW(hwnd, buffer, length)
    return buffer.value.strip()


def detect_context() -> ForegroundContext:
    title = get_foreground_title()
    if not title:
        return ForegroundContext.UNKNOWN
    return _classify_title(title)
