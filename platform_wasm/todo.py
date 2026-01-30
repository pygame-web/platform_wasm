import sys
import asyncio
import os
import select
import builtins


# ======================================================
def patch():
    global COLUMNS, LINES, CONSOLE

    import importlib

    importlib.invalidate_caches()

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
    import sys
    import asyncio
    import os
    import select
    import builtins

    # stdout flush is platform specific

    # stdin maybe not be a tty, select may not work on stdin

    if not aio.cross.simulator:
        import platform

        sys.stdout.flush = platform.flush

        def ESC(*argv):
            for arg in argv:
                sys.__stdout__.write(chr(0x1B))
                sys.__stdout__.write(arg)
            platform.flush()

        import select

        select.__select = select.select

        def patch_select(rlist, wlist, xlist, timeout=None, /):
            # stdin
            if not isinstance(rlist, set):
                if rlist[0] == 0:
                    return [platform.stdin_select()]

            return select.__select(rlist, wlist, xlist, timeout)

        select.select = patch_select

        def patch_os_read(fd, sz):
            return platform.os_read()

        os.read = patch_os_read

        COLUMNS = platform.window.get_terminal_cols()
        CONSOLE = platform.window.get_terminal_console()
        LINES = platform.window.get_terminal_lines() - CONSOLE

        def patch_os_get_terminal_size(fd=0):
            cols = os.environ.get("COLUMNS", 80)
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

        def ESC(*argv):
            for arg in argv:
                sys.__stdout__.write(chr(0x1B))
                sys.__stdout__.write(arg)
            sys.__stdout__.flush()

        COLUMNS, LINES = os.get_terminal_size()
        CONSOLE = 25

    def patch_get_console_size(fd=0):
        global CONSOLE
        CONSOLE = os.environ.get("CONSOLE", CONSOLE)
        try:
            return int(CONSOLE)
        except:
            CONSOLE = 5
        return int(CONSOLE)

    platform.get_console_size = patch_get_console_size

    # do not override platform
    try:
        CSI
    except:

        def CSI(*argv):
            for arg in argv:
                ESC(f"[{arg}")

        # these are for direct tty control
        builtins.ESC = ESC
        builtins.CSI = CSI

    os.environ["COLUMNS"] = str(COLUMNS)
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

        termios.tcgetattr = patch_termios_getattr
        termios.old_tcsetattr = None
        sys.modules["termios"] = termios
    else:
        import termios

        termios.old_tcsetattr = termios.tcsetattr

    termios.state = 0

    def patch_termios_setattr(*argv):
        def patch_termios_set_raw_mode(mode):
            # assume first set is raw mode
            try:
                from embed import warn
            except:
                warn = print
            cols = int(os.environ.get("COLUMNS", 80))
            lines = int(os.environ.get("LINES", 25))
            console = int(os.environ.get("CONSOLE", 5))

            warn(f"Term phy COLUMNS : {cols} LINES : {lines}  virt console : {console}")
            warn(f"Term logical : {os.get_terminal_size()}")

            # set console scrolling zone
            warn(f"Scroll zone start at {LINES=}")
            CSI(f"{lines+1};{lines+console}r", f"{lines+2};1H>T> ")

            import platform

            try:
                platform.window.set_raw_mode(1)
            except:
                pass

        if termios.old_tcsetattr:
            termios.old_tcsetattr(*argv)

        if not termios.state:
            patch_termios_set_raw_mode(1)
        else:
            if aio.cross.simulator:
                warn("216 : CALLED TWICE")
                return
            try:
                patch_termios_set_raw_mode(0)
                from embed import warn
            except:
                warn = print
            warn("222 : RESETTING TERMINAL")
        termios.state += 1

    if not aio.cross.simulator:
        termios.tcsetattr = patch_termios_setattr

    # // termios

    # FIXME: move evertyhing pyodide to its own file.

    # pyodide emulation
    # TODO: implement loadPackage()/pyimport()
    def runPython(code):
        from textwrap import dedent

        print("211: runPython N/I")

    platform.runPython = runPython

    # fake Decimal module for some wheel imports
    sys.modules["decimal"] = type(sys)("decimal")

    class Decimal:
        pass

    sys.modules["decimal"].Decimal = Decimal

    # patch builtins input()
    async def async_input(prompt=""):
        import platform

        platform.shell.is_interactive = False

        maybe = ""
        if prompt:
            print(prompt, end="")
        elif aio.async_input_filters:
            for aif in aio.async_input_filters:
                maybe = aif()
                if maybe:
                    break

        while not len(maybe):
            await asyncio.sleep(0)
            maybe = platform.readline()

        platform.shell.is_interactive = True
        return maybe.rstrip("\n")

    try:
        aio.async_input_filters
    except:
        aio.async_input_filters = []

    aio.async_input = async_input

    # TODO detect when await is missing or ctx not async
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
        import pygame.base
        from . import pygame
        from .pygame import vidcap

    def patch_textual():
        from . import textual

    platform.patches = {
        "matplotlib": patch_matplotlib_pyplot,
        "panda3d": patch_panda3d_showbase,
        "wcwidth": patch_cwcwidth,
        "pygame": patch_pygame,
        "pygame_ce": patch_pygame,
        "textual": patch_textual,
    }

    return platform.patches
