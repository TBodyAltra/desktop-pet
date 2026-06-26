"""Solo play activities and random encounters for the desktop cat."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum, auto


PLAY_W = 140
PLAY_H = 96
CAT_X = 46
CAT_Y = 68
GRAVITY = 0.18
ACTIVITY_MIN = 220
ACTIVITY_MAX = 320
SESSION_MIN = 240
SESSION_MAX = 400


class ActivityKind(Enum):
    YARN = auto()
    LASER = auto()
    FEATHER = auto()
    MOUSE = auto()
    DOG = auto()


@dataclass
class PlaySession:
    active: bool = False
    activity: ActivityKind = ActivityKind.YARN
    activity_ticks: int = 0
    activity_duration: int = 0
    celebrate_ticks: int = 0
    facing_left: bool = False
    paw_up: bool = False
    cat_offset_x: float = 0.0

    toy_x: float = 0.0
    toy_y: float = 0.0
    toy_vx: float = 0.0
    toy_vy: float = 0.0

    feather_bob: float = 0.0
    laser_angle: float = 0.0

    mouse_x: float = 100.0
    mouse_y: float = 78.0
    mouse_vx: float = 1.6

    dog_x: float = 150.0
    dog_phase: int = 0
    dog_wait: int = 0

    session_ticks: int = 0
    session_duration: int = 0

    def start(self, forced: ActivityKind | None = None) -> None:
        self.active = True
        self.celebrate_ticks = 0
        self.cat_offset_x = 0.0
        self.session_ticks = 0
        self.session_duration = random.randint(SESSION_MIN, SESSION_MAX)
        self._pick_activity(initial=True, forced=forced)

    def stop(self) -> None:
        self.active = False
        self.celebrate_ticks = 0
        self.paw_up = False
        self.cat_offset_x = 0.0
        self.session_ticks = 0

    def tick(self) -> bool:
        if not self.active:
            return False

        self.session_ticks += 1
        if self.session_ticks >= self.session_duration:
            self.stop()
            return True

        if self.celebrate_ticks > 0:
            self.celebrate_ticks -= 1
            return False

        self.activity_ticks += 1
        if self.activity_ticks >= self.activity_duration:
            self._pick_activity()
            return False

        tickers = {
            ActivityKind.YARN: self._tick_yarn,
            ActivityKind.LASER: self._tick_laser,
            ActivityKind.FEATHER: self._tick_feather,
            ActivityKind.MOUSE: self._tick_mouse,
            ActivityKind.DOG: self._tick_dog,
        }
        tickers[self.activity]()
        return False

    def _pick_activity(self, initial: bool = False, forced: ActivityKind | None = None) -> None:
        if forced is not None:
            self.activity = forced
        else:
            options = list(ActivityKind)
            if not initial:
                options = [kind for kind in options if kind != self.activity]
            self.activity = random.choice(options)
        self.activity_ticks = 0
        self.activity_duration = random.randint(ACTIVITY_MIN, ACTIVITY_MAX)
        self.facing_left = self.activity == ActivityKind.DOG
        self._reset_activity_state()

    def _reset_activity_state(self) -> None:
        self.paw_up = False
        self.cat_offset_x = 0.0
        self.dog_phase = 0
        self.dog_wait = 0
        self.laser_angle = random.uniform(0, math.tau)

        if self.activity == ActivityKind.YARN:
            self.toy_x = random.uniform(70, 110)
            self.toy_y = float(CAT_Y - 6)
            self.toy_vx = random.choice([-0.6, 0.6])
            self.toy_vy = 0.0
        elif self.activity == ActivityKind.LASER:
            self.toy_x = random.uniform(60, 120)
            self.toy_y = random.uniform(58, 76)
        elif self.activity == ActivityKind.FEATHER:
            self.toy_x = float(CAT_X + random.uniform(-8, 20))
            self.toy_y = float(CAT_Y - 32)
            self.feather_bob = 0.0
        elif self.activity == ActivityKind.MOUSE:
            self._spawn_mouse()
        else:
            self.dog_x = float(PLAY_W + 20)
            self.facing_left = True

    def _spawn_mouse(self) -> None:
        self.mouse_x = random.uniform(88, 128)
        self.mouse_y = random.uniform(72, 84)
        self.mouse_vx = random.choice([-1.0, -0.8, 0.8, 1.0])

    def _cat_x(self) -> float:
        return CAT_X + self.cat_offset_x

    def _move_cat_toward(self, target_x: float, *, speed: float = 0.9) -> None:
        dx = target_x - self._cat_x()
        if abs(dx) <= 1.5:
            return
        self.cat_offset_x += speed if dx > 0 else -speed
        self.facing_left = dx < 0

    def _tick_yarn(self) -> None:
        self.toy_x += self.toy_vx
        self.toy_vy += GRAVITY
        self.toy_y += self.toy_vy

        floor = CAT_Y - 4
        if self.toy_y >= floor:
            self.toy_y = floor
            self.toy_vy = 0.0

        if self.toy_x <= 24 or self.toy_x >= PLAY_W - 20:
            self.toy_vx *= -1

        self._move_cat_toward(self.toy_x, speed=0.8)
        dist = abs(self.toy_x - self._cat_x())
        self.paw_up = dist < 14 and self.activity_ticks % 28 < 4

        if dist < 12 and self.activity_ticks % 35 == 0:
            self.toy_vx = random.choice([-0.9, 0.9])
            self.paw_up = True

    def _tick_laser(self) -> None:
        self.laser_angle += 0.04
        self.toy_x = 88 + math.sin(self.laser_angle) * 28
        self.toy_y = 66 + math.cos(self.laser_angle * 1.2) * 8

        if self.activity_ticks % 70 == 0:
            self.toy_x = random.uniform(58, 118)
            self.toy_y = random.uniform(58, 74)

        self._move_cat_toward(self.toy_x, speed=0.85)
        dist = math.hypot(self.toy_x - self._cat_x(), self.toy_y - (CAT_Y - 10))
        self.paw_up = dist < 14 and self.activity_ticks % 32 < 3

        if dist < 11 and self.activity_ticks % 40 == 0:
            self.toy_x = random.uniform(58, 118)
            self.toy_y = random.uniform(58, 74)

    def _tick_feather(self) -> None:
        self.feather_bob += 0.06
        self.toy_x = CAT_X + 12 + math.sin(self.feather_bob) * 16
        self.toy_y = CAT_Y - 30 + math.cos(self.feather_bob) * 4

        self._move_cat_toward(self.toy_x - 4, speed=0.75)
        self.facing_left = self.toy_x < self._cat_x()
        dist = abs(self.toy_x - self._cat_x())
        self.paw_up = dist < 16 and self.activity_ticks % 36 < 4

    def _tick_mouse(self) -> None:
        self.mouse_x += self.mouse_vx
        self.mouse_y += math.sin(self.activity_ticks * 0.12) * 0.2

        if self.mouse_x <= 22 or self.mouse_x >= PLAY_W - 14:
            self.mouse_vx *= -1

        dx = self.mouse_x - self._cat_x()
        if abs(dx) > 3:
            step = 0.7 if abs(dx) > 24 else 1.0
            self.cat_offset_x += step if dx > 0 else -step
            self.facing_left = dx < 0

        self.paw_up = abs(dx) < 16 and self.activity_ticks % 30 < 3

        if math.hypot(self.mouse_x - self._cat_x(), self.mouse_y - (CAT_Y - 10)) < 12:
            self.celebrate_ticks = 16
            self.paw_up = True
            self._spawn_mouse()

    def _tick_dog(self) -> None:
        if self.dog_phase == 0:
            self.dog_x -= 1.8
            self.dog_wait += 1
            if self.dog_x < PLAY_W - 8 or self.dog_wait > 30:
                self.dog_phase = 1
            return

        flee_speed = 1.4 if self.dog_x - self._cat_x() < 36 else 1.0
        self.cat_offset_x -= flee_speed
        self.dog_x -= 1.5
        self.facing_left = True
        self.paw_up = False

        if self.cat_offset_x < -8:
            self.cat_offset_x = -8

        if self.dog_x < self._cat_x() - 50 or self.activity_ticks > 260:
            self.dog_phase = 2
            self.celebrate_ticks = 18
            self.dog_x = -30.0

        if self.dog_phase == 2:
            self.dog_x -= 2.0
