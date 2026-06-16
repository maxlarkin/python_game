"""Main, pause, settings, and end-choice menus."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

import constants
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

    def handle_events(self, menu_name: str, has_save: bool) -> tuple[str | None, bool]:
        """Process menu events and return selected action plus quit flag."""

        buttons = self._buttons(menu_name, has_save)
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

    def draw(self, surface: pygame.Surface, menu_name: str, has_save: bool) -> None:
        """Draw a named menu."""

        surface.fill((8, 10, 16))
        title = constants.WINDOW_TITLE if menu_name == "main" else "Пауза"
        if menu_name == "settings":
            title = "Настройки"
        title_surface = self._title_font.render(title, True, (235, 235, 240))
        surface.blit(title_surface, (80, 76))
        subtitle = "Флот обречённых ищет путь в легендарную Тишь."
        if menu_name == "settings":
            subtitle = "Громкость и раскладка пока фиксированы. WASD, мышь, H."
        surface.blit(
            self._small_font.render(subtitle, True, (170, 178, 195)), (84, 138)
        )

        for button in self._buttons(menu_name, has_save):
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

    def _buttons(self, menu_name: str, has_save: bool) -> list[Button]:
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
            if not enabled:
                label = f"{label} недоступно"
            rect = pygame.Rect(86, start_y + index * 58, 260, 42)
            buttons.append(
                Button(label=label, action=action, rect=rect, enabled=enabled)
            )
        return buttons

    def _draw_story_hook(self, surface: pygame.Surface) -> None:
        lines = [
            "Родная звезда медленно убивает ваш народ.",
            "Древние отказали в спасении, и война почти проиграна.",
            "Один флот ещё может прорваться туда, где их сила слабеет.",
        ]
        y = constants.SCREEN_HEIGHT - 118
        for line in lines:
            surface.blit(self._small_font.render(line, True, (188, 190, 205)), (84, y))
            y += 24
