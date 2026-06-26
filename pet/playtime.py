"""Solo play activities the cat performs on its own."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum, auto


PLAY_W = 140
PLAY_H = 96
CAT_X = 46
CAT_Y = 68
GRAVITY = 0.38
ACTIVITY_MIN = 200
ACTIVITY_MAX = 300
SESSION_MIN = 220
SESSION_MAX = 380
HOOP_X = 118
HOOP_Y = 34


class ActivityKind(Enum):
    JUGGLE = auto()
    SHOOT = auto()
    GAME = auto()


@dataclass
class PlaySession:
    active: bool = False
    activity: ActivityKind = ActivityKind.JUGGLE
    activity_ticks: int = 0
    activity_duration: int = 0
    celebrate_ticks: int = 0
    facing_left: bool = False
    paw_up: bool = False

    ball_x: float = 0.0
    ball_y: float = 0.0
    ball_vx: float = 0.0
    ball_vy: float = 0.0

    shoot_phase: int = 0
    shoot_wait: int = 0

    game_player_x: float = 78.0
    game_enemy_x: float = 108.0
    game_ball_x: float = 92.0
    game_ball_vx: float = 1.4
    game_frame: int = 0
    session_ticks: int = 0
    session_duration: int = 0

    def start(self) -> None:
        self.active = True
        self.celebrate_ticks = 0
        self.session_ticks = 0
        self.session_duration = random.randint(SESSION_MIN, SESSION_MAX)
        self._pick_activity(initial=True)

    def stop(self) -> None:
        self.active = False
        self.celebrate_ticks = 0
        self.paw_up = False
        self.session_ticks = 0

    def tick(self) -> bool:
        """Advance play session. Returns True when the session ends naturally."""
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

        if self.activity == ActivityKind.JUGGLE:
            self._tick_juggle()
        elif self.activity == ActivityKind.SHOOT:
            self._tick_shoot()
        else:
            self._tick_game()
        return False

    def activity_label(self) -> str:
        labels = {
            ActivityKind.JUGGLE: "颠球",
            ActivityKind.SHOOT: "投篮",
            ActivityKind.GAME: "打游戏",
        }
        return labels[self.activity]

    def _pick_activity(self, initial: bool = False) -> None:
        options = list(ActivityKind)
        if not initial:
            options = [kind for kind in options if kind != self.activity]
        self.activity = random.choice(options)
        self.activity_ticks = 0
        self.activity_duration = random.randint(ACTIVITY_MIN, ACTIVITY_MAX)
        self.facing_left = self.activity == ActivityKind.SHOOT
        self._reset_activity_state()

    def _reset_activity_state(self) -> None:
        self.paw_up = False
        self.shoot_phase = 0
        self.shoot_wait = 0
        self.game_frame = 0

        if self.activity == ActivityKind.JUGGLE:
            self.ball_x = float(CAT_X)
            self.ball_y = 24.0
            self.ball_vx = random.uniform(-0.4, 0.4)
            self.ball_vy = 0.0
        elif self.activity == ActivityKind.SHOOT:
            self.ball_x = float(CAT_X + 10)
            self.ball_y = float(CAT_Y - 18)
            self.ball_vx = 0.0
            self.ball_vy = 0.0
        else:
            self.game_player_x = 78.0
            self.game_enemy_x = 108.0
            self.game_ball_x = 92.0
            self.game_ball_vx = random.choice([-1.4, 1.4])

    def _tick_juggle(self) -> None:
        self.ball_vy += GRAVITY
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        head_y = CAT_Y - 30
        if self.ball_y >= head_y and self.ball_vy > 0:
            self.ball_y = head_y
            self.ball_vy = -(3.0 + random.uniform(0.2, 0.8))
            self.ball_vx = random.uniform(-0.8, 0.8)
            self.paw_up = True
        elif self.ball_y < 16:
            self.ball_y = 16
            self.ball_vy = abs(self.ball_vy)

        if abs(self.ball_x - CAT_X) > 14:
            self.ball_vx *= -0.6
            self.ball_x = CAT_X + (14 if self.ball_x > CAT_X else -14)

        if self.paw_up:
            if self.ball_vy < -1.0:
                self.paw_up = False

    def _tick_shoot(self) -> None:
        if self.shoot_phase == 0:
            self.shoot_wait += 1
            self.paw_up = self.shoot_wait > 8
            if self.shoot_wait >= 18:
                dx = HOOP_X - self.ball_x
                dy = HOOP_Y - self.ball_y
                length = math.hypot(dx, dy) or 1.0
                self.ball_vx = dx / length * 3.6
                self.ball_vy = dy / length * 3.6 - 1.2
                self.shoot_phase = 1
                self.paw_up = False
            return

        self.ball_vy += GRAVITY * 0.55
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        if (
            self.shoot_phase == 1
            and abs(self.ball_x - HOOP_X) < 7
            and abs(self.ball_y - HOOP_Y) < 8
        ):
            self.celebrate_ticks = 28
            self.shoot_phase = 2
            self.shoot_wait = 0
            return

        if self.ball_y > PLAY_H - 8 or self.ball_x > PLAY_W - 4:
            self.shoot_wait += 1
            if self.shoot_wait > 20:
                self._reset_activity_state()

    def _tick_game(self) -> None:
        self.game_frame += 1
        self.game_ball_x += self.game_ball_vx
        self.game_player_x += math.sin(self.game_frame * 0.18) * 0.8
        self.game_enemy_x += math.cos(self.game_frame * 0.14) * 0.6

        if self.game_ball_x <= 74 or self.game_ball_x >= 116:
            self.game_ball_vx *= -1

        self.paw_up = self.game_frame % 24 < 6
