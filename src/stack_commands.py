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
from .command_builder import *


def parse_nonzero_float(num):
    try:
        num = float(num)
        if num != 0:
            return num
    except Exception:
        return None


def parse_nonzero_int(num):
    try:
        num = int(num)
        if num != 0:
            return num
    except Exception:
        return None


def parse_float(num):
    try:
        num = float(num)
        return num
    except Exception:
        return None
    
    
def parse_int(num):
    try:
        num = int(num)
        return num
    except Exception:
        return None


def effect_arg(descr):
    return CommandArgument("EFFECT", "EFFECT", ObjectConverter(BaseEffect), descr)


class State(ControlState):
    def __init__(self, controller, pixels, send=print):
        self.controller = controller
        self.pixels = pixels
        self.send = send
        self.vars = {}
        self.last_command_result = None
        self.playback = None


rgb = CommandBuilder("rgb", lambda r, g, b, a: ColorAdapter(SingleColorSelector((r, g, b, a))), [
    CommandArgument("RED", "INTEGER(0, 255)", NumberConverter(0, 255, is_int=True), "Red channel value"),
    CommandArgument("GREEN", "INTEGER(0, 255)", NumberConverter(0, 255, is_int=True), "Green channel value"),
    CommandArgument("BLUE", "INTEGER(0, 255)", NumberConverter(0, 255, is_int=True), "Blue channel value"),
    CommandArgument("ALPHA", "NUMBER(0, 1)", NumberConverter(0, 1), "Alpha channel value", False, 1)
]).set_description("Create a color using RGBA values")
    
    
hex = CommandBuilder("hex", lambda x: ColorAdapter(SingleColorSelector(x)), arguments=[
    CommandArgument("HEX", "HEX-STRING", convert_hexstring, "Hexstring of the form #RRGGBB[AA] denoting a color")    
]).set_description("Create a color using a hexadecimal string")
    
    
alpha = CommandBuilder("alpha", AlphaAdapter, [
    CommandArgument("EFFECT", "EFFECT", ObjectConverter(BaseEffect), "Effect to change alpha value"),
    CommandArgument("ALPHA", "NUMBER(0, 1)", NumberConverter(0, 1), "Alpha channel value")
]).set_description("Change the alpha value of an effect")


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
            except Exception:
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


crop = CommandBuilder("crop", CropEffect, [
    effect_arg("Effect to crop"),
    CommandArgument("SIZE", "INTEGER>0", NumberConverter(1, is_int=True), "New size of the effect"),
    CommandArgument("OFFSET", "INTEGER>0", NumberConverter(1, is_int=True), "Offset to begin crop")
]).set_description("Crop an effect to the given size")


resize = CommandBuilder("resize", ResizeEffect, [
    effect_arg("Effect to resize"),
    CommandArgument("SIZE", "INTEGER>0", NumberConverter(1, is_int=True), "New size of the effect")
]).set_description("Resize an effect to the given size")


rainbow = CommandBuilder("rainbow", lambda: ColorAdapter(RainbowColorSelector())).set_description(
    "Display a rainbow"
)


blink = CommandBuilder("blink", BlinkEffect, [
    effect_arg("Effect to blink"),
    CommandArgument("TIME", "NUMBER!=0", NumberConverter(exclude=[0]), "The time between blinks")
]).set_description("Blink an effect on and off")


color_wipe = CommandBuilder("colorwipe", ColorWipe, [
    effect_arg("Effect to wipe"),
    CommandArgument("TIME", "NUMBER!=0", NumberConverter(exclude=[0]), "The time to complete the wipe")
]).set_description("Wipe an effect around the light strip")


fade_in = CommandBuilder("fadein", FadeIn, [
    effect_arg("Effect to fade in"),
    CommandArgument("TIME", "NUMBER>0", NumberConverter(min=0, exclude=[0]), "The time to fade in")
]).set_description("Fade an effect in")

