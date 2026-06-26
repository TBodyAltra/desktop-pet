"""Minecraft-style blocky cat sprites."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap

from pet.drops import Drop, DropKind


CANVAS = 112
SCALE = 4


class Pose(Enum):
    IDLE = auto()
    BLINK = auto()
    WALK = auto()
    HAPPY = auto()
    SLEEP = auto()
    DEBUG = auto()
    PANIC = auto()


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
    ear_inner: QColor
    eye: QColor
    eye_shine: QColor
    nose: QColor
    whisker: QColor
    zzz: QColor
    heart: QColor
    grass: QColor
    dirt: QColor
    accent: QColor = field(default_factory=lambda: QColor("#FF3030"))
    sweat: QColor = field(default_factory=lambda: QColor("#4FC3F7"))


def palette_for(variant: CatVariant) -> Palette:
    if variant == CatVariant.TUXEDO:
        return Palette(
            outline=QColor("#101010"),
            fur=QColor("#1A1A1A"),
            fur_dark=QColor("#0A0A0A"),
            belly=QColor("#F2F2F2"),
            ear_inner=QColor("#D8D8D8"),
            eye=QColor("#1A1A1A"),
            eye_shine=QColor("#FFFFFF"),
            nose=QColor("#D0A0A0"),
            whisker=QColor("#303030"),
            zzz=QColor("#FFFFFF"),
            heart=QColor("#FF2020"),
            grass=QColor("#5D9C2E"),
            dirt=QColor("#8B6914"),
        )
    if variant == CatVariant.SIAMESE:
        return Palette(
            outline=QColor("#2A1A10"),
            fur=QColor("#E8DCC8"),
            fur_dark=QColor("#4A3728"),
            belly=QColor("#F5EDE0"),
            ear_inner=QColor("#6A4A38"),
            eye=QColor("#4FC3F7"),
            eye_shine=QColor("#FFFFFF"),
            nose=QColor("#8A5A5A"),
            whisker=QColor("#4A3728"),
            zzz=QColor("#FFFFFF"),
            heart=QColor("#FF2020"),
            grass=QColor("#5D9C2E"),
            dirt=QColor("#8B6914"),
        )
    return Palette(
        outline=QColor("#1A1208"),
        fur=QColor("#C68C28"),
        fur_dark=QColor("#8B5A18"),
        belly=QColor("#E8C878"),
        ear_inner=QColor("#D9A060"),
        eye=QColor("#1A1A1A"),
        eye_shine=QColor("#FFFFFF"),
        nose=QColor("#C06060"),
        whisker=QColor("#3D2810"),
        zzz=QColor("#FFFFFF"),
        heart=QColor("#FF2020"),
        grass=QColor("#5D9C2E"),
        dirt=QColor("#8B6914"),
    )


def _px(painter: QPainter, x: int, y: int, color: QColor, size: int = SCALE) -> None:
    painter.fillRect(int(x * SCALE), int(y * SCALE), size, size, color)


def _fill_rect(painter: QPainter, x: int, y: int, w: int, h: int, color: QColor) -> None:
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
    _fill_rect(painter, x, y, w, h, fill)
    for col in range(w):
        _px(painter, x + col, y, palette.outline)
        _px(painter, x + col, y + h - 1, palette.outline)
    for row in range(h):
        _px(painter, x, y + row, palette.outline)
        _px(painter, x + w - 1, y + row, palette.outline)


def _draw_variant_marks(
    painter: QPainter,
    palette: Palette,
    variant: CatVariant,
    x: int,
    y: int,
) -> None:
    if variant == CatVariant.TUXEDO:
        for col in range(2, 6):
            _px(painter, x + col, y + 2, palette.belly)
            _px(painter, x + col, y + 3, palette.belly)
        _px(painter, x + 3, y + 6, palette.belly)
        _px(painter, x + 4, y + 6, palette.belly)
    elif variant == CatVariant.SIAMESE:
        for row in range(2, 6):
            for col in range(2, 6):
                _px(painter, x + col, y + row, palette.fur_dark)
        for col in range(3, 5):
            _px(painter, x + col, y + 6, palette.fur)


def _draw_head(
    painter: QPainter,
    palette: Palette,
    variant: CatVariant,
    *,
    eyes_open: bool,
    happy: bool,
    panic: bool,
    x: int = 8,
    y: int = 4,
) -> None:
    _draw_block_outline(painter, x, y, 8, 7, palette.fur, palette)
    _draw_variant_marks(painter, palette, variant, x, y)

    _px(painter, x, y - 1, palette.fur_dark)
    _px(painter, x + 1, y - 2, palette.fur_dark)
    _px(painter, x + 1, y - 1, palette.ear_inner)
    _px(painter, x + 7, y - 1, palette.fur_dark)
    _px(painter, x + 6, y - 2, palette.fur_dark)
    _px(painter, x + 6, y - 1, palette.ear_inner)

    if variant == CatVariant.TABBY:
        for col in range(2, 6):
            _px(painter, x + col, y + 1, palette.fur_dark)

    if panic:
        for eye_x in (x + 1, x + 4):
            _fill_rect(painter, eye_x, y + 2, 3, 2, palette.eye)
            _px(painter, eye_x + 1, y + 2, palette.eye_shine)
        _fill_rect(painter, x + 2, y + 5, 4, 2, palette.outline)
        _px(painter, x + 7, y + 1, palette.sweat)
        _px(painter, x + 7, y + 2, palette.sweat)
    elif happy:
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

    for whisker_y in (y + 4, y + 5):
        _px(painter, x - 1, whisker_y, palette.whisker)
        _px(painter, x + 8, whisker_y, palette.whisker)


def _draw_body(painter: QPainter, palette: Palette, variant: CatVariant, x: int = 8, y: int = 11) -> None:
    _draw_block_outline(painter, x, y, 8, 5, palette.fur, palette)
    for col in range(2, 6):
        _px(painter, x + col, y + 2, palette.belly)
        _px(painter, x + col, y + 3, palette.belly)
    if variant == CatVariant.TABBY:
        _px(painter, x + 3, y + 1, palette.fur_dark)
        _px(painter, x + 4, y + 1, palette.fur_dark)
    if variant == CatVariant.TUXEDO:
        _px(painter, x + 1, y + 1, palette.belly)
        _px(painter, x + 6, y + 1, palette.belly)


def _draw_legs(
    painter: QPainter,
    palette: Palette,
    frame: int,
    *,
    x: int = 8,
    y: int = 16,
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
    x: int = 8,
    y: int = 12,
) -> None:
    swing = frame % 4
    segments = [(palette.fur_dark, 0), (palette.fur, 1), (palette.fur_dark, 2)]
    base_x = x - 2 if facing_left else x + 8
    direction = -1 if facing_left else 1

    for index, (color, lift) in enumerate(segments):
        seg_x = base_x + direction * index
        seg_y = y + lift - (1 if swing in {1, 2} and index == 2 else 0)
        _px(painter, seg_x, seg_y, color)
        _px(painter, seg_x, seg_y + 1, color)


def _draw_grass_patch(painter: QPainter, palette: Palette, x: int = 7, y: int = 18) -> None:
    for col in range(10):
        color = palette.grass if col % 2 == 0 else palette.dirt
        _px(painter, x + col, y, color)


def _draw_debug_badge(painter: QPainter, palette: Palette, frame: int) -> None:
    blink = frame % 20 < 10
    if blink:
        _fill_rect(painter, 11, 1, 2, 2, palette.accent)
        _px(painter, 11, 1, QColor("#FFFFFF"))


def _draw_sleeping_cat(painter: QPainter, palette: Palette, variant: CatVariant) -> None:
    _draw_block_outline(painter, 6, 13, 12, 4, palette.fur, palette)
    _draw_block_outline(painter, 4, 12, 4, 4, palette.fur, palette)
    if variant == CatVariant.SIAMESE:
        for row in range(1, 3):
            for col in range(1, 3):
                _px(painter, 4 + col, 12 + row, palette.fur_dark)
    _px(painter, 5, 11, palette.fur_dark)
    _px(painter, 6, 11, palette.fur_dark)
    _px(painter, 5, 13, palette.outline)
    _px(painter, 6, 13, palette.outline)
    _px(painter, 16, 13, palette.fur_dark)
    _px(painter, 17, 13, palette.fur)
    _px(painter, 18, 13, palette.fur_dark)


def _draw_zzz(painter: QPainter, palette: Palette, frame: int) -> None:
    letters = ("z", "Z", "z")
    font = painter.font()
    font.setPixelSize(10)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(palette.zzz)
    for index, letter in enumerate(letters):
        offset = (frame + index) % 3
        painter.drawText(68 + index * 10, 15 - offset * 4, letter)


def _draw_mc_heart(painter: QPainter, palette: Palette, cx: int, cy: int) -> None:
    heart = [" ## ", "####", "####", " ## "]
    for row, line in enumerate(heart):
        for col, ch in enumerate(line):
            if ch == "#":
                _px(painter, cx + col, cy + row, palette.heart)


def _draw_hearts(painter: QPainter, palette: Palette, frame: int) -> None:
    for index in range(3):
        bob = (frame + index * 2) % 5
        _draw_mc_heart(painter, palette, 17 + index * 3, 2 - bob)


def _draw_xp_orb(painter: QPainter, drop: Drop) -> None:
    colors = [QColor("#9CFF2E"), QColor("#5DCC10"), QColor("#D8FF70")]
    for row in range(3):
        for col in range(3):
            _px(painter, drop.x + col, drop.y + row, colors[(row + col) % 3])


def _draw_fish(painter: QPainter, drop: Drop) -> None:
    body = QColor("#FF8866")
    highlight = QColor("#FFBBAA")
    _fill_rect(painter, drop.x, drop.y + 1, 3, 2, body)
    _px(painter, drop.x + 1, drop.y, highlight)
    _px(painter, drop.x + 3, drop.y + 1, body)
    _px(painter, drop.x + 3, drop.y + 2, QColor("#DD6040"))


def _draw_drops(painter: QPainter, drops: list[Drop]) -> None:
    for drop in drops:
        if drop.kind == DropKind.XP:
            _draw_xp_orb(painter, drop)
        else:
            _draw_fish(painter, drop)


def _draw_standing_cat(
    painter: QPainter,
    palette: Palette,
    variant: CatVariant,
    frame: int,
    *,
    pose: Pose,
    facing_left: bool,
) -> None:
    _draw_grass_patch(painter, palette)
    _draw_tail(painter, palette, frame, facing_left=facing_left)
    _draw_body(painter, palette, variant)
    _draw_legs(painter, palette, frame, walking=pose == Pose.WALK)
    _draw_head(
        painter,
        palette,
        variant,
        eyes_open=pose not in {Pose.BLINK, Pose.DEBUG},
        happy=pose == Pose.HAPPY,
        panic=pose == Pose.PANIC,
    )
    if pose == Pose.HAPPY:
        _draw_hearts(painter, palette, frame)
    if pose == Pose.DEBUG:
        _draw_debug_badge(painter, palette, frame)


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
    y_offset = 1 if pose in {Pose.IDLE, Pose.WALK, Pose.HAPPY, Pose.PANIC} and bounce in {1, 3} else 0
    if pose == Pose.PANIC and bounce in {0, 2}:
        y_offset = 0
    painter.translate(0, y_offset * SCALE)

    if facing_left:
        painter.translate(CANVAS, 0)
        painter.scale(-1, 1)

    if pose == Pose.SLEEP:
        _draw_sleeping_cat(painter, palette, variant)
        _draw_zzz(painter, palette, frame)
    else:
        _draw_standing_cat(
            painter,
            palette,
            variant,
            frame,
            pose=pose,
            facing_left=False,
        )

    if drops:
        _draw_drops(painter, drops)

    painter.end()
    return pixmap
