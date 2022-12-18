import math
from color_utils import *
from effects.effects import DYNAMIC, STATIC, BaseEffect
import random
from effects.physics_effects import PhysicsBody

class RandChoice(BaseEffect):
    def __init__(self, effects, rerolls=-1) -> None:
        super().__init__(effect.type)
        self.effects = effects
        self.rerolls = rerolls
        self.effect = random.choice(self.effects)
        
    def tick(self, pixels, time_delta):
        self.effect.tick(pixels, time_delta)
        
    def clone(self):
        if self.rerolls != 0:
            return RandChoice(self.effects.copy(), self.rerolls - 1)
        else:
            return self.effect.copy()


class RandTime(BaseEffect):
    def __init__(self, effect, lower, upper, rerolls=-1) -> None:
        super().__init__(effect.type)
        self.effect = effect
        self.lower = lower
        self.upper = upper
        self.time = random.random() * (upper - lower) + lower
        self.first_tick = True
        self.rerolls = rerolls
    
    def tick(self, pixels, time_delta):
        if self.first_tick:
            self.effect.tick(pixels, time_delta + self.time)
            self.first_tick = False
        else:
            self.effect.tick(pixels, time_delta)
        
    def clone(self):
        if self.rerolls != 0:
            return RandTime(self.effect.clone(), self.lower, self.upper, self.rerolls - 1)
        else:
            copy = RandTime(self.effect.clone(), self.lower, self.upper)
            copy.time = self.time
            return copy
        

class RandWarp(BaseEffect):
    def __init__(self, effect, lower, upper, rerolls=-1) -> None:
        super().__init__(effect.type)
        self.effect = effect
        self.lower = lower
        self.upper = upper
        self.warp = random.random() * (upper - lower) + lower
        self.rerolls = rerolls
    
    def tick(self, pixels, time_delta):
        self.effect.tick(pixels, time_delta * self.warp)
        
    def clone(self):
        if self.rerolls != 0:
            return RandWarp(self.effect.clone(), self.lower, self.upper, self.rerolls - 1)
        else:
            copy = RandWarp(self.effect.clone(), self.lower, self.upper)
            copy.warp = self.warp
            return copy
    

class RandSelector(BaseEffect):
    def __init__(self, effect, rerolls=-1):
        super().__init__(effect.type)
        self.effect = effect
        self.index = random.random()
        self.rerolls = rerolls
        self.color = None
        
    def tick(self, pixels, time_delta):
        if self.color is None or self.effect.type == DYNAMIC:
            colors = clone_pixels(pixels)
            self.effect.tick(colors, time_delta)
            N = len(pixels)
            self.color = colors[int(N * self.index)]
        
        fill_pixels(pixels, self.color)
    
    def clone(self):
        if self.rerolls != 0:
            return RandSelector(self.effect.clone(), self.rerolls - 1)
        else:
            copy = RandSelector(self.effect.clone(), 0)
            copy.index = self.index
            return copy


class RandPBody(PhysicsBody):
    def __init__(self, min_pos, max_pos, min_vel=0, max_vel=0, min_acc=0, max_acc=0, rerolls=-1):
        super().__init__(
            random.random() * (max_pos - min_pos) + min_pos,
            random.random() * (max_vel - min_vel) + min_vel,
            random.random() * (max_acc - min_acc) + min_acc
        )
        self.min_pos = min_pos
        self.max_pos = max_pos
        self.min_vel = min_vel
        self.max_vel = max_vel
        self.min_acc = min_acc
        self.max_acc = max_acc
        self.rerolls = rerolls
    
    def clone(self):
        if self.rerolls != 0:
            return RandPBody(
                self.min_pos,
                self.max_pos,
                self.min_vel,
                self.max_vel,
                self.min_acc,
                self.max_acc,
                self.rerolls - 1
            )
        else:
            return PhysicsBody(self.position, self.velocity, self.acceleration)
        