fade_out = CommandBuilder("fadeout", FadeOut, [
    effect_arg("Effect to fade out"),
    CommandArgument("TIME", "NUMBER>0", NumberConverter(min=0, exclude=[0]), "The time to fade out")
]).set_description("Fade an effect out")

blink_fade = CommandBuilder("blinkfade", BlinkFade, [
    effect_arg("Effect to blink fade"),
    CommandArgument("TIME", "NUMBER!=0", NumberConverter(exclude=[0]), "The time between blinks")
]).set_description("Fade an effect in and out")


slide = CommandBuilder("slide", SlidingEffect, [
    effect_arg("Effect to slide"),
    CommandArgument("TIME", "NUMBER!=0", NumberConverter(exclude=[0]), "The time to complete a full slide")
]).set_description("Slide an effect around the strip over time")

wave = CommandBuilder("wave", WaveEffect, [
    effect_arg("Effect to wave"),
    CommandArgument("PERIOD", "NUMBER!=0", NumberConverter(exclude=[0]), "The time between peaks of the wave"),
    CommandArgument("LENGTH", "INTEGER>0", NumberConverter(min=1, is_int=True), "The wavelength from peak to peak")
]).set_description("Create a wave of an effect")


wheel = CommandBuilder("wheel", WheelEffect, [
    effect_arg("Effect to wheel"),
    CommandArgument("PERIOD", "NUMBER!=0", NumberConverter(exclude=[0]), "The period of the wheel"),
]).set_description("Fill strip with a color using a wheel rotating back and forth")

wipe = CommandBuilder("wipe", WipeEffect, [
    effect_arg("Effect to use"),
    CommandArgument("TIME", "NUMBER!=0", NumberConverter(exclude=[0]), "The period to complete a full wipe")
]).set_description("Fill strip with a color changing over time using the given effect")


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
            raise Exception(f"Error: loading spotify")

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
            # raise Exception(f"Error: loading {file} from youtube")

    else:
        try:
            wavfile = wav.open(f"{config('music path', default='.')}/{file}", 'rb')
        except Exception:
            raise Exception(f"Error: {file} is not a valid FILENAME")

    state.last_command_result = PlayMusic(wavfile)


def spectrum(state, nargs, args):
    if nargs < 3:
        raise Exception(f"Format: {args[0]} EFFECT FILENAME")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error: {args[1]} is not a valid EFFECT')

    file = args[2]
    if file == "spotify":
        try:
            audio_stream = requests.get(
                "http://localhost:3000/stream", stream=True)
            audio_stream = audio_stream.raw
        except BaseException as error:
            # raise Exception(str(error))
            raise Exception(f"Error: loading spotify")

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
            raise Exception(f"Error: loading {file} from youtube")

    else:
        try:
            wavfile = wav.open(f"{config('music path', default='.')}/{file}", 'rb')
        except Exception:
            raise Exception(f"Error: {file} is not a valid FILENAME")

    state.last_command_result = SpectrumEffect(effect, wavfile, state.playback)


def piano(state, nargs, args):
    if nargs < 3:
        raise Exception(f"Format: {args[0]} EFFECT FILENAME")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error: {args[1]} is not a valid EFFECT')

    file = args[2]
    if file == "spotify":
        try:
            audio_stream = requests.get(
                "http://localhost:3000/stream", stream=True)
            audio_stream = audio_stream.raw
        except BaseException as error:
            # raise Exception(str(error))
            raise Exception(f"Error: loading spotify")

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
            raise Exception(f"Error: loading {file} from youtube")

    else:
        try:
            wavfile = wav.open(f"{config('music path', default='.')}/{file}", 'rb')
        except Exception:
            raise Exception(f"Error: {file} is not a valid FILENAME")

    state.last_command_result = SpectrumEffect(
        effect, wavfile, state.playback, linear=False, nbins=88, min_freq=26, max_freq=4430)


