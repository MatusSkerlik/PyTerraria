import pygame
import random
import time
from enum import Enum
from pathlib import Path
from pygame import Surface, Color, SRCALPHA, BLEND_RGBA_MIN
from typing import Tuple, Union, Dict

from src.actor import ActorState
from src.map import GridListener, GridType, Tile
from src.parellel import run_in_thread
from src.rect import Rect
from src.scene import SceneListener
from src.settings import ApplicationSettings
from src.tables import Actors, Tiles, Items
from src.vector import Vector

# tile states with corresponding areas

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


def chunk_key(chunk_col: int, chunk_row: int):
    """ :return: index for chunk col, row """
    return "col{}, row{}".format(chunk_col, chunk_row)


def gradient(size: Tuple[int, int], v_s: Color, v_e: Color, h_s: Color, h_e: Color, depth: int):
    """
    :param size size of returned surface
    :param v_s starting vertical color
    :param v_e ending vertical color
    :param h_s starting horizontal color
    :param h_e ending horizontal color
    :param depth depth of scaling
    :return: Surface
    """
    vertical = pygame.Surface((1, depth), pygame.SRCALPHA, 32)
    horizontal = pygame.Surface((depth, 1), pygame.SRCALPHA, 32)

    dd = 1.0 / depth
    vsr, vsg, vsb, vsa = v_s
    ver, veg, veb, vea = v_e
    vrm = (ver - vsr) * dd
    vgm = (veg - vsg) * dd
    vbm = (veb - vsb) * dd
    vam = (vea - vsa) * dd

    hsr, hsg, hsb, hsa = h_s
    her, heg, heb, hea = h_e
    hrm = (her - hsr) * dd
    hgm = (heg - hsg) * dd
    hbm = (heb - hsb) * dd
    ham = (hea - hsa) * dd

    for x in range(depth):
        horizontal.set_at((x, 0),
                          (
                              int(hsr + hrm * x),
                              int(hsg + hgm * x),
                              int(hsb + hbm * x),
                              int(hsa + ham * x)
                          ))
    horizontal = pygame.transform.scale(horizontal, size)

    for y in range(depth):
        vertical.set_at((0, y),
                        (
                            int(vsr + vrm * y),
                            int(vsg + vgm * y),
                            int(vsb + vbm * y),
                            int(vsa + vam * y)
                        ))
    vertical = pygame.transform.scale(vertical, size)
    horizontal.blit(vertical, (0, 0, size[0], size[1]))

    return horizontal


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
        self.surface.blit(surface, (dest.x, dest.y), area)

    def draw_sprite(self, sprite, pos: Vector, delta_time: float, translate: bool = True):
        if translate:
            n_pos = pos - self.pos
        else:
            n_pos = pos

        sprite.render(self.surface, n_pos, delta_time)

    def draw_surface(self, surface: Surface, pos: Vector, area: Tuple[Vector, Vector], translate: bool = True):
        """ Saves draw information into queue for next render to draw """
        if translate:
            n_pos = pos - self.pos
        else:
            n_pos = pos
        self._blit(surface, n_pos, area)

    def draw_rect(self, rect: Tuple[Vector, Vector], color: Color, translate: bool = True):
        """ Saves draw information into queue for next render to draw """

        pos, size = rect
        surface = Surface((size.x, size.y), SRCALPHA, 32)
        surface.fill(color)

        if translate:
            n_pos = pos - self.pos
        else:
            n_pos = pos

        self._blit(surface, n_pos, None)

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

        self._blit(text_surface, n_pos, None)

    def update(self, delta_time: float):
        followee = self.scene.get_followee()

        if followee:
            pos = self.pos
            new_pos = followee.pos + (followee.size / 2) - (self.size / 2)
            self.pos += (new_pos - pos) * 4 * delta_time
        self.scene.pos = self.pos

    def render(self, delta_time: float):
        """ Draw each layer into system surface """
        #
        # def update_screen(lock, arg):
        #     lock.acquire()
        #     pygame.display.update(*arg)
        #     lock.release()
        #
        # w, h = self.size.x, self.size.y
        # wh, hh = w / 2, h / 2
        #
        # l0 = _thread.allocate_lock()
        # l1 = _thread.allocate_lock()
        # l2 = _thread.allocate_lock()
        # l3 = _thread.allocate_lock()
        #
        # _thread.start_new_thread(update_screen, (l0, (0, 0, wh - 1, hh - 1)))
        # _thread.start_new_thread(update_screen, (l1, (wh, 0, wh - 1, hh - 1)))
        # _thread.start_new_thread(update_screen, (l2, (0, hh, wh - 1, hh - 1)))
        # _thread.start_new_thread(update_screen, (l3, (wh, hh, wh - 1, hh - 1)))
        #
        # locked = True
        # while locked:
        #     locked = l0.locked() or l1.locked() or l2.locked() or l3.locked()
        # _thread.start_new_thread(pygame.display.flip, tuple())
        # run_in_thread(pygame.display.flip, tuple(), priority=0)
        pygame.display.flip()


