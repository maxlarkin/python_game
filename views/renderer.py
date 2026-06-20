"""Pygame renderer for world entities and effects."""

from __future__ import annotations

import math
from pathlib import Path

import pygame

import constants
from models.entities import AncientShip, Asteroid, Planet, Projectile, Ship
from models.galaxy import StarSystem
from views.background import BackgroundGenerator


class Renderer:
    """Render the current star system from a top-down camera."""

    def __init__(self, screen: pygame.Surface) -> None:
        """Store target screen and initialize caches."""

        assets_dir = Path(__file__).resolve().parent.parent / "assets"
        self._player_sprite = self._load_ship_sprite(
            assets_dir / "sprites" / "player.png", constants.PLAYER_RADIUS
        )
        self._enemy_sprite = self._load_ship_sprite(
            assets_dir / "sprites" / "enemy.png", constants.ANCIENT_RADIUS
        )
        self._screen = screen
        self._backgrounds = BackgroundGenerator()
        self._camera = pygame.Vector2()

    @property
    def camera(self) -> pygame.Vector2:
        """Return the current camera offset."""

        return self._camera.copy()

    def screen_to_world(
        self, screen_pos: pygame.Vector2, focus: pygame.Vector2
    ) -> pygame.Vector2:
        """Convert a screen point to world coordinates."""

        camera = self._camera_for(focus)
        return screen_pos + camera

    def draw_system(self, system: StarSystem) -> None:
        """Draw background and all world entities."""

        self._camera = self._camera_for(system.player.position)
        background = self._backgrounds.get(system.seed, (system.width, system.height))
        self._screen.blit(background, (-round(self._camera.x), -round(self._camera.y)))
        if system.planet is not None:
            self._draw_planet(system.planet)
        for asteroid in system.asteroids:
            self._draw_asteroid(asteroid)
        for projectile in system.projectiles:
            self._draw_projectile(projectile)
        for effect in system.hit_effects:
            self._draw_hit_effect(effect.position, effect.ratio)
        for enemy in system.enemies:
            self._draw_ship(enemy, self._enemy_sprite)
        self._draw_ship(system.player, self._player_sprite)
        self._draw_warnings(system)

    def _camera_for(self, focus: pygame.Vector2) -> pygame.Vector2:
        return pygame.Vector2(
            max(
                0.0,
                min(
                    focus.x - constants.SCREEN_WIDTH / 2,
                    constants.WORLD_WIDTH - constants.SCREEN_WIDTH,
                ),
            ),
            max(
                0.0,
                min(
                    focus.y - constants.SCREEN_HEIGHT / 2,
                    constants.WORLD_HEIGHT - constants.SCREEN_HEIGHT,
                ),
            ),
        )

    def _world_to_screen(self, position: pygame.Vector2) -> pygame.Vector2:
        return position - self._camera

    def _draw_ship(self, ship: Ship, sprite: pygame.Surface) -> None:
        center = self._world_to_screen(ship.position)
        oriented_sprite = self._orient_sprite(sprite, ship.velocity)
        image_rect = oriented_sprite.get_rect(center=(round(center.x), round(center.y)))
        self._screen.blit(oriented_sprite, image_rect)
        if isinstance(ship, AncientShip):
            self._draw_health_tick(ship, center)

    @staticmethod
    def _load_ship_sprite(path: Path, radius: float) -> pygame.Surface:
        sprite = pygame.image.load(path).convert_alpha()
        target_size = max(1, round(radius * 3.0))
        return pygame.transform.smoothscale(sprite, (target_size, target_size))

    @staticmethod
    def _orient_sprite(
        sprite: pygame.Surface, velocity: pygame.Vector2
    ) -> pygame.Surface:
        if velocity.length_squared() <= 1.0:
            return sprite
        angle = math.degrees(math.atan2(-velocity.y, velocity.x)) - 90.0
        return pygame.transform.rotozoom(sprite, angle, 1.0)

    def _draw_health_tick(self, ship: AncientShip, center: pygame.Vector2) -> None:
        width = 38
        ratio = (
            0.0 if ship.max_health <= 0.0 else (ship.health or 0.0) / ship.max_health
        )
        x = round(center.x - width / 2)
        y = round(center.y - ship.radius * 1.8 - 10)
        pygame.draw.rect(
            self._screen,
            (28, 20, 20),
            (x, y, width, 4),
        )
        pygame.draw.rect(
            self._screen,
            (210, 76, 70),
            (x, y, round(width * ratio), 4),
        )

    def _draw_asteroid(self, asteroid: Asteroid) -> None:
        center = self._world_to_screen(asteroid.position)
        center_point = (round(center.x), round(center.y))
        radius = round(asteroid.radius)
        pygame.draw.circle(self._screen, (92, 91, 88), center_point, radius)
        for offset, crater_radius in (
            (pygame.Vector2(-0.32, -0.18), 0.22),
            (pygame.Vector2(0.24, 0.12), 0.18),
            (pygame.Vector2(-0.05, 0.34), 0.14),
        ):
            crater_center = center + offset * asteroid.radius
            pygame.draw.circle(
                self._screen,
                (76, 75, 74),
                (round(crater_center.x), round(crater_center.y)),
                max(2, round(asteroid.radius * crater_radius)),
            )

    def _draw_planet(self, planet: Planet) -> None:
        center = self._world_to_screen(planet.position)
        center_point = (round(center.x), round(center.y))
        radius = round(planet.radius)
        pygame.draw.circle(self._screen, (35, 68, 90), center_point, radius)
        pygame.draw.circle(self._screen, (85, 160, 150), center_point, radius, width=3)
        pygame.draw.arc(
            self._screen,
            (150, 195, 180),
            pygame.Rect(
                round(center.x - radius * 1.28),
                round(center.y - radius * 0.44),
                round(radius * 2.56),
                round(radius * 0.88),
            ),
            math.radians(8),
            math.radians(172),
            2,
        )
        if not planet.reward_claimed:
            pygame.draw.circle(
                self._screen,
                (136, 230, 170),
                center_point,
                radius + 14,
                width=1,
            )

    def _draw_projectile(self, projectile: Projectile) -> None:
        center = self._world_to_screen(projectile.position)
        center_point = (round(center.x), round(center.y))
        color = (
            (90, 240, 255) if projectile.faction.value == "player" else (255, 170, 80)
        )
        pygame.draw.circle(
            self._screen, color, center_point, round(projectile.radius + 2)
        )
        pygame.draw.circle(
            self._screen,
            (255, 255, 255),
            center_point,
            max(1, round(projectile.radius - 1)),
        )

    def _draw_hit_effect(self, position: pygame.Vector2, ratio: float) -> None:
        center = self._world_to_screen(position)
        alpha = max(0, min(255, int(220 * (1.0 - ratio))))
        radius = round(8 + 22 * ratio)
        surface = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(
            surface,
            (255, 236, 180, alpha),
            (radius + 2, radius + 2),
            radius,
            width=2,
        )
        self._screen.blit(
            surface,
            (round(center.x - radius - 2), round(center.y - radius - 2)),
        )

    def _draw_warnings(self, system: StarSystem) -> None:
        for enemy in system.enemies:
            distance = enemy.position.distance_to(system.player.position)
            if distance < 320.0:
                center = self._world_to_screen(enemy.position)
                pygame.draw.circle(
                    self._screen,
                    (230, 76, 70),
                    (round(center.x), round(center.y)),
                    38,
                    width=1,
                )