def pbody(state, nargs, args):
    if nargs not in [2, 3, 4, 5]:
        raise Exception(
            f"Format: {args[0]} POSITION <VELOCITY> <ACCELERATION> <MASS>")

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
        
    mass = 1
    if nargs >= 5:
        mass = parse_float(args[4])
        if mass is None:
            raise Exception(f"Error: {mass} is an invalid ACCELERATION")

    state.last_command_result = PhysicsBody(pos, vel, acc, mass)


def physics(state, nargs, args):
    if nargs != 2:
        raise Exception(f"Format: {args[0]} [PARTICLES]")

    particles = args[1]
    if not isinstance(particles, list):
        raise Exception(f"Error: {args[1]} is not a list of particles")
    for particle in particles:
        if not isinstance(particle, PhysicsEffect):
            raise Exception(f"Error: {args[1]} is not a list of particles, {particle} is not a valid effect")
    
    state.last_command_result = PhysicsEngine(particles)
    

def particle(state, nargs, args):
    if nargs not in [4, 5, 6, 7]:
        raise Exception(f"Format: {args[0]} EFFECT PBODY RADIUS <[BEHAVIORS]> <IS-COLLIDABLE> <[TAGS]>")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f"Error: {args[1]} is not a valid effect")

    pbody = args[2]
    if not isinstance(pbody, PhysicsBody):
        raise Exception(f'Error: {pbody} is not a valid PBODY')

    radius = parse_float(args[3])
    if radius is None:
        raise Exception(f"Error: {args[3]} is not a valid RADIUS")
    
    behaviors = []
    if nargs > 4:
        behaviors = args[4]
        if not isinstance(behaviors, list):
            raise Exception(f"Error: {args[4]} is not a list of behaviors")
        for behavior in behaviors:
            if not isinstance(behavior, ParticleBehavior):
                raise Exception(f"Error: {args[4]} is not a list of behaviors, {behavior} is not a valid particle behavior")
    
    collidable = False
    if nargs > 5:
        collidable = True if args[5] else False
        
    tags = []
    if nargs > 6:
        tags = args[6]
        if not isinstance(tags, list):
            raise Exception(f"Error: {args[6]} is not a list of tags or strings")
        for i in range(len(tags)):
            tag = tags[i]
            if isinstance(tag, str):
                tags[i] = Tag(tag)
            elif not isinstance(tag, Tag):
                raise Exception(f"Error: {args[6]} is not a list of tags or strings, {tag} is not a valid tag")
            
    state.last_command_result = ParticleEffect(effect, pbody, radius, behaviors, collidable, tags)


def emitter(state, nargs, args):
    if nargs != 3:
        raise Exception(f"Format: {args[0]} EMISSION DENSITY")
    
    emission = args[1]
    if not isinstance(emission, ParticleEffect):
        raise Exception(f"Error: {emission} is not a valid EMISSION, must be a particle")
    
    density = parse_nonzero_float(args[2])
    if density is None or density <= 0:
        raise Exception(f"Error: {args[2]} is not a valid DENSITY, must be a positive number")

    state.last_command_result = EmitterBehavior(emission, density)

    
def explosion(state, nargs, args):
    if nargs != 4:
        raise Exception(f"Format: {args[0]} EMISSION DENSITY FUSE")
    
    emission = args[1]
    if not isinstance(emission, ParticleEffect):
        raise Exception(f"Error: {emission} is not a valid EMISSION, must be a particle")
    
    density = parse_nonzero_int(args[2])
    if density is None or density <= 0:
        raise Exception(f"Error: {args[2]} is not a valid DENSITY, must be a positive number")
    
    fuse = parse_float(args[3])
    if fuse is None or fuse < 0:
        raise Exception(f"Error: {args[3]} is not a valid FUSE, must be a non-negative number")

    state.last_command_result = ExplosionBehavior(emission, density, fuse)
    

