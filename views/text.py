"""Font helpers with a fallback for pygame builds without SDL_ttf."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pygame

CYRILLIC_FONT_NAMES = (
    "dejavusans",
    "noto sans",
    "liberation sans",
    "free sans",
    "arial",
)
CYRILLIC_FONT_PATHS = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
)


class FallbackFont:
    """Minimal text renderer used when pygame.font is unavailable."""

    def __init__(self, size: int) -> None:
        """Store approximate font metrics.

        Args:
            size: Requested font size in pixels.
        """

        self._size = size

    def render(
        self, text: str, _antialias: bool, color: tuple[int, int, int]
    ) -> pygame.Surface:
        """Render text as compact marker strokes.

        Args:
            text: Text to represent.
            _antialias: Ignored compatibility flag.
            color: Stroke color.

        Returns:
            A transparent surface with deterministic visual markers.
        """

        width = max(12, min(900, int(len(text) * self._size * 0.44)))
        height = max(8, self._size + 4)
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        if text:
            pygame.draw.rect(surface, color, (0, height - 3, width, 2))
            step = max(3, self._size // 3)
            for index in range(0, width, step):
                marker_height = 3 + (index // step) % max(3, self._size // 2)
                pygame.draw.line(
                    surface,
                    color,
                    (index, height - 4),
                    (index, max(0, height - 4 - marker_height)),
                    1,
                )
        return surface


class FreeTypeFont:
    """Adapter for pygame._freetype fonts with pygame.font-like rendering."""

    def __init__(self, font: Any) -> None:
        """Store a low-level FreeType font.

        Args:
            font: Instance of ``pygame._freetype.Font``.
        """

        self._font = font

    def render(
        self, text: str, _antialias: bool, color: tuple[int, int, int]
    ) -> pygame.Surface:
        """Render text to a surface.

        Args:
            text: Text to render.
            _antialias: Ignored; FreeType antialiasing is handled internally.
            color: Text color.

        Returns:
            Surface with rendered glyphs.
        """

        surface, _rect = self._font.render(text, fgcolor=color)
        return surface


def _first_existing_font_path() -> Path | None:
    """Return a bundled system font path that supports Cyrillic."""

    for font_path in CYRILLIC_FONT_PATHS:
        if font_path.exists():
            return font_path
    return None


def _create_freetype_font(size: int) -> FreeTypeFont | None:
    """Create a font through pygame._freetype when pygame.font is unavailable."""

    font_path = _first_existing_font_path()
    if font_path is None:
        return None

    try:
        freetype = importlib.import_module("pygame._freetype")
        if not freetype.get_init():
            freetype.init()
        return FreeTypeFont(freetype.Font(str(font_path), size))
    except (ImportError, AttributeError, OSError, pygame.error):
        return None


def create_font(size: int, name: str = "dejavusans") -> Any:
    """Return a pygame font or a safe fallback.

    Args:
        size: Font size in pixels.
        name: Preferred system font name.

    Returns:
        Object with a pygame-compatible ``render`` method.
    """

    font_module = getattr(pygame, "font", None)
    if type(font_module).__name__ == "MissingModule":
        return _create_freetype_font(size) or FallbackFont(size)

    try:
        if not pygame.font.get_init():
            pygame.font.init()
        font_names = dict.fromkeys((name, *CYRILLIC_FONT_NAMES))
        for font_name in font_names:
            matched_path = pygame.font.match_font(font_name)
            if matched_path is not None:
                return pygame.font.Font(matched_path, size)
        font_path = _first_existing_font_path()
        if font_path is not None:
            return pygame.font.Font(font_path, size)
        return pygame.font.SysFont(name, size)
    except (AttributeError, ImportError, NotImplementedError, pygame.error):
        return _create_freetype_font(size) or FallbackFont(size)
