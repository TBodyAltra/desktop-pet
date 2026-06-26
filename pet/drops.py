"""Floating XP orbs and raw fish drops."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto


class DropKind(Enum):
    XP = auto()
    FISH = auto()


@dataclass
class Drop:
    kind: DropKind
    x: float
    y: float
    vy: float = -0.4
    life: int = 120
    frame: int = 0
    collected: bool = False

    def tick(self) -> None:
        self.frame += 1
        self.y += self.vy
        self.life -= 1

    @property
    def alive(self) -> bool:
        return self.life > 0 and not self.collected

    def contains(self, px: int, py: int) -> bool:
        return self.x <= px <= self.x + 3 and self.y <= py <= self.y + 3


@dataclass
class DropManager:
    drops: list[Drop] = field(default_factory=list)
    spawn_cooldown: int = field(default_factory=lambda: random.randint(300, 600))

    def tick(self) -> None:
        for drop in self.drops:
            drop.tick()
        self.drops = [drop for drop in self.drops if drop.alive]

        self.spawn_cooldown -= 1
        if self.spawn_cooldown <= 0 and len(self.drops) < 2:
            self._spawn_drop()
            self.spawn_cooldown = random.randint(400, 800)

    def _spawn_drop(self) -> None:
        kind = random.choice([DropKind.XP, DropKind.FISH])
        self.drops.append(
            Drop(
                kind=kind,
                x=random.uniform(2, 16),
                y=random.uniform(4, 10),
                vy=random.uniform(-0.6, -0.3),
            )
        )

    def try_collect(self, px: int, py: int) -> DropKind | None:
        for drop in self.drops:
            if drop.contains(px, py):
                drop.collected = True
                return drop.kind
        return None

    def on_pet(self) -> None:
        if random.random() < 0.35:
            self._spawn_drop()
