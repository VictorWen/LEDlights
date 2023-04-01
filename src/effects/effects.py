from copy import deepcopy
import math
from .color_utils import *


STATIC = 'static'
DYNAMIC = 'dynamic'


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
    

def is_all_static(effects):
    for effect in effects:
        if effect.type != STATIC:
            return DYNAMIC
    return STATIC


class BaseEffect:
    def __init__(self, type=DYNAMIC):
        self.type = type

    def tick(self, pixels, time_delta):
        pass

    def clone(self):
        raise NotImplementedError(f"{self}.clone() is not implemented yet")


class ColorAdapter(BaseEffect):
    def __init__(self, color_selector):
        super().__init__(type=STATIC)
        self.color = color_selector

    def tick(self, pixels, time_delta):
        n = len(pixels)
        for i in range(n):
            pixels[i] = self.color.get_color(i/n)

    def clone(self):
        return ColorAdapter(self.color)
    

class AlphaAdapter(BaseEffect):
    def __init__(self, effect, alpha):
        super().__init__(effect.type)
        self.effect = effect
        self.alpha = alpha
        
    def tick(self, pixels, time_delta):
        self.effect.tick(pixels, time_delta)
        for i in range(len(pixels)):
            color = pixels[i]
            a = 1 if len(color) < 4 else color[3]
            pixels[i] = (
                int(color[0] / a * self.alpha), 
                int(color[1] / a * self.alpha), 
                int(color[2] / a * self.alpha), 
                self.alpha
            )
            
    def clone(self):
        return AlphaAdapter(self.effect.clone(), self.alpha)


class DynamicSplit(BaseEffect):
    def __init__(self, color_effects):
        super().__init__(is_all_static(color_effects))
        if isinstance(color_effects, list):
            self.effects = color_effects
        else:
            self.effects = [color_effects]
        self.n = len(self.effects)
        self.portion = 1/self.n
        self.cached = {}

    def tick(self, pixels, time_delta):
        N = len(pixels)

        left = 0
        right = 0
        for i in range(self.n):
            right += self.portion * N
            if self.effects[i].type != STATIC or i not in self.cached:
                color = clone_spliced_pixels(pixels, int(right - left), left)
                self.effects[i].tick(color, time_delta)
                if self.effects[i].type == STATIC: 
                    self.cached[i] = color
            else:
                color = self.cached[i]
            pixels[left:int(right)] = color
            left = int(right)

    def clone(self):
        effects = []
        for effect in self.effects:
            effects.append(effect.clone())
        return DynamicSplit(effects)


class DynamicGradient(BaseEffect):
    def __init__(self, color_effects, sampling_weights=-1):
        super().__init__(is_all_static(color_effects))
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
            
        self.cached = {}

    def tick(self, pixels, time_delta):
        N = len(pixels)

        colors, differences = self._get_gradient_rays(pixels, time_delta)

        n = len(colors)

        for i in range(N):
            value = i / (N-1)
            if n == 1:
                pixels[i] = colors[0]
            elif value == 0:
                pixels[i] = colors[0]
            else:
                value *= (n - 1)
                j = math.ceil(value) - 1
                pixels[i] = self._get_gradient(colors[j], differences[j], (value - j))
                
    def _get_gradient_rays(self, pixels, time_delta):
        N = len(pixels)
        colors = []
        differences = []
        for i in range(len(self.effects)):
            is_dynamic = self.effects[i].type != STATIC
            do_tick = is_dynamic or i not in self.cached
            if do_tick:
                color = clone_pixels(pixels)
                self.effects[i].tick(color, time_delta)
                if not is_dynamic:
                    self.cached[i] = []
            weight = self.weights[i]
            for j in range(weight):
                pixel = color[int(j/weight * N)] if do_tick else self.cached[i][j]
                if len(colors) > 0:
                    differences.append(self._difference(pixel, colors[-1]))
                colors.append(pixel)
                if not is_dynamic and do_tick:
                    self.cached[i].append(pixel)
        return colors, differences
    
    def _difference(self, color1, color2):
        alpha1 = 1 if len(color1) < 4 else color1[3]
        alpha2 = 1 if len(color2) < 4 else color2[3]
        return (
            int(color1[0] - color2[0]),
            int(color1[1] - color2[1]),
            int(color1[2] - color2[2]),
            alpha1 - alpha2
        )
        
    def _get_gradient(self, color, diff, value):
        alpha = 1 if len(color) < 4 else color[3]
        return (
            int(color[0] + value * diff[0]),
            int(color[1] + value * diff[1]),
            int(color[2] + value * diff[2]),
            alpha + value * diff[3]
        )

    def clone(self):
        effects = []
        for effect in self.effects:
            effects.append(effect.clone())
        return DynamicGradient(effects, self.weights)


