import discord
import asyncio
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
        self.commands = commands
        self.state = state
        self.client = client

        self.queue = []
        self.queueing = False

    def get_command(self, name):
        for command in self.commands:
            if command.name == name:
                return command
        return None

    def parse_stack_command(self, command, args):
        argument_stack = []
        n = len(args)
        i = n - 1
        while i >= 0:
            arg = args[i]
            command = self.get_command(arg)
            if command is None:
                if arg == "[":
                    list_values = []
                    while (len(list_values) == 0 or list_values[-1] != "]") and len(argument_stack) > 0:
                        list_values.append(argument_stack.pop(-1))
                    if len(list_values) == 0 or list_values[-1] != "]":
                        self.state.send("Unmatched '['")
                        return None
                    arg = list_values[0:len(list_values) - 1]
                argument_stack.append(arg)
            else:
                if command.cmd_type != "EFFECT":
                    self.state.send("Invalid EFFECT command in stacked command")
                    return None
                self.state.last_command_result = None

                m = len(argument_stack)
                cmd_args = [command.name]
                for x in range(min(command.n_args, m)):
                    cmd_args.append(argument_stack.pop(-1))
                n_args = len(cmd_args)
                
                command.run(self.state, n_args, cmd_args)
                if self.state.last_command_result is None:
                    return None
                argument_stack.append(self.state.last_command_result)
            i -= 1
        
        if len(argument_stack) < 1:
            return None
        return argument_stack[-1]


    async def command(self, message):
        self.state.send = lambda s : asyncio.create_task(message.reply(s if s is not None else ""))

        if self.queueing:
            if message.content == "done":
                self.queueing = False
            else:
                self.queue.append(message.content)
                return
        else:
            self.queue.append(message.content)

        while not self.queueing and len(self.queue) > 0 :
            input_str = self.queue.pop(0)
            input_str = input_str.replace("[", " [ ").replace("]", " ] ")
            brackets = 0
            for c in input_str:
                if c == "[":
                    brackets += 1
                if c == "]":
                    brackets -= 1
            if brackets < 0:
                self.state.send("Unmatched ']'")
                return
            if brackets > 0:
                self.state.send("Unmatched '['")
                return

            words = input_str.strip().split()
            args = []
            
            i = 0
            while i < len(words):
                word = words[i]
                if (word.startswith("\"")):
                    end = 0
                    if (len(word) > 1 and word.endswith("\"")):
                        end = i
                    else:
                        end = i + 1
                        while end < len(words) and not words[end].endswith("\""):
                            end += 1
                        if end == len(words):
                            self.state.send("Unmatched '\"'")
                            args = []
                            break
                    word = " ".join(words[i:end+1])
                    word = word[1:len(word) - 1]
                    i = end
                args.append(word)
                i += 1

            nargs = len(args)
            if (nargs > 0):
                if (args[0] == "wait"):
                    if (nargs < 2):
                        self.state.send("wait takes one argument: TIME")
                        return
                    if (len(self.queue) <= 0):
                        self.state.send("wait can only be used before another command")
                        return
                    try:
                        time = float(args[1])
                    except:
                        self.state.send(f"Error: {args[1]} is not a valid TIME")
                        return
                    await asyncio.sleep(time)
                    return
                if (args[0] == "read"):
                    if (nargs < 2):
                        self.state.send("read takes one argument: FILENAME")
                        return
                    filename = args[1]
                    try:
                        with open(filename, 'r') as file:
                            old_queue = self.queue
                            self.queue = file.readlines()
                            self.queue.extend(old_queue)
                    except:
                        self.state.send(os.getcwd())
                        self.state.send("Invalid file")
                        return
                    continue
                if (args[0] == "do"):
                    self.queueing = True
                    return
                if (args[0] == "exit"):
                    self.running = False

                command = self.get_command(args[0])
                if (command is None):
                    self.state.send(f"Invalid command {args[0]}, try again")
                    return
                
                if (command.cmd_type == "CONTROL"):
                    command.run(self.state, nargs, args)
                elif (command.cmd_type == "EFFECT"):
                    effect = self.parse_stack_command(command, args)
                    if effect is None:
                        return
                    self.state.controller.set_effect(effect)


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