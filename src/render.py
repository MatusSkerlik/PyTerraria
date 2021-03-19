import random
from pathlib import Path
from typing import Tuple, Union, Dict

import pygame
from pygame import Surface, Color, SRCALPHA, BLEND_RGBA_MIN

from src.actor import ActorState
from src.asyncio import run_coroutine
from src.map import GridListener, GridType, Tile
from src.rect import Rect
from src.scene import SceneListener
from src.settings import ApplicationSettings
from src.tables import Actors, Tiles, Items, Backgrounds
from src.vector import Vector

# tile states with corresponding areas

_tile_state_areas = {

    0: [(18, 0, 16, 16), (36, 0, 16, 16), (54, 0, 16, 16)],  # top
    1: [(18, 36, 16, 16), (36, 36, 16, 16), (54, 36, 16, 16)],  # bottom
    2: [(0, 0, 16, 16), (0, 18, 16, 16), (0, 36, 16, 16)],  # left
    3: [(72, 0, 16, 16), (72, 18, 16, 16), (72, 36, 16, 16)],  # right
    4: [(18, 18, 16, 16), (36, 18, 16, 16), (54, 18, 16, 16)],  # center
    5: [(0, 54, 16, 16), (36, 54, 16, 16), (72, 54, 16, 16)],  # top left
    6: [(18, 54, 16, 16), (54, 54, 16, 16), (90, 54, 16, 16)],  # top right
    7: [(0, 72, 16, 16), (36, 72, 16, 16), (72, 72, 16, 16)],  # bottom left
    8: [(18, 72, 16, 16), (54, 72, 16, 16), (90, 72, 16, 16)],  # bottom right
    9: [(108, 0, 16, 16), (126, 0, 16, 16), (144, 0, 16, 16)],  # top isolated
    10: [(108, 54, 16, 16), (126, 54, 16, 16), (144, 54, 16, 16)],  # bottom isolated
    11: [(162, 0, 16, 16), (162, 18, 16, 16), (162, 36, 16, 16)],  # left isolated
    12: [(216, 0, 16, 16), (216, 18, 16, 16), (216, 36, 16, 16)],  # right isolated
    13: [(162, 54, 16, 16), (180, 54, 16, 16), (198, 54, 16, 16)],  # isolated
    14: [(90, 0, 16, 16), (90, 18, 16, 16), (90, 36, 16, 16)],  # tunnel vertical
    15: [(108, 72, 16, 16), (126, 72, 16, 16), (144, 72, 16, 16)],  # tunnel horizontal

    16: [(0, 90, 16, 16), (0, 126, 16, 16), (0, 162, 16, 16)],  # diffuse center top left
    17: [(18, 90, 16, 16), (18, 126, 16, 16), (18, 162, 16, 16)],  # diffuse center top right
    18: [(0, 108, 16, 16), (0, 144, 16, 16), (0, 180, 16, 16)],  # diffuse center bottom left
    19: [(18, 108, 16, 16), (18, 144, 16, 16), (18, 180, 16, 16)],  # diffuse center bottom right

    20: [(36, 90, 16, 16), (36, 126, 16, 16), (36, 162, 16, 16)],  # diffuse top top left
    21: [(54, 90, 16, 16), (54, 126, 16, 16), (54, 162, 16, 16)],  # diffuse top top right
    22: [(36, 108, 16, 16), (36, 144, 16, 16), (36, 180, 16, 16)],  # diffuse bottom bottom left
    23: [(54, 108, 16, 16), (54, 144, 16, 16), (54, 180, 16, 16)],  # diffuse bottom bottom right

    24: [(144, 108, 16, 16), (162, 108, 16, 16), (180, 108, 16, 16)],  # diffuse top
    25: [(144, 90, 16, 16), (162, 90, 16, 16), (180, 90, 16, 16)],  # diffuse bottom
    26: [(162, 126, 16, 16), (162, 144, 16, 16), (162, 162, 16, 16)],  # diffuse left
    27: [(144, 126, 16, 16), (144, 144, 16, 16), (144, 162, 16, 16)],  # diffuse right

    28: [(180, 126, 16, 16), (180, 144, 16, 16), (180, 162, 16, 16)],  # diffuse tunnel vertical
    29: [(144, 180, 16, 16), (162, 180, 16, 16), (180, 180, 16, 16)],  # diffuse tunnel horizontal

    30: [(198, 90, 16, 16), (198, 108, 16, 16), (198, 126, 16, 16)],  # diffuse isolated top
    31: [(198, 144, 16, 16), (198, 162, 16, 16), (198, 180, 16, 16)],  # diffuse isolated down
    32: [(216, 90, 16, 16), (216, 108, 16, 16), (216, 126, 16, 16)],  # diffuse isolated left
    33: [(216, 144, 16, 16), (216, 162, 16, 16), (216, 180, 16, 16)],  # diffuse isolated right

    34: [(108, 198, 16, 16), (126, 198, 16, 16), (144, 198, 16, 16)],  # diffuse isolated

    # f1 n1 s2 top, down, left, right

    35: [(234, 0, 16, 16), (252, 0, 16, 16), (270, 0, 16, 16)],  # none friendly same same
    36: [(234, 18, 16, 16), (252, 18, 16, 16), (270, 18, 16, 16)],  # friendly none same same
    37: [(234, 36, 16, 16), (252, 36, 16, 16), (270, 36, 16, 16)],  # same same none friendly
    38: [(234, 54, 16, 16), (252, 54, 16, 16), (270, 54, 16, 16)],  # same same friendly none

    # f1 n1 s2 left right (corner)
    39: [(72, 90, 16, 16), (72, 108, 16, 16), (72, 126, 16, 16)],  # same friendly none same
    40: [(90, 90, 16, 16), (90, 108, 16, 16), (90, 126, 16, 16)],  # same friendly same none
    41: [(72, 144, 16, 16), (72, 162, 16, 16), (72, 180, 16, 16)],  # friendly same none same
    42: [(90, 144, 16, 16), (90, 162, 16, 16), (72, 180, 16, 16)],  # friendly same same none

    # f1 n1 s2 top down (corner)
    43: [(0, 198, 16, 16), (18, 198, 16, 16), (36, 198, 16, 16)],  # none same friendly same
    44: [(0, 216, 16, 16), (18, 216, 16, 16), (36, 216, 16, 16)],  # same none friendly same
    45: [(54, 198, 16, 16), (72, 198, 16, 16), (90, 198, 16, 16)],  # none same same friendly
    46: [(54, 216, 16, 16), (72, 216, 16, 16), (90, 216, 16, 16)],  # same none same friendly

    # f1 n2 s1
    47: [(126, 90, 16, 16), (126, 108, 16, 16), (126, 126, 16, 16)],  # same friendly none none
    48: [(126, 144, 16, 16), (126, 162, 16, 16), (126, 180, 16, 16)],  # friendly same none none
    49: [(0, 252, 16, 16), (18, 252, 16, 16), (36, 252, 16, 16)],  # none none friendly same
    50: [(54, 252, 16, 16), (72, 252, 16, 16), (90, 252, 16, 16)],  # none none same friendly

    # f1 n3
    51: [(108, 90, 16, 16), (108, 108, 16, 16), (108, 126, 16, 16)],  # none friendly none none
    52: [(108, 144, 16, 16), (108, 162, 16, 16), (108, 180, 16, 16)],  # friendly none none none
    53: [(0, 234, 16, 16), (18, 234, 16, 16), (36, 234, 16, 16)],  # none none friendly none
    54: [(54, 234, 16, 16), (72, 234, 16, 16), (90, 234, 16, 16)],  # none none nne friendly

    # f2 n2
    55: [(108, 216, 16, 16), (108, 234, 16, 16), (108, 252, 16, 16)],  # friendly friendly none none
    56: [(162, 198, 16, 16), (180, 198, 16, 16), (198, 198, 16, 16)],  # none none friendly friendly

}

