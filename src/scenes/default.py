from typing import List

from src.actors.player import Player
from src.input import Input, KeyboardListener, MouseListener, Mouse, Key
from src.inventory import Inventory
from src.maps.procedural import ProceduralMap
from src.physics import resolve_dynamic_rect_vs_rect, dynamic_rect_vs_rect, CollisionInfo
from src.rect import Rect
from src.scene import World
from src.settings import SceneSettings
from src.tables import Tiles, TileLayers, Layers, Items, is_tile
from src.vector import Vector


class DefaultScene(MouseListener, KeyboardListener, World):

    def __init__(self) -> None:
        super().__init__(0, 0, 0, 0)
        self.keys_down = {}
        self.settings = SceneSettings({
            "WORLD_WIDTH": 500,
            "WORLD_HEIGHT": 500,
            "TILE_WIDTH": 16,
            "TILE_HEIGHT": 16,
            "CHUNK_HEIGHT": 12,
            "CHUNK_WIDTH": 12,
            "LIGHTING": True
        })
        self.input = Input()

        world_width = self.settings.get_world_width()
        world_height = self.settings.get_world_height()

        self.map = ProceduralMap(world_width, world_height)
        self.inventory = Inventory(50, 999)
        self.inventory.add(Items.IRON_PICKAXE, 1)
        self.inventory.add(Items.IRON_AXE, 1)
        self.inventory.add(Items.IRON_HAMMER, 1)
        self.inventory.add(Tiles.WHITE_TORCH, 999)
        self.player = Player(0, 0, 20, 42)

    def get_tiles_around(self, rect, delta_time: float) -> List[Rect]:

        def is_wall(tile_type: int):
            return tile_type != Tiles.NONE

        t_w = self.settings.get_tile_width()
        t_h = self.settings.get_tile_height()

        col = int(rect.pos.x / t_w)
        row = int(rect.pos.y / t_h)

        s_c = max(0, col - 4)
        s_r = max(0, row - 4)
        e_c = col + 4 + int(rect.size.x / t_w)
        e_r = row + 4 + int(rect.size.y / t_h)

        tiles = []
        for c_ in range(s_c, e_c + 1):
            for r_ in range(s_r, e_r + 1):
                tile = self.map.foreground.get_tile(c_, r_)
                if tile and is_wall(tile.type):
                    x = c_ * t_w
                    y = r_ * t_h
                    rect = Rect(x, y, t_w, t_h)
                    tiles.append(rect)
        return tiles

    def on_key_down(self, key) -> bool:
        self.keys_down[key] = True

        if key == Key.ESC:
            self.inventory.crafting = not self.inventory.crafting
            return True

        return False

    def on_key_up(self, key) -> bool:
        self.keys_down[key] = False
        return False

    def on_mouse_down(self, x: float, y: float, ev_type) -> bool:

        pos = self.pos + Vector(x, y)
        t_w = self.settings.get_tile_width()
        t_h = self.settings.get_tile_height()
        c = int(pos.x / t_w)
        r = int(pos.y / t_h)

        # check if click is on inventory item
        item_spacing = self.settings.get_inventory_spacing()
        item_width = self.settings.get_inventory_item_width()
        item_height = self.settings.get_inventory_item_height()

        for i, slot in self.inventory:
            index0 = int(i % 10)
            index1 = int(i / 10)
            s_x = item_spacing + index0 * (item_width + item_spacing)
            e_x = (index0 + 1) * (item_width + item_spacing)
            s_y = item_spacing + index1 * (item_height + item_spacing)
            e_y = (index1 + 1) * (item_height + item_spacing)
            if s_x < x < e_x and s_y < y < e_y:
                if ev_type == Mouse.LEFT:
                    slot = self.inventory.slots[i]
                    temp = self.inventory.temp
                    if temp.is_empty():
                        temp.set_type(slot.type)
                        temp.add(slot.amount)
                        slot.clear()
                    else:
                        if slot.is_empty():
                            slot.set_type(temp.type)
                            slot.add(temp.amount)
                            temp.clear()
                        else:
                            # add if same item
                            if temp.type == slot.type:
                                slot.add(temp.amount)
                                temp.clear()
                            else:  # swap tmp
                                t_type = slot.type
                                t_amount = slot.amount
                                slot.type = temp.type
                                slot.amount = temp.amount
                                temp.type = t_type
                                temp.amount = t_amount
                    return True

                elif ev_type == Mouse.RIGHT:
                    slot = self.inventory.slots[i]
                    temp = self.inventory.temp

                    if not slot.is_empty():
                        if temp.is_empty():
                            temp.set_type(slot.type)
                            temp.add(slot.remove(1))
                            return True
                        elif temp.type == slot.type:
                            temp.add(slot.remove(1))
                            return True

        # check crafting
        if self.inventory.crafting:
            temp = self.inventory.temp
            if ev_type == Mouse.LEFT or ev_type == Mouse.RIGHT:
                recipes = self.inventory.get_recipes()
                skip_y = int(self.inventory.capacity / 10) * (item_height + item_spacing) + item_spacing
                for i, recipe in zip(range(len(recipes)), recipes):
                    s_x = item_spacing
                    e_x = s_x + item_height
                    s_y = skip_y + i * (item_height + item_spacing)
                    e_y = s_y + item_height
                    if s_x < x < e_x and s_y < y < e_y:
                        for i_type, i_amount in recipe.get_ingredients().items():
                            if ev_type == Mouse.LEFT:
                                self.inventory.consume(i_type, i_amount)
                                self.inventory.add(recipe.get_type(), 1)
                                return True
                            else:
                                if temp.is_empty():
                                    self.inventory.consume(i_type, i_amount)
                                    temp.set_type(recipe.get_type())
                                    temp.add(1)
                                    return True
                                elif temp.type == recipe.get_type():
                                    self.inventory.consume(i_type, i_amount)
                                    temp.add(1)
                                    return True

        if ev_type == Mouse.LEFT:

            slot = self.inventory.temp
            if slot.is_empty():
                slot = self.inventory.slots[self.inventory.index]

            if abs((pos - (self.player.pos + (self.player.size / 2))).mag()) < 72:  # block removal
                if slot.type == Items.IRON_PICKAXE:  # mining
                    tile = self.map.foreground.get_tile(c, r)
                    if tile and tile.type != Tiles.NONE:
                        self.inventory.add(tile.type, 1)
                        self.map.foreground.set_tile(c, r, 0)
                        return True
                    tile = self.map.furniture.get_tile(c, r)
                    if tile and tile.type != Tiles.NONE:
                        self.inventory.add(tile.type, 1)
                        self.map.furniture.set_tile(c, r, 0)
                        return True
                elif slot.type == Items.IRON_HAMMER:  # mining background
                    tile = self.map.background.get_tile(c, r)
                    fg_tile = self.map.foreground.get_tile(c, r)
                    f_tile = self.map.furniture.get_tile(c, r)
                    if tile and tile.type != Tiles.NONE and \
                            fg_tile and fg_tile.type == Tiles.NONE and \
                            f_tile and f_tile.type == Tiles.NONE:
                        self.inventory.add(tile.type, 1)
                        self.map.background.set_tile(c, r, 0)
                        return True
                elif slot.type == Tiles.WHITE_TORCH:
                    tile = self.map.furniture.get_tile(c, r)
                    b_tile = self.map.background.get_tile(c, r)
                    fg_tile = self.map.foreground.get_tile(c, r)
                    if tile and tile.type == Tiles.NONE and b_tile and b_tile.type != Tiles.NONE and fg_tile and fg_tile.type == Tiles.NONE:
                        self.inventory.consume(slot.type, 1)
                        self.map.furniture.set_tile(c, r, slot.type)
                        return True
                else:  # building

                    build_item_type = slot.type

                    if is_tile(build_item_type):
                        if TileLayers[build_item_type] == Layers.FOREGROUND:
                            tile = self.map.foreground.get_tile(c, r)
                            if tile:
                                slot.amount -= 1
                                if slot.amount <= 0:
                                    slot.clear()
                                if tile.type != Tiles.NONE:
                                    self.inventory.add(tile.type, 1)
                                self.map.foreground.set_tile(c, r, build_item_type)
                                return True
                        else:
                            tile = self.map.background.get_tile(c, r)
                            if tile:
                                slot.amount -= 1
                                if slot.amount <= 0:
                                    slot.clear()
                                if tile.type != Tiles.NONE:
                                    self.inventory.add(tile.type, 1)
                                self.map.background.set_tile(c, r, build_item_type)
                                return True
            return False
        elif ev_type == Mouse.SCROLL_UP:
            self.inventory.shift_right()
        elif ev_type == Mouse.SCROLL_DOWN:
            self.inventory.shift_left()
        else:
            return False

    def on_mouse_drag(self, x: float, y: float, ev_type) -> bool:
        pos = self.pos + Vector(x, y)
        t_w = self.settings.get_tile_width()
        t_h = self.settings.get_tile_height()
        c = int(pos.x / t_w)
        r = int(pos.y / t_h)

        slot = self.inventory.temp
        if slot.is_empty():
            slot = self.inventory.slots[self.inventory.index]

        if slot.type == Items.IRON_PICKAXE:  # mining
            tile = self.map.foreground.get_tile(c, r)
            if tile and tile.type != Tiles.NONE:
                self.inventory.add(tile.type, 1)
                self.map.foreground.set_tile(c, r, 0)
                return True
            tile = self.map.furniture.get_tile(c, r)
            if tile and tile.type != Tiles.NONE:
                self.inventory.add(tile.type, 1)
                self.map.furniture.set_tile(c, r, 0)
                return True
        elif slot.type == Items.IRON_HAMMER:  # mining background
            tile = self.map.background.get_tile(c, r)
            fg_tile = self.map.foreground.get_tile(c, r)
            f_tile = self.map.furniture.get_tile(c, r)
            if tile and tile.type != Tiles.NONE and \
                    fg_tile and fg_tile.type == Tiles.NONE and \
                    f_tile and f_tile.type == Tiles.NONE:
                self.inventory.add(tile.type, 1)
                self.map.background.set_tile(c, r, 0)
                return True
        elif slot.type == Tiles.WHITE_TORCH:
            tile = self.map.furniture.get_tile(c, r)
            b_tile = self.map.background.get_tile(c, r)
            fg_tile = self.map.foreground.get_tile(c, r)
            if tile and tile.type == Tiles.NONE and b_tile and b_tile.type != Tiles.NONE and fg_tile and fg_tile.type == Tiles.NONE:
                self.inventory.consume(slot.type, 1)
                self.map.furniture.set_tile(c, r, slot.type)
                return True
        else:  # building

            build_item_type = slot.type

            if is_tile(build_item_type):
                if TileLayers[build_item_type] == Layers.FOREGROUND:
                    tile = self.map.foreground.get_tile(c, r)
                    if tile:
                        slot.amount -= 1
                        if slot.amount <= 0:
                            slot.clear()
                        if tile.type != Tiles.NONE:
                            self.inventory.add(tile.type, 1)
                        self.map.foreground.set_tile(c, r, build_item_type)
                        return True
                else:
                    tile = self.map.background.get_tile(c, r)
                    if tile:
                        slot.amount -= 1
                        if slot.amount <= 0:
                            slot.clear()
                        if tile.type != Tiles.NONE:
                            self.inventory.add(tile.type, 1)
                        self.map.background.set_tile(c, r, build_item_type)
                        return True
            return False

    def on_mouse_up(self, x: float, y: float, ev_type) -> bool:
        pass

    def update(self, delta_time: float):

        for actor in self.get_actors():
            # apply gravity
            if actor.vel.y < 1000:
                actor.vel.y += 2000 * delta_time
                if actor.vel.y > 1000:
                    actor.vel.y = 1000

            # resolve collisions
            contacts = []
            for tile in self.get_tiles_around(actor, delta_time):
                info = CollisionInfo()
                if dynamic_rect_vs_rect(actor, tile, delta_time, info):
                    contacts.append((tile, info.c_time))
            if contacts:
                contacts.sort(key=lambda v: v[1])
                for contact_pair in contacts:
                    tile, c_time = contact_pair
                    if resolve_dynamic_rect_vs_rect(actor, tile, delta_time):
                        # print("Resolved collision: [{}, {}] -> {}".format(tile.get_col(), tile.get_row(), c_time))
                        pass
            actor.update(delta_time)

    def init(self, application):
        self.input.init(self)
        self.map.init(self)
        self.input.add_keyboard_listener(self)
        self.input.add_mouse_listener(self)

        self.add_actor(self.player)
        self.input.add_keyboard_listener(self.player)
        self.input.add_mouse_listener(self.player)
        self.follow(self.player)

        self.initialized = True

    def exit(self):
        pass
