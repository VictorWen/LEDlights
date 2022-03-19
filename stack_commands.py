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

def colorname_to_color(colorname):
    if colorname in colors:
        return colors[colorname]
    print(f"Error: {colorname} is not a valid COLOR")
    return None

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

class State:
    def __init__(self, controller, pixels, send=print):
        self.controller = controller
        self.pixels = pixels
        self.send = send
        self.last_command_result = None

class Command:
    def __init__(self, name, call, cmd_type="CONTROL", n_args=0):
        self.name = name
        assert(cmd_type == "CONTROL" or cmd_type == "EFFECT")
        self.call = call
        self.cmd_type = cmd_type
        self.n_args = n_args


    def run(self, state, n_args, args):
        self.call(state, n_args, args)


def fill(state, nargs, args):
    if (nargs < 2):
        state.send(f"Format: {args[0]} COLOR")
        return

    color = colorname_to_color(args[1])
    if (color is None):
        return

    state.last_command_result = ColorAdapter(SingleColorSelector(color))


def gradient(state, nargs, args):
    if (nargs < 2):
        state.send(f"Format: {args[0]} COLOR1 COLOR2")
    
    color1 = colorname_to_color(args[1])
    if (color1 is None):
        return
    
    color2 = colorname_to_color(args[2])
    if (color2 is None):
        return
    
    state.last_command_result = ColorAdapter(GradientColorSelector(color1, color2))


def rainbow(state, nargs, args):
    state.last_command_result = ColorAdapter(RainbowColorSelector())


def rgb(state, nargs, args):
    if (nargs < 4):
        state.send(f"Format: {args[0]} R G B")
    
    rgb = parse_rgb_color(args[1], args[2], args[3])
    if (rgb is None):
        state.send(f"Error: ({args[1]}, {args[2]}, {args[3]}) is not a valid RGB Color")
        return None
    state.last_command_result = ColorAdapter(SingleColorSelector(rgb))


def hex(state, nargs, args):
    if (nargs < 2):
        state.send(f"Format: {args[0]} HEX")
    rgb = hexstring_to_rgb(args[1])
    if (rgb is None):
        state.send(f"Error: {args[1]} is not a valid hex color")
        return None
    state.last_command_result = ColorAdapter(SingleColorSelector(rgb))


def blink(state, nargs, args):
    if (nargs < 3):
        state.send(f"Format: {args[0]} EFFECT TIME")
        return

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        state.send(f'Error {args[1]} is not a valid EFFECT')
    
    time = parse_time(args[2])
    if (time is None):
        state.send(f'Error {args[2]} is not a valid TIME')
        return
    
    state.last_command_result = BlinkEffect(effect, time)


def color_wipe(state, nargs, args):
    if (nargs < 3):
        state.send(f"Format: {args[0]} EFFECT TIME")
        return

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        state.send(f'Error {args[1]} is not a valid EFFECT')
        return
    
    time = parse_time(args[2])
    if (time is None):
        state.send(f'Error {args[2]} is not a valid TIME')
        return
    
    state.last_command_result = ColorWipe(effect, time)

def fade_in(state, nargs, args):
    if (nargs < 3):
        state.send(f"Format: {args[0]} EFFECT TIME")
        return

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        state.send(f'Error {args[1]} is not a valid EFFECT')
        return
    
    time = parse_time(args[2])
    if (time is None):
        state.send(f'Error {args[2]} is not a valid TIME')
        return
    
    state.last_command_result = FadeIn(effect, time)

def fade_out(state, nargs, args):
    if (nargs < 3):
        state.send(f"Format: {args[0]} EFFECT TIME")
        return

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        state.send(f'Error {args[1]} is not a valid EFFECT')
        return
    
    time = parse_time(args[2])
    if (time is None):
        state.send(f'Error {args[2]} is not a valid TIME')
        return
    
    state.last_command_result = FadeOut(effect, time)

def blink_fade(state, nargs, args):
    if (nargs < 3):
        state.send(f"Format: {args[0]} EFFECT TIME")
        return

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        state.send(f'Error {args[1]} is not a valid EFFECT')
        return
    
    time = parse_time(args[2])
    if (time is None):
        state.send(f'Error {args[2]} is not a valid TIME')
        return
    
    state.last_command_result = BlinkFade(effect, time)

def wave(state, nargs, args):
    if (nargs < 4):
        state.send(f"Format: {args[0]} EFFECT PERIOD WAVELENGTH")
        return

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        state.send(f'Error {args[1]} is not a valid EFFECT')
        return
    
    time = parse_time(args[2])
    if (time is None):
        state.send(f'Error {args[2]} is not a valid PERIOD')
        return
    
    length = parse_time(args[3])
    if (time is None):
        state.send(f'Error {args[3]} is not a valid WAVELENGTH')
        return
    
    state.last_command_result = WaveEffect(effect, time, length)


def wheel(state, nargs, args):
    if (nargs < 3):
        state.send(f"Format: {args[0]} EFFECT TIME")
        return

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        state.send(f'Error {args[1]} is not a valid EFFECT')
        return
    
    time = parse_time(args[2])
    if (time is None):
        state.send(f'Error {args[2]} is not a valid TIME')
        return
    
    state.last_command_result = WheelEffect(effect, time)


def wipe(state, nargs, args):
    if (nargs < 3):
        state.send(f"Format: {args[0]} EFFECT TIME")
        return

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        state.send(f'Error {args[1]} is not a valid EFFECT')
        return
    
    time = parse_time(args[2])
    if (time is None):
        state.send(f'Error {args[2]} is not a valid TIME')
        return
    
    state.last_command_result = WipeEffect(effect, time)


def slide(state, nargs, args):
    if (nargs < 3):
        state.send(f"Format: {args[0]} EFFECT TIME")
        return

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        state.send(f'Error {args[1]} is not a valid EFFECT')
        return
    
    time = parse_time(args[2])
    if (time is None):
        state.send(f'Error {args[2]} is not a valid TIME')
        return
    
    state.last_command_result = SlidingEffect(effect, time)

# def music(state, nargs, args):
#     # multiplier = float(args[1])
#     file = " ".join(args[1:])
#     state.controller.set_effect(FFTEffect(file))

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
    pixel_control.set_effect(ColorWipe(ColorAdapter(RainbowColorSelector()), 1))

def get_colors(state, nargs, args):
    value = ""
    for color in colors.keys():
        value += color + "\n"
    state.send(value)
    

commands = [
    Command("fill", fill, "EFFECT", 1),
    Command("gradient", gradient, "EFFECT", 2),
    Command("rainbow", rainbow, "EFFECT", 0),
    Command("rgb", rgb, "EFFECT", 3),
    Command("hex", hex, "EFFECT", 1),

    Command("blink", blink, "EFFECT", 2),
    Command("colorwipe", color_wipe, "EFFECT", 2),
    Command("fadein", fade_in, "EFFECT", 2),
    Command("fadeout", fade_out, "EFFECT", 2),
    Command("blinkfade", blink_fade, "EFFECT", 2),
    Command("wave", wave, "EFFECT", 3),
    Command("wheel", wheel, "EFFECT", 2),
    Command("wipe", wipe, "EFFECT", 2),
    Command("slide", slide, "EFFECT", 2),

    Command("brightness", brightness, "CONTROL", 1),
    Command("pause", pause),
    Command("resume", resume),
    Command("exit", stop),
    Command("restart", restart),
    Command("colors", get_colors),
]