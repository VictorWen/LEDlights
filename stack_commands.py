from effects import *
from colors import *
from fft_effect import FFTEffect
import asyncio
from music_effects import PlayMusic
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
    "BLACK": (0, 0, 0),
    "CLEAR": (-1, -1, -1),
}

def colorname_to_color(colorname):
    try:
        if colorname in colors:
            return colors[colorname]
    except:
        pass
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
        return
    
    color1 = colorname_to_color(args[1])
    if (color1 is None):
        return
    
    color2 = colorname_to_color(args[2])
    if (color2 is None):
        return
    
    state.last_command_result = ColorAdapter(GradientColorSelector(color1, color2))


def gradient3(state, nargs, args):
    if (nargs < 4):
        state.send(f"Format: {args[0]} COLOR1 COLOR2 COLOR3")
        return
    
    color1 = colorname_to_color(args[1])
    if (color1 is None):
        return
    
    color2 = colorname_to_color(args[2])
    if (color2 is None):
        return
    
    color3 = colorname_to_color(args[3])
    if (color3 is None):
        return
    
    state.last_command_result = ColorAdapter(Gradient3ColorSelector(color1, color2, color3))


def ngradient(state, nargs, args):
    if (nargs < 2):
        state.send(f"Format: {args[0]} \"COLOR(1) COLOR(2) ... COLOR(N)\"")
        return
    
    if isinstance(args[1], str):
        colors = args[1].strip().split()
    elif isinstance(args[1], list):
        colors = args[1]
    else:
        state.send(f"Invalid COLOR list {args[1]}")
        return
    
    for i in range(len(colors)):
        color = colorname_to_color(colors[i])
        if (color is None):
            return
        colors[i] = color
    
    state.last_command_result = ColorAdapter(NGradientColorSelector(colors))


def dgradient(state, nargs, args):
    if nargs < 3:
        state.send(f"Format: {args[0]} [EFFECT(1) EFFECT(2) ... EFFECT(N)] [WEIGHT(1) WEIGHT(2) ... WEIGHT(N)]")
        return
    
    if isinstance(args[1], list):
        for effect in args[1]:
            if not isinstance(effect, BaseEffect):
                state.send(f"Invalid EFFECT {effect}")
                return    
    elif not isinstance(args[1], BaseEffect):
        state.send(f"Invalid EFFECT list {args[1]}")
        return
    
    if isinstance(args[2], list):
        weights = []
        for weight in args[2]:
            try:
                weights.append(int(weight))
            except:
                state.send(f"Invalid WEIGHT {weight}")
    elif isinstance(args[2], str):
        try:
            weights = int(args[2])
        except:
            state.send(f"Invalid WEIGHT {args[2]}")
    else:
        state.send(f"Invalid WEIGHT list {args[2]}")
        return

    state.last_command_result = DynamicGradient(args[1], weights)


def split(state, nargs, args):
    if (nargs < 2):
        state.send(f"Format: {args[0]} COLOR1 COLOR2")
        return
    
    color1 = colorname_to_color(args[1])
    if (color1 is None):
        return
    
    color2 = colorname_to_color(args[2])
    if (color2 is None):
        return
    
    state.last_command_result = ColorAdapter(SplitColorSelector(color1, color2))


def split3(state, nargs, args):
    if (nargs < 4):
        state.send(f"Format: {args[0]} COLOR1 COLOR2 COLOR3")
        return
    
    color1 = colorname_to_color(args[1])
    if (color1 is None):
        return
    
    color2 = colorname_to_color(args[2])
    if (color2 is None):
        return
    
    color3 = colorname_to_color(args[3])
    if (color3 is None):
        return
    
    state.last_command_result = ColorAdapter(Split3ColorSelector(color1, color2, color3))


def nsplit(state, nargs, args):
    if (nargs < 2):
        state.send(f"Format: {args[0]} \"COLOR(1) COLOR(2) ... COLOR(N)\"")
        return

    if isinstance(args[1], str):
        colors = args[1].strip().split()
    elif isinstance(args[1], list):
        colors = args[1]
    else:
        state.send(f"Invalid COLOR list {args[1]}")
        return
    
    for i in range(len(colors)):
        color = colorname_to_color(colors[i])
        if (color is None):
            return
        colors[i] = color

    state.last_command_result = ColorAdapter(NSplitColorSelector(colors))


