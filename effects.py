import math
from colors import ColorSelector

STATIC = 'static'
DYNAMIC = 'dynamic'

def gradient(color1, color2, value):
    return tuple(int(color1[i] + (color2[i] - color1[i]) * value) for i in range(3))

def rainbow(value):
    value *= 3
    if (value % 3 < 1):
        return (int(255 * (1 - (value % 1))), int(255 * (value % 1)), 0)
    elif (value % 3 < 2):
        return (0, int(255 * (2 - value)), int(255 * (value - 1)))
    elif (value % 3 < 3):
        return (int(255 * (value - 2)), 0, int(255 * (3 - value)))

def RGB(value):
    value *= 2
    if (value == 2):
        return (0, 0, 255)
    elif (value % 2 < 1):
        return (int(255 * (1 - (value % 1))), int(255 * (value % 1)), 0)
    elif (value % 2 < 2):
        return (0, int(255 * (2 - value)), int(255 * (value - 1)))

def fill_select(pixels, selector):
    n = len(pixels)
    for i in range(n):
        pixels[i] = selector.get_color(i/n)
    pixels.show()


def clone_pixels(pixels):
    return list(pixels[i] for i in range(len(pixels)))


def set_pixels(pixels, colors):
    for i in range(len(pixels)):
        pixels[i] = colors[i]


def scalar_mult(scalar, color):
    return tuple(int(scalar * color[i]) for i in range(3))


def scalar_mult_fill(scalar, pixels):
    for i in range(len(pixels)):
        pixels[i] = scalar_mult(scalar, pixels[i])


class BaseEffect:
    def __init__(self, type=DYNAMIC):
        self.type = type

    def tick(self, pixels, time_delta):
        pass


class ColorAdapter(BaseEffect):
    def __init__(self, color_selector):
        super().__init__(type=STATIC)
        self.color = color_selector

    def tick(self, pixels, time_delta):
        n = len(pixels)
        for i in range(n):
            pixels[i] = self.color.get_color(i/n)


class FillEffect(BaseEffect):
    def __init__(self, color_effect):
        super().__init__(type=STATIC)
        self.color = color_effect
    
    def tick(self, pixels, time_delta):
        self.color.tick(pixels, time_delta)


class BlinkEffect(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__()
        self.color = color
        self.time_length = time_length
        self.timer = time_length
    
    def tick(self, pixels, time_delta):
        self.timer -= time_delta
        
        colors = clone_pixels(pixels)
        self.color.tick(colors, time_delta)
        
        if (self.timer <= -self.time_length):
            self.timer = self.time_length
        
        if (self.timer <= 0):
            scalar_mult_fill(0, colors)
        elif (self.timer > 0):
            scalar_mult_fill(1, colors)

        set_pixels(pixels, colors)


class ColorWipe(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.time_length = time_length
        self.time_sum = 0

    def tick(self, pixels, time_delta):
        colors = clone_pixels(pixels)
        self.color.tick(colors, time_delta)
        
        n = len(pixels)
        
        i = 0
        self.time_sum += time_delta
        while (self.time_sum / self.time_length * n >= i and i < n):
            pixels[i] = colors[i]
            i += 1
        

class FadeIn(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.time_length = time_length
        self.time_sum = 0
    
    def tick(self, pixels, time_delta):
        self.time_sum += time_delta
        n = len(pixels)
        for i in range(n):
            color = self.color.get_color(i/n)
            color = tuple(int(color[j] * min(1, self.time_sum/self.time_length)) for j in range(3))
            pixels[i] = color


class FadeOut(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.time_length = time_length
        self.time_sum = time_length
    
    def tick(self, pixels, time_delta):
        self.time_sum -= time_delta
        n = len(pixels)
        for i in range(n):
            color = self.color.get_color(i/n)
            color = tuple(int(color[j] * max(0, self.time_sum/self.time_length)) for j in range(3))
            pixels[i] = color


class BlinkFade(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.time_length = time_length
        self.time_sum = 0
    
    def tick(self, pixels, time_delta):
        self.time_sum += time_delta
        n = len(pixels)
        for i in range(n):
            color = self.color.get_color(i/n)
            color = tuple(int(color[j] * (math.cos(self.time_sum/self.time_length * math.pi) + 1) / 2) for j in range(3))
            pixels[i] = color


class Wave(BaseEffect):
    def __init__(self, color1, color2, time_length, length):
        super().__init__(type=DYNAMIC)
        self.color1 = color1
        self.color2 = color2
        self.time_length = time_length
        self.length = length
        self.time_sum = 0
        self.color_diff = tuple(color2[i] - color1[i] for i in range(3))
    
    def tick(self, pixels, time_delta):
        self.time_sum += time_delta
        for i in range(len(pixels)):
            value = (math.cos((i / self.length - self.time_sum/self.time_length) * math.pi) + 1) / 2
            color = tuple(int(self.color1[j] + value * self.color_diff[j]) for j in range(3))
            pixels[i] = color


class RainbowWave(BaseEffect):
    def __init__(self, time_length, length):
        super().__init__(type=DYNAMIC)
        self.time_length = time_length
        self.length = length
        self.time_sum = 0

    def tick(self, pixels, time_delta):
        self.time_sum += time_delta
        for i in range(len(pixels)):
            value = (math.cos((i / self.length - self.time_sum/self.time_length) * math.pi) + 1) / 2
            color = rainbow(value)
            pixels[i] = color
