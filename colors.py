class ColorSelector:
    def get_color(self, value):
        pass

class SingleColorSelector(ColorSelector):
    def __init__(self, color) -> None:
        super().__init__()
        self.color = color
    
    def get_color(self, value):
        return self.color


class SplitColorSelector(ColorSelector):
    def __init__(self, color1, color2):
        super().__init__()
        self.color1 = color1
        self.color2 = color2

    def get_color(self, value):
        if value > 0.5:
            return self.color2
        else:
            return self.color1


class Split3ColorSelector(ColorSelector):
    def __init__(self, color1, color2, color3):
        super().__init__()
        self.color1 = color1
        self.color2 = color2
        self.color3 = color3

    def get_color(self, value):
        if value > 0.677:
            return self.color3
        elif value > 0.333:
            return self.color2
        else:
            return self.color1


class NSplitColorSelector(ColorSelector):
    def __init__(self, colors):
        super().__init__()
        self.colors = colors
        self.N = len(colors)
        self.portion = 1.0 / self.N

    def get_color(self, value):
        if value == 0:
            return self.colors[0]
        
        check = 1 - self.portion
        i = self.N - 1
        while value <= check:
            check -= self.portion
            i -= 1
        return self.colors[i]
        

class GradientColorSelector(ColorSelector):
    def __init__(self, color1, color2) -> None:
        super().__init__()
        self.color1 = color1
        self.color2 = color2
        self.difference = tuple(int(color2[i] - color1[i]) for i in range(3))
    
    def get_color(self, value):
        return tuple(int(self.color1[i] + value * self.difference[i]) for i in range(3))


class Gradient3ColorSelector(ColorSelector):
    def __init__(self, color1, color2, color3) -> None:
        super().__init__()
        self.color1 = color1
        self.color2 = color2
        self.color3 = color3
        self.difference1 = tuple(int(color2[i] - color1[i]) for i in range(3))
        self.difference2 = tuple(int(color3[i] - color2[i]) for i in range(3))
    
    def get_color(self, value):
        value *= 2
        if value > 1:
            return tuple(int(self.color2[i] + (value - 1) * self.difference2[i]) for i in range(3))
        else:
            return tuple(int(self.color1[i] + value * self.difference1[i]) for i in range(3))


class NGradientColorSelector(ColorSelector):
    def __init__(self, colors):
        super().__init__()
        self.colors = colors
        self.differences = []
        self.N = len(colors)
        for i in range(self.N - 1):
            self.differences.append(tuple(int(colors[i+1][j] - colors[i][j]) for j in range(3)))
        
    def get_color(self, value):
        if self.N == 1:
            return self.colors[0]
        if value == 0:
            return self.colors[0]
        
        value *= (self.N - 1)
        i = self.N - 1
        while value <= i:
            i -= 1
        return tuple(int(self.colors[i][j] + (value - i) * self.differences[i][j]) for j in range(3))


class RGBColorSelector(ColorSelector):
    def __init__(self) -> None:
        super().__init__()

    def get_color(self, value):
        value *= 2
        if (value == 2):
            return (0, 0, 255)
        elif (value % 2 < 1):
            return (int(255 * (1 - (value % 1))), int(255 * (value % 1)), 0)
        elif (value % 2 < 2):
            return (0, int(255 * (2 - value)), int(255 * (value - 1)))


class RainbowColorSelector(ColorSelector):
    def __init__(self) -> None:
        super().__init__()

    def get_color(self, value):
        value *= 3
        if (value % 3 < 1):
            return (int(255 * (1 - value)), int(255 * value), 0)
        elif (value % 3 < 2):
            return (0, int(255 * (2 - value)), int(255 * (value - 1)))
        elif (value % 3 < 3):
            return (int(255 * (value - 2)), 0, int(255 * (3 - value)))