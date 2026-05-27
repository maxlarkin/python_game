"""JSON save/load helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.player import PlayerData


def save_game(path: str | Path, universe_seed: int, player_data: PlayerData) -> None:
    """Persist game state to disk.

    Args:
        path: Save file path.
        universe_seed: Seed needed to reconstruct the universe.
        player_data: Persistent player progress.
    """

    payload = {
        "version": 1,
        "universe_seed": universe_seed,
        "player": player_data.to_dict(),
    }
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")


def load_game(path: str | Path) -> tuple[int, PlayerData] | None:
    """Load saved game state.

    Args:
        path: Save file path.

    Returns:
        Seed and player data, or None when no save exists or data is invalid.
    """

    save_path = Path(path)
    if not save_path.exists():
        return None
    try:
        payload: dict[str, Any] = json.loads(save_path.read_text("utf-8"))
        seed = int(payload["universe_seed"])
        player = PlayerData.from_dict(dict(payload["player"]))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return seed, player
