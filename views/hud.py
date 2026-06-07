"""Heads-up display and minimap rendering."""

from __future__ import annotations

import pygame

import constants
from models.galaxy import StarSystem, Universe
from models.player import PlayerData


class HUD:
    """Draw player status, objectives, and navigation widgets."""

    def __init__(self, font: pygame.font.Font) -> None:
        """Store font resources."""

        self._font = font
        self._small_font = pygame.font.SysFont("dejavusans", 16)

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
            objective = "Патруль уничтожен. H: гиперпрыжок"
        self._draw_text(surface, objective, (24, 148), (230, 230, 230))
        self._draw_text(
            surface,
            f"Ресурсы: {player_data.resources}   Артефакты: {len(player_data.artifacts)}",
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
        player_pos = (
            rect.x + int(system.player.position.x * scale_x),
            rect.y + int(system.player.position.y * scale_y),
        )
        pygame.draw.circle(surface, (80, 220, 220), player_pos, 4)

    def _draw_galaxy(
        self, surface: pygame.Surface, universe: Universe, player_data: PlayerData
    ) -> None:
        rect = pygame.Rect(constants.SCREEN_WIDTH - 210, 156, 180, 106)
        pygame.draw.rect(surface, (13, 15, 22), rect, border_radius=4)
        pygame.draw.rect(surface, (78, 82, 98), rect, width=1, border_radius=4)
        for node in universe.systems:
            x = rect.x + int(node.map_position[0] / constants.GALAXY_WIDTH * rect.width)
            y = rect.y + int(
                node.map_position[1] / constants.GALAXY_HEIGHT * rect.height
            )
            for connected_id in node.connections:
                if connected_id < node.system_id:
                    continue
                other = universe.systems[connected_id]
                ox = rect.x + int(
                    other.map_position[0] / constants.GALAXY_WIDTH * rect.width
                )
                oy = rect.y + int(
                    other.map_position[1] / constants.GALAXY_HEIGHT * rect.height
                )
                pygame.draw.line(surface, (54, 58, 78), (x, y), (ox, oy), 1)
        for node in universe.systems:
            x = rect.x + int(node.map_position[0] / constants.GALAXY_WIDTH * rect.width)
            y = rect.y + int(
                node.map_position[1] / constants.GALAXY_HEIGHT * rect.height
            )
            color = (110, 120, 140)
            if node.system_id in player_data.unlocked_systems:
                color = (110, 190, 210)
            if node.system_id == player_data.current_system_id:
                color = (245, 220, 130)
            pygame.draw.circle(surface, color, (x, y), 4)

    def _draw_text(
        self,
        surface: pygame.Surface,
        text: str,
        pos: tuple[int, int],
        color: tuple[int, int, int],
        font: pygame.font.Font | None = None,
    ) -> None:
        text_surface = (font or self._font).render(text, True, color)
        surface.blit(text_surface, pos)
