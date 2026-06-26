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
    CHASE = "chase"


GRAVITY = 1.4
AIR_FRICTION = 0.99
BOUNCE_DAMPING = 0.55
FLING_MIN_SPEED = 6.0


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
    context_changed: bool = False
    flying: bool = False
    vx: float = 0.0
    vy: float = 0.0
    chase_remaining: int = 0
    chase_dx: int = 0
    blink_next: int = field(default_factory=lambda: random.randint(20, 60))
    drops: DropManager = field(default_factory=DropManager)

    def pose(self) -> Pose:
        if self.flying:
            return Pose.BLINK
        if self.action == Action.SLEEP:
            return Pose.SLEEP
        if self.action == Action.HAPPY:
            return Pose.HAPPY
        if self.action in {Action.WALK, Action.CHASE}:
            return Pose.WALK
        if self.frame >= self.blink_next and self.frame < self.blink_next + 2:
            return Pose.BLINK
        return Pose.IDLE

    def fling(self, vx: float, vy: float) -> None:
        self.flying = True
        self.vx = vx
        self.vy = vy
        self.action = Action.IDLE

    def bounce_x(self) -> None:
        self.vx = -self.vx * BOUNCE_DAMPING

    def bounce_y(self) -> None:
        self.vy = -self.vy * BOUNCE_DAMPING

    def land(self) -> None:
        self.flying = False
        self.vx = 0.0
        self.vy = 0.0
        self.action = Action.HAPPY
        self.action_ticks = 28

    def chase_toward(self, dx: int) -> None:
        """Start trotting toward a horizontal offset (cursor direction)."""
        if self.flying or self.action in {Action.HAPPY, Action.CHASE}:
            return
        self.action = Action.CHASE
        self.chase_dx = 1 if dx > 0 else -1
        self.facing_left = self.chase_dx < 0
        self.chase_remaining = min(abs(dx), 160)

    def tick(self) -> tuple[int, int]:
        if self.paused:
            return 0, 0

        self.frame += 1
        self.drops.tick()

        if self.flying:
            self.vy += GRAVITY
            self.vx *= AIR_FRICTION
            return int(round(self.vx)), int(round(self.vy))

        if self.action == Action.CHASE:
            step = 3 * self.chase_dx
            self.chase_remaining -= abs(step)
            if self.chase_remaining <= 0:
                self.action = Action.IDLE
            return step, 0

        self.context_cooldown -= 1
        if self.context_cooldown <= 0:
            self.context_cooldown = 12
            new_context = detect_context()
            if new_context != self.context:
                self.context = new_context
                self.context_changed = True
                self._on_context_change()

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
        self.flying = False
        self.vx = 0.0
        self.vy = 0.0
        self.chase_remaining = 0
        self.blink_next = random.randint(20, 60)
        self.drops = DropManager()

    def _start_walk(self, length_range: tuple[int, int]) -> None:
        self.action = Action.WALK
        self.walk_direction = random.choice([-1, 1])
        self.facing_left = self.walk_direction < 0
        self.walk_remaining = random.randint(*length_range)

    def _start_sleep(self, ticks_range: tuple[int, int]) -> None:
        self.action = Action.SLEEP
        self.action_ticks = random.randint(*ticks_range)

    def _on_context_change(self) -> None:
        """React immediately and visibly when the foreground app changes."""
        if self.action == Action.HAPPY:
            return

        if self.context == ForegroundContext.CODING:
            # Curl up and doze next to the editor.
            self._start_sleep((140, 260))
        elif self.context == ForegroundContext.MEETING:
            self._start_sleep((200, 320))
        elif self.context == ForegroundContext.TERMINAL:
            # Get excited and trot around.
            self._start_walk((120, 220))
        elif self.context == ForegroundContext.BROWSING:
            self._start_walk((80, 160))
        else:
            self.action = Action.IDLE
            self.action_ticks = 0

    def _choose_next_action(self) -> None:
        roll = random.random()

        if self.context in {ForegroundContext.CODING, ForegroundContext.MEETING}:
            # Stay calm and nap while you focus.
            if roll < 0.7:
                self._start_sleep((140, 260))
            else:
                self.action = Action.IDLE
                self.action_ticks = 0
            return

        if self.context == ForegroundContext.TERMINAL:
            # Energetic: mostly pacing back and forth.
            if roll < 0.75:
                self._start_walk((100, 200))
            else:
                self.action = Action.IDLE
                self.action_ticks = 0
            return

        if roll < 0.18:
            self._start_sleep((120, 240))
            return

        if roll < 0.55:
            self._start_walk((80, 220))
            return

        self.action = Action.IDLE
        self.action_ticks = 0
