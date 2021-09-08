import numpy
from abc import abstractmethod, ABC
from enum import IntEnum
from typing import Union, List


class GridType(IntEnum):
    BACKGROUND = 0
    FURNITURE = 1
    FOREGROUND = 2
    LIGHTING = 3


class Tile:

    def __init__(self, col: int, row: int, t: int) -> None:
        self.col = col
        self.row = row
        self.type = t


class GridListener(ABC):

    @abstractmethod
    def on_tile_change(self, tile: Tile, grid_id: GridType):
        pass


class Grid:
    tiles: numpy.ndarray

    def __init__(self, grid_type: GridType, width: int, height: int) -> None:
        """
        :param grid_type
        :param width unit [tiles]
        :param height unit [tiles]
        """
        self.width = width
        self.height = height
        self.listeners = set()
        self.type = grid_type

    def add_listener(self, listener):
        self.listeners.add(listener)

    def remove_listener(self, listener):
        self.listeners.remove(listener)

    def get_width(self):
        """ :return width of map in tiles """
        return self.width

    def get_height(self):
        """ :return heigth of map in tiles """
        return self.height

    def get_nbs(self, col: int, row: int) -> List[Union[None, Tile]]:
        """ :return top, down, left, right neighbours in this order. """

        return [self.get_tile(col, row - 1),
                self.get_tile(col, row + 1),
                self.get_tile(col - 1, row),
                self.get_tile(col + 1, row)]

    def nbs_count(self, col: int, row: int, tile_type: int) -> int:
        """ :return count number of tiles around with same type """

        count = 0
        for nb in self.get_nbs(col, row):
            if nb == tile_type:
                count += 1
        return count

    def get_tile(self, col: int, row: int) -> Union[None, Tile]:
        if 0 <= col < self.width and 0 <= row < self.height:
            return Tile(col, row, int(self.tiles[col, row]))
        else:
            return None

    def set_tile(self, col: int, row: int, tile_type: int) -> None:
        if 0 <= col < self.width and 0 <= row < self.height:
            self.tiles[col, row] = tile_type
            tile = self.get_tile(col, row)
            for listener in self.listeners:
                listener.on_tile_change(tile, self.type)
        else:
            raise AttributeError


class Map(ABC):
    """ Implementation of map with layer switching, tiles are represented by int """

    foreground: Grid
    background: Grid
    furniture: Grid
    lighting: Grid

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.foreground = Grid(GridType.FOREGROUND, width, height)
        self.background = Grid(GridType.BACKGROUND, width, height)
        self.furniture = Grid(GridType.FURNITURE, width, height)
        self.lighting = Grid(GridType.LIGHTING, width, height)

    @abstractmethod
    def init(self, scene):
        pass

    @abstractmethod
    def exit(self):
        pass

    def add_map_listener(self, listener):
        self.foreground.add_listener(listener)
        self.background.add_listener(listener)
        self.furniture.add_listener(listener)

    def remove_map_listener(self, listener):
        self.foreground.remove_listener(listener)
        self.background.remove_listener(listener)
        self.furniture.remove_listener(listener)