class Sprite:

    def __init__(self, file_name, rects: Tuple[Tuple[int, int, int, int]], rect_time: float, alpha=True):
        """
        :param file_name of file
        :param rects ((x, y, w, h), ...)
        :param rect_time time for each rect to play in ms
        """
        self.alpha = alpha
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
            self.clips[i] = pygame.transform.scale(clip, (int(w * factor), int(h * factor)))

        self.clip = self.clips[self.i]

    def resize(self, width: int, height: int):
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
                if self.alpha:
                    clip = Surface((w, h), SRCALPHA, 32)
                else:
                    clip = Surface((w, h), 0, 8)
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

    def render(self, surface: Surface, pos: Vector, delta_time: float):
        if not self.static:
            self.time_elapsed += delta_time
            if self.time_elapsed >= self.rect_time:
                skip = int(self.time_elapsed / self.rect_time)
                self.time_elapsed -= skip * self.rect_time
                self.i += skip
                self.i %= self.len
                self.clip = self.clips[self.i]

        surface.blit(self.clip, [pos.x, pos.y, self.get_width(), self.get_height()], None)


class ActorSpriteResolver:
    textures = {
        Actors.PLAYER: "Silver"

    }

    class Areas(Enum):
        IDLE = [(0, 0, 40, 56)]
        INTERACTION = [(0, 56, 40, 56), (0, 112, 40, 56), (0, 168, 40, 56), (0, 224, 40, 56)]
        JUMPING = [(0, 280, 40, 56)]
        WALKING = [(0, 336, 40, 56), (0, 392, 40, 56), (0, 448, 40, 56), (0, 504, 40, 56), (0, 560, 40, 56),
                   (0, 616, 40, 56), (0, 672, 40, 56), (0, 728, 40, 56), (0, 784, 40, 56), (0, 840, 40, 56),
                   (0, 896, 40, 56),
                   (0, 952, 40, 56), (0, 1008, 40, 56), (0, 1064, 40, 56)]

    sprites = {}

    @classmethod
    def create_sprite(cls, actor, area_type: Areas):
        filename = cls.textures[actor.type]
        cls.sprites[area_type] = Sprite(filename, area_type.value, 0.05)

    @classmethod
    def resolve_actor_sprite_area_type(cls, actor):
        if actor.get_state() & ActorState.IDLE:
            return cls.Areas.IDLE
        elif actor.get_state() & ActorState.INTERACTION:
            return cls.Areas.INTERACTION
        elif actor.get_state() & ActorState.JUMPING:
            return cls.Areas.JUMPING
        elif actor.get_state() & ActorState.WALKING:
            return cls.Areas.WALKING
        else:
            raise AttributeError

    @classmethod
    def get_sprite(cls, actor):
        area_type = cls.resolve_actor_sprite_area_type(actor)
        if cls.sprites.get(area_type) is None:
            cls.create_sprite(actor, area_type)
        return cls.sprites.get(area_type)


