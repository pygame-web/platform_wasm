import asyncio

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


def patch_set_timer(cust_event_no, millis, loops=0):
    dlay = float(millis) / 1000
    cevent = pygame.event.Event(cust_event_no)
    loop = asyncio.get_event_loop()

    async def fire_event():
        while True:
            await asyncio.sleep(dlay)
            if loop.is_closed():
                break
            pygame.event.post(cevent)

    Thread(target=fire_event).start()


pygame.time.set_timer = patch_set_timer
