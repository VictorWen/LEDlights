from .effects.effects import *
from .effects.physics_effects import *
from .effects.positional_effects import *
from .effects.rand_effects import *
from .effects.control_effects import *
from .colors import *
import asyncio
from .effects.music_effects import *
from .neopixel_controller import *
import board
import neopixel
import wave as wav
import pafy
import ffmpeg
import requests
from .config import config


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
        if (-1 <= r <= 255 and -1 <= g <= 255 and -1 <= b <= 255):
            return (r, g, b)
    except:
        return None


def parse_nonzero_float(num):
    try:
        num = float(num)
        if num != 0:
            return num
    except:
        return None


def parse_nonzero_int(num):
    try:
        num = int(num)
        if num != 0:
            return num
    except:
        return None


def parse_float(num):
    try:
        num = float(num)
        return num
    except:
        return None
    
def parse_int(num):
    try:
        num = int(num)
        return num
    except:
        return None


class State:
    def __init__(self, controller, pixels, send=print):
        self.controller = controller
        self.pixels = pixels
        self.send = send
        self.vars = {}
        self.last_command_result = None
        self.playback = None


class Command:
    def __init__(self, name, call, cmd_type="CONTROL", n_args=0):
        self.name = name
        assert (cmd_type == "CONTROL" or cmd_type == "EFFECT")
        self.call = call
        self.cmd_type = cmd_type
        self.n_args = n_args

    def run(self, state, n_args, args):
        self.call(state, n_args, args)


def gradient(state, nargs, args):
    if nargs < 3:
        raise Exception(
            f"Format: {args[0]} EFFECT(1) EFFECT(2) <... EFFECT(N)> <[WEIGHT(1) WEIGHT(2) ... WEIGHT(N)]>")

    if isinstance(args[-1], BaseEffect):
        color_effects = args[1:]
        for effect in color_effects:
            if not isinstance(effect, BaseEffect):
                raise Exception(f"Invalid EFFECT {effect}")
        weights = -1
    else:
        color_effects = args[1:-1]
        weights = []
        if not isinstance(args[-1], list):
            raise Exception(
                f"Format: {args[0]} EFFECT(1) EFFECT(2) ... EFFECT(N) <[WEIGHT(1) WEIGHT(2) ... WEIGHT(N)]>")
        for w in args[-1]:
            try:
                weights.append(int(w))
            except:
                raise Exception(f"Invalid integer WEIGHT {w}")
        if len(weights) != len(color_effects):
            raise Exception(
                f"The number of WEIGHTs must equal the number of EFFECTs ({len(color_effects)})")

    for effect in color_effects:
        if not isinstance(effect, BaseEffect):
            raise Exception(f"Invalid EFFECT {effect}")

    state.last_command_result = DynamicGradient(color_effects, weights)


def split(state, nargs, args):
    if nargs < 3:
        raise Exception(
            f"Format: {args[0]} EFFECT(1) EFFECT(2) <... EFFECT(N)>")

    color_effects = args[1:]
    for effect in color_effects:
        if not isinstance(effect, BaseEffect):
            raise Exception(f"Invalid EFFECT {effect}")

    state.last_command_result = DynamicSplit(color_effects)


def crop(state, nargs, args):
    if nargs < 3 or nargs > 4:
        raise Exception(f"Format: {args[0]} EFFECT SIZE OFFSET")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')

    size = parse_nonzero_int(args[2])
    if size is None:
        raise Exception(f'Error {args[2]} is not a valid SIZE')

    offset = 0
    if nargs == 4:
        offset = parse_nonzero_int(args[3])
        if offset is None:
            raise Exception(f'Error {args[3]} is not a valid OFFSET')

    state.last_command_result = CropEffect(effect, size, offset)


def resize(state, nargs, args):
    if nargs != 3:
        raise Exception(f"Format: {args[0]} EFFECT SIZE")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')

    size = parse_nonzero_int(args[2])
    if size is None:
        raise Exception(f'Error {args[2]} is not a valid SIZE')

    state.last_command_result = ResizeEffect(effect, size)


