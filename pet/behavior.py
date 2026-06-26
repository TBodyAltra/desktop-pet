"""Behavior state machine with dev-context reactions."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from pet.dev_context import ForegroundContext, detect_context
from pet.drops import DropManager
from pet.sprites import CatVariant, Pose


class Action:
    IDLE = "idle"
    WALK = "walk"
    SLEEP = "sleep"
    HAPPY = "happy"


@dataclass
class BehaviorState:
    action: str = Action.IDLE
    frame: int = 0
    facing_left: bool = False
    paused: bool = False
    variant: CatVariant = CatVariant.TABBY
    walk_remaining: int = 0
    walk_direction: int = 1
    action_ticks: int = 0
    context: ForegroundContext = ForegroundContext.UNKNOWN
    context_cooldown: int = 0
    blink_next: int = field(default_factory=lambda: random.randint(20, 60))
    drops: DropManager = field(default_factory=DropManager)

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
        if self.paused:
            return 0, 0

        self.frame += 1
        self.drops.tick()

        self.context_cooldown -= 1
        if self.context_cooldown <= 0:
            self.context = detect_context()
            self._apply_context()
            self.context_cooldown = 50

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
        self.drops.on_pet()

    def toggle_pause(self) -> bool:
        self.paused = not self.paused
        return self.paused

    def cycle_variant(self) -> CatVariant:
        order = [CatVariant.TABBY, CatVariant.TUXEDO, CatVariant.SIAMESE]
        index = (order.index(self.variant) + 1) % len(order)
        self.variant = order[index]
        return self.variant

    def set_variant(self, variant: CatVariant) -> None:
        self.variant = variant

    def context_label(self) -> str:
        labels = {
            ForegroundContext.CODING: "coding",
            ForegroundContext.TERMINAL: "terminal",
            ForegroundContext.BROWSING: "browsing",
            ForegroundContext.MEETING: "meeting",
            ForegroundContext.UNKNOWN: "idle",
        }
        return labels[self.context]

    def reset(self) -> None:
        self.action = Action.IDLE
        self.frame = 0
        self.walk_remaining = 0
        self.action_ticks = 0
        self.blink_next = random.randint(20, 60)
        self.drops = DropManager()

    def _apply_context(self) -> None:
        if self.action == Action.HAPPY:
            return

        if self.context == ForegroundContext.MEETING:
            if self.action != Action.SLEEP:
                self.action = Action.SLEEP
                self.action_ticks = random.randint(150, 260)
            return

        if self.context == ForegroundContext.CODING:
            if random.random() < 0.12 and self.action == Action.IDLE:
                self.action = Action.SLEEP
                self.action_ticks = random.randint(90, 160)
            return

        if self.context == ForegroundContext.TERMINAL:
            if random.random() < 0.25 and self.action in {Action.IDLE, Action.SLEEP}:
                self.action = Action.WALK
                self.walk_direction = random.choice([-1, 1])
                self.facing_left = self.walk_direction < 0
                self.walk_remaining = random.randint(60, 140)
            return

        if self.context == ForegroundContext.BROWSING:
            if random.random() < 0.18 and self.action == Action.IDLE:
                self.action = Action.WALK
                self.walk_direction = -1 if random.random() < 0.5 else 1
                self.facing_left = self.walk_direction < 0
                self.walk_remaining = random.randint(40, 100)

    def _choose_next_action(self) -> None:
        roll = random.random()
        if self.context == ForegroundContext.MEETING:
            self.action = Action.SLEEP
            self.action_ticks = random.randint(150, 260)
            return

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
