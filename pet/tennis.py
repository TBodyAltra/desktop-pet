"""Casual tennis rally between the cat and the cursor."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


COURT_W = 360
COURT_H = 140
BALL_R = 5
CAT_X = 36
USER_X = COURT_W - 36
NET_X = COURT_W // 2
HIT_RADIUS = 26
CAT_HIT_RADIUS = 22
BALL_SPEED = 4.2
SERVE_DELAY = 24
MAX_BALL_VY = 3.4


@dataclass
class TennisGame:
    active: bool = False
    ball_x: float = field(default=0.0, init=False)
    ball_y: float = field(default=0.0, init=False)
    ball_vx: float = 0.0
    ball_vy: float = 0.0
    rally: int = 0
    cat_y: float = field(default=0.0, init=False)
    facing_left: bool = False
    serving: bool = True
    serve_ticks: int = 0
    last_miss: str | None = None
    celebrate_ticks: int = 0

    def start(self) -> None:
        self.active = True
        self.rally = 0
        self.last_miss = None
        self.celebrate_ticks = 0
        self.cat_y = COURT_H / 2
        self._begin_serve()

    def stop(self) -> None:
        self.active = False
        self.ball_vx = 0.0
        self.ball_vy = 0.0
        self.serving = False
        self.serve_ticks = 0
        self.last_miss = None
        self.celebrate_ticks = 0

    def tick(self, cursor_x: float, cursor_y: float) -> tuple[int, int]:
        """Advance one frame. Returns cat vertical movement delta."""
        if not self.active:
            return 0, 0

        if self.celebrate_ticks > 0:
            self.celebrate_ticks -= 1
            return 0, 0

        if self.serving:
            self.serve_ticks -= 1
            self.ball_x = CAT_X + 18
            self.ball_y = self.cat_y
            if self.serve_ticks <= 0:
                self._launch_toward(cursor_x, cursor_y, from_cat=True)
                self.serving = False
            return self._move_cat_toward(self.ball_y)

        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        if self.ball_y <= BALL_R + 8:
            self.ball_y = BALL_R + 8
            self.ball_vy = abs(self.ball_vy)
        elif self.ball_y >= COURT_H - BALL_R - 8:
            self.ball_y = COURT_H - BALL_R - 8
            self.ball_vy = -abs(self.ball_vy)

        cat_dy = self._move_cat_toward(self.ball_y)

        if self.ball_vx < 0 and self.ball_x <= CAT_X + 14:
            if abs(self.ball_y - self.cat_y) <= CAT_HIT_RADIUS:
                self._launch_toward(cursor_x, cursor_y, from_cat=True)
                self.rally += 1
                self.facing_left = False
            else:
                self._on_miss("cat")

        elif self.ball_vx > 0 and self.ball_x >= COURT_W - BALL_R - 4:
            self._on_miss("user")

    def try_hit(self, click_x: float, click_y: float) -> bool:
        if not self.active or self.serving or self.celebrate_ticks > 0:
            return False
        if self.ball_vx <= 0 or self.ball_x < NET_X:
            return False
        if math.hypot(click_x - self.ball_x, click_y - self.ball_y) > HIT_RADIUS + 8:
            return False

        angle = math.atan2(click_y - self.cat_y, CAT_X - click_x)
        speed = BALL_SPEED + min(self.rally * 0.08, 2.0)
        self.ball_vx = -math.cos(angle) * speed
        self.ball_vy = math.sin(angle) * speed
        self.ball_vy = max(-MAX_BALL_VY, min(MAX_BALL_VY, self.ball_vy))
        self.facing_left = True
        self.rally += 1
        return True

    def _begin_serve(self) -> None:
        self.serving = True
        self.serve_ticks = SERVE_DELAY
        self.ball_x = CAT_X + 18
        self.ball_y = self.cat_y
        self.ball_vx = 0.0
        self.ball_vy = 0.0
        self.facing_left = False

    def _launch_toward(self, target_x: float, target_y: float, *, from_cat: bool) -> None:
        if from_cat:
            origin_x, origin_y = CAT_X + 16, self.cat_y
            dest_x = max(NET_X + 20, min(USER_X, target_x))
        else:
            origin_x, origin_y = self.ball_x, self.ball_y
            dest_x = CAT_X + 8

        dest_y = target_y if from_cat else self.cat_y + random.uniform(-18, 18)
        dx = dest_x - origin_x
        dy = dest_y - origin_y
        length = math.hypot(dx, dy) or 1.0
        speed = BALL_SPEED + min(self.rally * 0.06, 1.8)
        self.ball_vx = dx / length * speed
        self.ball_vy = dy / length * speed
        self.ball_vx = abs(self.ball_vx) if from_cat else -abs(self.ball_vx)
        self.ball_vy = max(-MAX_BALL_VY, min(MAX_BALL_VY, self.ball_vy))

    def _move_cat_toward(self, target_y: float) -> int:
        delta = target_y - self.cat_y
        if abs(delta) < 1.2:
            return 0
        step = 2.6 if abs(delta) > 8 else 1.6
        self.cat_y += step if delta > 0 else -step
        self.cat_y = max(28, min(COURT_H - 28, self.cat_y))
        return 0

    def _on_miss(self, side: str) -> None:
        self.last_miss = side
        self.celebrate_ticks = 36 if side == "user" else 22
        self.rally = 0
        self.ball_vx = 0.0
        self.ball_vy = 0.0
        self._begin_serve()
