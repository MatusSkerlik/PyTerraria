import random

import noise
import numpy as np

from src.map import Map
from src.tables import Tiles

sky = [155, 209, 255]
caverns = [102, 51, 0]

grass = [28, 216, 94]
dirt = [151, 107, 75]
stone = [128, 128, 128]
copper = [150, 67, 22]
lead = [62, 82, 114]
silver = [185, 194, 195]
gold = [185, 164, 23]
ash = [60, 55, 60]
wood = [101, 97, 125]
gold_chest = [255, 102, 204]

cave_bg = [84, 57, 42]
caverns_bg = [72, 64, 57]


class ProceduralMap(Map):

    def init(self, scene):

        # ----------- BASICS ------------
        seed = 47
        width = scene.settings.get_world_width()
        height = scene.settings.get_world_height()
        shape = (height, width)

        sky_start = 0
        sky_end = int(height / 10)  # 1 / 10
        sky_height = sky_end - sky_start

        # ---------- MAP GENERATION ----------
        surface_start = sky_end
        surface_end = surface_start + int(2 * height / 10)  # 2 / 10
        surface_height = surface_end - surface_start

        cave_start = surface_end
        cave_end = cave_start + int(2 * height / 10)  # 2 / 10
        cave_height = cave_end - cave_start

        caverns_start = cave_end
        caverns_end = caverns_start + int(4 * height / 10)  # 4 / 10
        caverns_height = caverns_end - caverns_start

        hell_start = caverns_end  # 1 / 10
        hell_end = height
        hell_height = hell_end - hell_start

        random.seed(seed)

        def tree(col: int, row: int, tiles):
            tree_height = random.randint(10, 25)
            left_leaf = random.randint(5, tree_height - 4)
            right_leaf = random.randint(5, tree_height - 4)

            for _ in range(tree_height):
                tiles[col - _, row] = 100
                if _ == left_leaf:
                    tiles[col - _, row - 1] = 100
                if _ == right_leaf:
                    tiles[col - _, row + 1] = 100
            tiles[col - tree_height - 4, row - 2] = 105

        def lerp(v0, v1, t):
            return (1 - t) * v0 + t * v1

        def surface_noise(i, s):
            scale = height * 4
            octaves = 6
            persistence = 0.6
            lacunarity = 2.0

            return noise.pnoise1(i / scale,
                                 octaves=octaves,
                                 persistence=persistence,
                                 lacunarity=lacunarity,
                                 repeat=1024,
                                 base=s)

        def cave_noise(i, j, s):
            scale = 65
            octaves = 6
            persistence = 0.5
            lacunarity = 2.0

            return noise.pnoise2(i / scale,
                                 j / scale,
                                 octaves=octaves,
                                 persistence=persistence,
                                 lacunarity=lacunarity,
                                 repeatx=1024,
                                 repeaty=1024,
                                 base=s)

        def ore_noise(i, j, s):
            scale = 30
            octaves = 3
            persistence = 0.9
            lacunarity = 2.

            return noise.pnoise2(i / scale,
                                 j / scale,
                                 octaves=octaves,
                                 persistence=persistence,
                                 lacunarity=lacunarity,
                                 repeatx=1024,
                                 repeaty=1024,
                                 base=s)

        def filling_noise(i, j, s):
            scale = 40
            octaves = 4
            persistence = 0.4
            lacunarity = 4.

            return noise.pnoise2(i / scale,
                                 j / scale,
                                 octaves=octaves,
                                 persistence=persistence,
                                 lacunarity=lacunarity,
                                 repeatx=1024,
                                 repeaty=1024,
                                 base=s)

        def map_tiles(surface, caves, filling, cop, ld, sil, gd):

            tiles = np.zeros(shape)

            for i in range(shape[0]):
                for j in range(shape[1]):

                    if i < sky_end:  # sky

                        tiles[i][j] = Tiles.NONE  # sky

                    elif i < surface_end:

                        min_i = sky_end  # surface min value is 30% of dirt caves height (1.5 / 10)
                        max_i = surface_end - 1
                        p = (i - min_i) / (max_i - min_i)

                        if i - min_i > surface[j] * min_i:
                            if caves[i][j] < lerp(0.25, 0.2, p):
                                if cop[i][j] < -0.25:
                                    tiles[i][j] = Tiles.COPPER  # copper
                                elif ld[i][j] < -0.35:
                                    tiles[i][j] = Tiles.LEAD  # lead
                                else:
                                    if filling[i][j] < lerp(-0.5, -0.2, p):
                                        tiles[i][j] = Tiles.STONE  # stone
                                    else:
                                        tiles[i][j] = Tiles.DIRT  # dirt
                            elif caves[i][j] < 1.0:
                                tiles[i][j] = Tiles.NONE  # cave bg

                        else:
                            tiles[i][j] = Tiles.NONE

                    elif i < cave_end:  # caves (2 / 10)

                        min_i = surface_end
                        max_i = cave_end - 1
                        p = (i - min_i) / (max_i - min_i)

                        if caves[i][j] < lerp(0.2, 0.15, p):
                            if cop[i][j] < -0.35:
                                tiles[i][j] = Tiles.COPPER  # copper
                            elif ld[i][j] < -0.28:
                                tiles[i][j] = Tiles.LEAD  # lead
                            elif sil[i][j] < -0.35:
                                tiles[i][j] = Tiles.SILVER  # silver
                            elif gd[i][j] < -0.4:
                                tiles[i][j] = Tiles.GOLD  # gold
                            else:
                                if filling[i][j] < lerp(-0.2, 0.1, p):
                                    tiles[i][j] = Tiles.STONE  # stone
                                else:
                                    tiles[i][j] = Tiles.DIRT  # dirt
                        elif caves[i][j] < 0.45:
                            tiles[i][j] = Tiles.NONE  # cave bg
                        elif caves[i][j] < 1.0:
                            tiles[i][j] = Tiles.STONE  # stone

                    elif i < caverns_end:  # caverns (4 / 10)

                        min_i = cave_end
                        max_i = caverns_end - 1
                        p = (i - min_i) / (max_i - min_i)

                        if caves[i][j] < lerp(0.15, 0.05, p):
                            if cop[i][j] < -0.4:
                                tiles[i][j] = Tiles.COPPER  # copper
                            elif ld[i][j] < -0.3:
                                tiles[i][j] = Tiles.LEAD  # lead
                            elif sil[i][j] < -0.3:
                                tiles[i][j] = Tiles.SILVER  # silver
                            elif gd[i][j] < -0.32:
                                tiles[i][j] = Tiles.GOLD  # gold
                            else:
                                if filling[i][j] < lerp(0.1, 0.3, p):
                                    tiles[i][j] = Tiles.STONE  # stone
                                else:
                                    tiles[i][j] = Tiles.DIRT  # dirt

                        elif caves[i][j] < 0.35:  # size of caves
                            tiles[i][j] = Tiles.NONE  # caverns_bg
                        elif caves[i][j] < 1.0:
                            tiles[i][j] = Tiles.STONE  # stone

                    else:  # hell (1 / 10)
                        tiles[i][j] = Tiles.ASH  # ash

            # # treasure alg
            # for i in range(10):
            #     y = random.randint(int(4 * height / 10), int(height - 2 * height / 10))
            #     x = random.randint(0, width - 15)
            #     place_treasure_house(y, x, tiles)

            return tiles

        def lighting(background, foreground, depth):

            class Tile:
                def __init__(self, col: int, row: int, tile_type: int) -> None:
                    self.col = col
                    self.row = row
                    self.type = tile_type

                def __hash__(self):
                    return hash((self.col, self.row))

                def __eq__(self, other):
                    return self.col == other.col and self.row == other.row

            def nbs(tile, arr):
                nbs = []
                c = tile.col
                r = tile.row
                if c >= 0:
                    nbs.append(Tile(c - 1, r, arr[c - 1, r]))
                if c < shape[0] - 1:
                    nbs.append(Tile(c + 1, r, arr[c + 1, r]))
                if r >= 0:
                    nbs.append(Tile(c, r - 1, arr[c, r - 1]))
                if r < shape[1] - 1:
                    nbs.append(Tile(c, r + 1, arr[c, r + 1]))
                return nbs

            light = np.zeros(shape)
            for i in range(shape[0]):
                for j in range(shape[1]):
                    if foreground[j, i] == 0 and background[j, i] == 0:
                        light[i, j] = Tiles.NONE
                    else:
                        light[i, j] = Tiles.MASK8

            queue = set()
            for i in range(shape[0]):
                for j in range(shape[1]):
                    if light[i, j] == -depth - 1:
                        tile = Tile(i, j, 1)
                        n = nbs(tile, light)
                        light_count = 0
                        for _ in n:
                            if _.type == 0:
                                light_count += 1
                        if light_count > 0:
                            light[i, j] = 1
                            queue.add(tile)

            for d in range(1, depth + 1):
                next = set()
                for tile in queue:
                    col = tile.col
                    row = tile.row
                    light[col, row] = -d

                    try:
                        for nb in nbs(tile, light):
                            if nb.type < -d and nb not in queue:
                                next.add(nb)
                    except IndexError:
                        pass
                queue.clear()
                queue.update(next)

            return light.T

        surface = np.zeros(shape=width)
        caves = np.zeros(shape)
        filling = np.zeros(shape)

        # ore
        copper = np.zeros(shape)
        iron = np.zeros(shape)
        silver = np.zeros(shape)
        gold = np.zeros(shape)

        # mineral

        for j in range(shape[1]):
            for i in range(shape[0]):
                caves[i][j] = cave_noise(i, j, seed)
                filling[i][j] = filling_noise(i, j, seed + 10)
                copper[i][j] = ore_noise(i, j, seed + 1)
                iron[i][j] = ore_noise(i, j, seed + 2)
                silver[i][j] = ore_noise(i, j, seed + 3)
                gold[i][j] = ore_noise(i, j, seed + 4)
            surface[j] = abs(surface_noise(j, seed))

        surface *= 1 / np.max(surface)  # normalize

        background = np.zeros(shape)

        for j in range(shape[1]):
            for i in range(shape[0]):
                if i > surface_end:
                    background[i, j] = Tiles.B_DIRT  # dirt background

        # tree alg
        # for i in range(shape[0]):
        #     for j in range(shape[1]):
        #         min_i = height / 10
        #         if i - min_i == int(surface[j] * min_i) and j % random.randint(30, 50) == 0:
        #             tree(i, j, background)  # tree

        self.background.tiles = background.astype(np.uint8).T
        self.foreground.tiles = map_tiles(surface, caves, filling, copper, iron, silver, gold).astype(np.uint8).T
        self.lighting.tiles = lighting(self.background.tiles, self.foreground.tiles, 8)

    def exit(self) -> None:
        pass
