import time
import numpy as np

def clone_pixels(pixels):
    return list(tuple(pixels[i]) for i in range(len(pixels)))


def clone_spliced_pixels(pixels, size, offset):
    return list(tuple(pixels[i % len(pixels)]) for i in range(offset, offset+size))


def resize_clone(pixels, size):
    N = len(pixels)
    return list(tuple(pixels[int(i/(size-1)*(N-1))]) for i in range(size))


def set_pixels(pixels, colors):
    for i in range(len(pixels)):
        pixels[i] = colors[i]


def fill_pixels(pixels, color):
    for i in range(len(pixels)):
        pixels[i] = color


def clamp(val, a=0, b=255):
    return min(max(val, a), b)
    

def scalar_mult(scalar, color, scale_alpha=True):
    alpha = 1 if len(color) < 4 else color[3]
    return (
        clamp(int(scalar * color[0])), 
        clamp(int(scalar * color[1])), 
        clamp(int(scalar * color[2])), 
        clamp(scalar * alpha if scale_alpha else alpha, b=1))


def scalar_mult_fill(scalar, pixels):
    for i in range(len(pixels)):
        pixels[i] = scalar_mult(scalar, pixels[i])


def overlay_colors(color1, color2):
    N1 = len(color1)
    N2 = len(color2)
    if N2 < 4:
        return color2
    a1 = 1 if N1 < 4 else color1[3]
    a2 = color2[3]
    a3 = a1 * (1 - a2)
    
    alpha = a2 + a3
    return (
        clamp(int(a2 * color2[0] + a3 * color1[0])),
        clamp(int(a2 * color2[1] + a3 * color1[1])),
        clamp(int(a2 * color2[2] + a3 * color1[2])),
        clamp(alpha, 0, 1)
    )


def add_colors(color1, color2):
    alpha1 = 1 if len(color1) < 4 else color1[3]
    alpha2 = 1 if len(color2) < 4 else color2[3]
    return (
        clamp(int(color1[0] + color2[0])),
        clamp(int(color1[1] + color2[1])),
        clamp(int(color1[2] + color2[2])),
        clamp(alpha1 + alpha2, 0, 1)
    )


def blend_colors(color1, color2):
    alpha1 = 1 if len(color1) < 4 else color1[3]
    alpha2 = 1 if len(color2) < 4 else color2[3]
    return (
        clamp(int((color1[0] + color2[0]) / 2)),
        clamp(int((color1[1] + color2[1]) / 2)),
        clamp(int((color1[2] + color2[2]) / 2)),
        clamp((alpha1 + alpha2) / 2, 0, 1)
    )


def multiply_colors(color1, color2):
    alpha1 = 1 if len(color1) < 4 else color1[3]
    alpha2 = 1 if len(color2) < 4 else color2[3]
    return(
        clamp(int(color1[0] * color2[0] / 255)),
        clamp(int(color1[1] * color2[1] / 255)),
        clamp(int(color1[2] * color2[2] / 255)),
        clamp(alpha1 * alpha2, 0, 1)
    )
