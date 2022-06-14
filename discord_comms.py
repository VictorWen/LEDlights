import discord
import asyncio
from pythonCLI import StackCLI
from effects import *
from neopixel_controller import *
import asyncio
import board
import neopixel
from stack_commands import commands, State
from decouple import config

CLIENT_KEY = config('CLIENT_KEY')
AUTH_USERS = config('AUTH_USERS')
AUTH_USERS = AUTH_USERS.strip().split()
print(AUTH_USERS)

class DiscordCLI:
    def __init__(self, commands: dict, state, client):
        self.commands = commands
        self.state = state
        self.client = client

    async def print(self, message, text):
        await message.reply(text)

    async def command(self, message):
        self.state.send = lambda s : asyncio.create_task(message.reply(s if s is not None else ""))
        input_str = message.content
        args = input_str.strip().split()
        nargs = len(args)
        if (nargs > 0):
            command = args[0]
            if (command in self.commands):
                self.commands[command](self.state, nargs, args)
                if (command == "exit"):
                    self.running = False
            elif (command == "exit"):
                self.running = False
            else:
                await self.print(message, "Invalid command, try again")

class DiscordStackCommandLineInterpreter:
    def __init__(self, commands: list, state, client):
        self.state = state
        self.client = client
        self.cli = StackCLI(commands, state, end_queue="done")

    async def command(self, message):
        self.state.send = lambda s : asyncio.create_task(message.reply(s if s is not None else ""))
        input_str = message.content
        await self.cli.parse_input(input_str)


client = discord.Client()
cli = None

async def startup():
    n = 150

    global cli
    pixels = neopixel.NeoPixel(board.D10, n, brightness=0.5, auto_write=False)

    pixel_control = NeoPixelController(pixels, tps=60)
    state = State(pixel_control, pixels)

    cli = DiscordStackCommandLineInterpreter(commands, state, client)

    asyncio.create_task(pixel_control.run())

client.loop.create_task(startup())

@client.event
async def on_message(message):
    if (message.channel.type != discord.ChannelType.private or str(message.author.id) not in AUTH_USERS):
        return
    
    await cli.command(message)
    pass

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

# This will be reset
client.run(CLIENT_KEY)