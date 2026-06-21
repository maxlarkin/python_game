"""Main, pause, settings, and end-choice menus."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

import constants
from models.player import PlayerData
from views.text import create_font


@dataclass(frozen=True)
class Button:
    """Clickable menu button."""

    label: str
    action: str
    rect: pygame.Rect
    enabled: bool = True


class MenuSystem:
    """Draw and process simple Pygame menus."""

    def __init__(self, font: object) -> None:
        """Initialize fonts."""

        self._font = font
        self._title_font = create_font(48)
        self._small_font = create_font(18)

    def handle_events(
        self, menu_name: str, has_save: bool, player_data: PlayerData | None = None
    ) -> tuple[str | None, bool]:
        """Process menu events and return selected action plus quit flag."""

        buttons = self._buttons(menu_name, has_save, player_data)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit", True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if menu_name == "pause":
                    return "resume", False
                if menu_name == "settings":
                    return "back", False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in buttons:
                    if button.enabled and button.rect.collidepoint(event.pos):
                        return button.action, False
        return None, False

    def draw(
        self,
        surface: pygame.Surface,
        menu_name: str,
        has_save: bool,
        player_data: PlayerData | None = None,
    ) -> None:
        """Draw a named menu."""

        surface.fill((8, 10, 16))
        title = constants.WINDOW_TITLE if menu_name == "main" else "Пауза"
        if menu_name == "settings":
            title = "Настройки"
        title_surface = self._title_font.render(title, True, (235, 235, 240))
        surface.blit(title_surface, (80, 76))
        subtitle = "Флот обречённых ищет путь в легендарную Тишь."
        if menu_name == "settings":
            subtitle = "Управление: WASD, мышь, H, E, G."
        surface.blit(
            self._small_font.render(subtitle, True, (170, 178, 195)), (84, 138)
        )

        for button in self._buttons(menu_name, has_save, player_data):
            mouse_over = button.rect.collidepoint(pygame.mouse.get_pos())
            fill = (36, 43, 58) if button.enabled else (28, 30, 38)
            if mouse_over and button.enabled:
                fill = (58, 70, 90)
            pygame.draw.rect(surface, fill, button.rect, border_radius=5)
            pygame.draw.rect(
                surface, (95, 104, 126), button.rect, width=1, border_radius=5
            )
            color = (235, 235, 238) if button.enabled else (112, 116, 128)
            label = self._font.render(  # type: ignore[attr-defined]
                button.label, True, color
            )
            label_rect = label.get_rect(center=button.rect.center)
            surface.blit(label, label_rect)

        if menu_name == "main":
            self._draw_story_hook(surface)

    def handle_dialog_events(self) -> tuple[str | None, bool]:
        """Process dialog input and return an action plus quit flag."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit", True
            if event.type == pygame.KEYDOWN:
                if event.key in {pygame.K_RETURN, pygame.K_e}:
                    return "advance", False
                if event.key == pygame.K_ESCAPE:
                    return "close", False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return "advance", False
        return None, False

    def draw_dialog(
        self,
        surface: pygame.Surface,
        title: str,
        lines: list[str],
        page: int,
    ) -> None:
        """Draw a story dialog over the current game view."""

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))
        panel = pygame.Rect(60, constants.SCREEN_HEIGHT - 250, 1160, 186)
        pygame.draw.rect(surface, (16, 19, 28), panel, border_radius=6)
        pygame.draw.rect(surface, (96, 110, 138), panel, width=1, border_radius=6)
        surface.blit(
            self._font.render(title, True, (235, 235, 240)),
            (panel.x + 22, panel.y + 18),
        )
        visible_lines = lines[page : page + 3]
        wrapped_lines: list[str] = []
        for line in visible_lines:
            wrapped_lines.extend(self._wrap_text(line, panel.width - 44, self._small_font))
        y = panel.y + 56
        for line in wrapped_lines[:4]:
            surface.blit(
                self._small_font.render(line, True, (205, 212, 226)), (panel.x + 22, y)
            )
            y += 28
        hint = "E: далее   Esc: закрыть"
        surface.blit(
            self._small_font.render(hint, True, (145, 154, 174)),
            (panel.right - 206, panel.bottom - 30),
        )

    def draw_upgrades(self, surface: pygame.Surface, player_data: PlayerData) -> None:
        """Draw the ship upgrade overlay."""

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        panel = pygame.Rect(260, 90, 760, 540)
        pygame.draw.rect(surface, (14, 18, 28), panel, border_radius=6)
        pygame.draw.rect(surface, (96, 110, 138), panel, width=1, border_radius=6)
        surface.blit(
            self._title_font.render("Улучшения корабля", True, (238, 238, 242)),
            (panel.x + 28, panel.y + 24),
        )
        surface.blit(
            self._small_font.render(
                f"Ресурсы: {player_data.resources}   G/Esc: закрыть",
                True,
                (168, 176, 196),
            ),
            (panel.x + 32, panel.y + 84),
        )

        descriptions = {
            "hull": "+18 к максимальному корпусу",
            "shields": "+12 к максимальным щитам",
            "engine": "+24 к максимальной скорости",
            "reactor": "+16 к запасу энергии",
            "weapons": "+4 к урону каждого выстрела",
        }
        for button in self._upgrade_buttons(player_data):
            upgrade_key = button.action.removeprefix("upgrade_")
            mouse_over = button.rect.collidepoint(pygame.mouse.get_pos())
            fill = (34, 42, 56) if button.enabled else (26, 29, 38)
            if mouse_over and button.enabled:
                fill = (54, 66, 86)
            pygame.draw.rect(surface, fill, button.rect, border_radius=5)
            pygame.draw.rect(
                surface, (86, 96, 122), button.rect, width=1, border_radius=5
            )
            color = (236, 238, 242) if button.enabled else (116, 120, 132)
            surface.blit(
                self._font.render(button.label, True, color),
                (button.rect.x + 18, button.rect.y + 9),
            )
            surface.blit(
                self._small_font.render(
                    descriptions[upgrade_key], True, (160, 170, 190)
                ),
                (button.rect.x + 18, button.rect.y + 36),
            )

    def upgrade_action_at(
        self, pos: tuple[int, int], player_data: PlayerData
    ) -> str | None:
        """Return the upgrade key clicked by the player, if purchasable."""

        for button in self._upgrade_buttons(player_data):
            if button.enabled and button.rect.collidepoint(pos):
                return button.action.removeprefix("upgrade_")
        return None

    def _buttons(
        self, menu_name: str, has_save: bool, player_data: PlayerData | None = None
    ) -> list[Button]:
        labels = {
            "main": [
                ("Новая игра", "new_game"),
                ("Продолжить", "continue"),
                ("Настройки", "settings"),
                ("Выход", "exit"),
            ],
            "pause": [
                ("Продолжить", "resume"),
                ("Сохранить", "save"),
                ("Загрузить", "continue"),
                ("Настройки", "settings"),
                ("В меню", "main_menu"),
            ],
            "settings": [("Назад", "back")],
        }[menu_name]
        buttons: list[Button] = []
        start_y = 210
        for index, (label, action) in enumerate(labels):
            enabled = action != "continue" or has_save
            if action.startswith("upgrade_") and player_data is not None:
                upgrade_key = action.removeprefix("upgrade_")
                enabled = player_data.resources >= player_data.upgrade_cost(upgrade_key)
            if not enabled:
                label = f"{label} недоступно"
            rect = pygame.Rect(86, start_y + index * 58, 260, 42)
            buttons.append(
                Button(label=label, action=action, rect=rect, enabled=enabled)
            )
        return buttons

    def _upgrade_buttons(self, player_data: PlayerData) -> list[Button]:
        buttons: list[Button] = []
        for index, upgrade_key in enumerate(constants.UPGRADE_COSTS):
            level = player_data.upgrades.get(upgrade_key, 0)
            cost = player_data.upgrade_cost(upgrade_key)
            label = f"{constants.UPGRADE_LABELS[upgrade_key]} ур.{level} - {cost}"
            rect = pygame.Rect(302, 205 + index * 72, 676, 58)
            buttons.append(
                Button(
                    label=label,
                    action=f"upgrade_{upgrade_key}",
                    rect=rect,
                    enabled=player_data.resources >= cost,
                )
            )
        return buttons

    def _wrap_text(self, text: str, max_width: int, font: object) -> list[str]:
        words = text.split()
        if not words:
            return [""]
        lines: list[str] = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if self._text_width(candidate, font) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    @staticmethod
    def _text_width(text: str, font: object) -> int:
        surface = font.render(text, True, (255, 255, 255))  # type: ignore[attr-defined]
        return surface.get_width()

    def _draw_story_hook(self, surface: pygame.Surface) -> None:
        lines = [
            "Одинокий исследовательский корабль летит в неизведанную галактику.",
            "В некоторых секторах аугурами корабля были обнаружены подозрительные руины.",
            "Что вас ждет в неизвестности?",
        ]
        y = constants.SCREEN_HEIGHT - 118
        for line in lines:
            surface.blit(self._small_font.render(line, True, (188, 190, 205)), (84, y))
            y += 24