def collision(state, nargs, args):
    if nargs not in [2, 3, 4]:
        raise Exception(f"Format: {args[0]} [BEHAVIORS] <IS-ONCE> <[TAGS]>")

    behaviors = args[1]
    if not isinstance(behaviors, list):
        raise Exception(f"Error: {args[1]} is not a list of behaviors")
    for behavior in behaviors:
        if not isinstance(behavior, ParticleBehavior):
            raise Exception(f"Error: {args[41]} is not a list of behaviors, {behavior} is not a valid particle behavior")
        
    once = True
    if nargs > 2:
        once = True if args[2] else False
        
    tags = []
    if nargs > 3:
        tags = args[3]
        if not isinstance(tags, list):
            raise Exception(f"Error: {args[3]} is not a list of tags or strings")
        for i in range(len(tags)):
            tag = tags[i]
            if isinstance(tag, str):
                tags[i] = Tag(tag)
            elif not isinstance(tag, Tag):
                raise Exception(f"Error: {args[3]} is not a list of tags or strings, {tag} is not a valid tag")
    
    state.last_command_result = CollisionBehavior(behaviors, once, tags)
    
    
def rigid(state, nargs, args):
    if nargs not in [1, 2, 3]:
        raise Exception(f"Format: {args[0]} <[TAGS]> <COEFF-RESTITUTION>")
    
    tags = []
    if nargs > 1:
        tags = args[1]
        if not isinstance(tags, list):
            raise Exception(f"Error: {args[1]} is not a list of tags or strings")
        for i in range(len(tags)):
            tag = tags[i]
            if isinstance(tag, str):
                tags[i] = Tag(tag)
            elif not isinstance(tag, Tag):
                raise Exception(f"Error: {args[1]} is not a list of tags or strings, {tag} is not a valid tag")
            
    coeff = 1
    if nargs > 2:
        coeff = parse_float(args[2])
        if coeff is None:
            raise Exception(f"Error: {args[2]} is not a valid COEFF-RESITUTION")
        
    state.last_command_result = RigidColliderBehavior(coeff, tags)


def life(state, nargs, args):
    if nargs != 2:
        raise Exception(f"Format: {args[0]} LIFETIME")
    
    lifetime = parse_float(args[1])
    if lifetime is None or lifetime < 0:
        raise Exception(f"Error: {args[1]} is not a valid HALF-LIFE")
    
    state.last_command_result = LifetimeBehavior(lifetime)


def decay(state, nargs, args):
    if nargs != 2:
        raise Exception(f"Format: {args[0]} HALF-LIFE")
    
    half_life = parse_nonzero_float(args[1])
    if half_life is None or half_life <= 0:
        raise Exception(f"Error: {args[1]} is not a valid HALF-LIFE")
    
    state.last_command_result = DecayBehavior(half_life)
    
    
def impulse(state, nargs, args):
    if nargs not in [2, 3]:
        raise Exception(f"Format: {args[0]} CONSTANT <MOMENTUM-COEF>")
    
    constant = parse_float(args[1])
    if constant is None:
        raise Exception(f"Error: {args[1]} is not a valid CONSTANT")
    
    self_coef = 0
    if nargs > 2:
        self_coef = parse_float(args[2])
        if self_coef is None:
            raise Exception(f"Error: {args[2]} is not a valid MOMENTUM-COEF")
    
    state.last_command_result = ImpluseBehavior(constant, self_coef)
    
def field(state, nargs, args):
    if nargs != 4:
        raise Exception(f"Format: {args[0]} NAME CONSTANT DEGREE")
    
    name = args[1]
    
    constant = parse_float(args[2])
    if constant is None:
        raise Exception(f"Error: {args[2]} is not a valid CONSTANT")
    
    degree = parse_float(args[3])
    if degree is None:
        raise Exception(f"Error: {args[3]} is not a valid DEGREE")
    
    state.last_command_result = FieldBehavior(name, constant, degree)
    
