from math import isnan

from src.rect import Rect, Entity
from src.vector import Vector


class CollisionInfo:

    def __init__(self):
        self.cp = Vector(0, 0)
        self.cn = Vector(0, 0)
        self.c_time = .0


def ray_vs_rect(ray_org: Vector, ray_dir: Vector, target: Rect, info: CollisionInfo) -> bool:
    contact_normal = Vector(0, 0)
    contact_point = Vector(0, 0)

    invdir = 1.0 / ray_dir

    t_near = (target.pos - ray_org) * invdir
    t_far = (target.pos + target.size - ray_org) * invdir

    if isnan(t_near.x) or isnan(t_near.y):
        return False
    if isnan(t_far.x) or isnan(t_far.y):
        return False

    if t_near.x > t_far.x:
        tmp = t_near.x
        t_near.x = t_far.x
        t_far.x = tmp

    if t_near.y > t_far.y:
        tmp = t_near.y
        t_near.y = t_far.y
        t_far.y = tmp

    if t_near.x > t_far.y or t_near.y > t_far.x:
        return False

    t_hit_near = max(t_near.x, t_near.y)
    t_hit_far = min(t_far.x, t_far.y)

    if t_hit_far < 0:
        return False

    contact_point = ray_org + t_hit_near * ray_dir

    if t_near.x > t_near.y:
        if invdir.x < 0:
            contact_normal = Vector(1, 0)
        else:
            contact_normal = Vector(-1, 0)
    elif t_near.x < t_near.y:
        if invdir.y < 0:
            contact_normal = Vector(0, 1)
        else:
            contact_normal = Vector(0, -1)

    info.cp = contact_point
    info.cn = contact_normal
    info.c_time = t_hit_near

    return True


def dynamic_rect_vs_rect(r_dynamic: Entity, r_static: Rect, dt: float, info: CollisionInfo) -> bool:

    if r_dynamic.vel.x == 0 and r_dynamic.vel.y == 0:
        return False

    expanded_target = Rect(0, 0, 0, 0)
    expanded_target.pos = r_static.pos - (r_dynamic.size / 2)
    expanded_target.size = r_static.size + r_dynamic.size

    if ray_vs_rect(r_dynamic.pos + r_dynamic.size / 2, r_dynamic.vel * dt, expanded_target, info):
        return 0 <= info.c_time < 1
    else:
        return False


def resolve_dynamic_rect_vs_rect(r_dynamic: Entity, r_static: Rect, dt: float):

    info = CollisionInfo()
    if dynamic_rect_vs_rect(r_dynamic, r_static, dt, info):
        r_dynamic.vel += info.cn * Vector(abs(r_dynamic.vel.x), abs(r_dynamic.vel.y)) * (1.0 - info.c_time)
        r_dynamic.on_collision(r_static, info.cn)
        return True
    else:
        return False


