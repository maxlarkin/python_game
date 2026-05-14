"""Persistent player progress and roguelite resources."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PlayerData:
    """Persistent player state shared between runs."""

    resources: int = 0
    artifacts: list[str] = field(default_factory=list)
    upgrades: dict[str, int] = field(default_factory=lambda: {"hull": 0, "shields": 0})
    unlocked_systems: list[int] = field(default_factory=list)
    current_system_id: int = 0
    runs_completed: int = 0
    moral_choice: str | None = None

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
        player.upgrades = dict(data.get("upgrades", player.upgrades))
        player.unlocked_systems = list(
            data.get("unlocked_systems", player.unlocked_systems)
        )
        player.current_system_id = int(
            data.get("current_system_id", player.current_system_id)
        )
        player.runs_completed = int(data.get("runs_completed", player.runs_completed))
        moral_choice = data.get("moral_choice")
        player.moral_choice = str(moral_choice) if moral_choice is not None else None
        return player
