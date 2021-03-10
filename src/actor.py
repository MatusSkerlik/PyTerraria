from enum import Flag
from typing import Union

from src.rect import Entity
from src.scene import Scene


class ActorState(Flag):
    IDLE = 1
    LEFT = 2
    RIGHT = 4
    WALKING = 8
    JUMPING = 16
    INTERACTION = 32


class Actor(Entity):
    scene: Union[None, Scene]

    def __init__(self, x: float, y: float, width: int, height: int, actor_type: int) -> None:
        super(Actor, self).__init__(x, y, width, height)
        self.scene = None
        self.state = ActorState.IDLE
        self.type = actor_type

    def get_scene(self) -> Union[None, Scene]:
        return self.scene

    def or_state(self, state: ActorState):
        self.state |= state

    def and_state(self, state: ActorState):
        self.state &= state

    def set_state(self, state: ActorState):
        self.state = state

    def get_state(self) -> ActorState:
        return self.state

    def get_type(self) -> int:
        return self.type

    def added_to_scene(self, scene: Scene) -> None:
        self.scene = scene

    def removed_from_scene(self, scene: Scene) -> None:
        self.scene = None