_background_tile_state_areas = {
    0: [(36, 36, 32, 32), (72, 36, 32, 32), (108, 36, 32, 32)],  # center
    1: [(324, 108, 32, 32), (360, 108, 32, 32), (396, 108, 32, 32)],  # full
    2: [(0, 0, 32, 32), (0, 36, 32, 32), (0, 72, 32, 32)],  # only left empty
    3: [(108, 0, 32, 32), (108, 36, 32, 32), (108, 72, 32, 32)],  # only right empty
    4: [(36, 0, 32, 32), (72, 0, 32, 32), (108, 0, 32, 32)],  # only top empty
    5: [(36, 72, 32, 32), (72, 72, 32, 32), (108, 72, 32, 32)],  # only bottom empty
}

_tree_state_areas = {

    0: [(44, 132, 20, 20), (44, 154, 20, 20), (44, 176, 20, 20)],  # tip left
    1: [(22, 132, 20, 20), (22, 154, 20, 20), (44, 176, 20, 20)],  # tip right
    2: [(66, 132, 20, 20), (66, 154, 20, 20), (66, 176, 20, 20)],  # tree start left
    3: [(0, 132, 20, 20), (0, 154, 20, 20), (0, 176, 20, 20)],  # tree start right
    4: [(0, 0, 20, 20), (0, 22, 20, 20), (0, 44, 20, 20)],  # main0
    5: [(22, 0, 20, 20), (22, 22, 20, 20), (22, 44, 20, 20),
        (22, 66, 20, 20), (22, 88, 20, 20), (22, 110, 20, 20)],  # main1
    6: [(88, 66, 20, 20), (88, 88, 20, 20), (88, 110, 20, 20)],  # leaf left
    7: [(66, 0, 20, 20), (66, 22, 20, 20), (66, 44, 20, 20)],  # leaf right
    8: [(110, 66, 20, 20), (110, 88, 20, 20), (110, 110, 20, 20)],  # leaf root
}

_torch_areas = {
    0: [(4, 0, 16, 20)],
    1: [(22, 0, 20, 20)],
    2: [(44, 0, 20, 20)]
}

_tree_top_areas = {0: [(0, 0, 80, 80), (82, 0, 80, 80), (164, 0, 80, 80)]}

_actor_areas = {
    0: [(0, 0, 40, 56)],  # idle
    1: [(0, 56, 40, 56), (0, 112, 40, 56), (0, 168, 40, 56), (0, 224, 40, 56)],  # interaction
    2: [(0, 280, 40, 56)],  # jumping
    3: [(0, 336, 40, 56), (0, 392, 40, 56), (0, 448, 40, 56), (0, 504, 40, 56), (0, 560, 40, 56),
        (0, 616, 40, 56), (0, 672, 40, 56), (0, 728, 40, 56), (0, 784, 40, 56), (0, 840, 40, 56), (0, 896, 40, 56),
        (0, 952, 40, 56), (0, 1008, 40, 56), (0, 1064, 40, 56)]  # walking
}

_tileset_table = {

    # id, #filename, #diffusion tile, sprite_type, #areas dict
    Tiles.NONE: ("Tiles_00", 0, 0, _tile_state_areas),  # NONE / light
    Tiles.DIRT: ("Tiles_0", 1, 0, _tile_state_areas),  # dirt
    Tiles.STONE: ("Tiles_1", 1, 0, _tile_state_areas),  # stone
    Tiles.LEAD: ("Tiles_6", 1, 0, _tile_state_areas),  # lead
    Tiles.COPPER: ("Tiles_7", 1, 0, _tile_state_areas),  # copper
    Tiles.GOLD: ("Tiles_8", 1, 0, _tile_state_areas),  # gold
    Tiles.SILVER: ("Tiles_9", 1, 0, _tile_state_areas),  # silver
    Tiles.ASH: ("Tiles_57", 2, 0, _tile_state_areas),  # ash
    Tiles.WHITE_TORCH: ("Tiles_4", 0, 2, _torch_areas),  # torch

    100: ("Tiles_5", 0, 1, _tree_state_areas),  # tree log
    105: ("Tree_Tops", 0, 5, _tree_top_areas),  # tree top

    200: ("Wall_2", 0, 2, _background_tile_state_areas)
}

_actorset_table = {
    # id, # filename, # areas dict
    Actors.PLAYER: ("Silver", _actor_areas)
}

_itemset_table = {
    Tiles.NONE: ("Item_0", [0, 0, 16, 16]),
    Tiles.DIRT: ("Item_2", [0, 0, 16, 16]),
    Tiles.STONE: ("Item_3", [0, 0, 16, 16]),
    Tiles.LEAD: ("Item_11", [0, 0, 16, 16]),
    Tiles.COPPER: ("Item_12", [0, 0, 16, 16]),
    Tiles.GOLD: ("Item_13", [0, 0, 16, 16]),
    Tiles.SILVER: ("Item_14", [0, 0, 16, 16]),
    Tiles.ASH: ("Item_172", [0, 0, 16, 16]),
    Items.IRON_PICKAXE: ("Item_1", [0, 0, 32, 32]),
    Items.IRON_AXE: ("Item_10", [0, 0, 32, 32]),
    Items.IRON_HAMMER: ("Item_7", [0, 0, 32, 32]),
    Tiles.B_OAK_LOG: ("Item_9", [0, 0, 22, 24]),
    Tiles.B_DIRT: ("Item_30", [0, 0, 16, 16]),
    Tiles.WHITE_TORCH: ("Item_8", [0, 0, 16, 16])
}

