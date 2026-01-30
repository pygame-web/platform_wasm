import sys
import asyncio
import json

import platform


# =================================================
# do no change import order for *thread*
# patching threading.Thread
import aio.gthread

# patched module
from threading import Thread

# =================================================
# original module

import pygame

from . import timer

# ====================================================================
# pygame.quit is too hard on gc, and re-importing pygame is problematic
# if interpreter is not fully renewed.
# so just clear screen cut music and hope for the best.


def patch_pygame_quit():
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()
    try:
        pygame.display.update()
    except:
        pass


pygame.quit = patch_pygame_quit


# ====================================================================
# async camera

import platform_wasm.pygame.vidcap


# ====================================================================
# mixer.music module emulation via html5 audio

if platform.is_browser:
    # use html5 for music
    from . import mixer_music

    # =====================================================================
    # we want fullscreen-platform.windowed template for games as a default
    # so call javascript to resize canvas viewport to fill the current
    # platform.window each time mode is changed, also remove the "scaled" option

    __pygame_display_set_mode__ = pygame.display.set_mode

    def patch_pygame_display_set_mode(size=(0, 0), flags=0, depth=0, display=0, vsync=0):
        if size != (0, 0):
            if (sys.platform == "emscripten") and platform.is_browser:
                try:
                    platform.window.window_resize()
                except:
                    print("ERROR: browser host does not provide platform.window_resize() function", file=sys.__stderr__)

        # apparently no need to remove scaled.
        if flags or vsync or depth:

            if flags & pygame.OPENGL:
                print(f"3D CONTEXT ! {size=}, {flags=}, {depth=}, {display=}, {vsync=}")
                flags = pygame.OPENGL
            else:
                print(f"{size=}, {flags=}, {depth=}, {display=}, {vsync=}")
                flags = 0
            depth = 0
            vsync = 0
        try:
            return __pygame_display_set_mode__(size, flags, depth, display, vsync)
        except:
            raise

    pygame.display.set_mode = patch_pygame_display_set_mode


if platform.is_browser:
    # ====================================================================
    print("\n\n")
    print(open("/data/data/org.python/assets/pygame.six").read())

    print(sys._emscripten_info)
else:
    print(
        """
Running in Pygbag simulator
_______________________________
"""
    )
