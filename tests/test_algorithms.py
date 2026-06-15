"""Focused tests for core algorithms."""

from __future__ import annotations

from dataclasses import dataclass

from utils.bsp import BspGenerator
from utils.perlin import PerlinNoise
from utils.quad_tree import QuadTree, Rect


@dataclass
class Box:
    """Simple object indexed by QuadTree tests."""

    rect: Rect

    def bounds(self) -> Rect:
        """Return test bounds."""

        return self.rect


def test_perlin_noise_is_deterministic_and_normalized() -> None:
    """Perlin noise should repeat for a fixed seed and stay normalized."""

    first = PerlinNoise(seed=42)
    second = PerlinNoise(seed=42)
    value = first.normalized(3.25, 8.75)
    assert value == second.normalized(3.25, 8.75)
    assert 0.0 <= value <= 1.0


def test_bsp_generator_creates_rooms_and_corridors() -> None:
    """BSP generation should produce bounded rooms and connecting edges."""

    _, rooms, corridors = BspGenerator(100, 60, 14, 5, seed=7).generate()
    assert len(rooms) >= 8
    assert corridors
    for room in rooms:
        assert 0 <= room.x < 100
        assert 0 <= room.y < 60
        assert room.x + room.width <= 100
        assert room.y + room.height <= 60


def test_quad_tree_queries_intersections() -> None:
    """QuadTree should return intersecting objects and skip distant ones."""

    tree = QuadTree[Box](Rect(0, 0, 100, 100), capacity=1, max_depth=4)
    near = Box(Rect(10, 10, 5, 5))
    far = Box(Rect(80, 80, 5, 5))
    assert tree.insert(near)
    assert tree.insert(far)
    result = tree.query(Rect(8, 8, 12, 12))
    assert near in result
    assert far not in result
