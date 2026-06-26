"""Simple behavior state machine for the desktop pet."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto

from pet.sprites import Pose


class Action(Enum):
    IDLE = auto()
    WALK = auto()
    SLEEP = auto()
    HAPPY = auto()


@dataclass
class BehaviorState:
    action: Action = Action.IDLE
    frame: int = 0
    facing_left: bool = False
    paused: bool = False
    walk_remaining: int = 0
    walk_direction: int = 1
    action_ticks: int = 0
    blink_next: int = field(default_factory=lambda: random.randint(20, 60))

    def pose(self) -> Pose:
        if self.action == Action.SLEEP:
            return Pose.SLEEP
        if self.action == Action.HAPPY:
            return Pose.HAPPY
        if self.action == Action.WALK:
            return Pose.WALK
        if self.frame >= self.blink_next and self.frame < self.blink_next + 2:
            return Pose.BLINK
        return Pose.IDLE

    def tick(self) -> tuple[int, int]:
        """Advance animation and return optional movement delta (dx, dy)."""
        if self.paused:
            return 0, 0

        self.frame += 1
        dx = 0
        dy = 0

        if self.action == Action.HAPPY:
            self.action_ticks -= 1
            if self.action_ticks <= 0:
                self._choose_next_action()
            return dx, dy

        if self.action == Action.WALK:
            step = 2 * self.walk_direction
            dx = step
            self.walk_remaining -= abs(step)
            if self.walk_remaining <= 0:
                self._choose_next_action()
            return dx, dy

        if self.action == Action.SLEEP:
            self.action_ticks -= 1
            if self.action_ticks <= 0:
                self._choose_next_action()
            return dx, dy

        if self.frame >= self.blink_next:
            if self.frame >= self.blink_next + 3:
                self.blink_next = self.frame + random.randint(40, 100)
            return dx, dy

        if self.frame % 180 == 0:
            self._choose_next_action()

        return dx, dy

    def pet(self) -> None:
        self.action = Action.HAPPY
        self.action_ticks = 45

    def toggle_pause(self) -> bool:
        self.paused = not self.paused
        return self.paused

    def reset(self) -> None:
        self.action = Action.IDLE
        self.frame = 0
        self.walk_remaining = 0
        self.action_ticks = 0
        self.blink_next = random.randint(20, 60)

    def _choose_next_action(self) -> None:
        roll = random.random()
        if roll < 0.18:
            self.action = Action.SLEEP
            self.action_ticks = random.randint(120, 240)
            return

        if roll < 0.55:
            self.action = Action.WALK
            self.walk_direction = random.choice([-1, 1])
            self.facing_left = self.walk_direction < 0
            self.walk_remaining = random.randint(80, 220)
            return

        self.action = Action.IDLE
        self.action_ticks = 0