_background_table = {
    Backgrounds.DEFAULT: ("Forest_background_2", [0, 0, 1024, 838])
}

# blit surfaces for each tile state ( lazy )
_tile_sprites = {

}

# blit surfaces for each actor state ( lazy )
_actor_sprites = {

}

_item_sprites = {

}

_background_sprites = {

}


def get_tile_sprite(tile_type: int, state: int, index: int = -1):
    """ Get index or random sprite for tile with state """

    tile_state_dict = _tile_sprites.get(tile_type)
    if tile_state_dict is not None:
        state_choices = tile_state_dict.get(state)
        if state_choices is not None:
            if index > -1:
                return state_choices[index]
            else:
                length = len(state_choices)
                return state_choices[random.randint(0, length - 1)]
    return None


def get_actor_sprite(actor_type: int, type_state: int):
    actor_state_dict = _actor_sprites.get(actor_type)
    if actor_state_dict:
        return actor_state_dict.get(type_state)
    else:
        return None


def get_item_sprite(item_type: int):
    return _item_sprites[item_type]


def create_sprites_for_tile(camera, tile_type: int, scale: float = 1.0):
    """ Blit surfaces for tile types """
    filename, diffusion_type, sprite_type, ar = _tileset_table[tile_type]
    values = ar.values()

    _tile_sprites[tile_type] = {}

    for area_type_index, areas in zip(range(len(values)), values):
        sprites = [Sprite(camera, filename, (area,), 0) for area in areas]
        if scale != 1.0:
            for sprite in sprites:
                sprite.scale(scale)
        _tile_sprites[tile_type][area_type_index] = sprites


def create_sprites_for_actor(camera, actor_type: int):
    filename, ar = _actorset_table[actor_type]
    values = ar.values()

    _actor_sprites[actor_type] = {}

    for area_type_index, areas in zip(range(len(values)), values):
        _actor_sprites[actor_type][area_type_index] = Sprite(camera, filename, areas, 0.04)


def create_sprites_for_items(camera, item_type: int):
    filename, ar = _itemset_table[item_type]
    _item_sprites[item_type] = Sprite(camera, filename, (ar,), 0)


def chunk_key(chunk_col: int, chunk_row: int):
    """ :return: index for chunk col, row """
    return "col{}, row{}".format(chunk_col, chunk_row)


def horizontal_vertical(size, vertical_start, vertical_end, horizontal_start, horizontal_end, max_depth):
    surf_v = pygame.Surface((1, max_depth), pygame.SRCALPHA, 32)
    surf_h = pygame.Surface((max_depth, 1), pygame.SRCALPHA, 32)

    dd = 1.0 / max_depth
    vsr, vsg, vsb, vsa = vertical_start
    ver, veg, veb, vea = vertical_end
    vrm = (ver - vsr) * dd
    vgm = (veg - vsg) * dd
    vbm = (veb - vsb) * dd
    vam = (vea - vsa) * dd

    hsr, hsg, hsb, hsa = horizontal_start
    her, heg, heb, hea = horizontal_end
    hrm = (her - hsr) * dd
    hgm = (heg - hsg) * dd
    hbm = (heb - hsb) * dd
    ham = (hea - hsa) * dd

    for x in range(max_depth):
        surf_h.set_at((x, 0),
                      (
                          int(hsr + hrm * x),
                          int(hsg + hgm * x),
                          int(hsb + hbm * x),
                          int(hsa + ham * x)
                      ))
    surf_h = pygame.transform.scale(surf_h, size)

    for y in range(max_depth):
        surf_v.set_at((0, y),
                      (
                          int(vsr + vrm * y),
                          int(vsg + vgm * y),
                          int(vsb + vbm * y),
                          int(vsa + vam * y)
                      ))
    surf_v = pygame.transform.scale(surf_v, size)

    surf_h.blit(surf_v, (0, 0, size[0], size[1]))
    return surf_h


class TextureFactory:
    _loaded_textures = {}

    @classmethod
    def load(cls, name):
        """ Lazily load textures by name """

        if cls._loaded_textures.get(name) is None:
            for path in Path("./res/").rglob('{}.*'.format(name)):
                surface = pygame.image.load(path)
                cls._loaded_textures.setdefault(name, surface)
                return surface
        else:
            return cls._loaded_textures.get(name)


class Camera(Rect):
    """ Responsible to draw on application surface """
    followee: Union[None, Rect]

    def __init__(self, scene, width: int, height: int) -> None:
        super().__init__(0, 0, width, height)

        self.surface = pygame.display.get_surface()
        self.fonts = {}
        self.scene = scene

    def _blit(self, surface: Surface, dest: Vector, area: Union[None, Tuple[Vector, Vector]]):
        self.surface.blit(surface, dest, area)

    def draw_surface(self, surface: Surface, pos: Vector, area: Tuple[Vector, Vector], translate: bool = True):
        """ Saves draw information into queue for next render to draw """
        if translate:
            n_pos = pos - self.pos
        else:
            n_pos = pos
        self._blit(surface, (n_pos.x, n_pos.y), area)

    def draw_rect(self, rect: Tuple[Vector, Vector], color: Color, translate: bool = True):
        """ Saves draw information into queue for next render to draw """

        pos, size = rect
        surface = Surface((size.x, size.y), SRCALPHA, 32)
        surface.fill(color)

        if translate:
            n_pos = pos - self.pos
        else:
            n_pos = pos

        self._blit(surface, (n_pos.x, n_pos.y), None)

    def draw_line(self, start: Vector, end: Vector, width: int, color: Color, translate: bool = True):
        if translate:
            s_pos = start - self.pos
            e_pos = end - self.pos
        else:
            s_pos = start
            e_pos = end

        pygame.draw.line(self.surface, color, (s_pos.x, s_pos.y), (e_pos.x, e_pos.y), width)

    def draw_point(self, pos: Vector, radius: int, color: Color, translate: bool = True):
        if translate:
            n_pos = pos - self.pos
        else:
            n_pos = pos

        pygame.draw.circle(self.surface, color, (n_pos.x, n_pos.y), radius)

    def draw_text(self, text: str, size: int, pos: Vector, color: Color, translate: bool = True):
        sys_font = self.fonts.get(size)
        if not sys_font:
            self.fonts[size] = pygame.font.SysFont("Helvetica", size)
            sys_font = self.fonts[size]

        text_surface = sys_font.render(text, False, color)
        if translate:
            n_pos = pos - self.pos
        else:
            n_pos = pos

        self._blit(text_surface, (n_pos.x, n_pos.y), None)

    def update(self, delta_time: float):
        followee = self.scene.get_followee()

        if followee:
            pos = self.pos
            new_pos = followee.pos + (followee.size / 2) - (self.size / 2)
            self.pos += (new_pos - pos) * 4 * delta_time

        self.scene.pos = self.pos

    def render(self, delta_time: float):
        """ Draw each layer into system surface """
        pygame.display.flip()