def force(state, nargs, args):
    if nargs != 4:
        raise Exception(f"Format: {args[0]} NAME CONSTANT VELOCITY-MULTIPLIER")
    
    name = args[1]
    
    constant = parse_float(args[2])
    if constant is None:
        raise Exception(f"Error: {args[2]} is not a valid CONSTANT")
    
    vel_mult = parse_float(args[3])
    if vel_mult is None:
        raise Exception(f"Error: {args[3]} is not a valid VELOCITY-MULTIPLIER, must be a float")
    
    state.last_command_result = ForceBehavior(name, constant, vel_mult)
    
    
def tag(state, nargs, args):
    if nargs != 2:
        raise Exception(f"Format: {args[0]} NAME")
    
    name = args[1]
    if not isinstance(name, str):
        raise Exception(f"Error: {args[1]} is not a valid string")
    
    state.last_command_result = Tag(name)


def counttag(state, nargs, args):
    if nargs not in [1, 2, 3]:
        raise Exception(f"Format: {args[0]} <START> <PREFIX>")
    
    start = 0
    if nargs > 1:
        start = parse_int(args[1])
        if start is None:
            raise Exception(f"Error: {args[1]} is not a valid integer")
    
    prefix = ""
    if nargs > 2:
        prefix = args[2]
        if not isinstance(prefix, str):
            raise Exception(f"Error: {args[2]} is not a valid string")
    
    state.last_command_result = CountingTag(start, prefix)


def randchoice(state, nargs, args):
    if nargs not in [2, 3]:
        raise Exception(f"Format: {args[0]} [EFFECTS] <REROLLS>")
    
    effects = args[1]
    if not isinstance(effects, list):
        raise Exception(f"Error: {args[1]} is not a list of effects")
    for effect in effects:
        if not isinstance(effect, BaseEffect):
            raise Exception(f"Error: {args[1]} is not a list of effects, {effect} is not a valid effect")
        
    reroll = -1
    if nargs > 2:
        reroll = parse_int(args[2])
        if reroll is None:
            raise Exception(f"Error: {args[2]} is not a valid integer")
    
    state.last_command_result = RandChoice(effects, reroll)


def randtime(state, nargs, args):
    if nargs not in [4, 5]:
        raise Exception(f"Format: {args[0]} EFFECT LOWER UPPER <REROLLS>")
    
    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error: {args[1]} is not a valid EFFECT')
    
    lower = parse_float(args[2])
    if lower is None:
        raise Exception(f"Error: {args[2]} is not a valid number")
    upper = parse_float(args[3])
    if upper is None:
        raise Exception(f"Error: {args[3]} is not a valid number")
    
    reroll = -1
    if nargs > 4:
        reroll = parse_int(args[4])
        if reroll is None:
            raise Exception(f"Error: {args[4]} is not a valid integer")

    state.last_command_result = RandTime(effect, lower, upper, reroll)

def randwarp(state, nargs, args):
    if nargs not in [4, 5]:
        raise Exception(f"Format: {args[0]} EFFECT LOWER UPPER <REROLLS>")
    
    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error: {args[1]} is not a valid EFFECT')
    
    lower = parse_float(args[2])
    if lower is None:
        raise Exception(f"Error: {args[2]} is not a valid number")
    upper = parse_float(args[3])
    if upper is None:
        raise Exception(f"Error: {args[3]} is not a valid number")
    
    reroll = -1
    if nargs > 4:
        reroll = parse_int(args[4])
        if reroll is None:
            raise Exception(f"Error: {args[4]} is not a valid integer")

    state.last_command_result = RandWarp(effect, lower, upper, reroll)
    

