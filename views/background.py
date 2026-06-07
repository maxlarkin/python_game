"""Procedural nebula background generation."""

from __future__ import annotations

import pygame

import constants
from utils.perlin import PerlinNoise


class BackgroundGenerator:
    """Create cached Perlin-noise nebula surfaces."""

    def __init__(self) -> None:
        """Initialize the cache."""

        self._cache: dict[int, pygame.Surface] = {}

    def get(self, seed: int, size: tuple[int, int]) -> pygame.Surface:
        """Return a background surface for a system seed."""

        if seed not in self._cache:
            self._cache[seed] = self._generate(seed, size)
        return self._cache[seed]

    def _generate(self, seed: int, size: tuple[int, int]) -> pygame.Surface:
        width, height = size
        cell = constants.BACKGROUND_CELL_SIZE
        small_size = (max(1, width // cell), max(1, height // cell))
        surface = pygame.Surface(small_size)
        noise = PerlinNoise(seed=seed)
        for y in range(small_size[1]):
            for x in range(small_size[0]):
                value = noise.normalized(
                    x * constants.BACKGROUND_NOISE_SCALE * cell,
                    y * constants.BACKGROUND_NOISE_SCALE * cell,
                )
                stars = noise.normalized(x * 0.19 + 77.0, y * 0.19 - 31.0)
                red = int(9 + value * 30)
                green = int(10 + value * 18)
                blue = int(24 + value * 72)
                if stars > 0.84:
                    red = min(255, red + 90)
                    green = min(255, green + 90)
                    blue = min(255, blue + 110)
                surface.set_at((x, y), (red, green, blue))
        return pygame.transform.smoothscale(surface, size)
