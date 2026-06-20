"""Music playback helpers."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pygame

import constants


class MusicManager:
    """Manage lobby and in-game music playlists."""

    def __init__(self, assets_dir: Path) -> None:
        """Initialize the music manager.

        Args:
            assets_dir: Root assets directory.
        """

        self._music_dir = assets_dir / "music"
        self._enabled = self._initialize_mixer()
        self._context = ""
        self._current_track: Path | None = None
        self._game_index = 0
        self._lobby_track = self._music_dir / constants.LOBBY_TRACK
        self._game_tracks = self._discover_game_tracks()

    def update(self, mode: str, has_active_run: bool) -> None:
        """Keep music matched to the current game context.

        Args:
            mode: Current game loop mode.
            has_active_run: True when a star system is loaded.
        """

        if not self._enabled:
            return

        target_context = self._target_context(mode, has_active_run)
        if target_context != self._context:
            self._context = target_context
            if target_context == "lobby":
                self._play_lobby()
            elif target_context == "game":
                self._play_game_track(reset=False)
            return

        if self._context == "game" and not pygame.mixer.music.get_busy():
            self._play_game_track(reset=False)
        elif self._context == "lobby" and not pygame.mixer.music.get_busy():
            self._play_lobby()

    def stop(self) -> None:
        """Fade out music before shutdown."""

        if self._enabled:
            pygame.mixer.music.fadeout(constants.MUSIC_FADE_MS)

    def _initialize_mixer(self) -> bool:
        if os.getenv("SDL_VIDEODRIVER") == "dummy" and not os.getenv(
            "SDL_AUDIODRIVER"
        ):
            return False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.set_volume(constants.MUSIC_VOLUME)
        except pygame.error as error:
            logging.warning("Music mixer is unavailable: %s", error)
            return False
        return True

    def _discover_game_tracks(self) -> list[Path]:
        if not self._music_dir.exists():
            return []
        tracks = sorted(
            self._music_dir.glob("*.mp3"), key=lambda path: path.name.lower()
        )
        return [track for track in tracks if track.name != constants.LOBBY_TRACK]

    def _target_context(self, mode: str, has_active_run: bool) -> str:
        if mode == "main" or not has_active_run:
            return "lobby"
        return "game"

    def _play_lobby(self) -> None:
        if not self._lobby_track.exists():
            return
        self._play_track(self._lobby_track, loops=-1)

    def _play_game_track(self, reset: bool) -> None:
        if not self._game_tracks:
            return
        if reset:
            self._game_index = 0
        track = self._game_tracks[self._game_index]
        self._game_index = (self._game_index + 1) % len(self._game_tracks)
        self._play_track(track, loops=0)

    def _play_track(self, track: Path, loops: int) -> None:
        if self._current_track == track and pygame.mixer.music.get_busy():
            return
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(constants.MUSIC_VOLUME)
            pygame.mixer.music.play(loops=loops, fade_ms=constants.MUSIC_FADE_MS)
            self._current_track = track
        except pygame.error as error:
            logging.warning("Failed to play music track %s: %s", track, error)
            self._enabled = False