def rainbow(state, nargs, args):
    state.last_command_result = ColorAdapter(RainbowColorSelector())


def rgb(state, nargs, args):
    if (nargs < 4):
        raise Exception(f"Format: {args[0]} R G B")

    rgb = parse_rgb_color(args[1], args[2], args[3])
    if (rgb is None):
        raise Exception(
            f"Error: ({args[1]}, {args[2]}, {args[3]}) is not a valid RGB Color")

    state.last_command_result = ColorAdapter(SingleColorSelector(rgb))


def hex(state, nargs, args):
    if (nargs < 2):
        raise Exception(f"Format: {args[0]} HEX")

    rgb = hexstring_to_rgb(args[1])
    if (rgb is None):
        raise Exception(f"Error: {args[1]} is not a valid hex color")

    state.last_command_result = ColorAdapter(SingleColorSelector(rgb))


def blink(state, nargs, args):
    if (nargs < 3):
        raise Exception(f"Format: {args[0]} EFFECT TIME")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')

    time = parse_nonzero_float(args[2])
    if (time is None):
        raise Exception(f'Error {args[2]} is not a valid TIME')

    state.last_command_result = BlinkEffect(effect, time)


def color_wipe(state, nargs, args):
    if (nargs < 3):
        raise Exception(f"Format: {args[0]} EFFECT TIME")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')

    time = parse_nonzero_float(args[2])
    if (time is None):
        raise Exception(f'Error {args[2]} is not a valid TIME')

    state.last_command_result = ColorWipe(effect, time)


def fade_in(state, nargs, args):
    if (nargs < 3):
        raise Exception(f"Format: {args[0]} EFFECT TIME")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')

    time = parse_nonzero_float(args[2])
    if (time is None):
        raise Exception(f'Error {args[2]} is not a valid TIME')

    state.last_command_result = FadeIn(effect, time)


def fade_out(state, nargs, args):
    if (nargs < 3):
        raise Exception(f"Format: {args[0]} EFFECT TIME")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')

    time = parse_nonzero_float(args[2])
    if (time is None):
        raise Exception(f'Error {args[2]} is not a valid TIME')

    state.last_command_result = FadeOut(effect, time)


def blink_fade(state, nargs, args):
    if (nargs < 3):
        raise Exception(f"Format: {args[0]} EFFECT TIME")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')

    time = parse_nonzero_float(args[2])
    if (time is None):
        raise Exception(f'Error {args[2]} is not a valid TIME')

    state.last_command_result = BlinkFade(effect, time)


def wave(state, nargs, args):
    if (nargs < 4):
        raise Exception(f"Format: {args[0]} EFFECT PERIOD WAVELENGTH")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')

    time = parse_nonzero_float(args[2])
    if (time is None):
        raise Exception(f'Error {args[2]} is not a valid PERIOD')

    length = parse_nonzero_float(args[3])
    if (time is None):
        raise Exception(f'Error {args[3]} is not a valid WAVELENGTH')

    state.last_command_result = WaveEffect(effect, time, length)


def wheel(state, nargs, args):
    if (nargs < 3):
        raise Exception(f"Format: {args[0]} EFFECT TIME")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')

    time = parse_nonzero_float(args[2])
    if (time is None):
        raise Exception(f'Error {args[2]} is not a valid TIME')

    state.last_command_result = WheelEffect(effect, time)


def wipe(state, nargs, args):
    if (nargs < 3):
        raise Exception(f"Format: {args[0]} EFFECT TIME")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')

    time = parse_nonzero_float(args[2])
    if (time is None):
        raise Exception(f'Error {args[2]} is not a valid TIME')

    state.last_command_result = WipeEffect(effect, time)


