import math
from color_utils import *
from effects.effects import BaseEffect


class SizeEffect(BaseEffect):
    def __init__(self, effect, size, offset=0):
        super().__init__()
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
        return SizeEffect(self.effect, self.size, self.offset)