class Sprite:

    def __init__(self, camera, file_name, rects: Tuple[Tuple[int, int, int, int]], rect_time: float):
        """
        :param camera viewport
        :param file_name of file
        :param rects ((x, y, w, h), ...)
        :param rect_time time for each rect to play in ms
        """
        self.camera = camera

        self.filename = file_name
        self.rect_time = rect_time
        self.static = rect_time == 0
        self.len = len(rects)
        self.time_elapsed = 0
        self.i = 0

        self.flipped_x = False
        self.flipped_y = False

        self.clip = None
        self.clips = []
        self.set_clips(rects)

    def get_width(self):
        """ :returns: width of underlying image """
        return self.clip.get_width()

    def get_height(self):
        """ :returns: height of underlying image """
        return self.clip.get_height()

    def flip(self, x_bool, y_bool):
        """ Flip sprite """
        if x_bool:
            self.flipped_x = not self.flipped_x
        if y_bool:
            self.flipped_y = not self.flipped_y

        for i in range(self.len):
            self.clips[i] = pygame.transform.flip(self.clips[i], x_bool, y_bool)
        self.clip = self.clips[self.i]

    def flip_right(self):
        if self.is_left():
            self.flip(True, False)

    def flip_left(self):
        if self.is_right():
            self.flip(True, False)

    def flip_up(self):
        if self.is_down():
            self.flip(False, True)

    def flip_down(self):
        if self.is_up():
            self.flip(False, True)

    def is_left(self):
        return self.flipped_x is False

    def is_right(self):
        return self.flipped_x is True

    def is_up(self):
        return self.flipped_y is False

    def is_down(self):
        return self.flipped_y is True

    def scale(self, factor: float):
        """ Scale sprite width and height by factor """

        for i in range(self.len):
            clip = self.clips[i]
            w = clip.get_width()
            h = clip.get_height()
            self.clips[i] = pygame.transform.smoothscale(clip, (int(w * factor), int(h * factor)))
        self.clip = self.clips[self.i]

    def resize(self, width: int, height: int):
        for i in range(self.len):
            clip = self.clips[i]
            self.clips[i] = pygame.transform.smoothscale(clip, (width, height))
        self.clip = self.clips[self.i]

    def transform(self, width: int, height: int):
        """ Change sprite width and height """

        for i in range(self.len):
            clip = self.clips[i]
            self.clips[i] = pygame.transform.scale(clip, (width, height))
        self.clip = self.clips[self.i]

    def get_surface(self):
        return self.clip

    def set_clips(self, clips):
        """ Update clipping """

        self.i = 0
        self.len = len(clips)
        self.clips = []
        self.clip = None

        if self.len > 0:
            texture = TextureFactory.load(self.filename)
            for i in range(self.len):
                x, y, w, h = clips[i]
                clip = Surface((w, h), SRCALPHA, 32)
                clip.fill(Color(0, 0, 0, 0))
                clip.blit(texture, (0, 0), pygame.Rect(x, y, w, h))
                self.clips.append(clip)
            self.clip = self.clips[0]

    def set_clip(self, index: int):
        """ Update clip by index """
        self.clip = self.clips[index]

    def set_time(self, rect_time: float):
        self.rect_time = rect_time
        if rect_time == 0:
            self.static = True
        else:
            self.static = False

    def render(self, pos: Vector, delta_time: float):
        if not self.static:
            self.time_elapsed += delta_time
            if self.time_elapsed >= self.rect_time:
                skip = int(self.time_elapsed / self.rect_time)
                self.time_elapsed -= skip * self.rect_time
                self.i += skip
                self.i %= self.len
                self.clip = self.clips[self.i]

        self.camera.draw_surface(self.clip, pos, None)


class ActorSpriteResolver:

    def __init__(self, actor) -> None:
        self.actor = actor

    def get_state(self):
        if self.actor.get_state() & ActorState.IDLE:
            return 0
        elif self.actor.get_state() & ActorState.INTERACTION:
            return 1
        elif self.actor.get_state() & ActorState.JUMPING:
            return 2
        elif self.actor.get_state() & ActorState.WALKING:
            return 3
        else:
            raise AttributeError

    def get_sprite(self):
        return get_actor_sprite(self.actor.type, self.get_state())