class ForegroundSpriteResolver:
    textures = {
        Tiles.NONE: ["Tiles_00", Tiles.NONE],
        Tiles.DIRT: ["Tiles_0", Tiles.STONE],
        Tiles.STONE: ["Tiles_1", Tiles.DIRT],
        Tiles.LEAD: ["Tiles_6", Tiles.DIRT],
        Tiles.COPPER: ["Tiles_7", Tiles.DIRT],
        Tiles.GOLD: ["Tiles_8", Tiles.DIRT],
        Tiles.SILVER: ["Tiles_9", Tiles.DIRT],
        Tiles.ASH: ["Tiles_57", Tiles.STONE]
    }

    class Areas(Enum):
        SSSS = [(18, 18, 16, 16), (36, 18, 16, 16), (54, 18, 16, 16)]  # center
        NNNN = [(162, 54, 16, 16), (180, 54, 16, 16), (198, 54, 16, 16)]  # isolated

        FSFS = [(36, 90, 16, 16), (36, 126, 16, 16), (36, 162, 16, 16)]  # diffuse top top left
        FSSF = [(54, 90, 16, 16), (54, 126, 16, 16), (54, 162, 16, 16)]  # diffuse top top right
        SFFS = [(36, 108, 16, 16), (36, 144, 16, 16), (36, 180, 16, 16)]  # diffuse bottom bottom left
        SFSF = [(54, 108, 16, 16), (54, 144, 16, 16), (54, 180, 16, 16)]  # diffuse bottom bottom right

        FSSS = [(144, 108, 16, 16), (162, 108, 16, 16), (180, 108, 16, 16)]  # diffuse top
        SFSS = [(144, 90, 16, 16), (162, 90, 16, 16), (180, 90, 16, 16)]  # diffuse bottom
        SSFS = [(162, 126, 16, 16), (162, 144, 16, 16), (162, 162, 16, 16)]  # diffuse left
        SSSF = [(144, 126, 16, 16), (144, 144, 16, 16), (144, 162, 16, 16)]  # diffuse right

        SSFF = [(180, 126, 16, 16), (180, 144, 16, 16), (180, 162, 16, 16)]  # diffuse tunnel vertical
        FFSS = [(144, 180, 16, 16), (162, 180, 16, 16), (180, 180, 16, 16)]  # diffuse tunnel horizontal

        FSFF = [(198, 90, 16, 16), (198, 108, 16, 16), (198, 126, 16, 16)]  # diffuse isolated top
        SFFF = [(198, 144, 16, 16), (198, 162, 16, 16), (198, 180, 16, 16)]  # diffuse isolated down
        FFFS = [(216, 90, 16, 16), (216, 108, 16, 16), (216, 126, 16, 16)]  # diffuse isolated left
        FFSF = [(216, 144, 16, 16), (216, 162, 16, 16), (216, 180, 16, 16)]  # diffuse isolated right

        FFFF = [(108, 198, 16, 16), (126, 198, 16, 16), (144, 198, 16, 16)]  # diffuse isolated

        # f1 n1 s2 top, down, left, right
        NFSS = [(234, 0, 16, 16), (252, 0, 16, 16), (270, 0, 16, 16)]  # none friendly same same
        FNSS = [(234, 18, 16, 16), (252, 18, 16, 16), (270, 18, 16, 16)]  # friendly none same same
        SSNF = [(234, 36, 16, 16), (252, 36, 16, 16), (270, 36, 16, 16)]  # same same none friendly
        SSFN = [(234, 54, 16, 16), (252, 54, 16, 16), (270, 54, 16, 16)]  # same same friendly none

        # f1 n1 s2 left right (corner)
        SFNS = [(72, 90, 16, 16), (72, 108, 16, 16), (72, 126, 16, 16)]  # same friendly none same
        SFSN = [(90, 90, 16, 16), (90, 108, 16, 16), (90, 126, 16, 16)]  # same friendly same none
        FSNS = [(72, 144, 16, 16), (72, 162, 16, 16), (72, 180, 16, 16)]  # friendly same none same
        FSSN = [(90, 144, 16, 16), (90, 162, 16, 16), (72, 180, 16, 16)]  # friendly same same none

        # f1 n1 s2 top down (corner)
        NSFS = [(0, 198, 16, 16), (18, 198, 16, 16), (36, 198, 16, 16)]  # none same friendly same
        SNFS = [(0, 216, 16, 16), (18, 216, 16, 16), (36, 216, 16, 16)]  # same none friendly same
        NSSF = [(54, 198, 16, 16), (72, 198, 16, 16), (90, 198, 16, 16)]  # none same same friendly
        SNSF = [(54, 216, 16, 16), (72, 216, 16, 16), (90, 216, 16, 16)]  # same none same friendly

        # f1 n2 s1
        SFNN = [(126, 90, 16, 16), (126, 108, 16, 16), (126, 126, 16, 16)]  # same friendly none none
        FSNN = [(126, 144, 16, 16), (126, 162, 16, 16), (126, 180, 16, 16)]  # friendly same none none
        NNFS = [(0, 252, 16, 16), (18, 252, 16, 16), (36, 252, 16, 16)]  # none none friendly same
        NNSF = [(54, 252, 16, 16), (72, 252, 16, 16), (90, 252, 16, 16)]  # none none same friendly

        # f1 n3
        FNNN = [(108, 144, 16, 16), (108, 162, 16, 16), (108, 180, 16, 16)]  # friendly none none none
        NFNN = [(108, 90, 16, 16), (108, 108, 16, 16), (108, 126, 16, 16)]  # none friendly none none
        NNFN = [(0, 234, 16, 16), (18, 234, 16, 16), (36, 234, 16, 16)]  # none none friendly none
        NNNF = [(54, 234, 16, 16), (72, 234, 16, 16), (90, 234, 16, 16)]  # none none nne friendly

        # f2 n2
        FFNN = [(108, 216, 16, 16), (108, 234, 16, 16), (108, 252, 16, 16)]  # friendly friendly none none
        NNFF = [(162, 198, 16, 16), (180, 198, 16, 16), (198, 198, 16, 16)]  # none none friendly friendly

        NSNN = [(108, 0, 16, 16), (126, 0, 16, 16), (144, 0, 16, 16)]  # top isolated
        SNNN = [(108, 54, 16, 16), (126, 54, 16, 16), (144, 54, 16, 16)]  # bottom isolated
        NNNS = [(162, 0, 16, 16), (162, 18, 16, 16), (162, 36, 16, 16)]  # left isolated
        NNSN = [(216, 0, 16, 16), (216, 18, 16, 16), (216, 36, 16, 16)]  # right isolated

        NSNS = [(0, 54, 16, 16), (36, 54, 16, 16), (72, 54, 16, 16)]  # top left
        NSSN = [(18, 54, 16, 16), (54, 54, 16, 16), (90, 54, 16, 16)]  # top right
        SNNS = [(0, 72, 16, 16), (36, 72, 16, 16), (72, 72, 16, 16)]  # bottom left
        SNSN = [(18, 72, 16, 16), (54, 72, 16, 16), (90, 72, 16, 16)]  # bottom right

        NSSS = [(18, 0, 16, 16), (36, 0, 16, 16), (54, 0, 16, 16)]  # top
        SNSS = [(18, 36, 16, 16), (36, 36, 16, 16), (54, 36, 16, 16)]  # bottom
        SSNS = [(0, 0, 16, 16), (0, 18, 16, 16), (0, 36, 16, 16)]  # left
        SSSN = [(72, 0, 16, 16), (72, 18, 16, 16), (72, 36, 16, 16)]  # right

        SSNN = [(90, 0, 16, 16), (90, 18, 16, 16), (90, 36, 16, 16)]  # tunnel vertical
        NNSS = [(108, 72, 16, 16), (126, 72, 16, 16), (144, 72, 16, 16)]  # tunnel horizontal

    sprites = {}

    @classmethod
    def create_sprite(cls, tile, area_type: Areas):
        filename, diff = cls.textures[tile.type]
        cls.sprites[tile.type] = {}
        cls.sprites[tile.type][area_type] = Sprite(filename, area_type.value, 0)

    @classmethod
    def resolve_tile_sprite_area_type(cls, grid, tile):

        def is_friendly(t0, t1):
            _, diff_t0 = cls.textures[t0.type]
            _, diff_t1 = cls.textures[t1.type]
            return t1.type == diff_t0.value or t0.type == diff_t1.value

        def is_same(t0, t1):
            return t0.type == t1.type

        def is_none(t0, t1):
            return t1.type == Tiles.NONE or not is_same(t0, t1)

        def get_func(letter: str):
            if letter == "N":
                return is_none
            elif letter == "S":
                return is_same
            elif letter == "F":
                return is_friendly
            else:
                raise AttributeError

        top, bottom, left, right = grid.get_nbs(tile.col, tile.row)

        if top and bottom and left and right:
            for area_type in cls.Areas:
                area_name = area_type.name
                if get_func(area_name[0])(tile, top) and \
                        get_func(area_name[1])(tile, bottom) and \
                        get_func(area_name[2])(tile, left) and \
                        get_func(area_name[3])(tile, right):
                    return area_type
            raise AttributeError(
                Tiles(tile.type),
                Tiles(top.type),
                Tiles(bottom.type),
                Tiles(left.type),
                Tiles(right.type)
            )
        else:
            return cls.Areas.SSSS

    @classmethod
    def get_sprite(cls, grid, tile, size):
        area_type = cls.resolve_tile_sprite_area_type(grid, tile)
        try:
            _ = cls.sprites[tile.type][area_type]
        except KeyError:
            cls.create_sprite(tile, area_type)
        sprite = cls.sprites[tile.type][area_type]
        sprite.set_clip((tile.col + tile.row) % sprite.len)  # set clip from available

        if sprite.get_width() != size.x or sprite.get_height() != size.y:
            sprite.scale(size.x / 16)

        return sprite


