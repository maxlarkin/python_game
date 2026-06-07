"""Pygame renderer for world entities and effects."""

from __future__ import annotations

import math

import pygame

import constants
from models.entities import AncientShip, Asteroid, Projectile, Ship
from models.galaxy import StarSystem
from views.background import BackgroundGenerator


class Renderer:
    """Render the current star system from a top-down camera."""

    def __init__(self, screen: pygame.Surface) -> None:
        """Store target screen and initialize caches."""

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
        for asteroid in system.asteroids:
            self._draw_asteroid(asteroid)
        for projectile in system.projectiles:
            self._draw_projectile(projectile)
        for enemy in system.enemies:
            self._draw_ship(enemy, (220, 150, 74), (95, 52, 35))
        self._draw_ship(system.player, (70, 220, 225), (25, 92, 104))
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

    def _draw_ship(
        self,
        ship: Ship,
        color: tuple[int, int, int],
        outline: tuple[int, int, int],
    ) -> None:
        center = self._world_to_screen(ship.position)
        width = int(ship.radius * 2.2)
        height = int(ship.radius * 1.45)
        rect = pygame.Rect(0, 0, width, height)
        rect.center = (round(center.x), round(center.y))
        pygame.draw.rect(self._screen, outline, rect.inflate(5, 5), border_radius=3)
        pygame.draw.rect(self._screen, color, rect, border_radius=3)
        if ship.velocity.length_squared() > 16.0:
            direction = ship.velocity.normalize()
            nose = center + direction * ship.radius
            pygame.draw.line(self._screen, (240, 245, 245), center, nose, 2)
        if isinstance(ship, AncientShip):
            self._draw_health_tick(ship, center)

    def _draw_health_tick(self, ship: AncientShip, center: pygame.Vector2) -> None:
        width = 38
        ratio = (
            0.0 if ship.max_health <= 0.0 else (ship.health or 0.0) / ship.max_health
        )
        x = round(center.x - width / 2)
        y = round(center.y - 28)
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
        pygame.draw.circle(self._screen, (52, 52, 56), center_point, radius, width=2)
        spoke = pygame.Vector2(math.cos(asteroid.rotation), math.sin(asteroid.rotation))
        pygame.draw.line(
            self._screen,
            (122, 118, 112),
            center_point,
            center + spoke * asteroid.radius * 0.65,
            2,
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
