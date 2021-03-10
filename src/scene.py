from abc import ABC, abstractmethod

from src.input import Input
from src.inventory import Inventory
from src.map import Map
from src.rect import Rect
from src.settings import SceneSettings


class SceneListener(ABC):

    @abstractmethod
    def on_actor_added(self, actor):
        pass

    @abstractmethod
    def on_actor_removed(self, actor):
        pass

    @abstractmethod
    def on_scene_move(self, x, y):
        pass


class Scene(Rect, ABC):
    """ Represents viewport """

    initialized = False
    settings: SceneSettings
    actors = set()
    actions = set()
    listeners = set()
    followee = None

    input: Input

    @abstractmethod
    def init(self, application):
        """ Initialize all scene resources here """
        pass

    @abstractmethod
    def exit(self):
        """ Free all scene resources here """
        pass

    def follow(self, followee: Rect):
        self.followee = followee

    def unfollow(self):
        self.followee = None

    def is_initialized(self):
        return self.initialized

    def add_actor(self, actor):
        """ Adds actor that will be rendered on next call of render """
        self.actors.add(actor)
        actor.added_to_scene(self)

        # notify
        for listener in self.listeners:
            listener.on_actor_added(actor)

    def remove_actor(self, actor):
        """ Remove actor from scene """
        self.actors.remove(actor)
        actor.removed_from_scene(self)

        # notify
        for listener in self.listeners:
            listener.on_actor_removed(listener)

    def schedule_action(self, action, actor):
        """ Will schedule action on next tick on actor """
        action.set_actor(actor)
        self.actions.add(action)
        return lambda: self.actions.remove(action)

    def remove_action(self, action):
        """ Action will be removed before next tick """
        self.actions.remove(action)

    def execute_actions(self, delta_time: float):
        """ Execute actions and remove finished """
        expired = []
        for action in self.actions:  # execute actions
            if not action.is_done():
                action.execute(delta_time)
            if action.is_done():
                expired.append(action)
        for action in expired:  # remove expired
            self.actions.remove(action)

    def add_scene_listener(self, listener):
        self.listeners.add(listener)

    def remove_scene_listener(self, listener):
        self.listeners.remove(listener)

    def get_input(self):
        """ :return input processor """
        return self.input

    def get_actors(self):
        """ :return scene actors """
        return self.actors

    def get_settings(self):
        """ :return scene settings """
        return self.settings

    def get_followee(self):
        return self.followee

    @abstractmethod
    def update(self, delta_time: float):
        """ Update state of scene """
        pass


class World(Scene, ABC):
    """ Represents playable world """

    map: Map
    inventory: Inventory

    def get_map(self):
        """ :return scene map """
        return self.map

    def get_inventory(self):
        """ :return scene inventory """
        return self.inventory
