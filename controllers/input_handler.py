"""Keyboard and mouse input translation."""

from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class InputState:
    """Normalized gameplay input for one frame."""

    movement: pygame.Vector2
    aim_screen: pygame.Vector2
    firing: bool
    pause_pressed: bool = False
    hyperjump_pressed: bool = False
    weapon_delta: int = 0


class InputHandler:
    """Convert Pygame events and key state into gameplay commands."""

    def __init__(self) -> None:
        """Initialize mouse tracking."""

        self._aim_screen = pygame.Vector2()
        self._firing = False

    def poll(self) -> tuple[InputState, bool]:
        """Read one frame of input.

        Returns:
            A tuple of input state and quit request flag.
        """

        pause_pressed = False
        hyperjump_pressed = False
        weapon_delta = 0
        quit_requested = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_requested = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pause_pressed = True
                elif event.key == pygame.K_h:
                    hyperjump_pressed = True
            elif event.type == pygame.MOUSEMOTION:
                self._aim_screen = pygame.Vector2(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._firing = True
                elif event.button == 4:
                    weapon_delta = -1
                elif event.button == 5:
                    weapon_delta = 1
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._firing = False

        keys = pygame.key.get_pressed()
        movement = pygame.Vector2(
            float(keys[pygame.K_d] or keys[pygame.K_RIGHT])
            - float(keys[pygame.K_a] or keys[pygame.K_LEFT]),
            float(keys[pygame.K_s] or keys[pygame.K_DOWN])
            - float(keys[pygame.K_w] or keys[pygame.K_UP]),
        )
        mouse_pos = pygame.mouse.get_pos()
        self._aim_screen = pygame.Vector2(mouse_pos)

        state = InputState(
            movement=movement,
            aim_screen=self._aim_screen,
            firing=self._firing,
            pause_pressed=pause_pressed,
            hyperjump_pressed=hyperjump_pressed,
            weapon_delta=weapon_delta,
        )
        return state, quit_requested