def slide(state, nargs, args):
    if (nargs < 3):
        raise Exception(f"Format: {args[0]} EFFECT TIME")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')

    time = parse_nonzero_float(args[2])
    if (time is None):
        raise Exception(f'Error {args[2]} is not a valid TIME')

    state.last_command_result = SlidingEffect(effect, time)


def play_music(state, nargs, args):
    if nargs < 2:
        raise Exception(f"Format: {args[0]} FILENAME")

    file = args[1]

    if file == "spotify":
        try:
            audio_stream = requests.get(
                "http://localhost:3000/stream", stream=True)
            audio_stream = audio_stream.raw
        except BaseException as error:
            # raise Exception(str(error))
            raise Exception(f"Error loading spotify")

        state.last_command_result = PlayMusicStream(audio_stream)
        return

    if file.startswith("https://"):
        try:
            yt = pafy.new(file)
            audio_stream = yt.getbestaudio().url_https

            node_input = ffmpeg.input(audio_stream)
            node_output = node_input.output(
                'pipe:', acodec='pcm_s16le', f='wav')
            node_output = node_output.global_args(
                '-hide_banner', '-nostats', '-loglevel', 'panic', '-nostdin')
            process = node_output.run_async(pipe_stdout=True)
            wavfile = wav.open(process.stdout, 'rb')
        except BaseException as error:
            raise Exception(str(error))
            # raise Exception(f"Error loading {file} from youtube")

    else:
        try:
            wavfile = wav.open(f"{config('music path', default='.')}/{file}", 'rb')
        except:
            raise Exception(f"Error {file} is not a valid FILENAME")

    state.last_command_result = PlayMusic(wavfile)


def spectrum(state, nargs, args):
    if nargs < 3:
        raise Exception(f"Format: {args[0]} EFFECT FILENAME")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')

    file = args[2]
    if file == "spotify":
        try:
            audio_stream = requests.get(
                "http://localhost:3000/stream", stream=True)
            audio_stream = audio_stream.raw
        except BaseException as error:
            # raise Exception(str(error))
            raise Exception(f"Error loading spotify")

        state.last_command_result = SpectrumEffectStream(
            effect, audio_stream, playback=state.playback)
        return

    if file.startswith("https://"):
        try:
            yt = pafy.new(file)
            audio_stream = yt.getbestaudio().url_https

            node_input = ffmpeg.input(audio_stream)
            node_output = node_input.output(
                'pipe:', acodec='pcm_s16le', f='wav')
            node_output = node_output.global_args(
                '-hide_banner', '-nostats', '-loglevel', 'panic', '-nostdin')
            process = node_output.run_async(pipe_stdout=True)
            wavfile = wav.open(process.stdout, 'rb')
        except BaseException as error:
            print(error)
            raise Exception(f"Error loading {file} from youtube")

    else:
        try:
            wavfile = wav.open(f"{config('music path', default='.')}/{file}", 'rb')
        except:
            raise Exception(f"Error {file} is not a valid FILENAME")

    state.last_command_result = SpectrumEffect(effect, wavfile, state.playback)


def piano(state, nargs, args):
    if nargs < 3:
        raise Exception(f"Format: {args[0]} EFFECT FILENAME")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')

    file = args[2]
    if file == "spotify":
        try:
            audio_stream = requests.get(
                "http://localhost:3000/stream", stream=True)
            audio_stream = audio_stream.raw
        except BaseException as error:
            # raise Exception(str(error))
            raise Exception(f"Error loading spotify")

        state.last_command_result = SpectrumEffectStream(
            effect, audio_stream, playback=state.playback, linear=False, nbins=88, min_freq=26, max_freq=4430)
        return

    if file.startswith("https://"):
        try:
            yt = pafy.new(file)
            audio_stream = yt.getbestaudio().url_https

            node_input = ffmpeg.input(audio_stream)
            node_output = node_input.output(
                'pipe:', acodec='pcm_s16le', f='wav')
            node_output = node_output.global_args(
                '-hide_banner', '-nostats', '-loglevel', 'panic', '-nostdin')
            process = node_output.run_async(pipe_stdout=True)
            wavfile = wav.open(process.stdout, 'rb')
        except BaseException as error:
            print(error)
            raise Exception(f"Error loading {file} from youtube")

    else:
        try:
            wavfile = wav.open(f"{config('music path', default='.')}/{file}", 'rb')
        except:
            raise Exception(f"Error {file} is not a valid FILENAME")

    state.last_command_result = SpectrumEffect(
        effect, wavfile, state.playback, linear=False, nbins=88, min_freq=26, max_freq=4430)


