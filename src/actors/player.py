from src.actor import Actor, ActorState
from src.input import KeyboardListener, MouseListener, Key


class Player(MouseListener, KeyboardListener, Actor):

    def __init__(self, x: float, y: float, width: int, height: int) -> None:
        super().__init__(x, y, width, height, 0)
        self.keys_down = {}
        self.grounded = False

        self.set_state(ActorState.IDLE | ActorState.LEFT)

    def on_key_down(self, key) -> bool:
        self.keys_down[key] = True
        return False

    def on_key_up(self, key) -> bool:
        self.keys_down[key] = False
        return False

    def on_mouse_down(self, x: float, y: float, ev_type) -> bool:
        pass

    def on_mouse_drag(self, x: float, y: float, ev_type) -> bool:
        pass

    def on_mouse_up(self, x: float, y: float, ev_type) -> bool:
        pass

    def on_collision(self, collider, cn):
        if cn.y < 0:
            self.grounded = True

    def update(self, delta_time: float):
        super().update(delta_time)

        left = self.keys_down.get(Key.A)
        right = self.keys_down.get(Key.D)
        up = self.keys_down.get(Key.W)

        if up and self.grounded:
            self.vel.y = -600
            self.grounded = False
        if left and not right:
            if self.vel.x > 0:
                self.vel.x = 0
            if self.vel.x > -300:
                if self.vel.x == 0:
                    self.vel.x -= 150
                else:
                    self.vel.x += -300 * delta_time
                    if self.vel.x < -300:
                        self.vel.x = -300
        elif right and not left:
            if self.vel.x < 0:
                self.vel.x = 0
            if self.vel.x < 300:
                if self.vel.x == 0:
                    self.vel.x += 150
                else:
                    self.vel.x += 300 * delta_time
                    if self.vel.x > 300:
                        self.vel.x = 300
        elif (left and right) or (not left and not right):
            if self.vel.x < 0:
                self.vel.x += 2000 * delta_time
                if self.vel.x > 0:
                    self.vel.x = 0
            elif self.vel.x > 0:
                self.vel.x -= 2000 * delta_time
                if self.vel.x < 0:
                    self.vel.x = 0

        if not self.grounded or self.vel.y != 0:
            self.or_state(ActorState.JUMPING)
            self.and_state(~ActorState.WALKING)
            self.and_state(~ActorState.IDLE)
        else:
            if self.vel.x == 0 and self.vel.y == 0:
                self.or_state(ActorState.IDLE)
                self.and_state(~ActorState.WALKING)
                self.and_state(~ActorState.JUMPING)
            else:
                self.or_state(ActorState.WALKING)
                self.and_state(~ActorState.JUMPING)
                self.and_state(~ActorState.IDLE)

        if self.vel.x < 0:
            self.or_state(ActorState.LEFT)
            self.and_state(~ActorState.RIGHT)
        elif self.vel.x > 0:
            self.or_state(ActorState.RIGHT)
            self.and_state(~ActorState.LEFT)
