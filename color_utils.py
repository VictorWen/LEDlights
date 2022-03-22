def clone_pixels(pixels):
    return list(tuple(pixels[i]) for i in range(len(pixels)))

def set_pixels(pixels, colors):
    for i in range(len(pixels)):
        pixels[i] = colors[i]

def scalar_mult(scalar, color):
    return tuple(int(scalar * color[i]) for i in range(3))

def scalar_mult_fill(scalar, pixels):
    for i in range(len(pixels)):
        pixels[i] = scalar_mult(scalar, pixels[i])

def add_colors(color1, color2):
    return tuple(int(min(255, max(0, color1[i] + color2[i]))) for i in range(3))

def blend_colors(color1, color2):
    return tuple(int(min(255, max(0, (color1[i] + color2[i]) / 2))) for i in range(3))

def multiply_colors(color1, color2):
    return tuple(int(min(255, max(0, color1[i] * color2[i] / 255))) for i in range(3))