import sys
import asyncio
import json

from pathlib import Path
from platform import window

# picked up by real test on low end device J1900+v8.
BUFFERSIZE = 2048

# original module
import pygame
import pygame.mixer
import pygame.mixer.music


# =======================================================================
# pygame.mixer.music
#
# replace sdl thread music playing by browser native player
#

tracks = {"current": 0}


def patch_pygame_mixer_music_stop_pause_unload():
    last = tracks["current"]
    if last:
        window.MM.stop(last)
        tracks["current"] = 0


pygame.mixer.music.unload = patch_pygame_mixer_music_stop_pause_unload


def patch_pygame_mixer_music_load(fileobj, namehint=""):
    global tracks

    # stop previously loaded track
    patch_pygame_mixer_music_stop_pause_unload()

    tid = tracks.get(fileobj, None)

    # track was never loaded before
    if tid is None:
        track = patch_pygame_mixer_sound(fileobj, auto=False)
        tid = track.trackid

    # set new current track
    tracks["current"] = tid


pygame.mixer.music.load = patch_pygame_mixer_music_load


# TODO various buffer input
# FIXME tracks hash key
def patch_pygame_mixer_sound(data, auto=False):
    global tracks
    if isinstance(data, (Path, str)):
        data = str(data)
        trackid = tracks.get(data, None)
        if trackid is not None:
            return tracks[trackid]
    else:
        pdb(__file__, "137 TODO buffer types !")

    if Path(data).is_file():
        transport = "fs"
    else:
        transport = "url"

    cfg = {"url": data, "type": "audio", "auto": auto, "io": transport}

    track = window.MM.prepare(data, json.dumps(cfg))

    if track.error:
        pdb("ERROR: on track", cfg)
        # TODO stub track
        return "stub track"

    tracks[data] = track.trackid
    tracks[track.trackid] = track
    window.MM.load(track.trackid)
    return track


def patch_pygame_mixer_music_set_volume(vol: float):
    if vol < 0:
        return
    if vol > 1:
        vol = 1.0
    trackid = window.MM.current_trackid or tracks["current"]
    if trackid:
        window.MM.set_volume(trackid, vol)
    else:
        pdb(__file__, "ERROR 175: no track is loaded")


pygame.mixer.music.set_volume = patch_pygame_mixer_music_set_volume


def patch_pygame_mixer_music_get_volume():
    trackid = window.MM.current_trackid or tracks["current"]
    if trackid:
        return float(window.MM.get_volume(trackid))
    else:
        pdb(__file__, "ERROR 108: no track is loaded")


pygame.mixer.music.get_volume = patch_pygame_mixer_music_get_volume


def patch_pygame_mixer_music_play(loops=0, start=0.0, fade_ms=0):
    trackid = tracks["current"]
    if trackid:
        window.MM.pause(trackid)
        window.MM.play(trackid, loops)
    else:
        pdb(__file__, "ERROR 119: no track is loaded")


pygame.mixer.music.play = patch_pygame_mixer_music_play


def patch_pygame_mixer_music_get_pos():
    trackid = window.MM.current_trackid or tracks["current"]
    if trackid:
        return int(1000 * float(window.MM.get_pos(trackid)))
    return -1


pygame.mixer.music.get_pos = patch_pygame_mixer_music_get_pos


def patch_pygame_mixer_music_get_busy():
    # TODO
    # return false when paused
    return patch_pygame_mixer_music_get_pos() > 0


pygame.mixer.music.get_busy = patch_pygame_mixer_music_get_busy


def patch_pygame_mixer_music_queue(fileobj, namehint="", loops=0) -> None:
    window.MM.next = str(fileobj)
    window.MM.next_hint = str(namehint)
    window.MM.next_loops = int(loops)

    tid = tracks.get(fileobj, None)

    # track was never loaded before
    if tid is None:
        track = patch_pygame_mixer_sound(fileobj, auto=False)
        tid = track.trackid

    window.MM.next_tid = tid


pygame.mixer.music.queue = patch_pygame_mixer_music_queue


def patch_pygame_mixer_music_pause():
    last = window.MM.current_trackid or tracks["current"]
    if last:
        window.MM.pause(last)


def patch_pygame_mixer_music_unpause():
    last = window.MM.current_trackid or tracks["current"]
    if last:
        window.MM.unpause(last)


def patch_pygame_mixer_music_stop():
    last = window.MM.current_trackid or tracks["current"]
    if last:
        window.MM.stop(last)


pygame.mixer.music.stop = patch_pygame_mixer_music_stop
pygame.mixer.music.pause = patch_pygame_mixer_music_pause
pygame.mixer.music.unpause = patch_pygame_mixer_music_unpause

# TODO:
# https://www.pygame.org/docs/ref/music.html#pygame.mixer.music.fadeout

# =======================================================================
# pygame.mixer.Sound


# 0.2.0+ use huge buffer size instead of patching whole module.
# pro: full code compatibility
# con: sound lag
pygame.mixer.pre_init(buffer=BUFFERSIZE)

if 0:
    # 0.1.6 used to force soundpatch
    def patch_pygame_mixer_SoundPatch():
        print("pygame mixer SFX patch is already active you can remove this call")

else:

    def patch_pygame_mixer_SoundPatch():
        pygame.mixer.Sound = patch_pygame_mixer_sound
        print("pygame mixer SFX patch is now active")

    __pygame_mixer_init = pygame.mixer.init

    def patch_pygame_mixer_init(frequency=44100, size=-16, channels=2, buffer=512, devicename=None, allowedchanges=0) -> None:
        global BUFFERSIZE
        buffer = BUFFERSIZE
        print(f"pygame mixer init {frequency=}, {size=}, {channels=}, {buffer=}")
        __pygame_mixer_init(frequency, size, channels, buffer)

    pygame.mixer.init = patch_pygame_mixer_init

pygame.mixer.SoundPatch = patch_pygame_mixer_SoundPatch
