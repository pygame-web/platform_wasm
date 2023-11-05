import sys
import builtins
import asyncio

# ======================================================
def patch():
    global COLS, LINES, CONSOLE
    import platform

    import collections
    try:
        collections.Mapping
    except:
        import collections.abc
        collections.Mapping = collections.abc.Mapping
        collections.Iterable = collections.abc.Iterable


    if not __UPY__:
        # DeprecationWarning: Using or importing the ABCs from 'collections'
        # instead of from 'collections.abc' is deprecated since Python 3.3
        # and in 3.10 it will stop working
        import collections
        from collections.abc import MutableMapping

        collections.MutableMapping = MutableMapping

    # could use that ?
    # import _sqlite3
    # sys.modules['sqlite3'] = _sqlite3

    #
    import os

    if not aio.cross.simulator:

        COLS = platform.window.get_terminal_cols()
        CONSOLE = platform.window.get_terminal_console()
        LINES = platform.window.get_terminal_lines() - CONSOLE

        def patch_os_get_terminal_size(fd=0):
            cols = os.environ.get("COLS", 80)
            lines = os.environ.get("LINES", 25)
            try:
                res = (
                    int(cols),
                    int(lines),
                )
            except:
                res = (
                    80,
                    25,
                )
            return os.terminal_size(res)

        os.get_terminal_size = patch_os_get_terminal_size
    else:
        COLS, LINES = os.get_terminal_size()
        CONSOLE = 25

    os.environ["COLS"] = str(COLS)
    os.environ["LINES"] = str(LINES)
    os.environ["CONSOLE"] = str(CONSOLE)

    if not aio.cross.simulator:
        # fake termios module for some wheel imports
        termios = type(sys)("termios")
        termios.block2 = [
            b"\x03",
            b"\x1c",
            b"\x7f",
            b"\x15",
            b"\x04",
            b"\x00",
            b"\x01",
            b"\x00",
            b"\x11",
            b"\x13",
            b"\x1a",
            b"\x00",
            b"\x12",
            b"\x0f",
            b"\x17",
            b"\x16",
            b"\x00",
            b"\x00",
            b"\x00",
            b"\x00",
            b"\x00",
            b"\x00",
            b"\x00",
            b"\x00",
            b"\x00",
            b"\x00",
            b"\x00",
            b"\x00",
            b"\x00",
            b"\x00",
            b"\x00",
            b"\x00",
        ]

        def patch_termios_getattr(*argv):
            return [17664, 5, 191, 35387, 15, 15, termios.block2]

        def patch_termios_set_raw_mode():

            def ESC(*argv):
                for arg in argv:
                    sys.__stdout__.write(chr(0x1B))
                    sys.__stdout__.write(arg)
                try:
                    embed.flush()
                except:
                    sys.stdout.flush()
                    sys.stderr.flush()

            def CSI(*argv):
                for arg in argv:
                    ESC(f"[{arg}")

            # assume first set is raw mode
            try:
                from embed import warn
            except:
                warn = print
            cols = int( os.environ.get("COLS", 80) )
            lines = int( os.environ.get("LINES", 25) )

            warn(f"Term phy COLS : {cols}")
            warn(f"Term phy LINES : {lines}")
            warn(f"Term logical : {os.get_terminal_size()}")
            # set console scrolling zone
            warn(f"Scroll zone start at {LINES=}")
            CSI(f"{LINES+1};{LINES+CONSOLE}r", f"{LINES+2};1H>>> ")
            platform.window.set_raw_mode(1)

        def patch_termios_setattr(*argv):
            if not termios.state:
                patch_termios_set_raw_mode()
            else:
                print("RESETTING TERMINAL")

            termios.state += 1
            pass

        termios.set_raw_mode = patch_termios_set_raw_mode
        termios.tcgetattr = patch_termios_getattr
        termios.tcsetattr = patch_termios_setattr

        termios.state = 0
        termios.TCSANOW = 0x5402
        termios.TCSAFLUSH = 0x5410
        termios.ECHO = 8
        termios.ICANON = 2
        termios.IEXTEN = 32768
        termios.ISIG = 1
        termios.IXON = 1024
        termios.IXOFF = 4096
        termios.ICRNL = 256
        termios.INLCR = 64
        termios.IGNCR = 128
        termios.VMIN = 6

        sys.modules["termios"] = termios

    # // termios



    # pyodide emulation
    # TODO: implement loadPackage()/pyimport()
    def runPython(code):
        from textwrap import dedent

        print("1285: runPython N/I")

    platform.runPython = runPython

    # fake Decimal module for some wheel imports
    sys.modules["decimal"] = type(sys)("decimal")

    class Decimal:
        pass

    sys.modules["decimal"].Decimal = Decimal

    # patch builtins input()
    async def async_input(prompt=""):
        shell.is_interactive = False
        if prompt:
            print(prompt, end="")
        maybe = ""
        while not len(maybe):
            maybe = embed.readline()
            await asyncio.sleep(0)

        shell.is_interactive = True
        return maybe.rstrip("\n")

    import builtins

    builtins.input = async_input

    #
    def patch_matplotlib_pyplot():
        from .matplotlib import pyplot

    #
    def patch_panda3d_showbase():
        from . import panda3d

    def patch_cwcwidth():
        if not aio.cross.simulator:
            import cwcwidth
            sys.modules["wcwidth"] = cwcwidth

    def patch_pygame():
        from . import pygame
        from .pygame import vidcap



    platform.patches = {
        "matplotlib": patch_matplotlib_pyplot,
        "panda3d": patch_panda3d_showbase,
        "wcwidth": patch_cwcwidth,
        "pygame.base": patch_pygame,
    }

    return platform.patches

# ======================================================
# emulate pyodide display() cmd
# TODO: fixme target
async def display(obj, target=None, **kw):
    filename = aio.filelike.mktemp(".png")
    target = kw.pop("target", None)
    x = kw.pop("x", 0)
    y = kw.pop("y", 0)
    dpi = kw.setdefault("dpi", 72)
    if repr(type(obj)).find("matplotlib.figure.Figure") > 0:
        # print(f"matplotlib figure {platform.is_browser=}")
        if platform.is_browser:
            # Agg is not avail, save to svg only option.
            obj.canvas.draw()
            tmp = f"{filename}.svg"
            obj.savefig(tmp, format="svg", **kw)
            await platform.jsiter(platform.window.svg.render(tmp, filename))
        else:
            # desktop matplotlib can save to any format
            obj.canvas.draw()
            obj.savefig(filename, format="png", **kw)

    if target in [None, "pygame"]:
        import pygame

        screen = shell.pg_init()
        screen.fill((0, 0, 0))
        screen.blit(pygame.image.load(filename), (x, y))
        pygame.display.update()
















