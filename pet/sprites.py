"""Minecraft-style blocky cat sprites."""

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
    """Minecraft-inspired tabby cat palette."""

    outline: QColor = field(default_factory=lambda: QColor("#1A1208"))
    fur: QColor = field(default_factory=lambda: QColor("#C68C28"))
    fur_dark: QColor = field(default_factory=lambda: QColor("#8B5A18"))
    belly: QColor = field(default_factory=lambda: QColor("#E8C878"))
    ear_inner: QColor = field(default_factory=lambda: QColor("#D9A060"))
    eye: QColor = field(default_factory=lambda: QColor("#1A1A1A"))
    eye_shine: QColor = field(default_factory=lambda: QColor("#FFFFFF"))
    nose: QColor = field(default_factory=lambda: QColor("#C06060"))
    whisker: QColor = field(default_factory=lambda: QColor("#3D2810"))
    zzz: QColor = field(default_factory=lambda: QColor("#FFFFFF"))
    heart: QColor = field(default_factory=lambda: QColor("#FF2020"))
    grass: QColor = field(default_factory=lambda: QColor("#5D9C2E"))
    dirt: QColor = field(default_factory=lambda: QColor("#8B6914"))


PALETTE = Palette()


def _px(painter: QPainter, x: int, y: int, color: QColor, size: int = SCALE) -> None:
    painter.fillRect(x * SCALE, y * SCALE, size, size, color)


def _fill_rect(
    painter: QPainter,
    x: int,
    y: int,
    w: int,
    h: int,
    color: QColor,
    palette: Palette,
) -> None:
    for row in range(h):
        for col in range(w):
            _px(painter, x + col, y + row, color)


def _draw_block_outline(
    painter: QPainter,
    x: int,
    y: int,
    w: int,
    h: int,
    fill: QColor,
    palette: Palette,
) -> None:
    _fill_rect(painter, x, y, w, h, fill, palette)
    for col in range(w):
        _px(painter, x + col, y, palette.outline)
        _px(painter, x + col, y + h - 1, palette.outline)
    for row in range(h):
        _px(painter, x, y + row, palette.outline)
        _px(painter, x + w - 1, y + row, palette.outline)


def _draw_head(
    painter: QPainter,
    palette: Palette,
    *,
    eyes_open: bool,
    happy: bool,
    x: int = 6,
    y: int = 3,
) -> None:
    _draw_block_outline(painter, x, y, 8, 7, palette.fur, palette)

    # Ears poking out of head corners.
    _px(painter, x, y - 1, palette.fur_dark)
    _px(painter, x + 1, y - 2, palette.fur_dark)
    _px(painter, x + 1, y - 1, palette.ear_inner)
    _px(painter, x + 7, y - 1, palette.fur_dark)
    _px(painter, x + 6, y - 2, palette.fur_dark)
    _px(painter, x + 6, y - 1, palette.ear_inner)

    # Stripe on forehead.
    for col in range(2, 6):
        _px(painter, x + col, y + 1, palette.fur_dark)

    if happy:
        # Wide blocky grin.
        for col in range(2, 6):
            _px(painter, x + col, y + 5, palette.outline)
        _px(painter, x + 2, y + 4, palette.outline)
        _px(painter, x + 5, y + 4, palette.outline)
    else:
        if eyes_open:
            for eye_x in (x + 2, x + 5):
                _px(painter, eye_x, y + 3, palette.eye)
                _px(painter, eye_x + 1, y + 3, palette.eye_shine)
        else:
            for eye_x in (x + 2, x + 5):
                _px(painter, eye_x, y + 3, palette.outline)
                _px(painter, eye_x + 1, y + 3, palette.outline)

        _px(painter, x + 3, y + 5, palette.nose)
        _px(painter, x + 4, y + 5, palette.nose)
        _px(painter, x + 2, y + 6, palette.outline)
        _px(painter, x + 5, y + 6, palette.outline)

    # Whiskers as single-pixel lines.
    for whisker_y in (y + 4, y + 5):
        _px(painter, x - 1, whisker_y, palette.whisker)
        _px(painter, x + 8, whisker_y, palette.whisker)


def _draw_body(painter: QPainter, palette: Palette, x: int = 6, y: int = 10) -> None:
    _draw_block_outline(painter, x, y, 8, 5, palette.fur, palette)
    for col in range(2, 6):
        _px(painter, x + col, y + 2, palette.belly)
        _px(painter, x + col, y + 3, palette.belly)
    _px(painter, x + 3, y + 1, palette.fur_dark)
    _px(painter, x + 4, y + 1, palette.fur_dark)


