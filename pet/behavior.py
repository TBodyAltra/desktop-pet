"""Behavior state machine with dev-context reactions."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from pet.dev_context import ForegroundContext, detect_context
from pet.drops import DropManager
from pet.sprites import CatVariant, Pose
from pet.playtime import ActivityKind, PlaySession


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
BOREDOM_THRESHOLD = 280
BOREDOM_THRESHOLD_CODING = 160
PLAY_COOLDOWN = 360
PLAY_COOLDOWN_CODING = 220
ENCOUNTER_CHANCE = 0.0014


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
    playtime: PlaySession = field(default_factory=PlaySession)
    boredom_ticks: int = 0
    play_cooldown: int = field(default_factory=lambda: random.randint(120, 240))
    playtime_enter: bool = False
    playtime_forced: ActivityKind | None = None

    def pose(self) -> Pose:
        if self.playtime.active:
            if self.playtime.celebrate_ticks > 0:
                return Pose.HAPPY
            return Pose.PLAY
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
        self.stop_playtime()
        self.boredom_ticks = 0
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
        self.stop_playtime()
        self.boredom_ticks = 0
        self.action = Action.CHASE
        self.chase_dx = 1 if dx > 0 else -1
        self.facing_left = self.chase_dx < 0
        self.chase_remaining = min(abs(dx), 80)

    def tick(self) -> tuple[int, int]:
        if self.paused:
            return 0, 0

        self.frame += 1

        if self.playtime.active:
            return 0, 0

        self.drops.tick()

        if self.play_cooldown > 0:
            self.play_cooldown -= 1

        if self._is_bored_eligible():
            self.boredom_ticks += 1
            if self.boredom_ticks >= self._boredom_threshold() and self.play_cooldown <= 0:
                self.boredom_ticks = 0
                self.playtime_enter = True
        elif self.action != Action.IDLE:
            self.boredom_ticks = max(0, self.boredom_ticks - 3)

        if (
            not self.playtime.active
            and self.play_cooldown <= 0
            and not self.flying
            and self.action in {Action.IDLE, Action.WALK}
            and random.random() < ENCOUNTER_CHANCE
        ):
            self.playtime_enter = True
            self.playtime_forced = random.choice([ActivityKind.MOUSE, ActivityKind.DOG])

        if self.flying:
            self.vy += GRAVITY
            self.vx *= AIR_FRICTION
            return int(round(self.vx)), int(round(self.vy))

        if self.action == Action.CHASE:
            step = 1 * self.chase_dx
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
            step = 1 * self.walk_direction
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

        if self.frame % 240 == 0:
            self._choose_next_action()

        return dx, dy

    def pet(self) -> None:
        self.stop_playtime()
        self.boredom_ticks = 0
        self.play_cooldown = PLAY_COOLDOWN // 2
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

    def start_playtime(self) -> None:
        self.flying = False
        self.vx = 0.0
        self.vy = 0.0
        self.action = Action.IDLE
        self.playtime_enter = False
        forced = self.playtime_forced
        self.playtime_forced = None
        self.playtime.start(forced)

    def stop_playtime(self) -> None:
        if self.playtime.active:
            self.playtime.stop()
            self.play_cooldown = self._play_cooldown()
        self.playtime_enter = False
        self.playtime_forced = None

    def on_playtime_finished(self) -> None:
        self.playtime.stop()
        self.play_cooldown = self._play_cooldown()
        self.boredom_ticks = 0
        self.action = Action.IDLE
        self.action_ticks = 0

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
        self.playtime.stop()
        self.boredom_ticks = 0
        self.play_cooldown = random.randint(120, 240)
        self.playtime_enter = False
        self.playtime_forced = None

    def _boredom_threshold(self) -> int:
        if self.context == ForegroundContext.CODING:
            return BOREDOM_THRESHOLD_CODING
        return BOREDOM_THRESHOLD

    def _play_cooldown(self) -> int:
        if self.context == ForegroundContext.CODING:
            return PLAY_COOLDOWN_CODING
        return PLAY_COOLDOWN

    def _is_bored_eligible(self) -> bool:
        if self.paused or self.flying or self.play_cooldown > 0:
            return False
        if self.action != Action.IDLE:
            return False
        if self.context == ForegroundContext.MEETING:
            return False
        return True

    def _choose_coding_action(self) -> None:
        """Lazy cat while you code: mostly idle or a slow prowl."""
        roll = random.random()
        if roll < 0.45:
            self.action = Action.IDLE
            self.action_ticks = 0
        elif roll < 0.78:
            self._start_walk((100, 220))
        elif roll < 0.9:
            self._start_sleep((50, 90))
        else:
            self.boredom_ticks = max(self.boredom_ticks, self._boredom_threshold() - 40)
            self.action = Action.IDLE
            self.action_ticks = 0

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
            roll = random.random()
            if roll < 0.5:
                self._start_walk((90, 180))
            elif roll < 0.7:
                self._start_sleep((45, 80))
            else:
                self.action = Action.IDLE
                self.action_ticks = 0
        elif self.context == ForegroundContext.MEETING:
            self._start_sleep((200, 320))
        elif self.context == ForegroundContext.TERMINAL:
            self._start_walk((80, 160))
        elif self.context == ForegroundContext.BROWSING:
            self._start_walk((80, 160))
        else:
            self.action = Action.IDLE
            self.action_ticks = 0

    def _choose_next_action(self) -> None:
        roll = random.random()

        if self.context == ForegroundContext.CODING:
            self._choose_coding_action()
            return

        if self.context == ForegroundContext.MEETING:
            if roll < 0.7:
                self._start_sleep((140, 260))
            else:
                self.action = Action.IDLE
                self.action_ticks = 0
            return

        if self.context == ForegroundContext.TERMINAL:
            if roll < 0.55:
                self._start_walk((80, 160))
            else:
                self.action = Action.IDLE
                self.action_ticks = 0
            return

        if roll < 0.22:
            self._start_sleep((100, 200))
            return

        if roll < 0.62:
            self._start_walk((100, 260))
            return

        self.action = Action.IDLE
        self.action_ticks = 0
