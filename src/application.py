import pygame
from typing import Union

from src.parellel import tick
from src.render import PygameRenderer
from src.scene import Scene
from src.settings import ApplicationSettings

FPS = 60

class LogicError(Exception):
    pass


class Application:
    """ Main game class, runs game loop """

    _settings: ApplicationSettings
    _renderer: PygameRenderer
    _current_scene: Union[Scene, None]

    def __init__(self):
        self._initialized = False
        self._running = False
        self._current_scene = None
        self._clock = None

    def init(self):
        if self._initialized:
            raise LogicError("Game already initialized")
        else:
            self._settings = ApplicationSettings({
                "WIDTH": 1080,
                "HEIGHT": 768
            })
            self._renderer = PygameRenderer(self._settings)
            self._renderer.init()
            self._initialized = True
            self._clock = pygame.time.Clock()

    def loop(self):
        if not self._initialized:
            raise LogicError("You must first initialize app")

        self._running = self._current_scene is not None

        self._clock.tick()
        while self._running:
            delta_time = self._clock.tick(FPS) / 1000
            tick(FPS)
            # print(self._clock.get_fps())
            self._current_scene.get_input().handle_events(pygame.event.get(pump=True))
            self._current_scene.update(delta_time)
            self._renderer.update(delta_time)
            self._renderer.render(delta_time)

    def quit(self):
        if self._initialized:
            if self._current_scene:
                self._current_scene.exit()

            self._renderer.exit()
            self._initialized = False
        else:
            raise LogicError("Game not initialized")

    def set_scene(self, scene: Scene):
        self._current_scene = scene
        if not self._current_scene.is_initialized():
            scene.init(self)
            self._renderer.set_scene(scene)

    def get_settings(self):
        return self._settings
