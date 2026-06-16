"""Main game loop with delta time and fixed timestep accumulator."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pygame

import constants
from controllers.ai_controller import AIController
from controllers.collision_manager import CollisionManager
from controllers.input_handler import InputHandler, InputState
from models.galaxy import StarSystem, Universe
from models.player import PlayerData
from utils.save_load import load_game, save_game
from views.hud import HUD
from views.menu import MenuSystem
from views.renderer import Renderer
from views.text import create_font


class GameLoop:
    """Coordinate input, simulation, rendering, menus, and saving."""

    def __init__(self) -> None:
        """Initialize Pygame and game services."""

        log_level = os.getenv(constants.LOG_LEVEL_ENV, "INFO").upper()
        logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
        pygame.init()
        pygame.display.set_caption(constants.WINDOW_TITLE)
        self._screen = pygame.display.set_mode(
            (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        )
        self._clock = pygame.time.Clock()
        self._font = create_font(20)
        self._input = InputHandler()
        self._renderer = Renderer(self._screen)
        self._hud = HUD(self._font)
        self._menu = MenuSystem(self._font)
        self._ai = AIController()
        self._collisions = CollisionManager()
        self._save_path = Path(constants.SAVE_FILE)

        self._mode = "main"
        self._running = True
        self._accumulator = 0.0
        self._universe: Universe | None = None
        self._player_data = PlayerData()
        self._system: StarSystem | None = None

    def run(self) -> None:
        """Run until the user exits."""

        while self._running:
            frame_time = min(
                self._clock.tick(constants.FPS_LIMIT) / 1000.0,
                constants.MAX_FRAME_TIME,
            )
            if self._mode == "playing":
                self._run_playing(frame_time)
            else:
                self._run_menu(self._mode)
            pygame.display.flip()

        self._autosave()
        pygame.quit()

    def _run_playing(self, frame_time: float) -> None:
        state, quit_requested = self._input.poll()
        if quit_requested:
            self._running = False
            return
        if state.pause_pressed:
            self._mode = "pause"
            return

        self._accumulator += frame_time
        while self._accumulator >= constants.FIXED_TIME_STEP:
            self._fixed_update(state, constants.FIXED_TIME_STEP)
            self._accumulator -= constants.FIXED_TIME_STEP

        if self._system is not None and self._universe is not None:
            self._renderer.draw_system(self._system)
            self._hud.draw(
                self._screen, self._system, self._player_data, self._universe
            )

    def _run_menu(self, menu_name: str) -> None:
        has_save = self._save_path.exists()
        action, quit_requested = self._menu.handle_events(menu_name, has_save)
        if quit_requested:
            self._running = False
        elif action is not None:
            self._handle_menu_action(action)
        if self._running and self._mode != "playing":
            self._menu.draw(self._screen, self._mode, self._save_path.exists())

    def _fixed_update(self, state: InputState, dt: float) -> None:
        if self._system is None:
            return

        player = self._system.player
        player.accelerate(state.movement, dt)
        if state.weapon_delta:
            player.weapon_index = (player.weapon_index + state.weapon_delta) % 2
        if state.firing:
            target = self._renderer.screen_to_world(state.aim_screen, player.position)
            projectile = player.fire_at(target)
            if projectile is not None:
                self._system.add_projectile(projectile)

        for projectile in self._ai.update(self._system.enemies, player, dt):
            self._system.add_projectile(projectile)

        self._system.update_entities(dt)
        destroyed = self._collisions.resolve(self._system)
        if destroyed:
            self._player_data.resources += destroyed * 5

        if self._system.is_cleared() and not self._system.reward_granted:
            self._system.reward_granted = True
            self._player_data.resources += 35
            artifact = f"Осколок Тиши {self._system.node.system_id + 1}"
            if artifact not in self._player_data.artifacts:
                self._player_data.artifacts.append(artifact)

        if state.hyperjump_pressed and self._system.is_cleared():
            self._jump_to_next_system()

        if not player.alive:
            self._player_data.runs_completed += 1
            self._autosave()
            self._mode = "main"

    def _handle_menu_action(self, action: str) -> None:
        if action == "new_game":
            self._start_new_game()
        elif action == "continue":
            self._continue_game()
        elif action == "settings":
            self._mode = "settings"
        elif action == "resume":
            self._mode = "playing"
        elif action == "save":
            self._autosave()
            self._mode = "pause"
        elif action == "back":
            self._mode = "pause" if self._system is not None else "main"
        elif action == "main_menu":
            self._autosave()
            self._mode = "main"
        elif action == "exit":
            self._running = False

    def _start_new_game(self) -> None:
        self._universe = Universe()
        self._player_data = PlayerData()
        self._system = self._universe.create_star_system(0, self._player_data)
        self._accumulator = 0.0
        self._mode = "playing"
        self._autosave()

    def _continue_game(self) -> None:
        loaded = load_game(self._save_path)
        if loaded is None:
            return
        seed, player_data = loaded
        self._universe = Universe(seed)
        self._player_data = player_data
        system_id = min(
            max(0, self._player_data.current_system_id),
            len(self._universe.systems) - 1,
        )
        self._system = self._universe.create_star_system(system_id, self._player_data)
        self._accumulator = 0.0
        self._mode = "playing"

    def _jump_to_next_system(self) -> None:
        if self._universe is None or self._system is None:
            return
        connected = self._universe.connected_systems(self._system.node.system_id)
        if not connected:
            return
        unvisited = [
            node
            for node in connected
            if node.system_id not in self._player_data.unlocked_systems
        ]
        target = (unvisited or connected)[0]
        self._system = self._universe.create_star_system(
            target.system_id, self._player_data
        )
        self._autosave()

    def _autosave(self) -> None:
        if self._universe is None:
            return
        try:
            save_game(self._save_path, self._universe.seed, self._player_data)
        except OSError:
            logging.exception("Failed to save game")
