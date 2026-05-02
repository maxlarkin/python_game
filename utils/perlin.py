"""Classic two-dimensional Perlin noise implementation."""

from __future__ import annotations

import math
import random


class PerlinNoise:
    """Generate deterministic 2D Perlin noise values."""

    def __init__(self, seed: int | None = None, grid_size: int = 256) -> None:
        """Initialize gradients.

        Args:
            seed: Optional deterministic seed.
            grid_size: Number of gradient cells before wrapping.

        Raises:
            ValueError: If grid_size is too small.
        """

        if grid_size < 2:
            msg = "grid_size must be at least 2"
            raise ValueError(msg)
        self._grid_size = grid_size
        rng = random.Random(seed)
        self._gradients = [
            [self._random_unit_vector(rng) for _ in range(self._grid_size)]
            for _ in range(self._grid_size)
        ]

    def noise(self, x: float, y: float) -> float:
        """Return noise in the range approximately [-1, 1]."""

        x0 = math.floor(x)
        y0 = math.floor(y)
        x1 = x0 + 1
        y1 = y0 + 1

        sx = self._fade(x - x0)
        sy = self._fade(y - y0)

        n00 = self._dot_grid_gradient(x0, y0, x, y)
        n10 = self._dot_grid_gradient(x1, y0, x, y)
        n01 = self._dot_grid_gradient(x0, y1, x, y)
        n11 = self._dot_grid_gradient(x1, y1, x, y)

        ix0 = self._lerp(n00, n10, sx)
        ix1 = self._lerp(n01, n11, sx)
        return self._lerp(ix0, ix1, sy)

    def normalized(self, x: float, y: float) -> float:
        """Return noise remapped to the range [0, 1]."""

        return max(0.0, min(1.0, self.noise(x, y) * 0.5 + 0.5))

    @staticmethod
    def _fade(t: float) -> float:
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

    @staticmethod
    def _lerp(a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    @staticmethod
    def _random_unit_vector(rng: random.Random) -> tuple[float, float]:
        angle = rng.random() * math.tau
        return math.cos(angle), math.sin(angle)

    def _gradient(self, ix: int, iy: int) -> tuple[float, float]:
        return self._gradients[iy % self._grid_size][ix % self._grid_size]

    def _dot_grid_gradient(self, ix: int, iy: int, x: float, y: float) -> float:
        gradient_x, gradient_y = self._gradient(ix, iy)
        distance_x = x - ix
        distance_y = y - iy
        return distance_x * gradient_x + distance_y * gradient_y
