import discord
import asyncio
from pythonCLI import StackCLI
from effects import *
from neopixel_controller import *
import asyncio
import board
import neopixel
from stack_commands import commands, State
import sys
import os

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

# class DiscordPlayer:
#     def __init__(self):
#         self.buffer = b''
#         self.index = 0
    
#     def read(self, frames=3840):
#         next = self.index + frames
#         next = min(next, len(self.buffer))
#         data = self.buffer[self.index:next]
#         self.index = next
#         return data
    
#     def write(self, data):
#         self.buffer = b''.join([self.buffer, data])


# player = DiscordPlayer()

# async def join_vc(client: discord.Client, channel_id: int) -> Optional[discord.VoiceClient]:
#     channel = client.get_channel(channel_id)
#     guild = channel.guild
#     vc = guild.voice_client
#     if not vc:
#         print(f"Connecting to {channel}")
#         vc = await channel.connect(timeout=5)
#         print(f"Connected to {channel}")
#     elif vc.channel.id != channel.id:
#         print(f"Moving to {channel}")
#         await vc.move_to(channel)
#         print(f"Moved to {channel}")

#     timeout = 0
#     while not vc.is_connected() or vc.channel.id != channel.id:
#         timeout += 1
#         print(f"Waiting for Voice Client connection, attempt #{timeout}")
#         await asyncio.sleep(1)
#         if timeout >= 10:
#             print(f"Failed to connect to Voice Client")
#             await vc.disconnect(force=True)
#             print(f"Successfully disconnected")
#             return
#     return vc

# async def play_music(client: discord.Client, channel_id: int):
#     channel = client.get_channel(channel_id)
#     vc = channel.guild.voice_client
#     if not vc:
#         vc = await join_vc(client, channel_id)
#     audio = discord.PCMAudio(player)
#     audio_player = discord.PCMVolumeTransformer(audio)
#     print(f'Playing audio')
#     vc.play(audio_player)

@client.event
async def on_message(message):
    if (message.channel.type != discord.ChannelType.private or message.author.id != 142817055924551680):
        return
    
    await cli.command(message)
    pass

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

# This will be reset
client.run("ODEzNjQ5Njc5MjQ5OTY1MDU3.YDSYUA.ZzxitzNrOaQqdaTzSvTaadoI2Cs")