class BackgroundSpriteResolver:
    textures = {
        Tiles.B_DIRT: "Wall_2"
    }

    class Areas(Enum):
        SSSS = [(36, 36, 32, 32), (72, 36, 32, 32), (108, 36, 32, 32)]  # center
        NNNN = [(324, 108, 32, 32), (360, 108, 32, 32), (396, 108, 32, 32)]  # full
        SSNS = [(0, 0, 32, 32), (0, 36, 32, 32), (0, 72, 32, 32)]  # only left empty
        SSSN = [(108, 0, 32, 32), (108, 36, 32, 32), (108, 72, 32, 32)]  # only right empty
        NSSS = [(36, 0, 32, 32), (72, 0, 32, 32), (108, 0, 32, 32)]  # only top empty
        SNSS = [(36, 72, 32, 32), (72, 72, 32, 32), (108, 72, 32, 32)]  # only bottom empty

    sprites = {}

    @classmethod
    def create_sprite(cls, tile, area_type: Areas):
        filename = cls.textures[tile.type]
        cls.sprites[area_type] = Sprite(filename, area_type.value, 0)

    @classmethod
    def resolve_tile_sprite_area_type(cls, grid, tile):
        # def is_same(t0, t1):
        #     return t0.type == t1.type
        #
        # def is_none(t0, t1):
        #     return t0.type == Tiles.NONE
        #
        # def get_func(letter: str):
        #     if letter == "N":
        #         return is_none
        #     elif letter == "S":
        #         return is_same
        #     else:
        #         raise AttributeError
        #
        # top, bottom, left, right = grid.get_nbs(tile.col, tile.row)
        #
        # if top and bottom and left and right:
        #     for area_type in cls.Areas:
        #         area_name = area_type.name
        #         if get_func(area_name[0])(tile, top) and \
        #                 get_func(area_name[1])(tile, bottom) and \
        #                 get_func(area_name[2])(tile, left) and \
        #                 get_func(area_name[3])(tile, right):
        #             return area_type
        #     return cls.Areas.SSSS
        #     # raise AttributeError
        # else:
        return cls.Areas.SSSS

    @classmethod
    def get_sprite(cls, grid, tile, size):
        area_type = cls.resolve_tile_sprite_area_type(grid, tile)
        if cls.sprites.get(area_type) is None:
            cls.create_sprite(tile, area_type)

        sprite = cls.sprites.get(area_type)
        sprite.set_clip((tile.col + tile.row) % sprite.len)  # set clip from available

        if sprite.get_width() != size.x or sprite.get_height() != size.y:
            sprite.scale(size.x / 32)

        return sprite


