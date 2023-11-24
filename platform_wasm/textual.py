import sys
import os
import select
import termios
import tty

# preload
import pygments
import rich
import typing_extensions

import textual.events
import textual.driver
import textual.drivers.headless_driver
import textual._xterm_parser

__WASM__ = sys.platform in ("emscripten", "wasi")


class HeadlessDriver(textual.driver.Driver):
    def send_event(self, event: textual.events.Event) -> None:
        self._loop.create_task(self._app._post_message(event))

    def _get_terminal_size(self) -> tuple[int, int]:
        return tuple(map(int, __import__("os").get_terminal_size()))

    def write(self, data: str) -> None:
        sys.__stdout__.write(data)  # ctx()['io'] )

    def start_application_mode(self) -> None:
        import asyncio
        import sys
        import termios
        import tty
        import platform

        stdin = sys.stdin.fileno()
        self.stdin = stdin
        self.attrs_before = termios.tcgetattr(stdin)
        attrs_raw = termios.tcgetattr(stdin)
        attrs_raw[tty.LFLAG] &= ~(termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG)
        attrs_raw[tty.IFLAG] &= ~(termios.IXON | termios.IXOFF | termios.ICRNL | termios.INLCR | termios.IGNCR)
        attrs_raw[tty.CC][termios.VMIN] = 1

        termios.tcsetattr(stdin, termios.TCSANOW, attrs_raw)

        self._enable_mouse_support()

        try:
            platform.window.set_raw_mode(1)
        except:
            ...

        loop = asyncio.get_running_loop()
        loop.create_task(self.input_handler())

    if __WASM__ and not aio.cross.simulator:

        def flush(self):
            __import__("embed").flush()

    else:

        def flush(self):
            sys.__stdout__.flush()

    def _enable_mouse_support(self) -> None:
        if __WASM__:
            import platform

            platform.window.console.warn("""Enable reporting of mouse events.""")

        write = self.write
        write("\x1b[?1000h")  # SET_VT200_MOUSE
        write("\x1b[?1003h")  # SET_ANY_EVENT_MOUSE
        write("\x1b[?1015h")  # SET_VT200_HIGHLIGHT_MOUSE
        write("\x1b[?1006h")  # SET_SGR_EXT_MODE_MOUSE

        # write("\x1b[?1007h")
        self.flush()

    def _disable_mouse_support(self) -> None:
        if __WASM__:
            import platform

            platform.window.console.warn("""Disable reporting of mouse events.""")

        write = self.write
        write("\x1b[?1000l")  #
        write("\x1b[?1003l")  #
        write("\x1b[?1015l")
        write("\x1b[?1006l")
        self.flush()

    def disable_input(self) -> None:
        if __WASM__:
            import platform

            platform.window.console.warn("""Disabling input.""")

    def stop_application_mode(self) -> None:
        import termios

        termios.tcsetattr(self.stdin, termios.TCSANOW, self.attrs_before)
        self._disable_mouse_support()

    async def input_handler(self):
        import asyncio, sys, os, select

        import textual._xterm_parser

        STDIN = sys.stdin.fileno()

        def more_data() -> bool:
            return select.select([STDIN], [], [], 0)[0]

        parser = textual._xterm_parser.XTermParser(more_data, debug=self._debug)

        import platform

        platform.window.console.log(f"{parser=}")

        loop = asyncio.get_running_loop()

        while not loop.is_closed():
            await asyncio.sleep(0)
            if select.select([STDIN], [], [], 0)[0]:
                try:
                    payload = os.read(STDIN, 1024)
                    if payload:
                        for event in parser.feed(payload.decode("utf-8")):
                            platform.window.console.log(f"{event=}")
                            self.process_event(event)
                except OSError:
                    continue


textual.drivers.headless_driver.HeadlessDriver = HeadlessDriver
