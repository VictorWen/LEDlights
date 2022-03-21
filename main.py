from math import pi
from effects import *
from neopixel_controller import *
import asyncio
import os
import board
import neopixel
from pythonCLI import *
# from commands import commands, State
from stack_commands import commands, State
from colors import *
import sys
import wave
import numpy as np
# import discord_comms as dc

async def main():
    n = 150
    if (len(sys.argv) > 1):
        n = int(sys.argv[1])
    pixels = neopixel.NeoPixel(board.D10, n, brightness=0.35, auto_write=False)

    pixel_control = NeoPixelController(pixels, tps=50)
    state = State(pixel_control, pixels)
    cli = StackCommandLineInterpreter(commands, state)

    task = asyncio.create_task(pixel_control.run())
    pixel_control.set_effect(SlidingEffect(ColorWipe(ColorAdapter(RainbowColorSelector()), 10), 10))


    await asyncio.create_task(cli.run())

# dc.client.loop.create_task(main())
# dc.start()
asyncio.run(main())
