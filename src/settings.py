from collections import ChainMap


class SceneSettings:
    _default = {
        # map
        "TILE_WIDTH": 16,  # unit [px]
        "TILE_HEIGHT": 16,  # unit [px]
        "CHUNK_WIDTH": 16,  # unit [tiles]
        "CHUNK_HEIGHT": 16,  # unit [tiles]
        "WORLD_WIDTH": 800,  # unit [tiles]
        "WORLD_HEIGHT": 600,  # unit [tiles]

        # LIGHTING
        "LIGHTING": False,

        # INVENTORY
        "INVENTORY_ITEM_WIDTH": 32,
        "INVENTORY_ITEM_HEIGHT": 32,
        "INVENTORY_SPACING": 4,
    }

    def __init__(self, settings_: dict) -> None:
        self._settings = ChainMap(settings_, self._default)

    def get_tile_width(self):
        return self._settings["TILE_WIDTH"]

    def get_tile_height(self):
        return self._settings["TILE_HEIGHT"]

    def get_chunk_width(self):
        return self._settings["CHUNK_WIDTH"]

    def get_chunk_height(self):
        return self._settings["CHUNK_HEIGHT"]

    def get_world_width(self):
        return self._settings["WORLD_WIDTH"]

    def get_world_height(self):
        return self._settings["WORLD_HEIGHT"]

    def is_lighting_enabled(self):
        return self._settings["LIGHTING"]

    def get_inventory_item_width(self):
        return self._settings["INVENTORY_ITEM_WIDTH"]

    def get_inventory_item_height(self):
        return self._settings["INVENTORY_ITEM_HEIGHT"]

    def get_inventory_spacing(self):
        return self._settings["INVENTORY_SPACING"]


class ApplicationSettings:
    """ Main application settings """

    _default = {
        # BASIC
        "WIDTH": 1900,
        "HEIGHT": 800,
        "FPS": 60,
        "TEXTURE_PATH": "./res/",
        "MAP_PATH": "./save/default_map.raw",
    }

    def __init__(self, settings_: dict) -> None:
        self._settings = ChainMap(settings_, self._default)

    def get_width(self):
        return self._settings["WIDTH"]

    def get_height(self):
        return self._settings["HEIGHT"]

    def get_fps(self):
        return self._settings["FPS"]

    def get_texture_path(self):
        return self._settings["TEXTURE_PATH"]
