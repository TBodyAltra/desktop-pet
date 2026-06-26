"""Procedural pixel-art sprites for the desktop pet (pre-Minecraft style)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap

from pet.drops import Drop, DropKind
from pet.playtime import CAT_X, CAT_Y, PLAY_H, PLAY_W, ActivityKind, PlaySession


CANVAS = 96
SCALE = 4


class Pose(Enum):
    IDLE = auto()
    BLINK = auto()
    WALK = auto()
    HAPPY = auto()
    SLEEP = auto()
    PLAY = auto()


class CatVariant(Enum):
    TABBY = auto()
    TUXEDO = auto()
    SIAMESE = auto()


@dataclass(frozen=True)
class Palette:
    outline: QColor
    fur: QColor
    fur_dark: QColor
    belly: QColor
    cheek: QColor
    eye: QColor
    eye_shine: QColor
    nose: QColor
    whisker: QColor
    zzz: QColor


def palette_for(variant: CatVariant) -> Palette:
    if variant == CatVariant.TUXEDO:
        return Palette(
            outline=QColor("#0d0d0d"),
            fur=QColor("#2b2b2b"),
            fur_dark=QColor("#141414"),
            belly=QColor("#f5f5f5"),
            cheek=QColor("#f9a8a8"),
            eye=QColor("#1f2937"),
            eye_shine=QColor("#ffffff"),
            nose=QColor("#f9a8c0"),
            whisker=QColor("#cfcfcf"),
            zzz=QColor("#6366f1"),
        )
    if variant == CatVariant.SIAMESE:
        return Palette(
            outline=QColor("#3d2b1a"),
            fur=QColor("#ece2cf"),
            fur_dark=QColor("#5b4633"),
            belly=QColor("#f7f0e2"),
            cheek=QColor("#f6c6b0"),
            eye=QColor("#2f9fe0"),
            eye_shine=QColor("#ffffff"),
            nose=QColor("#a9756b"),
            whisker=QColor("#7a6450"),
            zzz=QColor("#6366f1"),
        )
    return Palette(
        outline=QColor("#2b1d0e"),
        fur=QColor("#f4a442"),
        fur_dark=QColor("#d97706"),
        belly=QColor("#fde68a"),
        cheek=QColor("#fca5a5"),
        eye=QColor("#1f2937"),
        eye_shine=QColor("#ffffff"),
        nose=QColor("#fb7185"),
        whisker=QColor("#78350f"),
        zzz=QColor("#6366f1"),
    )


PALETTE = palette_for(CatVariant.TABBY)


def _px(painter: QPainter, x: int, y: int, color: QColor, size: int = SCALE) -> None:
    painter.fillRect(int(x * SCALE), int(y * SCALE), size, size, color)


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


def _draw_xp_orb(painter: QPainter, drop: Drop) -> None:
    colors = [QColor("#9CFF2E"), QColor("#5DCC10"), QColor("#D8FF70")]
    for row in range(3):
        for col in range(3):
            _px(painter, drop.x + col, drop.y + row, colors[(row + col) % 3])


def _draw_fish(painter: QPainter, drop: Drop) -> None:
    body = QColor("#FF8866")
    highlight = QColor("#FFBBAA")
    for row in range(2):
        for col in range(3):
            _px(painter, drop.x + col, drop.y + 1 + row, body)
    _px(painter, drop.x + 1, drop.y, highlight)
    _px(painter, drop.x + 3, drop.y + 1, body)
    _px(painter, drop.x + 3, drop.y + 2, QColor("#DD6040"))


def _draw_drops(painter: QPainter, drops: list[Drop]) -> None:
    for drop in drops:
        if drop.kind == DropKind.XP:
            _draw_xp_orb(painter, drop)
        else:
            _draw_fish(painter, drop)


def _draw_yarn_ball(painter: QPainter, x: float, y: float) -> None:
    cx = int(x)
    cy = int(y)
    painter.setPen(QColor("#fda4af"))
    painter.drawLine(cx, cy, cx - 8, cy + 6)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#fb7185"))
    painter.drawEllipse(cx - 6, cy - 5, 12, 10)
    painter.setBrush(QColor("#fecdd3"))
    painter.drawEllipse(cx - 3, cy - 3, 5, 4)


def _draw_laser_dot(painter: QPainter, x: float, y: float) -> None:
    cx = int(x)
    cy = int(y)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(255, 40, 40, 60))
    painter.drawEllipse(cx - 7, cy - 7, 14, 14)
    painter.setBrush(QColor("#ef4444"))
    painter.drawEllipse(cx - 3, cy - 3, 6, 6)


def _draw_feather_wand(painter: QPainter, x: float, y: float) -> None:
    cx = int(x)
    cy = int(y)
    painter.setPen(QColor("#a16207"))
    painter.drawLine(cx, cy + 14, cx - 4, cy + 28)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#fde047"))
    for dx, dy in ((0, 0), (-4, 2), (4, 1), (-2, -4), (3, -3)):
        painter.drawEllipse(cx + dx - 2, cy + dy - 2, 5, 7)


def _draw_mouse(painter: QPainter, x: float, y: float) -> None:
    cx = int(x)
    cy = int(y)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#9ca3af"))
    painter.drawEllipse(cx - 4, cy - 3, 8, 6)
    painter.setBrush(QColor("#fca5a5"))
    painter.drawEllipse(cx + 3, cy - 4, 3, 3)
    painter.drawLine(cx - 6, cy - 1, cx - 10, cy - 3)
    painter.drawLine(cx - 6, cy + 1, cx - 10, cy + 2)


def _draw_dog(painter: QPainter, x: float) -> None:
    if x < -20 or x > PLAY_W + 20:
        return
    cx = int(x)
    cy = 72
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#92400e"))
    painter.drawEllipse(cx - 10, cy - 10, 22, 14)
    painter.drawEllipse(cx + 8, cy - 16, 10, 10)
    painter.setBrush(QColor("#1f2937"))
    for px in (cx - 4, cx + 2):
        painter.drawEllipse(px, cy - 12, 3, 3)
    painter.setBrush(QColor("#78350f"))
    painter.drawEllipse(cx - 12, cy - 2, 5, 4)
    painter.drawEllipse(cx + 10, cy - 2, 5, 4)


def render_play_frame(
    session: PlaySession,
    frame: int,
    *,
    variant: CatVariant = CatVariant.TABBY,
) -> QPixmap:
    palette = palette_for(variant)
    pixmap = QPixmap(PLAY_W, PLAY_H)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    if session.activity == ActivityKind.DOG:
        _draw_dog(painter, session.dog_x)

    happy = session.celebrate_ticks > 0
    bounce = frame % 4
    cat_shift = int(session.cat_offset_x)
    painter.translate(CAT_X - 48 + cat_shift, CAT_Y - 48)

    _draw_cat_body(painter, palette, bounce, session.facing_left)
    if session.paw_up and not happy:
        paw_x = 15 if not session.facing_left else 7
        _px(painter, paw_x, 13, palette.fur)

    _draw_face(
        painter,
        palette,
        eyes_open=True,
        happy=happy,
        facing_left=session.facing_left,
    )
    if happy:
        _draw_hearts(painter, frame)

    painter.resetTransform()

    if session.activity == ActivityKind.YARN:
        _draw_yarn_ball(painter, session.toy_x, session.toy_y)
    elif session.activity == ActivityKind.LASER:
        _draw_laser_dot(painter, session.toy_x, session.toy_y)
    elif session.activity == ActivityKind.FEATHER:
        _draw_feather_wand(painter, session.toy_x, session.toy_y)
    elif session.activity == ActivityKind.MOUSE:
        _draw_mouse(painter, session.mouse_x, session.mouse_y)

    painter.end()
    return pixmap


def render_frame(
    pose: Pose,
    frame: int,
    *,
    facing_left: bool = False,
    variant: CatVariant = CatVariant.TABBY,
    drops: list[Drop] | None = None,
) -> QPixmap:
    palette = palette_for(variant)
    pixmap = QPixmap(CANVAS, CANVAS)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    bounce = frame % 4
    y_offset = 1 if pose == Pose.HAPPY and bounce in {1, 3} else 0
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

    if drops:
        _draw_drops(painter, drops)

    painter.end()
    return pixmap
