"""AI controller that ticks behavior trees for enemies."""

from __future__ import annotations

from models.ai import AIContext, BehaviorNode, build_ancient_behavior_tree
from models.entities import AncientShip, Projectile, Ship


class AIController:
    """Own behavior trees and update all enemy ships."""

    def __init__(self) -> None:
        """Initialize an empty behavior registry."""

        self._trees: dict[int, BehaviorNode] = {}

    def update(
        self, enemies: list[AncientShip], player: Ship, dt: float
    ) -> list[Projectile]:
        """Tick all enemy AI trees.

        Args:
            enemies: Ancient ships to update.
            player: Player ship.
            dt: Fixed simulation step.

        Returns:
            Projectiles spawned by enemies during this tick.
        """

        spawned: list[Projectile] = []
        alive_ids = {id(enemy) for enemy in enemies}
        for enemy in enemies:
            tree = self._trees.setdefault(id(enemy), build_ancient_behavior_tree())
            tree.tick(
                AIContext(
                    enemy=enemy, player=player, dt=dt, spawned_projectiles=spawned
                )
            )
        for enemy_id in list(self._trees):
            if enemy_id not in alive_ids:
                del self._trees[enemy_id]
        return spawned