def pbody(state, nargs, args):
    if nargs not in [2, 3, 4]:
        raise Exception(
            f"Format: {args[0]} POSITION <VELOCITY> <ACCELERATION>")

    pos = parse_float(args[1])
    if pos is None:
        raise Exception(f"Error: {pos} is an invalid POSITION")

    vel = 0
    if nargs >= 3:
        vel = parse_float(args[2])
        if vel is None:
            raise Exception(f"Error: {vel} is an invalid VELOCITY")

    acc = 0
    if nargs >= 4:
        acc = parse_float(args[3])
        if acc is None:
            raise Exception(f"Error: {acc} is an invalid ACCELERATION")

    state.last_command_result = PhysicsBody(pos, vel, acc)


def physics(state, nargs, args):
    if nargs != 2:
        raise Exception(f"Format: {args[0]} [PARTICLES]")

    particles = args[1]
    if not isinstance(particles, list):
        raise Exception(f"Error {args[1]} is not a list of particles")
    for particle in particles:
        if not isinstance(particle, PhysicsEffect):
            raise Exception(f"Error {args[1]} is not a list of particles, {particle} is not a valid effect")
        
    # gravity = parse_float(args[2])
    # if gravity is None:
    #     raise Exception(f"Error: {gravity} is an invalid GRAVITY")
    
    state.last_command_result = PhysicsEngine(particles)
    

def particle(state, nargs, args):
    if nargs not in [4, 5, 6]:
        raise Exception(f"Format: {args[0]} EFFECT PBODY RADIUS <[BEHAVIORS]> <IS-COLLIDABLE>")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f"Error {args[1]} is not a valid effect")

    pbody = args[2]
    if not isinstance(pbody, PhysicsBody):
        raise Exception(f'Error {pbody} is not a valid PBODY')

    radius = parse_float(args[3])
    if radius is None:
        raise Exception(f"Error {args[3]} is not a valid RADIUS")
    
    behaviors = []
    if nargs > 4:
        behaviors = args[4]
        if not isinstance(behaviors, list):
            raise Exception(f"Error {args[4]} is not a list of behaviors")
        for behavior in behaviors:
            if not isinstance(behavior, ParticleBehavior):
                raise Exception(f"Error {args[4]} is not a list of behaviors, {behavior} is not a valid particle behavior")
    
    collidable = False
    if nargs > 5:
        collidable = True if args[5] else False

    state.last_command_result = ParticleEffect(effect, pbody, radius, behaviors, collidable)


def emitter(state, nargs, args):
    if nargs != 3:
        raise Exception(f"Format: {args[0]} EMISSION DENSITY")
    
    emission = args[1]
    if not isinstance(emission, ParticleEffect):
        raise Exception(f"Error {emission} is not a valid EMISSION, must be a particle")
    
    density = parse_nonzero_float(args[2])
    if density is None or density <= 0:
        raise Exception(f"Error {args[2]} is not a valid DENSITY, must be a positive number")

    state.last_command_result = EmitterBehavior(emission, density)

    
