import math
from color_utils import *
from effects.effects import DYNAMIC, STATIC, BaseEffect
import random
from effects.physics_effects import PhysicsBody

class RandChoice(BaseEffect):
    def __init__(self, effects) -> None:
        super().__init__()
        self.effects = effects
        self.effect = random.choice(self.effects)
        
    def tick(self, pixels, time_delta):
        self.effect.tick(pixels, time_delta)
        
    def clone(self):
        return RandChoice(self.effect)


class RandTime(BaseEffect):
    def __init__(self, effect, lower, upper) -> None:
        super().__init__()
        self.effect = effect
        self.lower = lower
        self.upper = upper
        self.time = random.random() * (upper - lower) + lower
        self.first_tick = True
    
    def tick(self, pixels, time_delta):
        if self.first_tick:
            self.effect.tick(pixels, time_delta + self.time)
            self.first_tick = False
        else:
            self.effect.tick(pixels, time_delta)
        
    def clone(self):
        return RandTime(self.effect, self.lower, self.upper)
        

class RandWarp(BaseEffect):
    def __init__(self, effect, lower, upper) -> None:
        super().__init__()
        self.effect = effect
        self.lower = lower
        self.upper = upper
        self.warp = random.random() * (upper - lower) + lower
        self.first_tick = True
    
    def tick(self, pixels, time_delta):
        self.effect.tick(pixels, time_delta * self.warp)
        
    def clone(self):
        return RandTime(self.effect, self.lower, self.upper)
    

class RandSelector(BaseEffect):
    def __init__(self, effect):
        super().__init__()
        self.effect = effect
        self.index = random.random()
        
    def tick(self, pixels, time_delta):
        colors = clone_pixels(pixels)
        self.effect.tick(colors, time_delta)
        
        N = len(pixels)
        fill_pixels(pixels, colors[int(N * self.index)])
    
    def clone(self):
        return RandSelector(self.effect)


class RandPBody(PhysicsBody):
    def __init__(self, min_pos, max_pos, min_vel=0, max_vel=0, min_acc=0, max_acc=0):
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
    
    def clone(self):
        return RandPBody(
            self.min_pos,
            self.max_pos,
            self.min_vel,
            self.max_vel,
            self.min_acc,
            self.max_acc
        )
        