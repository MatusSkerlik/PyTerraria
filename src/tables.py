from enum import IntEnum, Enum


class Tiles(IntEnum):
    MASK8 = -9
    MASK7 = -8
    MASK6 = -7
    MASK5 = -6
    MASK4 = -5
    MASK3 = -4
    MASK2 = -3
    MASK1 = -2
    MASK0 = -1

    NONE = 0
    DIRT = 1
    STONE = 2
    LEAD = 6
    COPPER = 7
    GOLD = 8
    SILVER = 9
    ASH = 57

    B_OAK_LOG = 100
    B_DIRT = 200

class Items(IntEnum):
    IRON_PICKAXE = 1001
    IRON_HAMMER = 1003
    IRON_AXE = 1002

def is_tile(item: int):
    try:
        _ = Tiles(item)
        return _
    except ValueError:
        return False

def is_item(item: int):
    try:
        _ = Items(item)
        return _
    except ValueError:
        return False


class Layers(IntEnum):
    FOREGROUND = 0
    BACKGROUND = 1


class _TileLayerMetaclass(type):
    def __getitem__(self, item):
        if isinstance(item, Tiles):
            if item.name.startswith("B_"):
                return Layers.BACKGROUND
            else:
                return Layers.FOREGROUND
        elif isinstance(item, int):
            if Tiles(item).name.startswith("B_"):
                return Layers.BACKGROUND
            else:
                return Layers.FOREGROUND
        else:
            raise AttributeError


class TileLayers(metaclass=_TileLayerMetaclass):
    """ Use as TileLayers[Tiles.SOME_TILE] to get Layer info """
    pass


class Actors(IntEnum):
    PLAYER = 0