class FurnitureSpriteResolver:
    textures = {
        Tiles.WHITE_TORCH: "Tiles_4"
    }

    class Areas(Enum):
        WHITE_TORCH = [(4, 0, 16, 20), (22, 0, 20, 20), (44, 0, 20, 20)]

    sprites = {}

    @classmethod
    def create_sprite(cls, tile, area_type: Areas):
        filename = cls.textures[tile.type]
        cls.sprites[area_type] = Sprite(filename, area_type.value, 0)

    @classmethod
    def resolve_tile_sprite_area_type(cls, grid, tile):

        if tile.type == Tiles.WHITE_TORCH:
            return cls.Areas.WHITE_TORCH
        else:
            raise AttributeError

    @classmethod
    def get_sprite(cls, grid, tile, size):
        area_type = cls.resolve_tile_sprite_area_type(grid, tile)
        if cls.sprites.get(area_type) is None:
            cls.create_sprite(tile, area_type)
        sprite = cls.sprites.get(area_type)

        if sprite.get_width() != size.x or sprite.get_height() != size.y:
            sprite.scale(size.x / 16)

        return sprite


class ItemSpriteResolver:
    textures = {
        Tiles.NONE: ["Item_0", [0, 0, 16, 16]],
        Tiles.DIRT: ["Item_2", [0, 0, 16, 16]],
        Tiles.STONE: ["Item_3", [0, 0, 16, 16]],
        Tiles.LEAD: ["Item_11", [0, 0, 16, 16]],
        Tiles.COPPER: ["Item_12", [0, 0, 16, 16]],
        Tiles.GOLD: ["Item_13", [0, 0, 16, 16]],
        Tiles.SILVER: ["Item_14", [0, 0, 16, 16]],
        Tiles.ASH: ["Item_172", [0, 0, 16, 16]],
        Items.IRON_PICKAXE: ["Item_1", [0, 0, 32, 32]],
        Items.IRON_AXE: ["Item_10", [0, 0, 32, 32]],
        Items.IRON_HAMMER: ["Item_7", [0, 0, 32, 32]],
        Tiles.B_OAK_LOG: ["Item_9", [0, 0, 22, 24]],
        Tiles.B_DIRT: ["Item_30", [0, 0, 16, 16]],
        Tiles.WHITE_TORCH: ["Item_8", [0, 0, 16, 16]]
    }

    sprites = {}

    @classmethod
    def create_sprite(cls, item_type):
        filename, area = cls.textures[item_type]
        cls.sprites[item_type] = Sprite(filename, (area,), 0)

    @classmethod
    def get_sprite(cls, item_type):
        if cls.sprites.get(item_type) is None:
            cls.create_sprite(item_type)
        return cls.sprites.get(item_type)