def randselect(state, nargs, args):
    if nargs not in [2, 3]:
        raise Exception(f"Format: {args[0]} EFFECT <REROLLS>")
    
    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error: {args[1]} is not a valid EFFECT')
    
    reroll = -1
    if nargs > 2:
        reroll = parse_int(args[2])
        if reroll is None:
            raise Exception(f"Error: {args[2]} is not a valid integer")
    
    state.last_command_result = RandSelector(effect, reroll)


def randpbody(state, nargs ,args):
    if nargs not in [3, 5, 7, 9, 10]:
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
        
    min_mass = 1
    max_mass = 1
    if nargs >= 8:
        min_mass = parse_float(args[7])
        if min_mass is None:
            raise Exception(f"Error: {min_mass} is not a valid number")
    if nargs >= 9:
        max_mass = parse_float(args[8])
        if max_mass is None:
            raise Exception(f"Error: {max_mass} is not a valid number")
        
    reroll = -1
    if nargs > 9:
        reroll = parse_int(args[9])
        if reroll is None:
            raise Exception(f"Error: {args[79]} is not a valid integer")

    state.last_command_result = RandPBody(min_pos, max_pos, min_vel, max_vel, min_acc, max_acc, min_mass, max_mass, reroll)
    
    
def share(state, nargs, args):
    if nargs not in [2, 3]:
        raise Exception(f"Format: {args[0]} EFFECT <RECLONES>")
    
    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error: {args[1]} is not a valid EFFECT')
    
    reclones = 0
    if nargs > 2:
        reclones = parse_int(args[2])
        if reclones is None:
            raise Exception(f"Error: {args[2]} is not a valid integer")
    state.last_command_result = ShareEffect(effect, reclones)


def debugclone(state, nargs, args):
    if nargs not in [2, 3]:
        raise Exception(f"Format: {args[0]} ID <EFFECT>")
    
    id = str(args[1])
    
    effect = None
    if nargs > 2:
        effect = args[2]
        if not isinstance(effect, BaseEffect):
            raise Exception(f"Error: {args[2]} is not a valid EFFECT")
    
    state.last_command_result = DebugClone(id, state.send, effect=effect)
    
    
def parent(state, nargs, args):
    if nargs != 2:
        raise Exception(f"Format: {args[0]} EFFECT")

    effect = args[1]
    if not isinstance(effect, BaseEffect):
        raise Exception(f'Error: {args[1]} is not a valid EFFECT')
    
    state.last_command_result = Parent(effect)
    

def child(state, nargs, args):
    if nargs != 2:
        raise Exception(f"Format: {args[0]} PARENT")

    parent = args[1]
    if not isinstance(parent, Parent):
        raise Exception(f'Error: {args[1]} is not a valid PARENT')
    
    state.last_command_result = Child(parent)


def brightness(state, nargs, args):
    if (nargs == 2):
        try:
            brightness = float(args[1])
        except Exception:
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
    except Exception:
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
    rainbow,

    rgb,
    hex,
    alpha,

    crop,
    resize,

    blink,
    color_wipe,
    fade_in,
    fade_out,
    blink_fade,
    wave,
    wheel,
    wipe,
    slide,

    Command("playmusic", play_music, "EFFECT"),
    Command("spectrum", spectrum, "EFFECT"),
    Command("piano", piano, "EFFECT"),

    Command("physics", physics, "EFFECT"),
    Command("pbody", pbody, "EFFECT"),
    Command("particle", particle, "EFFECT"),
    
    Command("emitter", emitter, "EFFECT"),
    Command("explosion", explosion, "EFFECT"),
    Command("collision", collision, "EFFECT"),
    Command("rigid", rigid, "EFFECT"),
    Command("life", life, "EFFECT"),
    Command("decay", decay, "EFFECT"),
    Command("impulse", impulse, "EFFECT"),
    Command("field", field, "EFFECT"),
    Command("force", force, "EFFECT"),
    
    Command("tag", tag, "EFFECT"),
    Command("counttag", counttag, "EFFECT"),
    
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