def dsplit(state, nargs, args):
    if nargs < 2:
        state.send(f"Format: {args[0]} [EFFECT(1) EFFECT(2) ... EFFECT(N)]")
        return
    
    if isinstance(args[1], list):
        for effect in args[1]:
            if not isinstance(effect, BaseEffect):
                state.send(f"Invalid EFFECT {effect}")
                return    
    elif not isinstance(args[1], BaseEffect):
        state.send(f"Invalid EFFECT list {args[1]}")
        return

    state.last_command_result = DynamicSplit(args[1])


def rainbow(state, nargs, args):
    state.last_command_result = ColorAdapter(RainbowColorSelector())

def redgreenblue(state, nargs, args):
    state.last_command_result = ColorAdapter(RGBColorSelector())


def rgb(state, nargs, args):
    if (nargs < 4):
        state.send(f"Format: {args[0]} R G B")
        return
    
    rgb = parse_rgb_color(args[1], args[2], args[3])
    if (rgb is None):
        state.send(f"Error: ({args[1]}, {args[2]}, {args[3]}) is not a valid RGB Color")
        return None
    state.last_command_result = ColorAdapter(SingleColorSelector(rgb))


def hex(state, nargs, args):
    if (nargs < 2):
        state.send(f"Format: {args[0]} HEX")
        return
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

def play_music(state, nargs, args):
    if nargs < 2:
        state.send(f"Format: {args[0]} FILENAME")
        return

    file = args[1]

    state.last_command_result = PlayMusic(file)

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

def add_layer(state, nargs, args):
    state.controller.add_layer()
    state.send(f"Added new layer ({state.controller.num_layers()})")
    state.send(f"Current layer index {state.controller.current_layer()} of {state.controller.num_layers()} layers")

def get_layer(state, nargs, args):
    state.send(f"Current layer index {state.controller.current_layer()} of {state.controller.num_layers()} layers")

def set_layer(state, nargs, args):
    if (nargs < 2):
        state.send(f"Format: {args[0]} INDEX")
        return
    
    index = 0
    try:
        index = int(args[1])
    except:
        state.send(f"Error: {args[1]} is not a valid INDEX")
        return

    state.controller.set_layer(index)
    state.send(f"Current layer index {state.controller.current_layer()} of {state.controller.num_layers()} layers")

def clear_layer(state, nargs, args):
    state.controller.clear_layer()
    state.send(f"Cleared layer index {state.controller.current_layer()}")

def reset_layers(state, nargs, args):
    state.controller.reset_layers()
    state.send(f"Reset layers")

def delete_layer(state, nargs, args):
    old = state.controller.current_layer()
    state.controller.delete_layer()
    state.send(f"Deleted layer index {old}")
    state.send(f"Current layer index {state.controller.current_layer()} of {state.controller.num_layers()} layers")

def change_merge(state, nargs, args):
    if nargs < 2:
        state.send(f"Format: {args[0]} BEHAVIOR")
        return
    
    valid = state.controller.change_merge_behavior(args[1])
    if not valid:
        state.send(f"Error: {args[1]} is not a valid BEHAVIOR")
    else:
        state.send(f"Changed merge behavior to {args[1]}")
    

commands = [
    Command("fill", fill, "EFFECT", 1),
    Command("gradient", gradient, "EFFECT", 2),
    Command("gradient3", gradient3, "EFFECT", 3),
    Command("ngradient", ngradient, "EFFECT", 1),
    Command("dgradient", dgradient, "EFFECT", 2),
    Command("split", split, "EFFECT", 2),
    Command("split3", split3, "EFFECT", 3),
    Command("nsplit", nsplit, "EFFECT", 1),
    Command("dsplit", dsplit, "EFFECT", 1),
    Command("rainbow", rainbow, "EFFECT", 0),
    Command("redgreenblue", redgreenblue, "EFFECT", 0),
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

    Command("playmusic", play_music, "EFFECT", 1),

    Command("brightness", brightness, n_args=1),
    Command("pause", pause),
    Command("resume", resume),
    Command("exit", stop),
    Command("restart", restart),
    Command("colors", get_colors),

    Command("addlayer", add_layer),
    Command("getlayer", get_layer),
    Command("setlayer", set_layer, n_args=1),
    Command("clearlayer", clear_layer),
    Command("resetlayers", reset_layers),
    Command("deletelayer", delete_layer),
    Command("changemerge", change_merge, n_args=1)
]