def explosion(state, nargs, args):
    if nargs != 4:
        raise Exception(f"Format: {args[0]} EMISSION DENSITY FUSE")
    
    emission = args[1]
    if not isinstance(emission, ParticleEffect):
        raise Exception(f"Error {emission} is not a valid EMISSION, must be a particle")
    
    density = parse_nonzero_int(args[2])
    if density is None or density <= 0:
        raise Exception(f"Error {args[2]} is not a valid DENSITY, must be a positive number")
    
    fuse = parse_float(args[3])
    if fuse is None or fuse < 0:
        raise Exception(f"Error {args[3]} is not a valid FUSE, must be a non-negative number")

    state.last_command_result = ExplosionBehavior(emission, density, fuse)
    

def collision(state, nargs, args):
    if nargs not in [2, 3]:
        raise Exception(f"Format: {args[0]} [BEHAVIORS] <IS-ONCE>")

    behaviors = args[1]
    if not isinstance(behaviors, list):
        raise Exception(f"Error {args[1]} is not a list of behaviors")
    for behavior in behaviors:
        if not isinstance(behavior, ParticleBehavior):
            raise Exception(f"Error {args[41]} is not a list of behaviors, {behavior} is not a valid particle behavior")
        
    once = True
    if nargs > 2:
        once = True if args[2] else False
    
    state.last_command_result = CollisionBehavior(behaviors, once)


def life(state, nargs, args):
    if nargs != 2:
        raise Exception(f"Format: {args[0]} LIFETIME")
    
    lifetime = parse_float(args[1])
    if lifetime is None or lifetime < 0:
        raise Exception(f"Format: {args[1]} is not a valid HALF-LIFE")
    
    state.last_command_result = LifetimeBehavior(lifetime)


def decay(state, nargs, args):
    if nargs != 2:
        raise Exception(f"Format: {args[0]} HALF-LIFE")
    
    half_life = parse_nonzero_float(args[1])
    if half_life is None or half_life <= 0:
        raise Exception(f"Format: {args[1]} is not a valid HALF-LIFE")
    
    state.last_command_result = DecayBehavior(half_life)
    

def randchoice(state, nargs, args):
    if nargs not in [2, 3]:
        raise Exception(f"Format: {args[0]} [EFFECTS] <REROLLS>")
    
    effects = args[1]
    if not isinstance(effects, list):
        raise Exception(f"Error {args[1]} is not a list of effects")
    for effect in effects:
        if not isinstance(effect, BaseEffect):
            raise Exception(f"Error {args[1]} is not a list of effects, {effect} is not a valid effect")
        
    reroll = -1
    if nargs > 2:
        reroll = parse_int(args[2])
        if reroll is None:
            raise Exception(f"Error {args[2]} is not a valid integer")
    
    state.last_command_result = RandChoice(effects, reroll)


def randtime(state, nargs, args):
    if nargs not in [4, 5]:
        raise Exception(f"Format: {args[0]} EFFECT LOWER UPPER <REROLLS>")
    
    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')
    
    lower = parse_float(args[2])
    if lower is None:
        raise Exception(f"Error {args[2]} is not a valid number")
    upper = parse_float(args[3])
    if upper is None:
        raise Exception(f"Error {args[3]} is not a valid number")
    
    reroll = -1
    if nargs > 4:
        reroll = parse_int(args[4])
        if reroll is None:
            raise Exception(f"Error {args[4]} is not a valid integer")

    state.last_command_result = RandTime(effect, lower, upper, reroll)

def randwarp(state, nargs, args):
    if nargs not in [4, 5]:
        raise Exception(f"Format: {args[0]} EFFECT LOWER UPPER <REROLLS>")
    
    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')
    
    lower = parse_float(args[2])
    if lower is None:
        raise Exception(f"Error {args[2]} is not a valid number")
    upper = parse_float(args[3])
    if upper is None:
        raise Exception(f"Error {args[3]} is not a valid number")
    
    reroll = -1
    if nargs > 4:
        reroll = parse_int(args[4])
        if reroll is None:
            raise Exception(f"Error {args[4]} is not a valid integer")

    state.last_command_result = RandWarp(effect, lower, upper, reroll)
    

