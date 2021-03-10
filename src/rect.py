from src.vector import Vector


class Rect:

    def __init__(self, x: float, y: float, width: int, height: int):
        self.pos = Vector(x, y)
        self.size = Vector(width, height)


class Entity(Rect):
    """ Rectangle with physics """

    def __init__(self, x: float, y: float, width: int, height: int) -> None:
        super(Entity, self).__init__(x, y, width, height)
        self.vel = Vector(0, 0)

    def on_collision(self, collider: Rect, cn: Vector):
        pass

    def update(self, delta_time: float):
        dt = delta_time
        self.pos += self.vel * dt
