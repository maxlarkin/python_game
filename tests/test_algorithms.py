"""Focused tests for core algorithms."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

import constants
from models.entities import create_player_ship
from models.galaxy import Universe
from models.player import PlayerData
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


def test_player_upgrades_spend_resources_and_survive_serialization() -> None:
    """Permanent upgrades should scale cost and serialize with save data."""

    player = PlayerData(resources=200)
    assert player.buy_upgrade("hull")
    assert player.resources == 140
    assert player.upgrades["hull"] == 1
    assert player.upgrade_cost("hull") == 90

    restored = PlayerData.from_dict(player.to_dict())
    assert restored.resources == player.resources
    assert restored.upgrades == player.upgrades


def test_star_system_planet_quest_rewards_once(monkeypatch) -> None:
    """Planet conversations should grant their reward only once."""

    monkeypatch.setattr(constants, "PLANET_CHANCE", 1.0)
    player = PlayerData()
    system = Universe(seed=123).create_star_system(0, player)
    assert system.planet is not None

    system.player.position = system.planet.position.copy()
    assert system.planet_in_range()
    lines = system.complete_planet_quest(player)

    assert lines
    assert player.resources == constants.PLANET_QUEST_REWARD
    assert player.completed_quests == [0]
    assert player.artifacts

    system.complete_planet_quest(player)
    assert player.resources == constants.PLANET_QUEST_REWARD
    assert player.completed_quests == [0]


def test_player_weapon_slots_have_distinct_projectiles() -> None:
    """Mouse-wheel weapon slots should change projectile behavior."""

    ship = create_player_ship(pygame.Vector2(100.0, 100.0))
    first = ship.fire_at(pygame.Vector2(200.0, 100.0))
    assert first is not None

    ship.cooldown_remaining = 0.0
    ship.weapon_index = 1
    second = ship.fire_at(pygame.Vector2(200.0, 100.0))
    assert second is not None
    assert second.damage > first.damage
    assert second.velocity.length() < first.velocity.length()