def randselect(state, nargs, args):
    if nargs not in [2, 3]:
        raise Exception(f"Format: {args[0]} EFFECT <REROLLS>")
    
    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')
    
    reroll = -1
    if nargs > 2:
        reroll = parse_int(args[2])
        if reroll is None:
            raise Exception(f"Error {args[2]} is not a valid integer")
    
    state.last_command_result = RandSelector(effect, reroll)


def randpbody(state, nargs ,args):
    if nargs not in [3, 5, 7, 8]:
        raise Exception(
            f"Format: {args[0]} MIN_POS MAX_POS <MIN_VEL> <MAX_VEL> <MIN_ACC> <MAX_ACC> <REROLL>")

    min_pos = parse_float(args[1])
    if min_pos is None:
        raise Exception(f"Error: {min_pos} is not a valid number")
    max_pos = parse_float(args[2])
    if max_pos is None:
        raise Exception(f"Error: {max_pos} is not a valid number")

    min_vel = 0
    max_vel = 0
    if nargs >= 4:
        min_vel = parse_float(args[3])
        if min_vel is None:
            raise Exception(f"Error: {min_vel} is not a valid number")
    if nargs >= 5:
        max_vel = parse_float(args[4])
        if max_vel is None:
            raise Exception(f"Error: {max_vel} is not a valid number")
        
    min_acc = 0
    max_acc = 0
    if nargs >= 6:
        min_acc = parse_float(args[5])
        if min_acc is None:
            raise Exception(f"Error: {min_acc} is not a valid number")
    if nargs >= 7:
        max_acc = parse_float(args[6])
        if max_acc is None:
            raise Exception(f"Error: {max_acc} is not a valid number")
        
    reroll = -1
    if nargs > 7:
        reroll = parse_int(args[7])
        if reroll is None:
            raise Exception(f"Error {args[7]} is not a valid integer")

    state.last_command_result = RandPBody(min_pos, max_pos, min_vel, max_vel, min_acc, max_acc, reroll)
    
    
def share(state, nargs, args):
    if nargs not in [2, 3]:
        raise Exception(f"Format: {args[0]} EFFECT <RECLONES>")
    
    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')
    
    reclones = 0
    if nargs > 2:
        reclones = parse_int(args[2])
        if reclones is None:
            raise Exception(f"Error {args[2]} is not a valid integer")
    state.last_command_result = ShareEffect(effect, reclones)


def debugclone(state, nargs, args):
    if nargs not in [2, 3]:
        raise Exception(f"Format: {args[0]} ID <EFFECT>")
    
    id = str(args[1])
    
    effect = None
    if nargs > 2:
        effect = args[2]
        if not isinstance(effect, BaseEffect):
            raise Exception(f"Error {args[2]} is not a valid EFFECT")
    
    state.last_command_result = DebugClone(id, state.send, effect=effect)
    
    
def parent(state, nargs, args):
    if nargs != 2:
        raise Exception(f"Format: {args[0]} EFFECT")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error {args[1]} is not a valid EFFECT')
    
    state.last_command_result = Parent(effect)
    

def child(state, nargs, args):
    if nargs != 2:
        raise Exception(f"Format: {args[0]} PARENT")

    parent = args[1]
    if not isinstance(parent, Parent):
        raise Exception(f'Error {args[1]} is not a valid PARENT')
    
    state.last_command_result = Child(parent)


def brightness(state, nargs, args):
    if (nargs == 2):
        try:
            brightness = float(args[1])
        except:
            raise Exception("Invalid brightness")

        if (brightness < 0 or brightness > 1):
            raise Exception("Invalid brightness")

    else:
        raise Exception(f"Format: {args[0]} value")

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
    pixels = neopixel.NeoPixel(
        board.D10, 150, brightness=0.35, auto_write=False)
    pixel_control = NeoPixelController(pixels, tps=60)
    state.controller = pixel_control
    state.pixels = pixels
    asyncio.create_task(pixel_control.run())


