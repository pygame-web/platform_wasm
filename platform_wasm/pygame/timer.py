import asyncio
from typing import Union
import uuid

# =================================================
# do no change import order for *thread*
# patching threading.Thread
import aio.gthread

# patched module
from threading import Thread

import pygame
import pygame.event
import pygame.time

# ====================================================================
# replace non working native function.

print(
    """\
https://github.com/pygame-web/pygbag/issues/16
    applying: use aio green thread for pygame.time.set_timer
"""
)

# build the event and send it directly in the queue
# caveats :
#   - could be possibly very late
#   - delay cannot be less than frametime at device refresh rate.

# Local testing wrap patch_set_timer in a function and
# only apply on emscripten platform, so running pygame vanilla doesn't break
#
# import platform
#
# def patch_timer():
#     THREADS = {}
#
#     def patch_set_timer(
#         event: Union[int, pygame.event.Event], millis: int, loops: int = 0):
#         ...

#         async def fire_event(thread_uuid):
#             ...
#
#     pygame.time.set_timer = patch_set_timer
#
# if platform.system().lower() == "emscripten":
#     patch_timer()


# Global var to keep track of timer threads
#   - key: event type
#   - value: thread uuid
THREADS = {}


def patch_set_timer(event: Union[int, pygame.event.Event], millis: int, loops: int = 0):
    """repeatedly create an event on the event queue

    Patches the pygame.time.set_timer function to use gthreads
    """
    dlay = float(millis) / 1000
    if isinstance(event, pygame.event.Event):
        event_type = event.type
        cevent = event
    else:
        event_type = int(event)
        cevent = pygame.event.Event(event)

    event_loop = asyncio.get_event_loop()

    async def fire_event(thread_uuid):
        """The thread's target function to handle the timer

        Early exit conditions:
          - event loop is closed
          - event type is no longer in THREADS dictionary
          - the thread's uuid is not the latest one
          - Max loop iterations if loops param is not zero
        """
        loop_counter = 0
        while True:
            await asyncio.sleep(dlay)
            if (
                event_loop.is_closed()
                or event_type not in THREADS
                or THREADS[event_type] != thread_uuid
                or (loops and loop_counter >= loops)
            ):
                break

            pygame.event.post(cevent)
            loop_counter += 1 if loops else 0

    if dlay > 0:
        # uuid is used to track the latest thread,
        # stale threads will be terminated
        thread_uuid = uuid.uuid4()
        Thread(target=fire_event, args=[thread_uuid]).start()
        THREADS[event_type] = thread_uuid

    else:
        # This cancels the timer for the event
        if event in THREADS:
            del THREADS[event_type]


pygame.time.set_timer = patch_set_timer
