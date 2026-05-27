"""Entry point for Exile of the Doomed."""

from __future__ import annotations

from controllers.game_loop import GameLoop


def main() -> None:
    """Create and run the game loop."""

    GameLoop().run()


if __name__ == "__main__":
    main()
