import asyncio
import sys
import os

async def ainput(string: str) -> str:
    print(string + ' ', end='', flush=True)
    return await asyncio.get_event_loop().run_in_executor(
            None, sys.stdin.readline)

def _create_command_dict(commands):
    out_dict = {}
    for command in commands:
        out_dict[command.name] = command
    return out_dict

def _check_brackets(input_str):
    input_str = input_str.replace("[", " [ ").replace("]", " ] ")
    brackets = 0
    for c in input_str:
        if c == "[":
            brackets += 1
        if c == "]":
            brackets -= 1
    if brackets < 0:
        raise Exception("Unmatched ']'")
    if brackets > 0:
        raise Exception("Unmatched '['")
    return input_str

class StackCLI:
    def __init__(self, commands: list, state, end_queue="\n"):
        self.commands = _create_command_dict(commands)
        self.state = state
        
        self.end_queue = end_queue
        
        self.queue = []
        self.queueing = False
        self.running = False


    async def run(self):
        self.running = True
        self.queue = []
        self.queueing = False

        while self.running:
            if self.queueing:
                input_str = await ainput(f"[{len(self.queue)}] ")
            else:
                input_str = await ainput("Input command:")
            await self.parse_input(input_str)


    async def parse_input(self, input_str):
        if self.queueing and input_str == self.end_queue:
            self.queueing = False
        else:
            self.queue.append(input_str)

        if self.queueing: 
            return

        try:
            await self._parse_queue()
        except Exception as e:
            self.state.send(e)


    async def _parse_queue(self):
        while not self.queueing and len(self.queue) > 0 :
            input_str = self.queue.pop(0)
            input_str = _check_brackets(input_str)
            words = input_str.strip().split()
            await self._parse_words(words)


    async def _parse_words(self, words):
        args = []
        
        self._parse_quotes(words, args)

        nargs = len(args)
        if (nargs > 0):
            if (args[0] == "wait"):
                await self._process_wait(args, nargs)
                return
            elif (args[0] == "read"):
                self._process_read(args, nargs)
                return
            elif (args[0] == "do"):
                self.queueing = True
                return
            elif (args[0] == "exit"):
                self.running = False
            
            self._process_command(args, nargs)

    def _parse_quotes(self, words, args):
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
                        raise Exception("Unmatched '\"'")
                word = " ".join(words[i:end+1])
                word = word[1:len(word) - 1]
                i = end
            args.append(word)
            i += 1

    async def _process_wait(self, args, nargs):
        if (nargs < 2):
                raise Exception("wait takes one argument: TIME")
        if (len(self.queue) <= 0):
            raise Exception("wait can only be used before another command")

        try:
            time = float(args[1])
        except:
            raise Exception(f"Error: {args[1]} is not a valid TIME")
        
        await asyncio.sleep(time)

    def _process_read(self, args, nargs):
        if (nargs < 2):
            raise Exception("read takes one argument: FILENAME")
        
        filename = args[1]
        try:
            with open(filename, 'r') as file:
                old_queue = self.queue
                self.queue = file.readlines()
                self.queue.extend(old_queue)
        except:
            self.state.send(os.getcwd())
            raise Exception("Invalid file")

    def _process_command(self, args, nargs):
        command = self._get_command(args[0])
            
        if (command.cmd_type == "CONTROL"):
            command.run(self.state, nargs, args)
        elif (command.cmd_type == "EFFECT"):
            effect = self._parse_stack_command(command, args)
            if effect is None:
                return
            self.state.controller.set_effect(effect)

    def _parse_stack_command(self, command, args):
        argument_stack = []
        n = len(args)
        i = n - 1
        while i >= 0:
            arg = args[i]
            if arg not in self.commands:
                if arg == "[":
                    list_values = []
                    while (len(list_values) == 0 or list_values[-1] != "]") and len(argument_stack) > 0:
                        list_values.append(argument_stack.pop(-1))
                    if len(list_values) == 0 or list_values[-1] != "]":
                        raise Exception("Unmatched '['")
                    arg = list_values[0:len(list_values) - 1]
                argument_stack.append(arg)
            else:
                command = self.commands[arg]
                if command.cmd_type != "EFFECT":
                    raise Exception("Invalid EFFECT command in stacked command")
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

    def _get_command(self, name):
        if name in self.commands:
            return self.commands[name]
        raise Exception(f"Invalid command {name}, try again")