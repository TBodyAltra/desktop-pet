"""Detect foreground app context and git status on Windows."""

from __future__ import annotations

import subprocess
import sys
from enum import Enum, auto
from pathlib import Path


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


def get_foreground_process_dir() -> Path | None:
    if sys.platform != "win32":
        return None

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None

    process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))

    process_handle = kernel32.OpenProcess(0x1000, False, process_id.value)
    if not process_handle:
        return None

    try:
        buffer = ctypes.create_unicode_buffer(260)
        size = wintypes.DWORD(260)
        if not kernel32.QueryFullProcessImageNameW(process_handle, 0, buffer, ctypes.byref(size)):
            return None
        return Path(buffer.value).parent
    finally:
        kernel32.CloseHandle(process_handle)


def find_git_root(start: Path | None) -> Path | None:
    if start is None or not start.exists():
        return None

    current = start if start.is_dir() else start.parent
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists():
            return candidate
    return None


def get_git_status_message(search_dirs: list[Path] | None = None) -> str:
    candidates: list[Path] = []
    if search_dirs:
        candidates.extend(search_dirs)

    foreground_dir = get_foreground_process_dir()
    if foreground_dir is not None:
        candidates.append(foreground_dir)

    candidates.append(Path.home())

    seen: set[Path] = set()
    for candidate in candidates:
        git_root = find_git_root(candidate)
        if git_root is None or git_root in seen:
            continue
        seen.add(git_root)

        try:
            merge_head = git_root / ".git" / "MERGE_HEAD"
            if merge_head.exists():
                return f"{git_root.name}: merge conflict!"

            result = subprocess.run(
                ["git", "-C", str(git_root), "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode != 0:
                continue

            lines = [line for line in result.stdout.splitlines() if line.strip()]
            if not lines:
                return f"{git_root.name}: working tree clean"
            return f"{git_root.name}: {len(lines)} file(s) changed"
        except (OSError, subprocess.SubprocessError):
            continue

    return "no git repo found"


def detect_context() -> ForegroundContext:
    title = get_foreground_title()
    if not title:
        return ForegroundContext.UNKNOWN
    return _classify_title(title)
