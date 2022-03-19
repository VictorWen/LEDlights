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
        self.original = None

    def tick(self, pixels, time_delta):
        if self.original is None:
            self.original = clone_pixels(pixels)
        colors = clone_pixels(self.original)
        self.color.tick(colors, time_delta)
        n = len(pixels)
        
        cutoff = self.time_sum / self.time_length * n
        self.time_sum += time_delta
        for i in range(n):
            if cutoff >= i:
                pixels[i] = colors[i]
            else:
                pixels[i] = self.original[i]
        

class FadeIn(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.time_length = time_length
        self.time_sum = 0
    
    def tick(self, pixels, time_delta):
        colors = clone_pixels(pixels)
        self.color.tick(colors, time_delta)
        
        self.time_sum += time_delta
        scalar_mult_fill(min(1, self.time_sum/self.time_length), colors)
        set_pixels(pixels, colors)


class FadeOut(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.time_length = time_length
        self.time_sum = time_length
    
    def tick(self, pixels, time_delta):
        colors = clone_pixels(pixels)
        self.color.tick(colors, time_delta)
        
        self.time_sum -= time_delta
        scalar_mult_fill(max(0, self.time_sum/self.time_length), colors)
        set_pixels(pixels, colors)


class BlinkFade(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.time_length = time_length
        self.time_sum = 0
    
    def tick(self, pixels, time_delta):
        colors = clone_pixels(pixels)
        self.color.tick(colors, time_delta)
        
        self.time_sum += time_delta
        scalar_mult_fill((math.cos(self.time_sum/self.time_length * math.pi) + 1) / 2, colors)
        set_pixels(pixels, colors)


class WaveEffect(BaseEffect):
    def __init__(self, color, period, wavelength):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.period = period
        self.wavelength = wavelength
        
        self.time_sum = 0

    def tick(self, pixels, time_delta):
        colors = clone_pixels(pixels)
        self.color.tick(colors, time_delta)

        self.time_sum += time_delta
        n = len(colors)
        for i in range(n):
            phase = (i/self.wavelength - self.time_sum/self.period) * 2 * math.pi
            value = (1 + math.cos(phase)) / 2
            pixels[i] = colors[int(value * (n - 1))]


class WheelEffect(BaseEffect):
    def __init__(self, color, period):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.period = period
        
        self.time_sum = 0

    def tick(self, pixels, time_delta):
        colors = clone_pixels(pixels)
        self.color.tick(colors, time_delta)

        self.time_sum += time_delta
        phase = (self.time_sum/self.period) * 2 * math.pi
        value = (1 + math.cos(phase)) / 2
        
        n = len(colors)
        for i in range(n):
            pixels[i] = colors[int(value * (n - 1))]


class WipeEffect(BaseEffect):
    def __init__(self, color, period):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.period = period

        self.time_sum = 0

    def tick(self, pixels, time_delta):
        n = len(pixels)
        prev_offset = int((self.time_sum / self.period) * n)
        colors = [pixels[prev_offset % n] for i in range(n)]
        self.color.tick(colors, time_delta)
        
        self.time_sum += time_delta
        offset = int((self.time_sum / self.period) * n)
        for i in range(n):
            pixels[i] = colors[offset % n]


class SlidingEffect(BaseEffect):
    def __init__(self, color, period):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.period = period

        self.time_sum = 0

    def tick(self, pixels, time_delta):
        n = len(pixels)
        # prev_offset = int((self.time_sum / self.period) * n)
        # colors = [pixels[(i + prev_offset) % n] for i in range(n)]
        colors = clone_pixels(pixels)
        self.color.tick(colors, time_delta)
        
        self.time_sum += time_delta
        offset = int((self.time_sum / self.period) * n)
        for i in range(n):
            pixels[i] = colors[(i - offset) % n]


class FadeEffect(BaseEffect):
    def __init__(self, color, period):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.period = period

        self.time_sum = 0

    def tick(self, pixels, time_delta):
        n = len(pixels)
        prev_offset = int((self.time_sum / self.period) * n)
        colors = [pixels[(i + prev_offset) % n] for i in range(n)]
        self.color.tick(colors, time_delta)
        
        self.time_sum += time_delta
        offset = int((self.time_sum / self.period) * n)
        for i in range(n):
            pixels[i] = colors[(i - offset) % n]


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
