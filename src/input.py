from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Set, Tuple

import pygame
from pygame.event import Event


class Key(IntEnum):
    W = 0
    S = 1
    A = 2
    D = 3
    ESC = 80


_key_translation_table = {
    pygame.K_w: Key.W,
    pygame.K_s: Key.S,
    pygame.K_a: Key.A,
    pygame.K_d: Key.D,
    pygame.K_ESCAPE: Key.ESC
}


class Mouse(IntEnum):
    LEFT = 0
    RIGHT = 1
    MIDDLE = 2
    SCROLL_UP = 3
    SCROLL_DOWN = 4


_mouse_translation_table = {
    pygame.BUTTON_LEFT: Mouse.LEFT,
    pygame.BUTTON_RIGHT: Mouse.RIGHT,
    pygame.BUTTON_MIDDLE: Mouse.MIDDLE,
    pygame.BUTTON_WHEELUP: Mouse.SCROLL_UP,
    pygame.BUTTON_WHEELDOWN: Mouse.SCROLL_DOWN
}


class MouseListener(ABC):

    @abstractmethod
    def on_mouse_down(self, x: float, y: float, ev_type) -> bool:
        pass

    @abstractmethod
    def on_mouse_drag(self, x: float, y: float, ev_type) -> bool:
        pass

    @abstractmethod
    def on_mouse_up(self, x: float, y: float, ev_type) -> bool:
        pass


class KeyboardListener(ABC):

    @abstractmethod
    def on_key_down(self, key) -> bool:
        pass

    @abstractmethod
    def on_key_up(self, key) -> bool:
        pass


class Input:
    """ Basic input processor """

    _scene = None
    _mouse_down: bool  # TODO limited to any mouse button
    _keyboard_listeners: Set[KeyboardListener]
    _mouse_listeners: Set[MouseListener]

    def __init__(self) -> None:
        self._mouse_down = False
        self._mouse_listeners = set()
        self._keyboard_listeners = set()

    def init(self, scene):
        self._scene = scene

    def exit(self):
        self._scene = None
        self._mouse_down = False
        self._keyboard_listeners.clear()
        self._mouse_listeners.clear()

    def add_mouse_listener(self, listener: MouseListener):
        """ Scene will dispatch events to this listener """
        self._mouse_listeners.add(listener)

    def remove_mouse_listener(self, listener: MouseListener):
        """ Dont forget to remove listener """
        self._mouse_listeners.remove(listener)

    def add_keyboard_listener(self, listener: KeyboardListener):
        """ Scene will dispatch events to this listener """
        self._keyboard_listeners.add(listener)

    def remove_keyboard_listener(self, listener: KeyboardListener):
        """ Dont forget to remove listener """
        self._keyboard_listeners.remove(listener)

    def handle_events(self, event_list: Tuple[Event]):
        """ Will handle events to proper listeners """
        for ev in event_list:
            if ev.type == pygame.KEYUP:
                for listener in self._keyboard_listeners:
                    try:
                        key = _key_translation_table[ev.key]
                        if listener.on_key_up(key):
                            break
                    except KeyError:
                        pass
            elif ev.type == pygame.KEYDOWN:
                for listener in self._keyboard_listeners:
                    try:
                        key = _key_translation_table[ev.key]
                        if listener.on_key_down(key):
                            break
                    except KeyError:
                        pass
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                self._mouse_down = True
                for listener in self._mouse_listeners:
                    try:
                        key = _mouse_translation_table[ev.button]
                        x, y = pygame.mouse.get_pos()
                        if listener.on_mouse_down(x, y, key):
                            break
                    except KeyError:
                        pass
            elif ev.type == pygame.MOUSEBUTTONUP:
                self._mouse_down = False
                for listener in self._mouse_listeners:
                    try:
                        key = _mouse_translation_table[ev.button]
                        x, y = pygame.mouse.get_pos()
                        if listener.on_mouse_up(x, y, key):
                            break
                    except KeyError:
                        pass
            # TODO drag
            # elif self._mouse_down:
            #     for listener in self._mouse_listeners:
            #         try:
            #             key = _mouse_translation_table[ev.button]
            #             x, y = pygame.mouse.get_pos()
            #             if listener.on_mouse_drag(x, y, key):
            #                 break
            #         except KeyError:
            #             pass