class BlinkEffect(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__()
        self.color = color
        self.time_length = time_length
        self.timer = time_length
        self.colors = None

    def tick(self, pixels, time_delta):
        self.timer -= time_delta

        if self.colors is None or self.color.type != STATIC:
            self.colors = clone_pixels(pixels)
            self.color.tick(self.colors, time_delta)


        if (self.timer <= -self.time_length):
            self.timer = self.time_length

        if (self.timer <= 0):
            scalar_mult_fill(0, self.colors)
        elif (self.timer > 0):
            scalar_mult_fill(1, self.colors)

        set_pixels(pixels, self.colors)

    def clone(self):
        return BlinkEffect(self.color.clone(), self.time_length)


class ColorWipe(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.time_length = time_length
        self.time_sum = 0
        self.original = None
        self.colors = None

    def tick(self, pixels, time_delta):
        if self.original is None:
            self.original = clone_pixels(pixels)
        if self.colors is None or self.color.type != STATIC:
            self.colors = clone_pixels(self.original)
            self.color.tick(self.colors, time_delta)
        n = len(pixels)

        cutoff = self.time_sum / self.time_length * n
        self.time_sum += time_delta
        if (self.time_length > 0):
            for i in range(n):
                if cutoff >= i:
                    pixels[i] = self.colors[i]
                else:
                    pixels[i] = self.original[i]
        else:
            for i in range(-1, -(n + 1), -1):
                if cutoff - 1 <= i:
                    pixels[i] = self.colors[i]
                else:
                    pixels[i] = self.original[i]

    def clone(self):
        return ColorWipe(self.color.clone(), self.time_length)


class FadeIn(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.time_length = time_length
        self.time_sum = 0
        self.colors = None

    def tick(self, pixels, time_delta):
        if self.colors is None or self.color.type != STATIC:
            self.colors = clone_pixels(pixels)
            self.color.tick(self.colors, time_delta)

        self.time_sum += time_delta
        scalar_mult_fill(min(1, self.time_sum/self.time_length), self.colors)
        set_pixels(pixels, self.colors)

    def clone(self):
        return FadeIn(self.color.clone(), self.time_length)


class FadeOut(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.time_length = time_length
        self.time_sum = time_length
        self.colors = None

    def tick(self, pixels, time_delta):
        if self.colors is None or self.color.type != STATIC:
            self.colors = clone_pixels(pixels)
            self.color.tick(self.colors, time_delta)

        self.time_sum -= time_delta
        scalar_mult_fill(max(0, self.time_sum/self.time_length), self.colors)
        set_pixels(pixels, self.colors)

    def clone(self):
        return FadeOut(self.color.clone(), self.time_length)


class BlinkFade(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.time_length = time_length
        self.time_sum = 0
        self.colors = None

    def tick(self, pixels, time_delta):
        if self.colors is None or self.color.type != STATIC:
            self.colors = clone_pixels(pixels)
            self.color.tick(self.colors, time_delta)

        self.time_sum += time_delta
        scalar_mult_fill(
            (math.sin(self.time_sum/self.time_length * math.pi) + 1) / 2, self.colors)
        set_pixels(pixels, self.colors)

    def clone(self):
        return BlinkFade(self.color.clone(), self.time_length)


class WaveEffect(BaseEffect):
    def __init__(self, color, period, wavelength):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.period = period
        self.wavelength = wavelength

        self.time_sum = 0
        self.colors = None

    def tick(self, pixels, time_delta):
        if self.colors is None or self.color.type != STATIC:
            self.colors = clone_pixels(pixels)
            self.color.tick(self.colors, time_delta)

        self.time_sum += time_delta
        n = len(self.colors)
        for i in range(n):
            phase = (i/self.wavelength - self.time_sum /
                     self.period) * 2 * math.pi
            value = (1 + math.sin(phase)) / 2
            pixels[i] = self.colors[int(value * (n - 1))]

    def clone(self):
        return WaveEffect(self.color.clone(), self.period, self.wavelength)


class WheelEffect(BaseEffect):
    def __init__(self, color, period):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.period = period

        self.time_sum = 0
        self.colors = None

    def tick(self, pixels, time_delta):
        if self.colors is None or self.color.type != STATIC:
            self.colors = clone_pixels(pixels)
            self.color.tick(self.colors, time_delta)

        self.time_sum += time_delta
        phase = (self.time_sum/self.period) * 2 * math.pi
        value = (1 + math.sin(phase)) / 2

        n = len(self.colors)
        for i in range(n):
            pixels[i] = self.colors[int(value * (n - 1))]

    def clone(self):
        return WheelEffect(self.color.clone(), self.period)


class WipeEffect(BaseEffect):
    def __init__(self, color, period):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.period = period

        self.time_sum = 0
        self.colors = None

    def tick(self, pixels, time_delta):
        n = len(pixels)
        if self.colors is None or self.color.type != STATIC:
            self.colors = clone_pixels(pixels)
            self.color.tick(self.colors, time_delta)

        self.time_sum += time_delta
        offset = int((self.time_sum / self.period) * n)
        for i in range(n):
            pixels[i] = self.colors[offset % n]

    def clone(self):
        return WipeEffect(self.color.clone(), self.period)


class SlidingEffect(BaseEffect):
    def __init__(self, color, period):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.period = period

        self.time_sum = 0
        self.colors = None

    def tick(self, pixels, time_delta):
        n = len(pixels)
        if self.colors is None or self.color.type != STATIC:
            self.colors = clone_pixels(pixels)
            self.color.tick(self.colors, time_delta)

        self.time_sum += time_delta
        offset = int((self.time_sum / self.period) * n)
        for i in range(n):
            pixels[i] = self.colors[(i - offset) % n]

    def clone(self):
        return SlidingEffect(self.color.clone(), self.period)
