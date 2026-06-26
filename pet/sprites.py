"""Procedural pixel-art sprites for the desktop pet."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap


CANVAS = 96
SCALE = 4


class Pose(Enum):
    IDLE = auto()
    BLINK = auto()
    WALK = auto()
    HAPPY = auto()
    SLEEP = auto()


@dataclass(frozen=True)
class Palette:
    outline: QColor = field(default_factory=lambda: QColor("#2b1d0e"))
    fur: QColor = field(default_factory=lambda: QColor("#f4a442"))
    fur_dark: QColor = field(default_factory=lambda: QColor("#d97706"))
    belly: QColor = field(default_factory=lambda: QColor("#fde68a"))
    cheek: QColor = field(default_factory=lambda: QColor("#fca5a5"))
    eye: QColor = field(default_factory=lambda: QColor("#1f2937"))
    eye_shine: QColor = field(default_factory=lambda: QColor("#ffffff"))
    nose: QColor = field(default_factory=lambda: QColor("#fb7185"))
    whisker: QColor = field(default_factory=lambda: QColor("#78350f"))
    zzz: QColor = field(default_factory=lambda: QColor("#6366f1"))


PALETTE = Palette()


def _px(painter: QPainter, x: int, y: int, color: QColor, size: int = SCALE) -> None:
    painter.fillRect(x * SCALE, y * SCALE, size, size, color)


def _draw_cat_body(painter: QPainter, palette: Palette, bounce: int, facing_left: bool) -> None:
    tail_swing = 1 if bounce % 2 == 0 else 0
    ear_tilt = 1 if bounce % 3 == 0 else 0

    if facing_left:
        tail_x = 17 + tail_swing
        ear_left = 8 + ear_tilt
        ear_right = 12 - ear_tilt
    else:
        tail_x = 4 - tail_swing
        ear_left = 8 - ear_tilt
        ear_right = 12 + ear_tilt

    # Tail
    for y in range(10, 14):
        _px(painter, tail_x, y, palette.fur_dark)
    _px(painter, tail_x + (1 if facing_left else -1), 9, palette.fur_dark)

    # Body
    for y in range(12, 18):
        for x in range(7, 15):
            color = palette.belly if 9 <= x <= 12 and y >= 14 else palette.fur
            _px(painter, x, y, color)

    # Back stripe
    for y in range(12, 15):
        _px(painter, 11, y, palette.fur_dark)

    # Paws
    for x in (8, 10, 12, 14):
        _px(painter, x, 18, palette.outline)

    # Head
    for y in range(6, 12):
        for x in range(7, 15):
            _px(painter, x, y, palette.fur)

    # Ears
    _px(painter, ear_left, 5, palette.fur_dark)
    _px(painter, ear_left + 1, 4, palette.fur_dark)
    _px(painter, ear_right, 5, palette.fur_dark)
    _px(painter, ear_right + 1, 4, palette.fur_dark)
    _px(painter, ear_left + 1, 5, palette.cheek)
    _px(painter, ear_right + 1, 5, palette.cheek)


def _draw_face(
    painter: QPainter,
    palette: Palette,
    *,
    eyes_open: bool,
    happy: bool,
    facing_left: bool,
) -> None:
    _px(painter, 11, 9, palette.nose)

    if happy:
        for dx in (-1, 1):
            _px(painter, 10 + dx, 10, palette.outline)
            _px(painter, 10 + dx, 11, palette.outline)
        return

    if eyes_open:
        for dx in (-2, 2):
            eye_x = 10 + dx
            _px(painter, eye_x, 8, palette.eye)
            _px(painter, eye_x + (1 if dx > 0 else -1), 8, palette.eye_shine)
    else:
        for dx in (-2, 2):
            _px(painter, 10 + dx, 8, palette.outline)

    mouth_x = 11
    # Whiskers
    side = -1 if facing_left else 1
    for y in (9, 10):
        _px(painter, mouth_x + side * 3, y, palette.whisker)
        _px(painter, mouth_x + side * 4, y, palette.whisker)
    _px(painter, mouth_x, 10, palette.outline)


def _draw_zzz(painter: QPainter, palette: Palette, frame: int) -> None:
    letters = ("z", "Z", "z")
    for index, letter in enumerate(letters):
        offset = (frame + index) % 3
        painter.setPen(palette.zzz)
        painter.setFont(painter.font())
        painter.drawText(58 + index * 10, 18 - offset * 4, letter)


def _draw_hearts(painter: QPainter, frame: int) -> None:
    colors = [QColor("#fb7185"), QColor("#f472b6"), QColor("#fda4af")]
    for index, color in enumerate(colors):
        y = 8 - ((frame + index) % 4)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        cx = 62 + index * 12
        painter.drawEllipse(cx, y * SCALE, 6, 6)
        painter.drawEllipse(cx + 5, y * SCALE, 6, 6)
        painter.drawEllipse(cx + 2, (y + 1) * SCALE - 2, 8, 8)


def render_frame(
    pose: Pose,
    frame: int,
    *,
    facing_left: bool = False,
    palette: Palette = PALETTE,
) -> QPixmap:
    pixmap = QPixmap(CANVAS, CANVAS)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    bounce = frame % 4
    y_offset = 1 if pose in {Pose.IDLE, Pose.WALK, Pose.HAPPY} and bounce in {1, 3} else 0
    painter.translate(0, y_offset * SCALE)

    if pose == Pose.SLEEP:
        for y in range(13, 18):
            for x in range(7, 15):
                _px(painter, x, y, palette.fur if y < 16 else palette.fur_dark)
        for x in range(8, 14):
            _px(painter, x, 12, palette.fur)
        _px(painter, 9, 11, palette.fur_dark)
        _px(painter, 14, 11, palette.fur_dark)
        for dx in (-2, 2):
            _px(painter, 10 + dx, 10, palette.outline)
        _draw_zzz(painter, palette, frame)
    else:
        _draw_cat_body(painter, palette, bounce, facing_left)
        _draw_face(
            painter,
            palette,
            eyes_open=pose != Pose.BLINK,
            happy=pose == Pose.HAPPY,
            facing_left=facing_left,
        )
        if pose == Pose.HAPPY:
            _draw_hearts(painter, frame)

    painter.end()
    return pixmap