def get_vars(state, nargs, args):
    value = "==========================\nVariables\n==========================\n"
    max_len = 0
    for var in state.vars:
        max_len = max(max_len, len(var))
    for var in state.vars:
        value += f"{var + ':':<{max_len+2}}  {state.vars[var]}\n"
    state.send(value)


def add_layer(state, nargs, args):
    state.controller.add_layer()
    state.send(f"Added new layer ({state.controller.num_layers()})")
    state.send(
        f"Current layer index {state.controller.current_layer()} of {state.controller.num_layers()} layers")


def get_layer(state, nargs, args):
    state.send(
        f"Current layer index {state.controller.current_layer()} of {state.controller.num_layers()} layers")


def set_layer(state, nargs, args):
    if (nargs < 2):
        raise Exception(f"Format: {args[0]} INDEX")

    index = 0
    try:
        index = int(args[1])
    except:
        raise Exception(f"Error: {args[1]} is not a valid INDEX")

    state.controller.set_layer(index)
    state.send(
        f"Current layer index {state.controller.current_layer()} of {state.controller.num_layers()} layers")


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
    state.send(
        f"Current layer index {state.controller.current_layer()} of {state.controller.num_layers()} layers")


def change_merge(state, nargs, args):
    if nargs < 2:
        raise Exception(f"Format: {args[0]} BEHAVIOR")

    valid = state.controller.change_merge_behavior(args[1])
    if not valid:
        raise Exception(f"Error: {args[1]} is not a valid BEHAVIOR")
    else:
        state.send(f"Changed merge behavior to {args[1]}")


commands = [
    Command("gradient", gradient, "EFFECT"),
    Command("split", split, "EFFECT"),
    Command("rainbow", rainbow, "EFFECT"),
    Command("rgb", rgb, "EFFECT"),
    Command("hex", hex, "EFFECT"),

    Command("crop", crop, "EFFECT"),
    Command("resize", resize, "EFFECT"),

    Command("blink", blink, "EFFECT"),
    Command("colorwipe", color_wipe, "EFFECT"),
    Command("fadein", fade_in, "EFFECT"),
    Command("fadeout", fade_out, "EFFECT"),
    Command("blinkfade", blink_fade, "EFFECT"),
    Command("wave", wave, "EFFECT"),
    Command("wheel", wheel, "EFFECT"),
    Command("wipe", wipe, "EFFECT"),
    Command("slide", slide, "EFFECT"),

    Command("playmusic", play_music, "EFFECT"),
    Command("spectrum", spectrum, "EFFECT"),
    Command("piano", piano, "EFFECT"),

    Command("physics", physics, "EFFECT"),
    Command("pbody", pbody, "EFFECT"),
    Command("particle", particle, "EFFECT"),
    
    Command("emitter", emitter, "EFFECT"),
    Command("explosion", explosion, "EFFECT"),
    Command("collision", collision, "EFFECT"),
    Command("life", life, "EFFECT"),
    Command("decay", decay, "EFFECT"),
    
    Command("randchoice", randchoice, "EFFECT"),
    Command("randtime", randtime, "EFFECT"),
    Command("randwarp", randwarp, "EFFECT"),
    Command("randpbody", randpbody, "EFFECT"),
    Command("randselect", randselect, "EFFECT"),
    
    Command("share", share, "EFFECT"),
    Command("debugclone", debugclone, "EFFECT"),
    Command("parent", parent, "EFFECT"),
    Command("child", child, "EFFECT"),

    Command("brightness", brightness, n_args=1),
    Command("pause", pause),
    Command("resume", resume),
    Command("exit", stop),
    Command("restart", restart),
    Command("vars", get_vars),

    Command("addlayer", add_layer),
    Command("getlayer", get_layer),
    Command("setlayer", set_layer, n_args=1),
    Command("clearlayer", clear_layer),
    Command("resetlayers", reset_layers),
    Command("deletelayer", delete_layer),
    Command("changemerge", change_merge, n_args=1)
]