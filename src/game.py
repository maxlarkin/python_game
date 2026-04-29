import os
import pygame as pg
from .import constants as c
from . import controller


ORIGINAL_CAPTION = c.ORIGINAL_CAPTION


os.environ['SDL_VIDEO_CENTERED'] = '1'
pg.init()
pg.display.set_caption(c.ORIGINAL_CAPTION)

SCREEN = pg.display.set_mode(c.SCREEN_SIZE)
SCREEN_RECT = SCREEN.get_rect()


# FONTS = tools.load_all_fonts(os.path.join("resources","fonts"))
# MUSIC = tools.load_all_music(os.path.join("resources","music"))
# GFX   = controller.load_all_gfx(os.path.join("resources","graphics"))
# SFX   = tools.load_all_sfx(os.path.join("resources","sound"))


def main():
    """Add states to control here."""
    run_it = controller.Controller(ORIGINAL_CAPTION)

    run_it.main()
