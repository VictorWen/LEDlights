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


class StackCommandLineInterpreter:
    def __init__(self, commands: list, state):
        self.commands = commands
        self.state = state

    def get_command(self, name):
        for command in self.commands:
            if command.name == name:
                return command
        return None

    
    def parse_stack_command(self, command, args):
        command_stack = []
        argument_stack = []

        n = len(args)
        i = n - 1
        while i >= 0:
            arg = args[i]
            command = self.get_command(arg)
            if command is None:
                argument_stack.append(arg)
            else:
                if command.cmd_type != "EFFECT":
                    self.state.send("Invalid EFFECT command in stacked command")
                command_stack.append(command)
            i -= 1
        
        while len(command_stack) > 0:
            self.state.last_command_result = None
            command = command_stack.pop(0)
            m = len(argument_stack)
            args = [command.name]
            for i in range(min(command.n_args, m)):
                args.append(argument_stack.pop(-1))
            n_args = len(args)
            
            command.run(self.state, n_args, args)
            if self.state.last_command_result is None:
                return None
            argument_stack.append(self.state.last_command_result)
        
        if len(argument_stack) < 1:
            return None
        return argument_stack[-1]


    async def run(self):
        self.running = True
        while self.running:
            input_str = await ainput("Input command:")
            args = input_str.strip().split()
            nargs = len(args)
            if (nargs > 0):
                if (args[0] == "exit"):
                    self.running = False

                command = self.get_command(args[0])
                if (command is None):
                    self.state.send("Invalid command, try again")
                    continue
                
                if (command.cmd_type == "CONTROL"):
                    command.run(self.state, nargs, args)
                elif (command.cmd_type == "EFFECT"):
                    effect = self.parse_stack_command(command, args)
                    if effect is None:
                        continue
                    self.state.controller.set_effect(effect)
