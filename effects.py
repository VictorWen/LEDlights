import math
from color_utils import *


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


class DynamicSplit(BaseEffect):
    def __init__(self, color_effects):
        super().__init__()
        if isinstance(color_effects, list):
            self.effects = color_effects
        else:
            self.effects = [color_effects]
        self.n = len(self.effects)
        self.portion = 1/self.n
    
    def tick(self, pixels, time_delta):
        N = len(pixels)

        colors = []
        for i in range(self.n):
            color = clone_pixels(pixels)
            self.effects[i].tick(color, time_delta)
            colors.append(color)

        for i in range(N):
            value = i / N
            if value == 0:
                pixels[i] = colors[0][i]
            else:
                check = 1 - self.portion
                j = self.n - 1
                while value <= check:
                    check -= self.portion
                    j -= 1
                pixels[i] =  colors[j][i]


class DynamicGradient(BaseEffect):
    def __init__(self, color_effects, sampling_weights=-1):
        super().__init__()
        if isinstance(color_effects, list):
            self.effects = color_effects
        else:
            self.effects = [color_effects]
        
        if sampling_weights == -1:
            self.weights = [1 for effect in self.effects]
        elif isinstance(sampling_weights, list):
            self.weights = sampling_weights
        else:
            self.weights = [sampling_weights]
    
    def tick(self, pixels, time_delta):
        N = len(pixels)

        colors = []
        differences = []
        for i in range(len(self.effects)):
            color = clone_pixels(pixels)
            self.effects[i].tick(color, time_delta)
            weight = self.weights[i]
            for j in range(weight):
                pixel = color[int(j/weight * N)]
                if len(colors) > 0:
                    differences.append(tuple(int(pixel[j] - colors[-1][j]) for j in range(3)))
                colors.append(pixel)

        n = len(colors)

        for i in range(N):
            value = i / N
            if n == 1:
                pixels[i] = colors[0]
            elif value == 0:
                pixels[i] = colors[0]
            else:
                value *= (n - 1)
                j = n - 1
                while value <= j:
                    j -= 1
                pixels[i] = tuple(int(colors[j][k] + (value - j) * differences[j][k]) for k in range(3))
        


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
        if (self.time_length > 0):
            for i in range(n):
                if cutoff >= i:
                    pixels[i] = colors[i]
                else:
                    pixels[i] = self.original[i]
        else:
            for i in range(-1, -(n + 1), -1):
                if cutoff - 1 <= i:
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
        scalar_mult_fill((math.sin(self.time_sum/self.time_length * math.pi) + 1) / 2, colors)
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
            value = (1 + math.sin(phase)) / 2
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
        value = (1 + math.sin(phase)) / 2
        
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
        colors = clone_pixels(pixels)
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
            value = (math.sin((i / self.length - self.time_sum/self.time_length) * math.pi) + 1) / 2
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
            value = (math.sin((i / self.length - self.time_sum/self.time_length) * math.pi) + 1) / 2
            color = rainbow(value)
            pixels[i] = color
