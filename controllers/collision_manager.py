"""Collision broad-phase and resolution."""

from __future__ import annotations

import pygame

import constants
from models.entities import Asteroid, Entity, Faction, Planet, Projectile, Ship
from models.galaxy import StarSystem
from utils.quad_tree import QuadTree, Rect


class CollisionManager:
    """Resolve projectile and body collisions through a QuadTree."""

    def __init__(self) -> None:
        """Initialize the manager."""

        self._tree = QuadTree[Entity](
            Rect(0.0, 0.0, constants.WORLD_WIDTH, constants.WORLD_HEIGHT),
            constants.QUADTREE_CAPACITY,
            constants.QUADTREE_MAX_DEPTH,
        )

    def resolve(self, system: StarSystem) -> int:
        """Resolve collisions in a system.

        Args:
            system: Current star system.

        Returns:
            Number of enemies destroyed during this pass.
        """

        enemies_before = sum(1 for enemy in system.enemies if enemy.alive)
        self._tree.clear()
        for entity in system.entities:
            if entity.alive:
                self._tree.insert(entity)

        self._resolve_projectiles(system)
        self._resolve_ship_asteroids(system.player, system.asteroids)
        for enemy in system.enemies:
            self._resolve_ship_asteroids(enemy, system.asteroids)
        enemies_after = sum(1 for enemy in system.enemies if enemy.alive)
        return enemies_before - enemies_after

    def _resolve_projectiles(self, system: StarSystem) -> None:
        for projectile in system.projectiles:
            if not projectile.alive:
                continue
            nearby = self._tree.query(projectile.bounds())
            for target in nearby:
                if target is projectile or not target.alive:
                    continue
                if isinstance(target, Projectile | Planet):
                    continue
                if target.faction == projectile.faction:
                    continue
                if projectile.collides_with(target):
                    target.take_damage(projectile.damage)
                    projectile.alive = False
                    system.add_hit_effect(projectile.position)
                    break

    def _resolve_ship_asteroids(self, ship: Ship, asteroids: list[Asteroid]) -> None:
        if not ship.alive:
            return
        nearby = self._tree.query(ship.bounds())
        for asteroid in nearby:
            if not isinstance(asteroid, Asteroid) or not asteroid.alive:
                continue
            if not ship.collides_with(asteroid):
                continue
            push = ship.position - asteroid.position
            if push.length_squared() == 0.0:
                push = pygame.Vector2(1.0, 0.0)
            push = push.normalize()
            ship.position += push * 8.0
            ship.velocity = ship.velocity.reflect(push) * 0.35
            if ship.faction != Faction.NEUTRAL:
                ship.take_damage(3.0)
