import math

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


class FillEffect(BaseEffect):
    def __init__(self, color_selector):
        super().__init__(type=STATIC)
        self.color = color_selector
    
    def tick(self, pixels, time_delta):
        fill_select(pixels, self.color)


class BlinkEffect(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__()
        self.color = color
        self.time_length = time_length
        self.timer = time_length
    
    def tick(self, pixels, time_delta):
        self.timer -= time_delta
        if (self.timer <= 0):
            pixels.fill((0, 0, 0))
        if (self.timer <= -self.time_length):
            self.timer = self.time_length
            fill_select(pixels, self.color)
        pixels.show()


class ColorWipe(BaseEffect):
    def __init__(self, color, time_length):
        super().__init__(type=DYNAMIC)
        self.color = color
        self.time_length = time_length
        self.index = 0
        self.time_sum = 0

    def tick(self, pixels, time_delta):
        n = len(pixels)
        if (self.index >= n):
            return
        self.time_sum += time_delta
        while (self.time_sum / self.time_length * n >= self.index and self.index < n):
            pixels[self.index] = self.color.get_color(self.index/n)
            self.index += 1
            pixels.show()
        

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
        pixels.show()

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
        pixels.show()

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
        pixels.show()

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
        pixels.show()

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
        pixels.show()