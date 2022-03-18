import asyncio
import sys

async def ainput(string: str) -> str:
    print(string + ' ', end='', flush=True)
    return await asyncio.get_event_loop().run_in_executor(
            None, sys.stdin.readline)

class CommandLineInterpreter:
    def __init__(self, commands: dict, state):
        self.commands = commands
        self.state = state

    async def run(self):
        self.running = True
        while self.running:
            input_str = await ainput("Input command:")
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
                    print("Invalid command, try again")
