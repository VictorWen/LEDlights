import math
from .color_utils import *
from .effects import BaseEffect, DYNAMIC


class CropEffect(BaseEffect):
    def __init__(self, effect, size, offset=0):
        super().__init__(effect.type)
        self.effect = effect
        self.size = size
        self.offset = offset

    def tick(self, pixels, time_delta):
        colors = clone_spliced_pixels(pixels, self.size, self.offset)
        self.effect.tick(colors, time_delta)

        N = len(pixels)
        for i in range(0, self.size):
            pixels[(i + self.offset) % N] = colors[i]
    
    def clone(self):
        return CropEffect(self.effect.clone(), self.size, self.offset)
    

class ResizeEffect(BaseEffect):
    def __init__(self, effect, size):
        super().__init__(effect.type)
        self.effect = effect
        self.size = size
        self.colors = None
    
    def tick(self, pixels, time_delta):
        N = len(pixels)
        ratio = (N - 1) / (self.size - 1)
        
        if self.colors is None or self.effect.type == DYNAMIC:
            self.colors = resize_clone(pixels, self.size)
            self.effect.tick(self.colors, time_delta)
        
        for i in range(N):
            pixels[i] = self.colors[int(i / ratio)]
            
    def clone(self):
        return ResizeEffect(self.effect.clone(), self.size)
