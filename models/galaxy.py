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
    Faction,
    Planet,
    Projectile,
    Ship,
    create_ancient_ship,
    create_asteroid,
    create_player_ship,
)
from models.player import PlayerData
from models.story import story_dialog
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
class HitEffect:
    """Short-lived visual marker for a weapon impact."""

    position: pygame.Vector2
    age: float = 0.0
    duration: float = constants.HIT_EFFECT_DURATION

    @property
    def alive(self) -> bool:
        """Return True while the effect should be rendered."""

        return self.age < self.duration

    @property
    def ratio(self) -> float:
        """Return normalized life progress in the range [0, 1]."""

        if self.duration <= 0.0:
            return 1.0
        return max(0.0, min(1.0, self.age / self.duration))

    def update(self, dt: float) -> None:
        """Advance the effect timer."""

        self.age += dt


@dataclass
class StarSystem:
    """Current playable location with entities and objectives."""

    node: SystemNode
    seed: int
    player: Ship
    asteroids: list[Asteroid]
    enemies: list[AncientShip]
    planet: Planet | None = None
    projectiles: list[Projectile] = field(default_factory=list)
    hit_effects: list[HitEffect] = field(default_factory=list)
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

    def add_hit_effect(self, position: pygame.Vector2) -> None:
        """Add a visual impact effect at a world position."""

        self.hit_effects.append(HitEffect(position.copy()))

    def update_entities(self, dt: float) -> None:
        """Advance all entities and remove destroyed objects."""

        for entity in self.entities:
            entity.update(dt)
            self._wrap_entity(entity)

        for effect in self.hit_effects:
            effect.update(dt)

        self.asteroids = [asteroid for asteroid in self.asteroids if asteroid.alive]
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]
        self.projectiles = [
            projectile for projectile in self.projectiles if projectile.alive
        ]
        self.hit_effects = [effect for effect in self.hit_effects if effect.alive]

    def is_cleared(self) -> bool:
        """Return True when no enemies remain."""

        return not self.enemies

    def planet_in_range(self) -> bool:
        """Return True when the player can contact the system planet."""

        if self.planet is None:
            return False
        return (
            self.player.position.distance_squared_to(self.planet.position)
            <= constants.PLANET_INTERACTION_DISTANCE
            * constants.PLANET_INTERACTION_DISTANCE
        )

    def complete_planet_quest(self, player_data: PlayerData) -> list[str]:
        """Complete the planet conversation and grant its one-time reward.

        Args:
            player_data: Persistent player progress.

        Returns:
            Dialog lines to show to the player.
        """

        if self.planet is None:
            return []
        lines = list(self.planet.dialog_lines)
        if self.node.system_id in player_data.completed_quests:
            return [f"{self.planet.name}: канал молчит. Архив уже изучен."]

        self.planet.reward_claimed = True
        player_data.completed_quests.append(self.node.system_id)
        player_data.story_dialog_index += 1
        player_data.resources += constants.PLANET_QUEST_REWARD
        artifact = f"Запись {self.planet.name}"
        if artifact not in player_data.artifacts:
            player_data.artifacts.append(artifact)
        lines.append(
            f"Получено: {constants.PLANET_QUEST_REWARD} ресурсов и архивный фрагмент."
        )
        return lines

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
        player.max_speed += player_data.upgrades.get("engine", 0) * 24.0
        player.max_energy += player_data.upgrades.get("reactor", 0) * 16.0
        player.energy = player.max_energy
        player.weapon_damage_bonus = player_data.upgrades.get("weapons", 0) * 4.0

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
        if system_id in player_data.cleared_systems:
            enemies = []
        planet = self._create_planet(node, rng, player_data)
        return StarSystem(
            node=node,
            seed=self.seed + system_id,
            player=player,
            asteroids=asteroids,
            enemies=enemies,
            planet=planet,
            reward_granted=system_id in player_data.cleared_systems,
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

    def _create_planet(
        self, node: SystemNode, rng: random.Random, player_data: PlayerData
    ) -> Planet | None:
        if rng.random() >= constants.PLANET_CHANCE:
            return None

        position = pygame.Vector2(
            rng.randint(180, constants.WORLD_WIDTH - 180),
            rng.randint(180, constants.WORLD_HEIGHT - 180),
        )
        if (
            position.distance_to(
                pygame.Vector2(constants.WORLD_WIDTH / 2, constants.WORLD_HEIGHT / 2)
            )
            < constants.PLANET_INTERACTION_DISTANCE
        ):
            position += pygame.Vector2(constants.PLANET_INTERACTION_DISTANCE, 0.0)

        name = f"Мир {node.system_id + 1:02d}"
        dialog_lines = story_dialog(player_data.story_dialog_index, name)
        return Planet(
            position=position,
            velocity=pygame.Vector2(),
            radius=constants.PLANET_RADIUS,
            faction=Faction.NEUTRAL,
            max_health=10_000.0,
            name=name,
            dialog_lines=dialog_lines,
            reward_claimed=node.system_id in player_data.completed_quests,
        )