class TileSpriteResolver:

    def __init__(self, map_, tile: Tile) -> None:
        self.map = map_
        self.tile = tile

    def get_diffusion_type(self) -> int:
        filename, diffusion_type, sprite_type, areas = _tileset_table[self.tile.type]
        return diffusion_type

    def get_state(self):
        """ Returns state of tile sprite """

        def is_same(tile: Tile):
            return self.tile.type == tile.type

        def is_friendly(tile: Tile):
            return tile.type == self.get_diffusion_type()

        def is_none(tile: Tile):
            return tile.type == Tiles.NONE or (self.tile.type != tile.type and not is_reversed(tile))

        def is_reversed(tile: Tile):
            _, diff, __, ___ = _tileset_table[tile.type]
            return tile.type != Tiles.NONE and diff == self.tile.type

        def nbs_count(nbs):
            same_count, friendly_count, none, revers = 0, 0, 0, 0

            for n in nbs:
                if is_same(n):
                    same_count += 1
                elif is_friendly(n):
                    friendly_count += 1
                elif is_reversed(n):
                    revers += 1

                if is_none(n):
                    none += 1

            return same_count, friendly_count, none, revers

        col = self.tile.col
        row = self.tile.row
        top, down, left, right = self.map.get_nbs(col, row)

        if top and down and left and right:

            same, friendly, none, revers = nbs_count((top, down, left, right))

            if same == 4:
                return 4
            elif same == 3 and friendly == 1:
                if is_friendly(top):
                    return 24
                elif is_friendly(down):
                    return 25
                elif is_friendly(left):
                    return 26
                elif is_friendly(right):
                    return 27
            elif same == 2 and friendly == 2:
                if is_friendly(top) and is_friendly(down):
                    return 29
                elif is_friendly(left) and is_friendly(right):
                    return 28
                elif is_friendly(top):
                    if is_friendly(left):
                        return 20
                    elif is_friendly(right):
                        return 21
                elif is_friendly(down):
                    if is_friendly(left):
                        return 22
                    elif is_friendly(right):
                        return 23
            elif same == 1 and friendly == 3:
                if is_friendly(left) and is_friendly(right):
                    if is_friendly(top):
                        return 30
                    elif is_friendly(down):
                        return 31
                else:
                    if is_friendly(left):
                        return 32
                    elif is_friendly(right):
                        return 33
            elif same == 2 and friendly == 1:  # not same = 1
                if not is_same(top):
                    if is_friendly(down):
                        return 35
                    elif is_friendly(left):
                        return 43
                    elif is_friendly(right):
                        return 45
                elif not is_same(down):
                    if is_friendly(top):
                        return 36
                    elif is_friendly(left):
                        return 44
                    elif is_friendly(right):
                        return 46
                elif not is_same(left):
                    if is_friendly(left):
                        return 38
                    elif is_friendly(down):
                        return 39
                    elif is_friendly(top):
                        return 41
                elif not is_same(right):
                    if is_friendly(left):
                        return 37
                    elif is_friendly(down):
                        return 40
                    elif is_friendly(top):
                        return 42
            elif same == 1 and friendly == 1 and none == 2:  # not same = 2
                if is_friendly(down):
                    return 47
                elif is_friendly(top):
                    return 48
                if is_friendly(left):
                    return 49
                elif is_friendly(right):
                    return 50
            elif friendly == 2 and none == 2:
                if is_friendly(top) and is_friendly(down):
                    return 55
                elif is_friendly(left) and is_friendly(right):
                    return 56
            elif friendly == 1 and none == 3:  # not same = 3
                if is_friendly(down):
                    return 51
                elif is_friendly(top):
                    return 52
                elif is_friendly(left):
                    return 53
                elif is_friendly(right):
                    return 54
            elif friendly == 4:
                return 34
            elif same + revers == 3:
                if is_none(top):
                    return 0
                elif is_none(down):
                    return 1
                elif is_none(left):
                    return 2
                elif is_none(right):
                    return 3
            elif same + revers == 2:
                if is_none(top) and is_none(down):
                    return 15
                elif is_none(left) and is_none(right):
                    return 14
                elif is_none(top):
                    if is_none(left):
                        return 5
                    elif is_none(right):
                        return 6
                elif is_none(down):
                    if is_none(left):
                        return 7
                    elif is_none(right):
                        return 8
            elif same + revers == 1:
                if is_none(left) and is_none(right):
                    if is_none(top):
                        return 9
                    elif is_none(down):
                        return 10
                elif is_none(top) and is_none(down):
                    if is_none(left):
                        return 11
                    elif is_none(right):
                        return 12
            elif same == 0 and revers != 4:
                return 13

        return 4  # return center

    def get_surface(self):
        return get_tile_sprite(self.tile.type, self.get_state()).get_surface()


class TreeSpriteResolver:

    def __init__(self, map_, tile: Tile) -> None:
        self.map = map_
        self.tile = tile

    def get_state(self):

        def is_tree(tile: Tile):
            return tile and tile.type == 100

        def is_none(tile: Tile):
            return not tile or tile.type == Tiles.NONE

        col = self.tile.col
        row = self.tile.row

        top, down, left, right = self.map.get_nbs(col, row)

        if not is_tree(down) and not is_none(down):
            return random.randint(2, 3)
        elif is_tree(down) and (is_tree(left) or is_tree(right)):
            return 8
        elif not is_tree(down) and is_tree(right):
            return 7
        elif not is_tree(down) and is_tree(left):
            return 6
        else:
            return random.randint(4, 5)

    def get_surface(self):
        return get_tile_sprite(self.tile.type, self.get_state()).get_surface()


class TreeTopSpriteResolver:

    def __init__(self, map_, tile: Tile) -> None:
        self.map = map_
        self.tile = tile

    def get_surface(self):
        return get_tile_sprite(self.tile.type, 0).get_surface()


class BackgroundSpriteResolver:
    def __init__(self, map_, tile: Tile) -> None:
        self.map = map_
        self.tile = tile

    def get_state(self):
        return 0

    def get_surface(self):
        return get_tile_sprite(self.tile.type, self.get_state()).get_surface()


class LightMaskSpriteResolver:
    def __init__(self, map_, tile: Tile) -> None:
        self.map = map_
        self.tile = tile

    def get_surface(self):
        col = self.tile.col
        row = self.tile.row
        top, down, left, right = self.map.get_nbs(col, row)

        if self.tile.type != 0:
            t_v = abs(top.type) if top else 0
            d_v = abs(down.type) if down else 0
            l_v = abs(left.type) if left else 0
            r_v = abs(right.type) if right else 0
            return horizontal_vertical((16, 16),
                                       (0, 0, 0, t_v / 15 * 255),
                                       (0, 0, 0, d_v / 15 * 255),
                                       (0, 0, 0, l_v / 15 * 255),
                                       (0, 0, 0, r_v / 15 * 255),
                                       2)
        else:
            return get_tile_sprite(0, 0).get_surface()


