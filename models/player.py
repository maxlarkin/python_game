"""Persistent player progress and roguelite resources."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import constants


@dataclass
class PlayerData:
    """Persistent player state shared between runs."""

    resources: int = 0
    artifacts: list[str] = field(default_factory=list)
    upgrades: dict[str, int] = field(
        default_factory=lambda: {
            "hull": 0,
            "shields": 0,
            "engine": 0,
            "reactor": 0,
        }
    )
    unlocked_systems: list[int] = field(default_factory=list)
    completed_quests: list[int] = field(default_factory=list)
    current_system_id: int = 0
    runs_completed: int = 0
    moral_choice: str | None = None

    def upgrade_cost(self, upgrade_key: str) -> int:
        """Return the current resource cost for an upgrade.

        Args:
            upgrade_key: Upgrade identifier.

        Returns:
            Resource cost scaled by the current upgrade level.

        Raises:
            KeyError: If the upgrade is unknown.
        """

        base_cost = constants.UPGRADE_COSTS[upgrade_key]
        level = self.upgrades.get(upgrade_key, 0)
        return base_cost + level * base_cost // 2

    def buy_upgrade(self, upgrade_key: str) -> bool:
        """Try to buy one permanent upgrade level.

        Args:
            upgrade_key: Upgrade identifier.

        Returns:
            True when resources were spent and the level increased.
        """

        if upgrade_key not in constants.UPGRADE_COSTS:
            return False
        cost = self.upgrade_cost(upgrade_key)
        if self.resources < cost:
            return False
        self.resources -= cost
        self.upgrades[upgrade_key] = self.upgrades.get(upgrade_key, 0) + 1
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize progress to plain JSON-compatible data.

        Returns:
            A dictionary containing player progress.
        """

        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerData:
        """Create progress data from a dictionary.

        Args:
            data: JSON-compatible data.

        Returns:
            A populated PlayerData instance.
        """

        player = cls()
        player.resources = int(data.get("resources", player.resources))
        player.artifacts = list(data.get("artifacts", player.artifacts))
        loaded_upgrades = dict(data.get("upgrades", player.upgrades))
        player.upgrades.update(
            {
                key: int(loaded_upgrades.get(key, value))
                for key, value in player.upgrades.items()
            }
        )
        player.unlocked_systems = list(
            data.get("unlocked_systems", player.unlocked_systems)
        )
        player.completed_quests = list(
            data.get("completed_quests", player.completed_quests)
        )
        player.current_system_id = int(
            data.get("current_system_id", player.current_system_id)
        )
        player.runs_completed = int(data.get("runs_completed", player.runs_completed))
        moral_choice = data.get("moral_choice")
        player.moral_choice = str(moral_choice) if moral_choice is not None else None
        return player
