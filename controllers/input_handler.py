"""Keyboard and mouse input translation."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

LEFT_SCANCODES = {pygame.KSCAN_A, pygame.KSCAN_LEFT}
RIGHT_SCANCODES = {pygame.KSCAN_D, pygame.KSCAN_RIGHT}
UP_SCANCODES = {pygame.KSCAN_W, pygame.KSCAN_UP}
DOWN_SCANCODES = {pygame.KSCAN_S, pygame.KSCAN_DOWN}
HYPERJUMP_SCANCODES = {pygame.KSCAN_H}
INTERACT_SCANCODES = {pygame.KSCAN_E}


@dataclass
class InputState:
    """Normalized gameplay input for one frame."""

    movement: pygame.Vector2
    aim_screen: pygame.Vector2
    firing: bool
    pause_pressed: bool = False
    hyperjump_pressed: bool = False
    interact_pressed: bool = False
    weapon_delta: int = 0


class InputHandler:
    """Convert Pygame events and key state into gameplay commands."""

    def __init__(self) -> None:
        """Initialize mouse tracking."""

        self._aim_screen = pygame.Vector2()
        self._firing = False
        self._pressed_scancodes: set[int] = set()

    def poll(self) -> tuple[InputState, bool]:
        """Read one frame of input.

        Returns:
            A tuple of input state and quit request flag.
        """

        pause_pressed = False
        hyperjump_pressed = False
        interact_pressed = False
        weapon_delta = 0
        quit_requested = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_requested = True
            elif event.type == pygame.KEYDOWN:
                scancode = getattr(event, "scancode", None)
                if scancode is not None:
                    self._pressed_scancodes.add(scancode)
                if event.key == pygame.K_ESCAPE:
                    pause_pressed = True
                elif event.key == pygame.K_h or scancode in HYPERJUMP_SCANCODES:
                    hyperjump_pressed = True
                elif event.key == pygame.K_e or scancode in INTERACT_SCANCODES:
                    interact_pressed = True
            elif event.type == pygame.KEYUP:
                scancode = getattr(event, "scancode", None)
                if scancode is not None:
                    self._pressed_scancodes.discard(scancode)
            elif event.type == pygame.WINDOWFOCUSLOST:
                self._pressed_scancodes.clear()
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
        moving_right = self._is_key_down(
            keys, pygame.K_d, pygame.K_RIGHT
        ) or self._has_scancode(RIGHT_SCANCODES)
        moving_left = self._is_key_down(
            keys, pygame.K_a, pygame.K_LEFT
        ) or self._has_scancode(LEFT_SCANCODES)
        moving_down = self._is_key_down(
            keys, pygame.K_s, pygame.K_DOWN
        ) or self._has_scancode(DOWN_SCANCODES)
        moving_up = self._is_key_down(
            keys, pygame.K_w, pygame.K_UP
        ) or self._has_scancode(UP_SCANCODES)
        movement = pygame.Vector2(
            float(moving_right) - float(moving_left),
            float(moving_down) - float(moving_up),
        )
        mouse_pos = pygame.mouse.get_pos()
        self._aim_screen = pygame.Vector2(mouse_pos)

        state = InputState(
            movement=movement,
            aim_screen=self._aim_screen,
            firing=self._firing,
            pause_pressed=pause_pressed,
            hyperjump_pressed=hyperjump_pressed,
            interact_pressed=interact_pressed,
            weapon_delta=weapon_delta,
        )
        return state, quit_requested

    def _has_scancode(self, scancodes: set[int]) -> bool:
        """Return True when any physical key from a scancode group is pressed."""

        return any(scancode in self._pressed_scancodes for scancode in scancodes)

    def _is_key_down(self, keys: pygame.key.ScancodeWrapper, *key_codes: int) -> bool:
        """Return True when any Pygame key code is currently pressed."""

        return any(keys[key_code] for key_code in key_codes)
