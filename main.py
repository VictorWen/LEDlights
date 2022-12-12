from effects.effects import *
from neopixel_controller import *
import asyncio
import board
import neopixel
from pythonCLI import *
from stack_commands import commands, State
from colors import *
import sys
from effects.music_effects import PyAudioPlayer


async def main():
    n = 150
    if (len(sys.argv) > 1):
        n = int(sys.argv[1])
    pixels = neopixel.NeoPixel(board.D10, n, brightness=0.5, auto_write=False)

    pixel_control = NeoPixelController(pixels, tps=60)
    state = State(pixel_control, pixels)
    state.playback = PyAudioPlayer()

    cli = StackCLI(commands, state, debug=True)

    task = asyncio.create_task(pixel_control.run())
    pixel_control.set_effect(SlidingEffect(ColorWipe(ColorAdapter(RainbowColorSelector()), 10), 10))


    await asyncio.create_task(cli.run())

asyncio.run(main())