class PygameRenderer:
    class ActorRenderer:

        def __init__(self, camera, actor) -> None:
            self.camera = camera
            self.actor = actor
            self.resolver = ActorSpriteResolver(actor)
            create_sprites_for_actor(camera, actor.type)

        def update(self, delta_time: float):
            sprite = self.resolver.get_sprite()

            if self.actor.get_state() & ActorState.RIGHT:
                sprite.flip_right()
            elif self.actor.get_state() & ActorState.LEFT:
                sprite.flip_left()

            vel = 1 / self.actor.vel
            sprite.set_time(abs(vel.x) * 7)

        def render(self, delta_time: float):
            sprite = self.resolver.get_sprite()
            sprite.render(self.actor.pos - Vector(10, 10), delta_time)

            pos = self.actor.pos
            size = self.actor.size
            vel = self.actor.vel
            start = pos + size / 2

            if vel.x != 0 or vel.y != 0:
                self.camera.draw_line(start, start + vel * delta_time, 2, Color(255, 0, 0))

            # draw position
            text_pos0 = pos - Vector(0, size.y + 32)
            text_pos1 = pos - Vector(0, size.y + 16)
            text_pos2 = pos - Vector(0, size.y)
            self.camera.draw_text("[x({}), y({})]".format(pos.x, pos.y), 16, text_pos0, Color(0, 0, 0))
            self.camera.draw_text("[c({}), r({})]".format(int(pos.x / 16), int(pos.y / 16)), 16, text_pos1,
                                  Color(0, 0, 0))
            self.camera.draw_text("[vx({}), vy({})]".format(vel.x, vel.y), 16, text_pos2, Color(0, 0, 0))

    class MapRenderer(GridListener):
        """ Renders map in self contained layering system -> background then foreground """

        # TODO render background and foreground on one surface

        class Chunk(Rect):

            def __init__(self, camera, map_, surface, col: int, row: int, tile_width: int, tile_height: int,
                         tiles_x: int,
                         tiles_y: int, lighting: bool) -> None:
                self.camera = camera
                self.map = map_
                self.surface = surface
                self.col = col
                self.row = row
                self.tile_width = tile_width
                self.tile_height = tile_height
                self.tiles_x = tiles_x
                self.tiles_y = tiles_y
                self.initialized = False
                self.initializing = False
                self.lighting = lighting

                width = tiles_x * tile_width
                height = tiles_y * tile_height
                x = col * width
                y = row * height
                super().__init__(x, y, width, height)

            async def init_surface(self):
                """ Initialize chunk surface """

                for col in range(self.tiles_x):
                    for row in range(self.tiles_y):
                        tile = self.get_tile(col, row, GridType.BACKGROUND0)
                        if tile and tile.type != Tiles.NONE:
                            self.blit_tile(tile, GridType.BACKGROUND0)
                        tile = self.get_tile(col, row, GridType.BACKGROUND1)
                        if tile and tile.type != Tiles.NONE:
                            self.blit_tile(tile, GridType.BACKGROUND1)
                        tile = self.get_tile(col, row, GridType.FOREGROUND)
                        if tile and tile.type != Tiles.NONE:
                            self.blit_tile(tile, GridType.FOREGROUND)
                        if self.lighting:
                            tile = self.get_tile(col, row, GridType.LIGHTING)
                            if tile and tile.type != Tiles.NONE:
                                self.blit_tile(tile, GridType.LIGHTING)

            def get_tile(self, col: int, row: int, grid_type: GridType):

                tile_col = col + self.col * self.tiles_x
                tile_row = row + self.row * self.tiles_y

                if grid_type == GridType.BACKGROUND0:
                    return self.map.background0.get_tile(tile_col, tile_row)
                elif grid_type == GridType.BACKGROUND1:
                    return self.map.background1.get_tile(tile_col, tile_row)
                elif grid_type == GridType.FOREGROUND:
                    return self.map.foreground.get_tile(tile_col, tile_row)
                elif grid_type == GridType.LIGHTING:
                    return self.map.lighting.get_tile(tile_col, tile_row)
                else:
                    raise AttributeError

            def blit_tile(self, tile: Tile, grid_type: GridType):
                """ Blit tile sprite into chunk surface """

                maps = {
                    GridType.BACKGROUND0: self.map.background0,
                    GridType.BACKGROUND1: self.map.background1,
                    GridType.FOREGROUND: self.map.foreground,
                    GridType.LIGHTING: self.map.lighting
                }

                if grid_type != GridType.LIGHTING:
                    filename, diffusion_type, sprite_type, areas = _tileset_table[tile.type]
                    if sprite_type == 0:
                        sprite = TileSpriteResolver(maps[grid_type], tile)
                    elif sprite_type == 1:
                        sprite = TreeSpriteResolver(maps[grid_type], tile)
                    elif sprite_type == 2:
                        sprite = BackgroundSpriteResolver(maps[grid_type], tile)
                    # elif sprite_type == 3:
                    #     sprite = LightMaskSpriteResolver(maps[grid_type], tile)
                    elif sprite_type == 5:
                        sprite = TreeTopSpriteResolver(maps[grid_type], tile)
                    else:
                        raise AttributeError
                else:
                    sprite = LightMaskSpriteResolver(maps[grid_type], tile)

                # translate map col - row to chunk col - row
                col = tile.col % self.tiles_x
                row = tile.row % self.tiles_y
                x = col * self.tile_width + (self.tile_width / 2 if grid_type != GridType.BACKGROUND0 else 0)
                y = row * self.tile_height + (self.tile_height / 2 if grid_type != GridType.BACKGROUND0 else 0)

                self.surface.blit(sprite.get_surface(), (x, y))

            def blit_empty(self, col, row):
                # translate map col - row to chunk col - row
                x = col * self.tile_width + 8
                y = row * self.tile_height + 8
                surface = Surface([self.tile_width, self.tile_height], SRCALPHA, 32)
                self.surface.blit(surface, (x, y), special_flags=BLEND_RGBA_MIN)

            def update_tile(self, col: int, row: int):
                col = col % self.tiles_x
                row = row % self.tiles_y

                self.blit_empty(col, row)
                tile = self.get_tile(col, row, GridType.BACKGROUND0)
                if tile and tile.type != Tiles.NONE:
                    self.blit_tile(tile, GridType.BACKGROUND0)
                tile = self.get_tile(col, row, GridType.BACKGROUND1)
                if tile and tile.type != Tiles.NONE:
                    self.blit_tile(tile, GridType.BACKGROUND1)
                tile = self.get_tile(col, row, GridType.FOREGROUND)
                if tile and tile.type != Tiles.NONE:
                    self.blit_tile(tile, GridType.FOREGROUND)
                if self.lighting:
                    tile = self.get_tile(col, row, GridType.LIGHTING)
                    if tile and tile.type != Tiles.NONE:
                        self.blit_tile(tile, GridType.LIGHTING)

            def update(self, delta_time: float):
                if not self.initialized and not self.initializing:
                    self.initializing = True

                    def on_success(result):
                        self.initialized = True
                        self.initializing = False

                    def on_error(error):
                        self.initialized = False
                        self.initializing = False

                    run_coroutine(
                        coroutine=self.init_surface(),
                        on_success=on_success,
                        on_error=on_error,
                        priority=20
                    )

            def render(self, delta_time: float):
                if self.initialized:
                    self.camera.draw_surface(self.surface, self.pos - 8, None)

        def __init__(self, camera, map_, tile_width: int, tile_height: int, chunk_width: int,
                     chunk_height: int, lighting_enabled: bool) -> None:
            self.camera = camera
            self.map = map_

            self.lighting_enabled = lighting_enabled
            self.tile_width = tile_width
            self.tile_height = tile_height
            self.chunk_width = chunk_width
            self.chunk_height = chunk_height
            self.chunks: Dict[str, PygameRenderer.MapRenderer.Chunk] = {}

            for col in range(int(self.map.width / chunk_width) + 1):
                for row in range(int(self.map.height / chunk_height) + 1):
                    surface = Surface(
                        (chunk_width * tile_width + tile_width, chunk_height * tile_height + tile_height),
                        SRCALPHA, 32)
                    self.chunks[chunk_key(col, row)] = PygameRenderer.MapRenderer.Chunk(
                        self.camera,
                        self.map,
                        surface,
                        col,
                        row,
                        self.tile_width,
                        self.tile_height,
                        self.chunk_width,
                        self.chunk_height,
                        lighting_enabled
                    )

            # prepare surfaces for tiles
            for tile in Tiles:
                create_sprites_for_tile(camera, tile, tile_width / 16)

            self.map.add_map_listener(self)

        def get_chunk(self, chunk_col: int, chunk_row: int) -> Chunk:
            """ :return chunk: """
            return self.chunks[chunk_key(chunk_col, chunk_row)]

        def get_tile_chunk(self, tile_col: int, tile_row: int) -> Chunk:
            """ :return: chunk for tile """

            chunk_col = int(tile_col / self.chunk_width)
            chunk_row = int(tile_row / self.chunk_height)

            return self.get_chunk(chunk_col, chunk_row)

        async def update_light(self, tile: Tile):

            destroyed = tile.type == Tiles.NONE
            redraw = set()

            if destroyed:  # tile removed ( light added )

                lc, lr = tile.col, tile.row
                min_d = {}
                for c in range(tile.col - 14, tile.col + 16):
                    for r in range(tile.row - 14, tile.row + 16):
                        dx = lc - c if lc > c else c - lc
                        dy = lr - r if lr > r else r - lr
                        d = dx + dy
                        min_d[(c, r)] = d

                for tc, tr in min_d.keys():
                    d = min_d.get((tc, tr))
                    t = self.map.lighting.get_tile(tc, tr)
                    if t and d <= abs(t.type):
                        self.map.lighting.set_tile(tc, tr, -d)
                        redraw.add((tc, tr))

            else:  # tile added ( light removed )

                lc, lr = tile.col, tile.row
                max_d = {}
                for c in range(tile.col - 14, tile.col + 16):
                    for r in range(tile.row - 14, tile.row + 16):
                        dx = lc - c if lc > c else c - lc
                        dy = lr - r if lr > r else r - lr
                        d = dx + dy

                        if d < 16:
                            max_d[(c, r)] = d

                lights = set()
                masks = set()
                for tc, tr in max_d.keys():
                    d = max_d.get((tc, tr))
                    t = self.map.lighting.get_tile(tc, tr)
                    if t:
                        if d > abs(t.type):
                            lights.add((tc, tr, abs(t.type)))
                        else:
                            self.map.lighting.set_tile(tc, tr, -14)
                            redraw.add((tc, tr))
                            masks.add((tc, tr))

                min_d = {}
                for lc, lr, dp in lights:
                    for c, r in masks:
                        dx = lc - c if lc > c else c - lc
                        dy = lr - r if lr > r else r - lr
                        d = dx + dy
                        if dp + d < 16:
                            m_d = min_d.get((c, r))
                            if m_d is None:
                                min_d[(c, r)] = dp + d
                            else:
                                min_d[(c, r)] = min(m_d, dp + d)

                for tc, tr in min_d.keys():
                    d = min_d[(tc, tr)]
                    t = self.map.lighting.get_tile(tc, tr)
                    if t and d <= abs(t.type):
                        self.map.lighting.set_tile(tc, tr, -d)
                        redraw.add((tc, tr))

            for c, r in redraw:
                chunk = self.get_tile_chunk(c, r)
                tile = self.map.lighting.get_tile(c, r)
                chunk.update_tile(tile.col, tile.row)

        def on_tile_change(self, tile: Tile, grid_id: GridType):

            c = tile.col
            r = tile.row
            cords = [(c, r)]
            if c > 0:
                cords.append((c - 1, r))
            if c < self.map.width:
                cords.append((c + 1, r))
            if r > 0:
                cords.append((c, r - 1))
            if r < self.map.height:
                cords.append((c, r + 1))

            for col, row in cords:
                chunk = self.get_tile_chunk(col, row)
                chunk.update_tile(col, row)

            b_tile = self.map.background0.get_tile(c, r)
            if self.lighting_enabled and (b_tile.type == Tiles.NONE or grid_id == GridType.BACKGROUND0):
                run_coroutine(
                    coroutine=self.update_light(tile),
                    on_success=None,
                    on_error=None,
                    priority=10
                )

        def update(self, delta_time):
            x = self.camera.pos.x
            y = self.camera.pos.y

            if x < 0:
                x = 0
            if y < 0:
                y = 0

            # create chunks if can be visible
            chunk_width = self.chunk_width * self.tile_width
            chunk_height = self.chunk_height * self.tile_height
            chunk_col = int(x / chunk_width)
            chunk_row = int(y / chunk_height)
            chunks_per_width = int(self.camera.size.x / chunk_width) + 2
            chunks_per_height = int(self.camera.size.y / chunk_height) + 2

            s_col = chunk_col - 2
            s_row = chunk_row - 2
            e_col = chunk_col + chunks_per_width + 2
            e_row = chunk_row + chunks_per_height + 2

            if s_col < 0:
                s_col = 0
            if s_row < 0:
                s_row = 0
            m_col = int(self.map.width / self.chunk_width) + 1
            m_row = int(self.map.height / self.chunk_height) + 1
            if e_col > m_col:
                e_col = m_col
            if e_row > m_row:
                e_row = m_row

            for col in range(s_col, e_col):
                for row in range(s_row, e_row):
                    chunk = self.get_chunk(col, row)
                    chunk.update(delta_time)

        def render(self, delta_time: float):
            x = self.camera.pos.x
            y = self.camera.pos.y

            if x < 0:
                x = 0
            if y < 0:
                y = 0

            tile_width = self.tile_width
            tile_height = self.tile_height
            chunk_width = self.chunk_width * tile_width
            chunk_height = self.chunk_height * tile_height
            chunk_col = int(x / chunk_width)
            chunk_row = int(y / chunk_height)
            chunks_per_width = int(self.camera.size.x / chunk_width) + 2
            chunks_per_height = int(self.camera.size.y / chunk_height) + 2

            s_col = chunk_col
            s_row = chunk_row
            e_col = chunk_col + chunks_per_width
            e_row = chunk_row + chunks_per_height

            m_col = int(self.map.width / self.chunk_width) + 1
            m_row = int(self.map.height / self.chunk_height) + 1
            if e_col > m_col:
                e_col = m_col
            if e_row > m_row:
                e_row = m_row

            for col in range(s_col, e_col):
                for row in range(s_row, e_row):
                    chunk = self.get_chunk(col, row)
                    chunk.render(delta_time)

    class WorldRenderer(SceneListener):

        class InventoryRenderer:

            def __init__(self, camera, inventory, item_width: int, item_height: int, item_spacing: int) -> None:
                self.camera = camera
                self.inventory = inventory
                self.item_width = item_width
                self.item_height = item_height
                self.item_spacing = item_spacing

                for item in Items:
                    create_sprites_for_items(camera, item)
                for item in Tiles:
                    if item.value >= 0:
                        create_sprites_for_items(camera, item)

            def update(self, delta_time: float):
                pass

            def render(self, delta_time: float):

                pos = Vector(self.item_spacing, self.item_spacing)
                size = Vector(self.item_width, self.item_height)

                # draw inventory
                for i, slot in self.inventory:

                    if i % 10 == 0 and i != 0:
                        pos.x -= 10 * (self.item_width + self.item_spacing)
                        pos.y += self.item_width + self.item_spacing

                    if self.inventory.index == i:  # activated must be brighter
                        self.camera.draw_rect((pos, size), Color(0, 0, 255, 160), translate=False)
                    else:
                        self.camera.draw_rect((pos, size), Color(0, 0, 255, 64), translate=False)

                    if slot.type:
                        sprite = get_item_sprite(slot.type)
                        item_pos = pos + 0.5 * size - 0.5 * Vector(sprite.get_width(), sprite.get_height())
                        text_pos = pos + 0.5 * size + Vector(0, -2)
                        self.camera.draw_surface(sprite.get_surface(), item_pos, None, translate=False)
                        self.camera.draw_text(str(slot.amount), 16, text_pos, Color(0, 0, 0), translate=False)

                    pos.x += self.item_width + self.item_spacing

                # draw crafting station
                if self.inventory.crafting:
                    pos = Vector(
                        self.item_spacing,
                        int(self.inventory.capacity / 10) * (self.item_height + self.item_spacing) + self.item_spacing
                    )
                    size = Vector(self.item_width, self.item_height)
                    for recipe in self.inventory.get_recipes():
                        self.camera.draw_rect((pos, size), Color(0, 0, 255, 160), translate=False)
                        sprite = get_item_sprite(recipe.get_type())
                        item_pos = pos + 0.5 * size - 0.5 * Vector(sprite.get_width(), sprite.get_height())
                        self.camera.draw_surface(sprite.get_surface(), item_pos, None, translate=False)
                        pos.y += self.item_height + self.item_spacing

                # draw mouse slot
                if not self.inventory.temp.is_empty():
                    slot = self.inventory.temp
                    pos = Vector(*pygame.mouse.get_pos())
                    sprite = get_item_sprite(slot.type)
                    item_pos = pos + 0.5 * size - 0.5 * Vector(sprite.get_width(), sprite.get_height())
                    text_pos = pos + 0.5 * size + Vector(0, -2)
                    self.camera.draw_surface(sprite.get_surface(), item_pos, None, translate=False)
                    self.camera.draw_text(str(slot.amount), 16, text_pos, Color(0, 0, 0),
                                          translate=False)

        def __init__(self, scene, width: int, height: int) -> None:
            self.scene = scene
            self.actor_renderers = {}
            self.camera = Camera(scene, width, height)

            settings = scene.get_settings()
            tile_width = settings.get_tile_width()
            tile_height = settings.get_tile_height()
            chunk_width = settings.get_chunk_width()
            chunk_height = settings.get_chunk_width()

            inv_item_width = settings.get_inventory_item_width()
            inv_item_height = settings.get_inventory_item_height()
            inv_item_spacing = settings.get_inventory_spacing()

            lighting = settings.is_lighting_enabled()

            self.map_renderer = PygameRenderer.MapRenderer(self.camera, scene.get_map(), tile_width, tile_height,
                                                           chunk_width, chunk_height, lighting)
            self.inv_renderer = PygameRenderer.WorldRenderer.InventoryRenderer(
                self.camera, scene.inventory, inv_item_width, inv_item_height, inv_item_spacing)

            for actor in scene.get_actors():
                self.actor_renderers[str(actor)] = PygameRenderer.ActorRenderer(self.camera, actor)

        def on_actor_added(self, actor):
            self.actor_renderers[str(actor)] = PygameRenderer.ActorRenderer(self.camera, actor)

        def on_actor_removed(self, actor):
            self.actor_renderers.pop(actor)

        def on_scene_move(self, x, y):
            pass

        def update(self, delta_time: float):
            """ Update actors and map """
            self.map_renderer.update(delta_time)
            for actor_renderer in self.actor_renderers.values():
                actor_renderer.update(delta_time)
            self.inv_renderer.update(delta_time)
            self.camera.update(delta_time)

        def render(self, delta_time: float):
            """ Renders actors and map """
            self.camera.draw_rect((self.camera.pos, self.camera.size), Color(135, 206, 235))
            self.map_renderer.render(delta_time)
            for actor_renderer in self.actor_renderers.values():
                actor_renderer.render(delta_time)
            self.inv_renderer.render(delta_time)
            self.camera.render(delta_time)

    def __init__(self, settings: ApplicationSettings) -> None:
        self._screen_width = settings.get_width()
        self._screen_height = settings.get_height()
        self._scene_renderer = None

    def set_scene(self, scene):
        if self._scene_renderer:
            scene.remove_scene_listener(self._scene_renderer)
        self._scene_renderer = PygameRenderer.WorldRenderer(scene, self._screen_width, self._screen_height)
        scene.add_scene_listener(self._scene_renderer)

    def init(self):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("Merraria")
        flags = pygame.DOUBLEBUF
        pygame.display.set_mode([self._screen_width, self._screen_height], flags, 32)

    def update(self, delta_time: float):
        if self._scene_renderer:
            self._scene_renderer.update(delta_time)

    def render(self, delta_time: float):
        if self._scene_renderer:
            self._scene_renderer.render(delta_time)

    def exit(self):
        pygame.display.quit()
        pygame.font.quit()
        pygame.quit()