def _draw_legs(
    painter: QPainter,
    palette: Palette,
    frame: int,
    *,
    x: int = 6,
    y: int = 15,
    walking: bool = False,
) -> None:
    step = frame % 2 if walking else 0
    front_offset = 1 if step == 0 else 0
    back_offset = 0 if step == 0 else 1

    for leg_x, offset in ((x + 1, front_offset), (x + 5, back_offset)):
        for row in range(2):
            color = palette.fur_dark if row == 1 else palette.fur
            _px(painter, leg_x, y + offset + row, color)
            _px(painter, leg_x + 1, y + offset + row, color)


def _draw_tail(
    painter: QPainter,
    palette: Palette,
    frame: int,
    *,
    facing_left: bool,
    x: int = 6,
    y: int = 11,
) -> None:
    swing = frame % 4
    segments = [
        (palette.fur_dark, 0),
        (palette.fur, 1),
        (palette.fur_dark, 2),
    ]
    base_x = x - 2 if facing_left else x + 8
    direction = -1 if facing_left else 1

    for index, (color, lift) in enumerate(segments):
        seg_x = base_x + direction * index
        seg_y = y + lift - (1 if swing in {1, 2} and index == 2 else 0)
        _px(painter, seg_x, seg_y, color)
        _px(painter, seg_x, seg_y + 1, color)


def _draw_grass_patch(painter: QPainter, palette: Palette, x: int = 5, y: int = 17) -> None:
    for col in range(10):
        color = palette.grass if col % 2 == 0 else palette.dirt
        _px(painter, x + col, y, color)


def _draw_sleeping_cat(painter: QPainter, palette: Palette) -> None:
    _draw_block_outline(painter, 4, 12, 12, 4, palette.fur, palette)
    _draw_block_outline(painter, 2, 11, 4, 4, palette.fur, palette)
    _px(painter, 3, 10, palette.fur_dark)
    _px(painter, 4, 10, palette.fur_dark)
    _px(painter, 3, 12, palette.outline)
    _px(painter, 4, 12, palette.outline)
    _px(painter, 14, 12, palette.fur_dark)
    _px(painter, 15, 12, palette.fur)
    _px(painter, 16, 12, palette.fur_dark)


def _draw_zzz(painter: QPainter, palette: Palette, frame: int) -> None:
    letters = ("z", "Z", "z")
    font = painter.font()
    font.setPixelSize(10)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(palette.zzz)
    for index, letter in enumerate(letters):
        offset = (frame + index) % 3
        painter.drawText(58 + index * 10, 14 - offset * 4, letter)


def _draw_mc_heart(painter: QPainter, palette: Palette, cx: int, cy: int) -> None:
    # 5x4 pixel Minecraft heart.
    heart = [
        " ## ",
        "####",
        "####",
        " ## ",
    ]
    for row, line in enumerate(heart):
        for col, ch in enumerate(line):
            if ch == "#":
                _px(painter, cx + col, cy + row, palette.heart)


def _draw_hearts(painter: QPainter, palette: Palette, frame: int) -> None:
    for index in range(3):
        bob = (frame + index * 2) % 5
        _draw_mc_heart(painter, palette, 15 + index * 3, 2 - bob)


def _draw_standing_cat(
    painter: QPainter,
    palette: Palette,
    frame: int,
    *,
    pose: Pose,
    facing_left: bool,
) -> None:
    _draw_grass_patch(painter, palette)
    _draw_tail(painter, palette, frame, facing_left=facing_left)
    _draw_body(painter, palette)
    _draw_legs(
        painter,
        palette,
        frame,
        walking=pose == Pose.WALK,
    )
    _draw_head(
        painter,
        palette,
        eyes_open=pose != Pose.BLINK,
        happy=pose == Pose.HAPPY,
    )
    if pose == Pose.HAPPY:
        _draw_hearts(painter, palette, frame)


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

    if facing_left:
        painter.translate(CANVAS, 0)
        painter.scale(-1, 1)

    if pose == Pose.SLEEP:
        _draw_sleeping_cat(painter, palette)
        _draw_zzz(painter, palette, frame)
    else:
        _draw_standing_cat(
            painter,
            palette,
            frame,
            pose=pose,
            facing_left=False,
        )

    painter.end()
    return pixmap
