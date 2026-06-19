"""Game entities and shared movement physics."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
import random

import pygame

import constants
from utils.quad_tree import Rect


class Faction(Enum):
    """Entity allegiance used for combat filtering."""

    PLAYER = "player"
    ANCIENT = "ancient"
    NEUTRAL = "neutral"


@dataclass
class Entity:
    """Base class for simulated world objects."""

    position: pygame.Vector2
    velocity: pygame.Vector2
    radius: float
    faction: Faction
    max_health: float
    health: float | None = None
    alive: bool = True

    def __post_init__(self) -> None:
        """Fill health when not explicitly provided."""

        if self.health is None:
            self.health = self.max_health

    def bounds(self) -> Rect:
        """Return axis-aligned bounds for broad-phase collision."""

        return Rect(
            self.position.x - self.radius,
            self.position.y - self.radius,
            self.radius * 2.0,
            self.radius * 2.0,
        )

    def update(self, dt: float) -> None:
        """Advance the entity by velocity.

        Args:
            dt: Elapsed simulation seconds.
        """

        self.position += self.velocity * dt

    def apply_force(self, force: pygame.Vector2, dt: float, max_speed: float) -> None:
        """Apply acceleration and clamp resulting speed.

        Args:
            force: Acceleration vector.
            dt: Elapsed simulation seconds.
            max_speed: Maximum allowed velocity magnitude.
        """

        self.velocity += force * dt
        if self.velocity.length_squared() > max_speed * max_speed:
            self.velocity.scale_to_length(max_speed)

    def take_damage(self, amount: float) -> None:
        """Reduce health and mark entity dead when depleted.

        Args:
            amount: Damage points to apply.
        """

        if self.health is None:
            return
        self.health = max(0.0, self.health - amount)
        if self.health <= 0.0:
            self.alive = False

    def collides_with(self, other: Entity) -> bool:
        """Return True when circular collision shapes overlap."""

        distance_squared = self.position.distance_squared_to(other.position)
        radius_sum = self.radius + other.radius
        return distance_squared <= radius_sum * radius_sum


@dataclass
class Projectile(Entity):
    """Projectile with finite lifetime and fixed damage."""

    damage: float = constants.PLAYER_PROJECTILE_DAMAGE
    lifetime: float = constants.PROJECTILE_LIFETIME

    def update(self, dt: float) -> None:
        """Move and expire the projectile."""

        super().update(dt)
        self.lifetime -= dt
        if self.lifetime <= 0.0:
            self.alive = False


@dataclass
class Planet(Entity):
    """Story planet with a one-time quest conversation."""

    name: str = ""
    dialog_lines: list[str] = field(default_factory=list)
    reward_claimed: bool = False

    def update(self, dt: float) -> None:
        """Planets are static but keep the Entity interface."""


@dataclass
class Ship(Entity):
    """Controllable ship with shields, energy, and weapons."""

    max_shields: float = constants.PLAYER_MAX_SHIELDS
    shields: float = constants.PLAYER_MAX_SHIELDS
    max_energy: float = constants.PLAYER_MAX_ENERGY
    energy: float = constants.PLAYER_MAX_ENERGY
    max_speed: float = constants.PLAYER_MAX_SPEED
    acceleration: float = constants.PLAYER_ACCELERATION
    fire_cooldown: float = constants.PLAYER_FIRE_COOLDOWN
    cooldown_remaining: float = 0.0
    weapon_index: int = 0

    def update(self, dt: float) -> None:
        """Advance ship physics and regenerate energy."""

        super().update(dt)
        self.velocity *= constants.PLAYER_FRICTION ** (dt * 60.0)
        self.cooldown_remaining = max(0.0, self.cooldown_remaining - dt)
        self.energy = min(self.max_energy, self.energy + 18.0 * dt)

    def accelerate(self, direction: pygame.Vector2, dt: float) -> None:
        """Accelerate toward an input direction.

        Args:
            direction: Desired movement direction.
            dt: Elapsed simulation seconds.
        """

        if direction.length_squared() == 0.0:
            return
        self.apply_force(direction.normalize() * self.acceleration, dt, self.max_speed)

    def fire_at(self, target: pygame.Vector2) -> Projectile | None:
        """Create a projectile aimed at a world-space target.

        Args:
            target: Target point.

        Returns:
            A projectile or None if the weapon is cooling down.
        """

        profile = constants.PLAYER_WEAPONS[
            self.weapon_index % len(constants.PLAYER_WEAPONS)
        ]
        energy_cost = (
            float(profile["energy_cost"]) if self.faction == Faction.PLAYER else 4.0
        )
        if self.cooldown_remaining > 0.0 or self.energy < energy_cost:
            return None
        direction = target - self.position
        if direction.length_squared() == 0.0:
            direction = pygame.Vector2(1.0, 0.0)
        direction = direction.normalize()
        if self.faction == Faction.PLAYER:
            self.cooldown_remaining = float(profile["cooldown"])
            damage = float(profile["damage"])
            speed = float(profile["speed"])
            lifetime = float(profile["lifetime"])
        else:
            self.cooldown_remaining = self.fire_cooldown
            damage = constants.PLAYER_PROJECTILE_DAMAGE
            speed = constants.PROJECTILE_SPEED
            lifetime = constants.PROJECTILE_LIFETIME
        self.energy -= energy_cost
        return Projectile(
            position=self.position + direction * (self.radius + 8.0),
            velocity=direction * speed,
            radius=constants.PROJECTILE_RADIUS,
            faction=self.faction,
            max_health=1.0,
            damage=damage,
            lifetime=lifetime,
        )

    def take_damage(self, amount: float) -> None:
        """Apply shield-first damage to the ship."""

        absorbed = min(self.shields, amount)
        self.shields -= absorbed
        remaining = amount - absorbed
        if remaining > 0.0:
            super().take_damage(remaining)


@dataclass
class AncientShip(Ship):
    """Enemy ship controlled by steering and behavior trees."""

    patrol_points: list[pygame.Vector2] = field(default_factory=list)
    patrol_index: int = 0

    def __post_init__(self) -> None:
        """Ensure Ancient defaults are independent of player ship values."""

        super().__post_init__()
        self.max_shields = 30.0
        self.shields = min(self.shields, self.max_shields)
        self.max_speed = constants.ANCIENT_MAX_SPEED
        self.acceleration = constants.ANCIENT_ACCELERATION
        self.fire_cooldown = constants.ANCIENT_FIRE_COOLDOWN

    def next_patrol_point(self) -> pygame.Vector2:
        """Return the current patrol target and advance when reached."""

        if not self.patrol_points:
            return self.position
        point = self.patrol_points[self.patrol_index]
        if self.position.distance_to(point) < 42.0:
            self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
            point = self.patrol_points[self.patrol_index]
        return point

    def fire_at(self, target: pygame.Vector2) -> Projectile | None:
        """Fire an Ancient projectile at a target."""

        projectile = super().fire_at(target)
        if projectile is not None:
            projectile.damage = constants.ANCIENT_PROJECTILE_DAMAGE
        return projectile


@dataclass
class Asteroid(Entity):
    """Neutral obstacle that drifts slowly through a system."""

    rotation: float = 0.0
    angular_velocity: float = 0.0

    def update(self, dt: float) -> None:
        """Move and rotate the asteroid."""

        super().update(dt)
        self.rotation = (self.rotation + self.angular_velocity * dt) % math.tau


def create_player_ship(position: pygame.Vector2) -> Ship:
    """Create a fully initialized player ship."""

    return Ship(
        position=position,
        velocity=pygame.Vector2(),
        radius=constants.PLAYER_RADIUS,
        faction=Faction.PLAYER,
        max_health=constants.PLAYER_MAX_HEALTH,
    )


def create_ancient_ship(
    position: pygame.Vector2, rng: random.Random, world_size: tuple[int, int]
) -> AncientShip:
    """Create an Ancient patrol ship.

    Args:
        position: Spawn point.
        rng: Random source.
        world_size: Width and height of the system.

    Returns:
        A configured enemy ship.
    """

    width, height = world_size
    patrol_points = [
        pygame.Vector2(rng.randint(120, width - 120), rng.randint(120, height - 120))
        for _ in range(3)
    ]
    return AncientShip(
        position=position,
        velocity=pygame.Vector2(),
        radius=constants.ANCIENT_RADIUS,
        faction=Faction.ANCIENT,
        max_health=constants.ANCIENT_MAX_HEALTH,
        max_shields=30.0,
        shields=30.0,
        max_energy=80.0,
        energy=80.0,
        patrol_points=patrol_points,
    )


def create_asteroid(
    position: pygame.Vector2, radius: float, rng: random.Random
) -> Asteroid:
    """Create a neutral asteroid."""

    velocity = pygame.Vector2(rng.uniform(-25.0, 25.0), rng.uniform(-25.0, 25.0))
    return Asteroid(
        position=position,
        velocity=velocity,
        radius=radius,
        faction=Faction.NEUTRAL,
        max_health=radius * 2.0,
        rotation=rng.random() * math.tau,
        angular_velocity=rng.uniform(-0.55, 0.55),
    )
