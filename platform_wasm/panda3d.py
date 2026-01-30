import sys
import os
import asyncio

import panda3d
import panda3d.core
from direct.showbase.ShowBase import ShowBase

try:
    print(f"panda3d: apply model path {os.getcwd()} patch")
    panda3d.core.get_model_path().append_directory(os.getcwd())
    panda3d.core.load_prc_file_data("", "win-size 1024 600")
    panda3d.core.load_prc_file_data("", "support-threads #f")
    panda3d.core.load_prc_file_data("", "model-cache-dir")
    # panda3d.core.load_prc_file_data("", "textures-power-2 up")
    # panda3d.core.load_prc_file_data("", "textures-square up")
    # samples expect that
    panda3d.core.load_prc_file_data("", "default-model-extension .egg")

    def run(*argv, **env):
        print("ShowBase.run patched to launch asyncio.run(main())")
        import direct.task.TaskManagerGlobal
        import platform

        async def main():
            platform.window.window_resize()

            # normal loop
            while not asyncio.get_running_loop().is_closed():
                # go to host
                await asyncio.sleep(0)
                # render
                try:
                    direct.task.TaskManagerGlobal.taskMgr.step()
                except SystemExit:
                    print("87: Panda3D stopped", file=sys.stderr)
                    break

        asyncio.run(main())

    ShowBase.run = run
    print("Panda3D: applied ShowBase.run patch, default-model-extension is .egg")

except Exception as e:
    sys.print_exception(e)
