"""Heads-up display and minimap rendering."""

from __future__ import annotations

import pygame

import constants
from models.galaxy import StarSystem, Universe
from models.player import PlayerData
from views.text import create_font


class HUD:
    """Draw player status, objectives, and navigation widgets."""

    def __init__(self, font: object) -> None:
        """Store font resources."""

        self._font = font
        self._small_font = create_font(16)

    def draw(
        self,
        surface: pygame.Surface,
        system: StarSystem,
        player_data: PlayerData,
        universe: Universe,
    ) -> None:
        """Draw the complete in-game HUD."""

        self._draw_bar(
            surface,
            (24, 24),
            "Корпус",
            system.player.health or 0.0,
            system.player.max_health,
            (190, 70, 75),
        )
        self._draw_bar(
            surface,
            (24, 52),
            "Щиты",
            system.player.shields,
            system.player.max_shields,
            (80, 150, 230),
        )
        self._draw_bar(
            surface,
            (24, 80),
            "Энергия",
            system.player.energy,
            system.player.max_energy,
            (80, 210, 155),
        )
        speed = system.player.velocity.length()
        self._draw_bar(
            surface,
            (24, 108),
            "Скорость",
            speed,
            system.player.max_speed,
            (220, 190, 85),
        )

        objective = system.objective_text
        if system.is_cleared():
            objective = "Патруль уничтожен. H: карта гиперпрыжка"
        elif system.planet_in_range():
            objective = "E: связаться с планетой"
        self._draw_text(surface, objective, (24, 148), (230, 230, 230))
        weapon = constants.PLAYER_WEAPONS[
            system.player.weapon_index % len(constants.PLAYER_WEAPONS)
        ]
        self._draw_text(
            surface,
            (
                f"Ресурсы: {player_data.resources}   "
                f"Артефакты: {len(player_data.artifacts)}   "
                f"Оружие: {weapon['name']}   G: улучшения"
            ),
            (24, 176),
            (210, 210, 210),
        )
        self._draw_minimap(surface, system)
        self._draw_galaxy(surface, universe, player_data)

    def _draw_bar(
        self,
        surface: pygame.Surface,
        pos: tuple[int, int],
        label: str,
        value: float,
        maximum: float,
        color: tuple[int, int, int],
    ) -> None:
        pygame.draw.rect(surface, (24, 28, 36), (*pos, 230, 18), border_radius=3)
        ratio = 0.0 if maximum <= 0.0 else max(0.0, min(1.0, value / maximum))
        pygame.draw.rect(
            surface,
            color,
            (pos[0] + 2, pos[1] + 2, int(226 * ratio), 14),
            border_radius=2,
        )
        self._draw_text(
            surface,
            f"{label}: {int(value)}/{int(maximum)}",
            (pos[0] + 8, pos[1] - 1),
            (245, 245, 245),
            self._small_font,
        )

    def _draw_minimap(self, surface: pygame.Surface, system: StarSystem) -> None:
        rect = pygame.Rect(constants.SCREEN_WIDTH - 210, 22, 180, 120)
        pygame.draw.rect(surface, (14, 17, 24), rect, border_radius=4)
        pygame.draw.rect(surface, (90, 95, 112), rect, width=1, border_radius=4)
        scale_x = rect.width / system.width
        scale_y = rect.height / system.height
        for asteroid in system.asteroids:
            pos = (
                rect.x + int(asteroid.position.x * scale_x),
                rect.y + int(asteroid.position.y * scale_y),
            )
            pygame.draw.circle(surface, (96, 95, 92), pos, 2)
        for enemy in system.enemies:
            pos = (
                rect.x + int(enemy.position.x * scale_x),
                rect.y + int(enemy.position.y * scale_y),
            )
            pygame.draw.rect(surface, (220, 150, 80), (pos[0] - 2, pos[1] - 2, 4, 4))
        if system.planet is not None:
            pos = (
                rect.x + int(system.planet.position.x * scale_x),
                rect.y + int(system.planet.position.y * scale_y),
            )
            pygame.draw.circle(surface, (126, 190, 128), pos, 5, width=1)
        player_pos = (
            rect.x + int(system.player.position.x * scale_x),
            rect.y + int(system.player.position.y * scale_y),
        )
        pygame.draw.circle(surface, (80, 220, 220), player_pos, 4)

    def draw_hyperjump_map(
        self,
        surface: pygame.Surface,
        universe: Universe,
        player_data: PlayerData,
        current_system_id: int,
    ) -> None:
        """Draw an interactive galaxy map for choosing the next system."""

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        rect = self._hyperjump_rect()
        pygame.draw.rect(surface, (12, 15, 24), rect, border_radius=6)
        pygame.draw.rect(surface, (96, 108, 136), rect, width=1, border_radius=6)
        self._draw_text(
            surface,
            "Карта гиперпрыжка",
            (rect.x + 24, rect.y + 20),
            (238, 238, 242),
        )
        self._draw_text(
            surface,
            "Выберите связанную систему мышью или клавишами 1-9. Esc: назад.",
            (rect.x + 24, rect.y + 52),
            (168, 176, 196),
            self._small_font,
        )
        reachable_ids = {
            node.system_id for node in universe.connected_systems(current_system_id)
        }
        self._draw_galaxy_connections(surface, universe, rect)
        for node in universe.systems:
            pos = self._galaxy_position(rect, node.map_position)
            color = (84, 90, 112)
            radius = 7
            if node.system_id in player_data.unlocked_systems:
                color = (104, 176, 202)
            if node.system_id in player_data.cleared_systems:
                color = (116, 220, 150)
            if node.system_id in reachable_ids:
                color = (120, 220, 150)
                radius = 9
            if node.system_id == current_system_id:
                color = (245, 218, 116)
                radius = 10
            pygame.draw.circle(surface, color, pos, radius)
            pygame.draw.circle(surface, (18, 20, 28), pos, radius, width=1)
            if node.system_id in player_data.cleared_systems:
                pygame.draw.circle(surface, (235, 245, 235), pos, radius + 3, width=1)
            self._draw_text(
                surface,
                str(node.system_id + 1),
                (pos[0] + 12, pos[1] - 8),
                (222, 226, 236),
                self._small_font,
            )

    def hyperjump_node_at(
        self, screen_pos: tuple[int, int], universe: Universe, current_system_id: int
    ) -> int | None:
        """Return the reachable node under a screen position, if any."""

        rect = self._hyperjump_rect()
        reachable_ids = {
            node.system_id for node in universe.connected_systems(current_system_id)
        }
        point = pygame.Vector2(screen_pos)
        for node in universe.systems:
            if node.system_id not in reachable_ids:
                continue
            pos = pygame.Vector2(self._galaxy_position(rect, node.map_position))
            if point.distance_squared_to(pos) <= 16.0 * 16.0:
                return node.system_id
        return None

    def _draw_galaxy(
        self, surface: pygame.Surface, universe: Universe, player_data: PlayerData
    ) -> None:
        rect = pygame.Rect(constants.SCREEN_WIDTH - 210, 156, 180, 106)
        pygame.draw.rect(surface, (13, 15, 22), rect, border_radius=4)
        pygame.draw.rect(surface, (78, 82, 98), rect, width=1, border_radius=4)
        self._draw_galaxy_connections(surface, universe, rect)
        for node in universe.systems:
            x, y = self._galaxy_position(rect, node.map_position)
            color = (110, 120, 140)
            if node.system_id in player_data.unlocked_systems:
                color = (110, 190, 210)
            if node.system_id in player_data.cleared_systems:
                color = (116, 220, 150)
            if node.system_id == player_data.current_system_id:
                color = (245, 220, 130)
            pygame.draw.circle(surface, color, (x, y), 4)
            if node.system_id in player_data.cleared_systems:
                pygame.draw.circle(surface, (220, 240, 220), (x, y), 7, width=1)

    def _draw_galaxy_connections(
        self, surface: pygame.Surface, universe: Universe, rect: pygame.Rect
    ) -> None:
        for node in universe.systems:
            x, y = self._galaxy_position(rect, node.map_position)
            for connected_id in node.connections:
                if connected_id < node.system_id:
                    continue
                other = universe.systems[connected_id]
                ox, oy = self._galaxy_position(rect, other.map_position)
                pygame.draw.line(surface, (54, 58, 78), (x, y), (ox, oy), 1)

    def _galaxy_position(
        self, rect: pygame.Rect, map_position: tuple[int, int]
    ) -> tuple[int, int]:
        return (
            rect.x + int(map_position[0] / constants.GALAXY_WIDTH * rect.width),
            rect.y + int(map_position[1] / constants.GALAXY_HEIGHT * rect.height),
        )

    @staticmethod
    def _hyperjump_rect() -> pygame.Rect:
        return pygame.Rect(230, 86, 820, 548)

    def _draw_text(
        self,
        surface: pygame.Surface,
        text: str,
        pos: tuple[int, int],
        color: tuple[int, int, int],
        font: object | None = None,
    ) -> None:
        text_surface = (font or self._font).render(  # type: ignore[attr-defined]
            text, True, color
        )
        surface.blit(text_surface, pos)
