from math import sqrt, inf


class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        elif isinstance(other, int) or isinstance(other, float):
            return Vector(self.x + other, self.y + other)
        else:
            raise AttributeError

    def __sub__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x - other.x, self.y - other.y)
        elif isinstance(other, int) or isinstance(other, float):
            return Vector(self.x - other, self.y - other)
        else:
            raise AttributeError

    def __mul__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x * other.x, self.y * other.y)
        elif isinstance(other, int) or isinstance(other, float):
            return Vector(self.x * other, self.y * other)
        else:
            raise AttributeError

    def __truediv__(self, other):
        if isinstance(other, Vector):
            if other.x != 0 and other.y != 0:
                return Vector(self.x / other.x, self.y / other.y)
            elif other.x == 0 and other.y != 0:
                return Vector(inf, self.y / other.y)
            elif other.x != 0 and other.y == 0:
                return Vector(self.x / other.x, inf)
        elif isinstance(other, int) or isinstance(other, float):
            return Vector(self.x / other, self.y / other)
        else:
            raise AttributeError

    def __rtruediv__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            if self.x != 0 and self.y != 0:
                return Vector(other / self.x, other / self.y)
            elif self.x != 0 and self.y == 0:
                return Vector(other / self.x, inf)
            elif self.x == 0 and self.y != 0:
                return Vector(inf, other / self.y)
            else:
                return Vector(inf, inf)
        else:
            raise AttributeError

    def __matmul__(self, other):
        if isinstance(other, Vector):
            return self.dot(other)
        else:
            raise AttributeError

    __radd__ = __add__
    __rsub__ = __sub__
    __rmul__ = __mul__

    def normalize(self):
        return Vector(self.x / self.mag(), self.y / self.mag())

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def normal(self):
        return Vector(self.y, -self.x)

    def mag(self):
        return sqrt(self.x ** 2 + self.y ** 2)
