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
- `Esc`: pause
- `H`: hyperjump after clearing a patrol

Progress is saved to `save.dat`.
