from abc import abstractmethod, ABC

from src.actor import Actor


class Action(ABC):
    _actor: Actor

    def __init__(self) -> None:
        super().__init__()
        self._done = False

    def set_actor(self, actor: Actor):
        self._actor = actor

    def get_actor(self):
        return self._actor

    def finish(self):
        self._done = True

    def is_done(self):
        return self._done

    @abstractmethod
    def execute(self, deltaTime: float):
        pass

