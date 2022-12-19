class ColorSelector:
    def get_color(self, value):
        pass


class SingleColorSelector(ColorSelector):
    def __init__(self, color) -> None:
        super().__init__()
        self.color = color
    
    def get_color(self, value):
        return self.color


class RainbowColorSelector(ColorSelector):
    def __init__(self) -> None:
        super().__init__()

    def get_color(self, value):
        value *= 3
        if (value % 3 < 1):
            return (int(255 * (1 - value)), int(255 * value), 0, 1)
        elif (value % 3 < 2):
            return (0, int(255 * (2 - value)), int(255 * (value - 1)), 1)
        elif (value % 3 < 3):
            return (int(255 * (value - 2)), 0, int(255 * (3 - value)), 1)