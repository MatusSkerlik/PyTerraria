from src.input import Input, KeyboardListener, Key
from src.inventory import Inventory
from src.maps.procedural import ProceduralMap
from src.scene import World
from src.settings import SceneSettings


class GeneratorScene(KeyboardListener, World):

    def __init__(self) -> None:
        super().__init__(0, 0, 0, 0)
        self.keys_down = {}
        self.settings = SceneSettings({
            "WORLD_WIDTH": 500,
            "WORLD_HEIGHT": 500,
            "TILE_WIDTH": 4,
            "TILE_HEIGHT": 4,
            "CHUNK_HEIGHT": 32,
            "CHUNK_WIDTH": 32,
            "LIGHTING": False
        })
        self.input = Input()

        world_width = self.settings.get_world_width()
        world_height = self.settings.get_world_height()
        self.map = ProceduralMap(world_width, world_height)
        self.inventory = Inventory(0, 0)

    def on_key_down(self, key) -> bool:
        self.keys_down[key] = True
        return False

    def on_key_up(self, key) -> bool:
        self.keys_down[key] = False
        return False

    def update(self, delta_time: float):

        if self.keys_down.get(Key.W):
            self.pos.y += -750 * delta_time

        if self.keys_down.get(Key.S):
            self.pos.y += 750 * delta_time

        if self.keys_down.get(Key.A):
            self.pos.x += -750 * delta_time

        if self.keys_down.get(Key.D):
            self.pos.x += 750 * delta_time

    def init(self, application):
        self.input.init(self)
        self.map.init(self)
        self.input.add_keyboard_listener(self)

        self.initialized = True

    def exit(self):
        pass
