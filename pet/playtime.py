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
GRAVITY = 0.32
ACTIVITY_MIN = 200
ACTIVITY_MAX = 300
SESSION_MIN = 220
SESSION_MAX = 380


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

    def activity_label(self) -> str:
        labels = {
            ActivityKind.YARN: "玩毛线球",
            ActivityKind.LASER: "追激光点",
            ActivityKind.FEATHER: "扑逗猫棒",
            ActivityKind.MOUSE: "抓老鼠",
            ActivityKind.DOG: "快跑",
        }
        return labels[self.activity]

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
            self.toy_vx = random.choice([-1.2, 1.2])
            self.toy_vy = 0.0
        elif self.activity == ActivityKind.LASER:
            self.toy_x = random.uniform(60, 120)
            self.toy_y = random.uniform(50, 80)
        elif self.activity == ActivityKind.FEATHER:
            self.toy_x = float(CAT_X + random.uniform(-8, 20))
            self.toy_y = float(CAT_Y - 38)
            self.feather_bob = 0.0
        elif self.activity == ActivityKind.MOUSE:
            self._spawn_mouse()
        else:
            self.dog_x = float(PLAY_W + 20)
            self.facing_left = True

    def _spawn_mouse(self) -> None:
        self.mouse_x = random.uniform(88, 128)
        self.mouse_y = random.uniform(72, 84)
        self.mouse_vx = random.choice([-1.8, -1.4, 1.4, 1.8])

    def _cat_x(self) -> float:
        return CAT_X + self.cat_offset_x

    def _move_cat_toward(self, target_x: float, *, speed: float = 2.0) -> None:
        dx = target_x - self._cat_x()
        if abs(dx) <= 2:
            return
        self.cat_offset_x += speed if dx > 0 else -speed
        self.facing_left = dx < 0

    def _tick_yarn(self) -> None:
        self.toy_vy += GRAVITY
        self.toy_x += self.toy_vx
        self.toy_y += self.toy_vy

        floor = CAT_Y - 4
        if self.toy_y >= floor:
            self.toy_y = floor
            self.toy_vy = -abs(self.toy_vy) * 0.55
            if abs(self.toy_vy) < 0.5:
                self.toy_vy = 0.0

        if self.toy_x <= 20 or self.toy_x >= PLAY_W - 16:
            self.toy_vx *= -0.8
        self.toy_vx *= 0.995

        self._move_cat_toward(self.toy_x, speed=1.6)
        dist = math.hypot(self.toy_x - self._cat_x(), self.toy_y - (CAT_Y - 14))
        self.paw_up = dist < 20 and self.activity_ticks % 10 < 5

        if dist < 16 and abs(self.toy_vy) < 1.5:
            self.toy_vx = random.uniform(-2.5, 2.5)
            self.toy_vy = -random.uniform(2.0, 3.5)
            self.paw_up = True

    def _tick_laser(self) -> None:
        self.laser_angle += 0.09
        self.toy_x = 88 + math.sin(self.laser_angle) * 34
        self.toy_y = 62 + math.cos(self.laser_angle * 1.4) * 18

        if self.activity_ticks % 45 == 0:
            self.toy_x = random.uniform(52, 128)
            self.toy_y = random.uniform(48, 78)

        self._move_cat_toward(self.toy_x, speed=2.2)
        dist = math.hypot(self.toy_x - self._cat_x(), self.toy_y - (CAT_Y - 12))
        self.paw_up = dist < 18

        if dist < 10:
            self.celebrate_ticks = 8
            self.toy_x = random.uniform(52, 128)
            self.toy_y = random.uniform(48, 78)

    def _tick_feather(self) -> None:
        self.feather_bob += 0.14
        self.toy_x = CAT_X + 14 + math.sin(self.feather_bob) * 22
        self.toy_y = CAT_Y - 36 + math.cos(self.feather_bob * 1.6) * 10

        self._move_cat_toward(self.toy_x - 6, speed=1.4)
        self.facing_left = self.toy_x < self._cat_x()
        dist = math.hypot(self.toy_x - self._cat_x(), self.toy_y - (CAT_Y - 20))
        self.paw_up = dist < 24 and self.activity_ticks % 12 < 7

        if dist < 14 and self.activity_ticks % 20 == 0:
            self.toy_y = CAT_Y - 42
            self.paw_up = True

    def _tick_mouse(self) -> None:
        self.mouse_x += self.mouse_vx
        self.mouse_y += math.sin(self.activity_ticks * 0.22) * 0.35

        if self.mouse_x <= 18 or self.mouse_x >= PLAY_W - 10:
            self.mouse_vx *= -1

        dx = self.mouse_x - self._cat_x()
        step = 1.2 if abs(dx) > 28 else 2.4
        if abs(dx) > 4:
            self.cat_offset_x += step if dx > 0 else -step
            self.facing_left = dx < 0

        self.paw_up = abs(dx) < 22 and self.activity_ticks % 16 < 8

        if math.hypot(self.mouse_x - self._cat_x(), self.mouse_y - (CAT_Y - 10)) < 14:
            self.celebrate_ticks = 24
            self.paw_up = True
            self._spawn_mouse()
            self.cat_offset_x *= 0.4

    def _tick_dog(self) -> None:
        if self.dog_phase == 0:
            self.dog_x -= 2.8
            self.dog_wait += 1
            if self.dog_x < PLAY_W - 8 or self.dog_wait > 24:
                self.dog_phase = 1
            return

        flee_speed = 2.6 if self.dog_x - self._cat_x() < 36 else 1.8
        self.cat_offset_x -= flee_speed
        self.dog_x -= 2.2
        self.facing_left = True
        self.paw_up = self.activity_ticks % 6 < 3

        if self.cat_offset_x < -8:
            self.cat_offset_x = -8

        if self.dog_x < self._cat_x() - 50 or self.activity_ticks > 220:
            self.dog_phase = 2
            self.celebrate_ticks = 26
            self.dog_x = -30.0

        if self.dog_phase == 2:
            self.dog_x -= 3.0
