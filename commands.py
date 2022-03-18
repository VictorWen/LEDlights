from effects import *
from colors import *
from fft_effect import FFTEffect
import asyncio
from neopixel_controller import *
import board
import neopixel

colors = {
    "RED": (255, 0 ,0),
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
    "YELLOW" : (255, 255, 0),
    "CYAN": (0, 255, 255),
    "PURPLE": (255, 0, 255),
    "VIOLET": (255, 0, 255),
    "WHITE": (255, 255, 255),
    "PINK": (255, 64, 64),
    "ORANGE": (255, 64, 0),
    "MAGENTA": (255, 0, 64),
    "LIGHT_GREEN": (64, 255, 64),
    "LIME": (64, 255, 0),
    "AQUAMARINE": (0, 255, 64),
    "AQUA": (0, 64, 255),
    "INDIGO": (64, 0, 255),
    "LIGHT_BLUE": (64, 64, 255),
    "CLEAR": (0, 0, 0),
}

def hexstring_to_rgb(hex):
    hex = hex.strip('#')
    try:
        return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
    except:
        return None

def parse_rgb_color(r, g, b):
    try:
        r = int(r)
        g = int(g)
        b = int(b)
        if (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            return (r, g, b)
    except:
        pass    
    return None

def parse_time(time):
    try:
        time = float(time)
        if time != 0:
            return time
    except:
        pass
    return None

def fullparse_color(state, nargs, args):
    flag = args[1]
    if flag == '-RAINBOW':
        color = RainbowColorSelector()
    elif flag == '-GRAD-RGB':
        if (nargs < 4):
            state.send(f'Format: {args[0]} -GRAD-RGB HEX1 HEX2')
            return None
        rgb1 = hexstring_to_rgb(args[2])
        if (rgb1 is None):
            state.send(f"Error: {args[2]} is not a valid hex color")
            return None
        rgb2 = hexstring_to_rgb(args[3])
        if (rgb2 is None):
            state.send(f"Error: {args[3]} is not a valid hex color")
            return None
        color = GradientColorSelector(rgb1, rgb2)
    elif flag == '-GRAD':
        if (nargs < 4):
            state.send(f"Format: {args[0]} -GRAD COLOR1 COLOR2")
            return None
        if (args[2] not in colors):
            state.send(f"Error: {args[2]} is not a valid COLOR")
            return None
        if (args[3] not in colors):
            state.send(f"Error: {args[3]} is not a valid COLOR")
            return None
        color = GradientColorSelector(colors[args[2]], colors[args[3]])
    elif flag == '-RGB':
        if (nargs >= 5):
            rgb = parse_rgb_color(args[2], args[3], args[4])
            if (rgb is None):
                state.send(f"Error: ({args[2]}, {args[3]}, {args[4]}) is not a valid RGB Color")
                return None
            color = SingleColorSelector(rgb)
        elif (nargs >= 3):
            rgb = hexstring_to_rgb(args[2])
            if (rgb is None):
                state.send(f"Error: {args[2]} is not a valid hex color")
                return None
            color = SingleColorSelector(rgb)
        else:
            state.send(f"Formats: \n\t{args[0]} -RGB R G B\n\t{args[0]} -RGB HEX")
            return None
    else:
        if (args[1] not in colors):
            state.send(f"Error: {args[1]} is not a valid COLOR")
            return None
        color = SingleColorSelector(colors[args[1]])

    return color

def parse_color_time_args(state, nargs, args):
    if (nargs == 5):
        try: 
            color = (int(args[1]), int(args[2]), int(args[3]))
        except: 
            state.send("Invalid RGB COLOR")
            return None, None
        time = args[4]
    elif (nargs == 3):
        if (args[1] not in colors):
            color = hexstring_to_rgb(args[1])
            if (color is None):
                state.send("Invalid COLOR")
                return None, None
        else:
            color = colors[args[1]]
        time = args[2]
    else:
        state.send(f"Format: {args[0]} R G B Time, or {args[0]} COLOR Time")
        return None, None
    try: time = float(time)
    except:
        state.send("Invalid Time")
        return None, None
    
    return color, time

class State:
    def __init__(self, controller, pixels, send=print):
        self.controller = controller
        self.pixels = pixels
        self.send = send

def fill(state, nargs, args):
    if (nargs < 2):
        state.send(f"""Formats:
    {args[0]} COLOR
    {args[0]} -RGB R G B
    {args[0]} -RGB HEX
    {args[0]} -GRAD COLOR1 COLOR2
    {args[0]} -GRAD-RGB HEX1 HEX2
    {args[0]} -RAINBOW""")
        return
    
    color = fullparse_color(state, nargs, args)
    if (color is None):
        return

    state.controller.set_effect(FillEffect(color))


def blink(state, nargs, args):
    if (nargs < 3):
        state.send(f"""Formats:
    {args[0]} COLOR TIME
    {args[0]} -RGB R G B TIME
    {args[0]} -RGB HEX TIME
    {args[0]} -GRAD COLOR1 COLOR2 TIME
    {args[0]} -GRAD-RGB HEX1 HEX2 TIME
    {args[0]} -RAINBOW TIME""")
        return

    color = fullparse_color(state, nargs, args)
    if (color is None):
        return
    
    time = parse_time(args[-1])
    if (time is None):
        state.send(f'Error {args[-1]} is not a valid time')
        return
    
    state.controller.set_effect(BlinkEffect(color, time))

def color_wipe(state, nargs, args):
    if (nargs < 3):
        state.send(f"""Formats:
    {args[0]} COLOR TIME
    {args[0]} -RGB R G B TIME
    {args[0]} -RGB HEX TIME
    {args[0]} -GRAD COLOR1 COLOR2 TIME
    {args[0]} -GRAD-RGB HEX1 HEX2 TIME
    {args[0]} -RAINBOW TIME""")
        return

    color = fullparse_color(state, nargs, args)
    if (color is None):
        return
    
    time = parse_time(args[-1])
    if (time is None):
        state.send(f'Error {args[-1]} is not a valid time')
        return
    
    state.controller.set_effect(ColorWipe(color, time))

def fade_in(state, nargs, args):
    if (nargs < 3):
        state.send(f"""Formats:
    {args[0]} COLOR TIME
    {args[0]} -RGB R G B TIME
    {args[0]} -RGB HEX TIME
    {args[0]} -GRAD COLOR1 COLOR2 TIME
    {args[0]} -GRAD-RGB HEX1 HEX2 TIME
    {args[0]} -RAINBOW TIME""")
        return

    color = fullparse_color(state, nargs, args)
    if (color is None):
        return
    
    time = parse_time(args[-1])
    if (time is None):
        state.send(f'Error {args[-1]} is not a valid time')
        return
    state.controller.set_effect(FadeIn(color, time))

def fade_out(state, nargs, args):
    if (nargs < 3):
        state.send(f"""Formats:
    {args[0]} COLOR TIME
    {args[0]} -RGB R G B TIME
    {args[0]} -RGB HEX TIME
    {args[0]} -GRAD COLOR1 COLOR2 TIME
    {args[0]} -GRAD-RGB HEX1 HEX2 TIME
    {args[0]} -RAINBOW TIME""")
        return

    color = fullparse_color(state, nargs, args)
    if (color is None):
        return
    
    time = parse_time(args[-1])
    if (time is None):
        state.send(f'Error {args[-1]} is not a valid time')
        return
    state.controller.set_effect(FadeOut(color, time))

def fade_out(state, nargs, args):
    if (nargs < 3):
        state.send(f"""Formats:
    {args[0]} COLOR TIME
    {args[0]} -RGB R G B TIME
    {args[0]} -RGB HEX TIME
    {args[0]} -GRAD COLOR1 COLOR2 TIME
    {args[0]} -GRAD-RGB HEX1 HEX2 TIME
    {args[0]} -RAINBOW TIME""")
        return

    color = fullparse_color(state, nargs, args)
    if (color is None):
        return
    
    time = parse_time(args[-1])
    if (time is None):
        state.send(f'Error {args[-1]} is not a valid time')
        return
    state.controller.set_effect(FadeOut(color, time))

def blink_fade(state, nargs, args):
    if (nargs < 3):
        state.send(f"""Formats:
    {args[0]} COLOR TIME
    {args[0]} -RGB R G B TIME
    {args[0]} -RGB HEX TIME
    {args[0]} -GRAD COLOR1 COLOR2 TIME
    {args[0]} -GRAD-RGB HEX1 HEX2 TIME
    {args[0]} -RAINBOW TIME""")
        return

    color = fullparse_color(state, nargs, args)
    if (color is None):
        return
    
    time = parse_time(args[-1])
    if (time is None):
        state.send(f'Error {args[-1]} is not a valid time')
        return
    state.controller.set_effect(BlinkFade(color, time))

def wave(state, nargs, args):
    if (nargs < 5):
        state.send(f"""Formats:
    {args[0]} COLOR1 COLOR2 TIME LENGTH""")
        return
    if args[1] in colors:
        color1 = colors[args[1]]
    else: 
        state.send(f"Error {args[1]} is not a valid COLOR")
        return
    if args[2] in colors:
        color2 = colors[args[2]]
    else: 
        state.send(f"Error {args[2]} is not a valid COLOR")
        return
    try:
        time = float(args[3])
    except:
        state.send(f"Error: {args[3]} is not a valid time")
        return
    try:
        length = int(args[4])
    except:
        state.send(f"Error: {args[4]} is not a valid length")
        return
    state.controller.set_effect(Wave(color1, color2, time, length))

def rainbow_wave(state, nargs, args):
    if (nargs < 3):
        state.send(f"""Formats:
    {args[0]} TIME LENGTH""")
        return
    try:
        time = float(args[1])
    except:
        state.send(f"Error: {args[1]} is not a valid time")
        return
    try:
        length = int(args[2])
    except:
        state.send(f"Error: {args[2]} is not a valid length")
        return
    state.controller.set_effect(RainbowWave(time, length))

def music(state, nargs, args):
    # multiplier = float(args[1])
    file = " ".join(args[1:])
    state.controller.set_effect(FFTEffect(file))

def brightness(state, nargs, args):
    if (nargs == 2):
        try: brightness = float(args[1])
        except:
            state.send("Invalid brightness")
            return
        if (brightness < 0 or brightness > 1):
            state.send("Invalid brightness")
            return
    else:
        state.send(f"Format: {args[0]} value")
        return

    state.pixels.brightness = brightness
    state.pixels.show()

def pause(state, nargs, args):
    state.controller.pause()

def resume(state, nargs, args):
    state.controller.resume()

def stop(state, nargs, args):
    state.controller.stop()
    state.controller = None

def restart(state, nargs, args):
    if state.controller is not None:
        state.controller.stop()
    pixels = neopixel.NeoPixel(board.D18, 150, brightness=0.35, auto_write=False)
    pixel_control = NeoPixelController(pixels, tps=25)
    state.controller = pixel_control
    state.pixels = pixels
    asyncio.create_task(pixel_control.run())
    pixel_control.set_effect(ColorWipe(RainbowColorSelector(), 1))

def get_colors(state, nargs, args):
    value = ""
    for color in colors.keys():
        value += color + "\n"
    state.send(value)

commands = {
    "fill" : fill,

    "blink": blink,
    "colorwipe": color_wipe,
    "fadein" : fade_in,
    "fadeout" : fade_out,
    "blinkfade" : blink_fade,
    "wave" : wave,
    "rainbowwave" : rainbow_wave,
    "rbwave" : rainbow_wave,
    "music" : music,
    
    "brightness": brightness,

    "pause" : pause,
    "play" : resume,
    "resume": resume,
    "stop": stop,
    "exit": stop,
    "restart": restart,

    "colors": get_colors
}