class WorldBackgroundResolver:
    class Textures(Enum):
        FOREST = ["Forest_background_2", [0, 0, 1024, 838]]

    backgrounds = {}

    @classmethod
    def create_sprite(cls, texture_enum):
        filename, area = texture_enum.value
        cls.backgrounds[texture_enum.name] = Sprite(filename, (area,), 0, alpha=False)

    @classmethod
    def resolve_background(cls, map_, pos: Vector, t_size: Vector):
        return cls.Textures.FOREST

    @classmethod
    def get_sprite(cls, map_, camera, t_size: Vector):
        pos = camera.pos
        texture = cls.resolve_background(map_, pos, t_size)
        if cls.backgrounds.get(texture.name) is None:
            cls.create_sprite(texture)
        sprite = cls.backgrounds[texture.name]

        w, h = sprite.get_width(), sprite.get_height()
        sw, sh = camera.size.x, camera.size.y
        if h != (sh / h) * 2:
            sprite.scale((sh / h) * 2)

        return sprite


class GradientTile:

    @staticmethod
    def get_surface(grid, tile, size):
        col = tile.col
        row = tile.row
        top, down, left, right = grid.get_nbs(col, row)

        t_v = abs(top.type) if top else 0
        d_v = abs(down.type) if down else 0
        l_v = abs(left.type) if left else 0
        r_v = abs(right.type) if right else 0
        return gradient((size.x, size.y),
                        (0, 0, 0, t_v / 15 * 255),
                        (0, 0, 0, d_v / 15 * 255),
                        (0, 0, 0, l_v / 15 * 255),
                        (0, 0, 0, r_v / 15 * 255),
                        2)


