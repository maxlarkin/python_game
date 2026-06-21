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
from views.audio import MusicManager
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
        pygame.display.init()
        pygame.display.set_caption(constants.WINDOW_TITLE)
        display_flags = pygame.FULLSCREEN if constants.FULLSCREEN else 0
        self._screen = pygame.display.set_mode(
            (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), display_flags
        )
        self._clock = pygame.time.Clock()
        self._font = create_font(20)
        self._assets_dir = Path(__file__).resolve().parent.parent / "assets"
        self._input = InputHandler()
        self._renderer = Renderer(self._screen)
        self._music = MusicManager(self._assets_dir)
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
        self._dialog_title = ""
        self._dialog_lines: list[str] = []
        self._dialog_page = 0

    def run(self) -> None:
        """Run until the user exits."""

        while self._running:
            frame_time = min(
                self._clock.tick(constants.FPS_LIMIT) / 1000.0,
                constants.MAX_FRAME_TIME,
            )
            self._music.update(self._mode, self._system is not None)
            if self._mode == "playing":
                self._run_playing(frame_time)
            elif self._mode == "dialog":
                self._run_dialog()
            elif self._mode == "galaxy_map":
                self._run_galaxy_map()
            elif self._mode == "upgrades":
                self._run_upgrades()
            else:
                self._run_menu(self._mode)
            pygame.display.flip()

        self._autosave()
        self._music.stop()
        pygame.quit()

    def _run_playing(self, frame_time: float) -> None:
        state, quit_requested = self._input.poll()
        if quit_requested:
            self._running = False
            return
        if state.pause_pressed:
            self._mode = "pause"
            return
        if state.upgrades_pressed:
            self._mode = "upgrades"
            self._draw_playing()
            return
        if state.interact_pressed and self._open_planet_dialog():
            self._draw_playing()
            return

        self._accumulator += frame_time
        while self._accumulator >= constants.FIXED_TIME_STEP:
            self._fixed_update(state, constants.FIXED_TIME_STEP)
            self._accumulator -= constants.FIXED_TIME_STEP

        self._draw_playing()

    def _run_menu(self, menu_name: str) -> None:
        has_save = self._save_path.exists()
        action, quit_requested = self._menu.handle_events(
            menu_name, has_save, self._player_data
        )
        if quit_requested:
            self._running = False
        elif action is not None:
            self._handle_menu_action(action)
        if self._running and self._mode != "playing":
            self._menu.draw(
                self._screen,
                self._mode,
                self._save_path.exists(),
                self._player_data,
            )

    def _run_dialog(self) -> None:
        action, quit_requested = self._menu.handle_dialog_events()
        if quit_requested:
            self._running = False
        elif action == "advance":
            if self._dialog_page + 3 >= len(self._dialog_lines):
                self._mode = "playing"
            else:
                self._dialog_page += 3
        elif action == "close":
            self._mode = "playing"

        self._draw_playing()
        if self._running:
            self._menu.draw_dialog(
                self._screen,
                self._dialog_title,
                self._dialog_lines,
                self._dialog_page,
            )

    def _run_galaxy_map(self) -> None:
        if self._system is None or self._universe is None:
            self._mode = "main"
            return

        current_system_id = self._system.node.system_id
        connected = self._universe.connected_systems(current_system_id)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._mode = "playing"
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    index = event.key - pygame.K_1
                    if index < len(connected):
                        self._jump_to_system(connected[index].system_id)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                target_id = self._hud.hyperjump_node_at(
                    event.pos, self._universe, current_system_id
                )
                if target_id is not None:
                    self._jump_to_system(target_id)

        self._draw_playing()
        if self._running and self._mode == "galaxy_map":
            self._hud.draw_hyperjump_map(
                self._screen,
                self._universe,
                self._player_data,
                current_system_id,
            )

    def _run_upgrades(self) -> None:
        if self._system is None or self._universe is None:
            self._mode = "main"
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in {pygame.K_ESCAPE, pygame.K_g}:
                    self._mode = "playing"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = self._menu.upgrade_action_at(event.pos, self._player_data)
                if action is not None:
                    self._buy_upgrade(action)

        self._draw_playing()
        if self._running and self._mode == "upgrades":
            self._menu.draw_upgrades(self._screen, self._player_data)

    def _fixed_update(self, state: InputState, dt: float) -> None:
        if self._system is None:
            return

        player = self._system.player
        player.accelerate(state.movement, dt)
        if state.weapon_delta:
            player.weapon_index = (player.weapon_index + state.weapon_delta) % len(
                constants.PLAYER_WEAPONS
            )
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
            system_id = self._system.node.system_id
            if system_id not in self._player_data.cleared_systems:
                self._player_data.cleared_systems.append(system_id)
            artifact = f"Осколок Тиши {self._system.node.system_id + 1}"
            if artifact not in self._player_data.artifacts:
                self._player_data.artifacts.append(artifact)

        if state.hyperjump_pressed and self._system.is_cleared():
            self._mode = "galaxy_map"

        if not player.alive:
            self._player_data.runs_completed += 1
            self._player_data.reset_run_progress()
            self._autosave()
            self._mode = "main"

    def _handle_menu_action(self, action: str) -> None:
        if action == "new_game":
            self._start_new_game()
        elif action == "continue":
            self._continue_game()
        elif action == "settings":
            self._mode = "settings"
        elif action.startswith("upgrade_"):
            self._buy_upgrade(action.removeprefix("upgrade_"))
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

    def _jump_to_system(self, target_system_id: int) -> None:
        if self._universe is None or self._system is None:
            return
        connected_ids = {
            node.system_id
            for node in self._universe.connected_systems(self._system.node.system_id)
        }
        if target_system_id not in connected_ids:
            return
        self._system = self._universe.create_star_system(
            target_system_id, self._player_data
        )
        self._mode = "playing"
        self._autosave()

    def _open_planet_dialog(self) -> bool:
        if self._system is None or not self._system.planet_in_range():
            return False
        lines = self._system.complete_planet_quest(self._player_data)
        if not lines:
            return False
        planet = self._system.planet
        self._dialog_title = planet.name if planet is not None else "Связь"
        self._dialog_lines = lines
        self._dialog_page = 0
        self._mode = "dialog"
        self._autosave()
        return True

    def _draw_playing(self) -> None:
        if self._system is None or self._universe is None:
            return
        self._renderer.draw_system(self._system)
        self._hud.draw(self._screen, self._system, self._player_data, self._universe)

    def _buy_upgrade(self, upgrade_key: str) -> None:
        if not self._player_data.buy_upgrade(upgrade_key):
            return
        if self._system is not None:
            player = self._system.player
            if upgrade_key == "hull":
                player.max_health += 18.0
                player.health = min(player.max_health, (player.health or 0.0) + 18.0)
            elif upgrade_key == "shields":
                player.max_shields += 12.0
                player.shields = min(player.max_shields, player.shields + 12.0)
            elif upgrade_key == "engine":
                player.max_speed += 24.0
            elif upgrade_key == "reactor":
                player.max_energy += 16.0
                player.energy = min(player.max_energy, player.energy + 16.0)
            elif upgrade_key == "weapons":
                player.weapon_damage_bonus += 4.0
        self._autosave()

    def _autosave(self) -> None:
        if self._universe is None:
            return
        try:
            save_game(self._save_path, self._universe.seed, self._player_data)
        except OSError:
            logging.exception("Failed to save game")
