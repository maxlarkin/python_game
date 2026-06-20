# Исход Обречённых

Top-down roguelite space battle prototype on Pygame.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

On Python 3.14, `pip` may try to build `pygame` from source. Install the
distribution package `python3-pygame` or SDL development headers if no wheel is
available for your interpreter.

## Controls

- `WASD` or arrows: movement
- Mouse: aim
- Left mouse button: fire
- Mouse wheel: switch weapon slot
- `E`: contact a nearby story planet
- `G`: open ship upgrades
- `Esc`: pause
- `H`: open the hyperjump map after clearing a patrol
- Upgrade window: buy permanent hull, shield, engine, reactor, and weapon upgrades

Progress is saved to `save.dat`.