class PygameRenderer:
    class ActorRenderer:

        def __init__(self, camera, actor, map_, tile_width: int, tile_height: int) -> None:
            self.camera = camera
            self.actor = actor

            self.map = map_
            self.tile_width = tile_width
            self.tile_height = tile_height
            self.light_surface = Surface([actor.size.x + 10, actor.size.y + 10], SRCALPHA, 32)

        def update(self, delta_time: float):
            sprite = ActorSpriteResolver.get_sprite(self.actor)

            if self.actor.get_state() & ActorState.RIGHT:
                sprite.flip_right()
            elif self.actor.get_state() & ActorState.LEFT:
                sprite.flip_left()

            vel = 1 / self.actor.vel
            sprite.set_time(abs(vel.x) * 7)

            self.light_surface.fill(Color(255, 255, 255, 0))
            x, y = self.actor.pos.x, self.actor.pos.y
            w, h = self.actor.size.x + 5, self.actor.size.y + 5

            s_c, s_r = int(x / self.tile_width), int(y / self.tile_height)
            e_c, e_r = s_c + int(w / self.tile_width) + 1, s_r + int(h / self.tile_height) + 1
            size = Vector(self.tile_width, self.tile_height)

            for c in range(s_c, e_c + 1):
                for r in range(s_r, e_r + 1):
                    tile = self.map.lighting.get_tile(c, r)
                    if tile and tile.type != Tiles.NONE:
                        gradient_surface = GradientTile.get_surface(self.map.lighting, tile, size)
                        t_x = c * self.tile_width - x
                        t_y = r * self.tile_height - y
                        self.light_surface.blit(gradient_surface, [t_x, t_y, w, h], None)

        def render(self, delta_time: float):
            sprite = ActorSpriteResolver.get_sprite(self.actor)
            self.camera.draw_sprite(sprite, self.actor.pos - 10, delta_time)
            self.camera.draw_surface(self.light_surface, self.actor.pos - 4, None)

            # pos = self.actor.pos
            # size = self.actor.size
            # vel = self.actor.vel
            # start = pos + size / 2

            # if vel.x != 0 or vel.y != 0:
            #     self.camera.draw_line(start, start + vel * delta_time, 2, Color(255, 0, 0))

            # draw position
            # text_pos0 = pos - Vector(0, size.y + 32)
            # text_pos1 = pos - Vector(0, size.y + 16)
            # text_pos2 = pos - Vector(0, size.y)
            # self.camera.draw_text("[x({}), y({})]".format(pos.x, pos.y), 16, text_pos0, Color(0, 0, 0))
            # self.camera.draw_text("[c({}), r({})]".format(int(pos.x / 16), int(pos.y / 16)), 16, text_pos1,
            #                       Color(0, 0, 0))
            # self.camera.draw_text("[vx({}), vy({})]".format(vel.x, vel.y), 16, text_pos2, Color(0, 0, 0))

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

            def init_surface(self):
                """ Initialize chunk surface """

                for col in range(self.tiles_x):
                    for row in range(self.tiles_y):
                        if self.lighting:
                            tile = self.get_tile(col, row, GridType.LIGHTING)
                            if tile and tile.type > -15:  # lighting depth
                                tile = self.get_tile(col, row, GridType.BACKGROUND)
                                if tile and tile.type != Tiles.NONE:
                                    self.blit_tile(tile, GridType.BACKGROUND)
                                tile = self.get_tile(col, row, GridType.FURNITURE)
                                if tile and tile.type != Tiles.NONE:
                                    self.blit_tile(tile, GridType.FURNITURE)
                                tile = self.get_tile(col, row, GridType.FOREGROUND)
                                if tile and tile.type != Tiles.NONE:
                                    self.blit_tile(tile, GridType.FOREGROUND)
                            tile = self.get_tile(col, row, GridType.LIGHTING)
                            if tile and tile.type != Tiles.NONE:
                                self.blit_tile(tile, GridType.LIGHTING)
                        else:
                            tile = self.get_tile(col, row, GridType.BACKGROUND)
                            if tile and tile.type != Tiles.NONE:
                                self.blit_tile(tile, GridType.BACKGROUND)
                            tile = self.get_tile(col, row, GridType.FURNITURE)
                            if tile and tile.type != Tiles.NONE:
                                self.blit_tile(tile, GridType.FURNITURE)
                            tile = self.get_tile(col, row, GridType.FOREGROUND)
                            if tile and tile.type != Tiles.NONE:
                                self.blit_tile(tile, GridType.FOREGROUND)

                self.initialized = True
                self.initializing = False

            def get_tile(self, col: int, row: int, grid_type: GridType):

                tile_col = col + self.col * self.tiles_x
                tile_row = row + self.row * self.tiles_y

                if grid_type == GridType.BACKGROUND:
                    return self.map.background.get_tile(tile_col, tile_row)
                elif grid_type == GridType.FURNITURE:
                    return self.map.furniture.get_tile(tile_col, tile_row)
                elif grid_type == GridType.FOREGROUND:
                    return self.map.foreground.get_tile(tile_col, tile_row)
                elif grid_type == GridType.LIGHTING:
                    return self.map.lighting.get_tile(tile_col, tile_row)
                else:
                    raise AttributeError

            def blit_tile(self, tile: Tile, grid_type: GridType):
                """ Blit tile sprite into chunk surface """

                size = Vector(self.tile_width, self.tile_height)

                if grid_type == GridType.FOREGROUND:
                    tile_surface = ForegroundSpriteResolver.get_sprite(self.map.foreground, tile, size).get_surface()
                elif grid_type == GridType.BACKGROUND:
                    tile_surface = BackgroundSpriteResolver.get_sprite(self.map.background, tile,
                                                                       size + 16).get_surface()
                elif grid_type == GridType.LIGHTING:
                    tile_surface = GradientTile.get_surface(self.map.lighting, tile, size)
                elif grid_type == GridType.FURNITURE:
                    tile_surface = FurnitureSpriteResolver.get_sprite(self.map.furniture, tile, size).get_surface()
                else:
                    raise AttributeError

                # translate map col - row to chunk col - row
                col = tile.col % self.tiles_x
                row = tile.row % self.tiles_y
                x = col * self.tile_width + (self.tile_width / 2 if grid_type != GridType.BACKGROUND else 0)
                y = row * self.tile_height + (self.tile_height / 2 if grid_type != GridType.BACKGROUND else 0)

                self.surface.blit(tile_surface, (x, y))

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
                tile = self.get_tile(col, row, GridType.BACKGROUND)
                if tile and tile.type != Tiles.NONE:
                    self.blit_tile(tile, GridType.BACKGROUND)
                tile = self.get_tile(col, row, GridType.FURNITURE)
                if tile and tile.type != Tiles.NONE:
                    self.blit_tile(tile, GridType.FURNITURE)
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
                    run_in_thread(self.init_surface, tuple(), priority=10)

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

            self.map.add_map_listener(self)

        def get_chunk(self, chunk_col: int, chunk_row: int) -> Chunk:
            """ :return chunk: """
            return self.chunks[chunk_key(chunk_col, chunk_row)]

        def get_tile_chunk(self, tile_col: int, tile_row: int) -> Chunk:
            """ :return: chunk for tile """

            chunk_col = int(tile_col / self.chunk_width)
            chunk_row = int(tile_row / self.chunk_height)

            return self.get_chunk(chunk_col, chunk_row)

        def update_light(self, tile: Tile, grid_type: GridType):

            if grid_type == GridType.FOREGROUND:
                destroyed = (tile.type == Tiles.NONE)
            elif grid_type == GridType.BACKGROUND:
                destroyed = (tile.type == Tiles.NONE)
            else:
                destroyed = (tile.type == Tiles.WHITE_TORCH)

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

            b_tile = self.map.background.get_tile(c, r)
            if self.lighting_enabled and (
                    (grid_id == GridType.FOREGROUND and b_tile.type == Tiles.NONE) or
                    (grid_id != GridType.FOREGROUND)
            ):
                run_in_thread(self.update_light, (tile, grid_id), priority=5)

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

        class BackgroundRenderer:

            def __init__(self, camera, scene, t_width: int, t_height: int) -> None:
                self.camera = camera
                self.scene = scene
                self.map = scene.get_map()
                self.tile_width = t_width
                self.tile_height = t_height
                self.chunk_width = 512
                self.chunk_height = 512

                screen_x, screen_y = self.camera.size.x, self.camera.size.y
                self.chunks_x = int(screen_x / self.chunk_width) + 1
                self.chunks_y = int(screen_y / self.chunk_height) + 1

            def update(self, delta_time: float):
                pass

            def render(self, delta_time: float):
                t_size = Vector(self.tile_width, self.tile_height)
                sprite = WorldBackgroundResolver.get_sprite(self.map, self.camera, t_size)

                w, h = sprite.get_width(), sprite.get_height()
                x, y = self.camera.pos.x, self.camera.pos.y
                sw, sh = self.camera.size.x, self.camera.size.y

                translated_y = -h * 0.35 - y * 0.5
                min_y = -0.5 * h

                for _ in range(int(sw / w) + 2):
                    pos = Vector(_ * w - ((x * 0.25) % w), translated_y if translated_y > min_y else min_y)
                    self.camera.draw_sprite(sprite, pos, delta_time, translate=False)

        class InventoryRenderer:

            def __init__(self, camera, inventory, item_width: int, item_height: int, item_spacing: int) -> None:
                self.camera = camera
                self.inventory = inventory
                self.item_width = item_width
                self.item_height = item_height
                self.item_spacing = item_spacing

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
                        sprite = ItemSpriteResolver.get_sprite(slot.type)
                        item_pos = pos + 0.5 * size - 0.5 * Vector(sprite.get_width(), sprite.get_height())
                        text_pos = pos + 0.5 * size + Vector(0, -2)
                        self.camera.draw_surface(sprite.get_surface(), item_pos, None, translate=False)
                        self.camera.draw_text(str(slot.amount), 16, text_pos, Color(255, 255, 255), translate=False)

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
                        sprite = ItemSpriteResolver.get_sprite(recipe.get_type())
                        item_pos = pos + 0.5 * size - 0.5 * Vector(sprite.get_width(), sprite.get_height())
                        self.camera.draw_surface(sprite.get_surface(), item_pos, None, translate=False)
                        pos.y += self.item_height + self.item_spacing

                # draw mouse slot
                if not self.inventory.temp.is_empty():
                    slot = self.inventory.temp
                    pos = Vector(*pygame.mouse.get_pos())
                    sprite = ItemSpriteResolver.get_sprite(slot.type)
                    item_pos = pos + 0.5 * size - 0.5 * Vector(sprite.get_width(), sprite.get_height())
                    text_pos = pos + 0.5 * size + Vector(0, -2)
                    self.camera.draw_surface(sprite.get_surface(), item_pos, None, translate=False)
                    self.camera.draw_text(str(slot.amount), 16, text_pos, Color(255, 255, 255),
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

            self.background_renderer = PygameRenderer.WorldRenderer.BackgroundRenderer(self.camera, scene,
                                                                                       tile_width, tile_height)

            self.map_renderer = PygameRenderer.MapRenderer(self.camera, scene.get_map(), tile_width, tile_height,
                                                           chunk_width, chunk_height, lighting)
            self.inv_renderer = PygameRenderer.WorldRenderer.InventoryRenderer(
                self.camera, scene.inventory, inv_item_width, inv_item_height, inv_item_spacing)

            for actor in scene.get_actors():
                self.actor_renderers[str(actor)] = PygameRenderer.ActorRenderer(self.camera, actor, scene.get_map(),
                                                                                tile_width, tile_height)

        def on_actor_added(self, actor):
            self.actor_renderers[str(actor)] = PygameRenderer.ActorRenderer(self.camera, actor)

        def on_actor_removed(self, actor):
            self.actor_renderers.pop(actor)

        def on_scene_move(self, x, y):
            pass

        def update(self, delta_time: float):
            """ Update actors and map """
            self.background_renderer.update(delta_time)
            self.map_renderer.update(delta_time)
            for actor_renderer in self.actor_renderers.values():
                actor_renderer.update(delta_time)
            self.inv_renderer.update(delta_time)
            self.camera.update(delta_time)

        def render(self, delta_time: float):
            """ Renders actors and map """
            self.background_renderer.render(delta_time)
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
