"""Behavior tree and steering behaviours for Ancient patrols."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto

import pygame

import constants
from models.entities import AncientShip, Ship


class BehaviorStatus(Enum):
    """Behavior tree node result."""

    SUCCESS = auto()
    FAILURE = auto()
    RUNNING = auto()


class BehaviorNode:
    """Base class for behavior tree nodes."""

    def tick(self, context: AIContext) -> BehaviorStatus:
        """Evaluate the node.

        Args:
            context: Current AI context.

        Returns:
            Node execution status.
        """

        raise NotImplementedError


@dataclass
class AIContext:
    """Mutable context passed through a behavior tree tick."""

    enemy: AncientShip
    player: Ship
    dt: float
    spawned_projectiles: list


class SequenceNode(BehaviorNode):
    """Run children until one fails or all succeed."""

    def __init__(self, children: list[BehaviorNode]) -> None:
        """Store ordered child nodes."""

        self._children = children

    def tick(self, context: AIContext) -> BehaviorStatus:
        """Tick each child in order."""

        for child in self._children:
            status = child.tick(context)
            if status != BehaviorStatus.SUCCESS:
                return status
        return BehaviorStatus.SUCCESS


class SelectorNode(BehaviorNode):
    """Run children until one succeeds."""

    def __init__(self, children: list[BehaviorNode]) -> None:
        """Store ordered child nodes."""

        self._children = children

    def tick(self, context: AIContext) -> BehaviorStatus:
        """Tick each child until one does not fail."""

        for child in self._children:
            status = child.tick(context)
            if status != BehaviorStatus.FAILURE:
                return status
        return BehaviorStatus.FAILURE


class ConditionNode(BehaviorNode):
    """Leaf node wrapping a boolean predicate."""

    def __init__(self, predicate: Callable[[AIContext], bool]) -> None:
        """Store predicate."""

        self._predicate = predicate

    def tick(self, context: AIContext) -> BehaviorStatus:
        """Return SUCCESS when the predicate is true."""

        return (
            BehaviorStatus.SUCCESS
            if self._predicate(context)
            else BehaviorStatus.FAILURE
        )


class ActionNode(BehaviorNode):
    """Leaf node wrapping an action callback."""

    def __init__(self, action: Callable[[AIContext], BehaviorStatus]) -> None:
        """Store action callback."""

        self._action = action

    def tick(self, context: AIContext) -> BehaviorStatus:
        """Execute the action callback."""

        return self._action(context)


def seek(
    position: pygame.Vector2,
    target: pygame.Vector2,
    velocity: pygame.Vector2,
    max_speed: float,
) -> pygame.Vector2:
    """Return steering force toward a target."""

    desired = target - position
    if desired.length_squared() == 0.0:
        return pygame.Vector2()
    desired = desired.normalize() * max_speed
    return desired - velocity


def flee(
    position: pygame.Vector2,
    threat: pygame.Vector2,
    velocity: pygame.Vector2,
    max_speed: float,
) -> pygame.Vector2:
    """Return steering force away from a threat."""

    desired = position - threat
    if desired.length_squared() == 0.0:
        return pygame.Vector2()
    desired = desired.normalize() * max_speed
    return desired - velocity


def arrive(
    position: pygame.Vector2,
    target: pygame.Vector2,
    velocity: pygame.Vector2,
    max_speed: float,
    slowing_radius: float = 180.0,
) -> pygame.Vector2:
    """Return steering force that slows near a target."""

    desired = target - position
    distance = desired.length()
    if distance == 0.0:
        return -velocity
    speed = max_speed * min(distance / slowing_radius, 1.0)
    desired = desired.normalize() * speed
    return desired - velocity


def build_ancient_behavior_tree() -> BehaviorNode:
    """Create the default behavior tree for an Ancient patrol."""

    return SelectorNode(
        [
            SequenceNode(
                [
                    ConditionNode(_is_low_health),
                    ActionNode(_flee_from_player),
                ]
            ),
            SequenceNode(
                [
                    ConditionNode(_can_detect_player),
                    ActionNode(_attack_player),
                ]
            ),
            ActionNode(_patrol),
        ]
    )


def _is_low_health(context: AIContext) -> bool:
    health = context.enemy.health or 0.0
    return health / context.enemy.max_health <= constants.ANCIENT_FLEE_HEALTH_RATIO


def _can_detect_player(context: AIContext) -> bool:
    return (
        context.enemy.position.distance_squared_to(context.player.position)
        <= constants.ANCIENT_DETECTION_RADIUS ** 2
    )


def _flee_from_player(context: AIContext) -> BehaviorStatus:
    steering = flee(
        context.enemy.position,
        context.player.position,
        context.enemy.velocity,
        context.enemy.max_speed,
    )
    context.enemy.apply_force(steering, context.dt, context.enemy.max_speed)
    return BehaviorStatus.RUNNING


def _attack_player(context: AIContext) -> BehaviorStatus:
    steering = seek(
        context.enemy.position,
        context.player.position,
        context.enemy.velocity,
        context.enemy.max_speed,
    )
    context.enemy.apply_force(steering, context.dt, context.enemy.max_speed)
    if context.enemy.position.distance_to(context.player.position) < 520.0:
        projectile = context.enemy.fire_at(context.player.position)
        if projectile is not None:
            context.spawned_projectiles.append(projectile)
    return BehaviorStatus.RUNNING


def _patrol(context: AIContext) -> BehaviorStatus:
    target = context.enemy.next_patrol_point()
    steering = arrive(
        context.enemy.position,
        target,
        context.enemy.velocity,
        context.enemy.max_speed * 0.75,
    )
    context.enemy.apply_force(steering, context.dt, context.enemy.max_speed)
    return BehaviorStatus.RUNNING
