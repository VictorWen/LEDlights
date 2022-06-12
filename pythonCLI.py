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


# TODO: Refactor
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


    async def run(self):
        self.running = True
        queue = []
        queueing = False

        while self.running:
            if queueing:
                input_str = await ainput(f"[{len(queue)}] ")
                if input_str == "\n":
                    queueing = False
                else:
                    queue.append(input_str)
                    continue
            elif len(queue) > 0:
                input_str = queue.pop(0)            
            else:
                input_str = await ainput("Input command:")

            input_str = input_str.replace("[", " [ ").replace("]", " ] ")
            brackets = 0
            for c in input_str:
                if c == "[":
                    brackets += 1
                if c == "]":
                    brackets -= 1
            if brackets < 0:
                self.state.send("Unmatched ']'")
                continue
            if brackets > 0:
                self.state.send("Unmatched '['")
                continue

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
                        continue
                    if (len(queue) <= 0):
                        self.state.send("wait can only be used before another command")
                        continue
                    try:
                        time = float(args[1])
                    except:
                        self.state.send(f"Error: {args[1]} is not a valid TIME")
                        continue
                    await asyncio.sleep(time)
                    continue
                if (args[0] == "read"):
                    if (nargs < 2):
                        self.state.send("read takes one argument: FILENAME")
                        continue
                    filename = args[1]
                    try:
                        with open(filename, 'r') as file:
                            old_queue = queue
                            queue = file.readlines()
                            queue.extend(old_queue)
                    except:
                        self.state.send("Invalid file")
                    continue
                if (args[0] == "do"):
                    queueing = True
                    continue
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
