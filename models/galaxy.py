"""Universe and star-system generation."""

from __future__ import annotations

from dataclasses import dataclass, field
import random

import pygame

import constants
from models.entities import (
    AncientShip,
    Asteroid,
    Entity,
    Projectile,
    Ship,
    create_ancient_ship,
    create_asteroid,
    create_player_ship,
)
from models.player import PlayerData
from utils.bsp import BspGenerator, Rect


@dataclass
class SystemNode:
    """A generated star system on the galaxy map."""

    system_id: int
    name: str
    map_position: tuple[int, int]
    room: Rect
    connections: set[int] = field(default_factory=set)
    visited: bool = False


@dataclass
class StarSystem:
    """Current playable location with entities and objectives."""

    node: SystemNode
    seed: int
    player: Ship
    asteroids: list[Asteroid]
    enemies: list[AncientShip]
    projectiles: list[Projectile] = field(default_factory=list)
    width: int = constants.WORLD_WIDTH
    height: int = constants.WORLD_HEIGHT
    objective_text: str = "Уничтожьте патруль Древних"
    reward_granted: bool = False

    @property
    def entities(self) -> list[Entity]:
        """Return all live entities in the system."""

        return [self.player, *self.asteroids, *self.enemies, *self.projectiles]

    def add_projectile(self, projectile: Projectile) -> None:
        """Add a projectile to the system."""

        self.projectiles.append(projectile)

    def update_entities(self, dt: float) -> None:
        """Advance all entities and remove destroyed objects."""

        for entity in self.entities:
            entity.update(dt)
            self._wrap_entity(entity)

        self.asteroids = [asteroid for asteroid in self.asteroids if asteroid.alive]
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]
        self.projectiles = [
            projectile for projectile in self.projectiles if projectile.alive
        ]

    def is_cleared(self) -> bool:
        """Return True when no enemies remain."""

        return not self.enemies

    def _wrap_entity(self, entity: Entity) -> None:
        entity.position.x %= self.width
        entity.position.y %= self.height


class Universe:
    """BSP-generated galaxy map and system factory."""

    def __init__(self, seed: int | None = None) -> None:
        """Generate a new universe.

        Args:
            seed: Optional deterministic seed.
        """

        self.seed = seed if seed is not None else random.randint(1, 999_999)
        self._random = random.Random(self.seed)
        self.systems: list[SystemNode] = []
        self._generate()

    def connected_systems(self, system_id: int) -> list[SystemNode]:
        """Return systems directly reachable from the given system."""

        node = self.systems[system_id]
        return [self.systems[index] for index in sorted(node.connections)]

    def create_star_system(self, system_id: int, player_data: PlayerData) -> StarSystem:
        """Create a playable star system from a galaxy node.

        Args:
            system_id: Galaxy system identifier.
            player_data: Persistent player data.

        Returns:
            A generated star system.
        """

        node = self.systems[system_id]
        node.visited = True
        if system_id not in player_data.unlocked_systems:
            player_data.unlocked_systems.append(system_id)
        player_data.current_system_id = system_id

        rng = random.Random(self.seed + system_id * 997)
        player = create_player_ship(
            pygame.Vector2(constants.WORLD_WIDTH / 2, constants.WORLD_HEIGHT / 2)
        )
        player.max_health += player_data.upgrades.get("hull", 0) * 18.0
        player.health = player.max_health
        player.max_shields += player_data.upgrades.get("shields", 0) * 12.0
        player.shields = player.max_shields

        asteroids = [
            create_asteroid(
                pygame.Vector2(
                    rng.randint(80, constants.WORLD_WIDTH - 80),
                    rng.randint(80, constants.WORLD_HEIGHT - 80),
                ),
                rng.randint(
                    constants.ASTEROID_MIN_RADIUS, constants.ASTEROID_MAX_RADIUS
                ),
                rng,
            )
            for _ in range(
                rng.randint(constants.ASTEROID_COUNT_MIN, constants.ASTEROID_COUNT_MAX)
            )
        ]
        enemies = [
            create_ancient_ship(
                pygame.Vector2(
                    rng.randint(120, constants.WORLD_WIDTH - 120),
                    rng.randint(120, constants.WORLD_HEIGHT - 120),
                ),
                rng,
                (constants.WORLD_WIDTH, constants.WORLD_HEIGHT),
            )
            for _ in range(
                rng.randint(constants.ANCIENT_COUNT_MIN, constants.ANCIENT_COUNT_MAX)
            )
        ]
        return StarSystem(
            node=node,
            seed=self.seed + system_id,
            player=player,
            asteroids=asteroids,
            enemies=enemies,
        )

    def _generate(self) -> None:
        generator = BspGenerator(
            constants.GALAXY_WIDTH,
            constants.GALAXY_HEIGHT,
            constants.BSP_MIN_LEAF_SIZE,
            constants.BSP_MAX_DEPTH,
            self.seed,
        )
        _, rooms, corridors = generator.generate()
        self._random.shuffle(rooms)
        target_count = self._random.randint(
            constants.SYSTEM_COUNT_MIN, constants.SYSTEM_COUNT_MAX
        )
        selected_rooms = rooms[:target_count]
        self.systems = [
            SystemNode(
                system_id=index,
                name=f"Сектор {index + 1:02d}",
                map_position=room.center,
                room=room,
            )
            for index, room in enumerate(selected_rooms)
        ]
        self._connect_nearest_rooms(corridors)

    def _connect_nearest_rooms(
        self, corridors: list[tuple[tuple[int, int], tuple[int, int]]]
    ) -> None:
        if len(self.systems) < 2:
            return
        for index in range(len(self.systems) - 1):
            self._connect(index, index + 1)

        for start, end in corridors:
            start_id = self._nearest_system_id(start)
            end_id = self._nearest_system_id(end)
            if start_id != end_id:
                self._connect(start_id, end_id)

    def _nearest_system_id(self, point: tuple[int, int]) -> int:
        point_vec = pygame.Vector2(point)
        return min(
            self.systems,
            key=lambda system: point_vec.distance_squared_to(system.map_position),
        ).system_id

    def _connect(self, left_id: int, right_id: int) -> None:
        self.systems[left_id].connections.add(right_id)
        self.systems[right_id].connections.add(left_id)
