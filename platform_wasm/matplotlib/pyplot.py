import matplotlib
import matplotlib.pyplot


def patch_matplotlib_pyplot_show(*args, **kwargs):
    import pygame
    import matplotlib.pyplot
    import matplotlib.backends.backend_agg

    figure = matplotlib.pyplot.gcf()
    canvas = matplotlib.backends.backend_agg.FigureCanvasAgg(figure)
    canvas.draw()
    renderer = canvas.get_renderer()
    raw_data = renderer.tostring_rgb()
    size = canvas.get_width_height()

    screen = shell.pg_init()
    surf = pygame.image.fromstring(raw_data, size, "RGB")
    screen.blit(surf, (0, 0))
    pygame.display.update()


matplotlib.pyplot.show = patch_matplotlib_pyplot_show

matplotlib.pyplot.__pause__ = matplotlib.pyplot.pause


def patch_matplotlib_pyplot_pause(interval):
    matplotlib.pyplot.__pause__(0.0001)
    patch_matplotlib_pyplot_show()
    return asyncio.sleep(interval)


matplotlib.pyplot.pause = patch_matplotlib_pyplot_pause
