from typing import Union, Callable


class ControlState:
    controller = None
    send = print
    vars = {}
    last_command_result = None


class Command:    
    def __init__(self, name, call, cmd_type="CONTROL", n_args=0, description="No Description"):
        self.name = name
        assert (cmd_type == "CONTROL" or cmd_type == "EFFECT")
        self.call = call
        self.cmd_type = cmd_type
        self.n_args = n_args
        self.description = description
        
    def set_description(self, descr):
        self.description = descr
        return self
    
    def get_format(self):
        return f"{self.name} {self.description}"
    
    def get_help_text(self):
        return f"{self.name} {self.description}"

    def run(self, state: ControlState, n_args, args):
        self.call(state, n_args, args)


class CommandArgument:
    name:str
    type: str
    converter: Callable
    description: str
    required: bool
    default: any
    
    def __init__(self, name, type, converter, description, required=True, default=None) -> None:
        self.name = name
        self.type = type
        self.converter = converter
        self.description = description
        self.required = required
        self.default = default
    
    def __repr__(self) -> str:
        name = self.name if self.required else f"<{self.name}>"
        return f"{name}: {self.type} - {self.description}"
    
    def get_name(self) -> str:
        return self.name if self.required else f"<{self.name}>"

    def validate(self, value):
        if value is not None:
            new_value = self.converter(value)
            if new_value is not None:
                return new_value
            raise Exception(f"ERROR: {value} is not a valid {self.type} for {self.name}")
        else:
            return self.default


class CommandBuilder(Command):
    name: str
    description: Union[str, None] = None
    arguments: list[CommandArgument]
    result: Callable
    
    def __init__(self, name: str, result, arguments: list[CommandArgument] = None) -> None:
        super().__init__(name, self.run, "EFFECT")
        self.name = name
        self.result = result
        self.arguments = arguments if arguments is not None else []
        
    def __repr__(self) -> str:
        return self.get_help_text()
            
    def get_format(self, name=None):
        output = f"{self.name if name is None else name} "
        for arg in self.arguments:
            output += f"{arg.get_name()} "
        return output
    
    def get_help_text(self):
        output = self.get_format()
        if self.description is not None:
            output += "\n\n"
            output += self.description
        output += "\n\n"
        for arg in self.arguments:
            output += f"{arg}\n"
        return output
        
    def set_description(self, descr):
        self.description = descr
        return self
        
    def add_argument(self, argument: CommandArgument):
        self.arguments.append(argument)
        return self
        
    def _validate_arguments(self, n_args: int, args: list) -> list:
        validated = []
        last_arg_was_fulfilled = True
        for i, argument in enumerate(self.arguments):
            arg = args[i] if i < n_args else None
            if last_arg_was_fulfilled and argument.required and arg is None:
                raise Exception(f"ERROR: {argument.name} is required")
            validated.append(argument.validate(arg))
            last_arg_was_fulfilled = arg is not None
        return validated
    
    def run(self, state: ControlState, n_args: int, args: list):
        name = args[0]
        try:
            args = self._validate_arguments(n_args - 1, args[1:])
        except Exception as e:
            raise Exception(f"{e}\n\tFORMAT: {self.get_format(name=name)}")
        state.last_command_result = self.result(*args)


def convert_hexstring(hex):
    try:
        hex = hex.strip('#')
        N = len(hex)
        if N != 6 and N != 8:
            return None
        return tuple(int(hex[i:i+2], 16) for i in range(0, N, 2))
    except Exception:
        return None


class NumberConverter:
    def __init__(self, min=None, max=None, exclude:list = None, is_int=False) -> None:
        self.min = min
        self.max = max
        self.exclude = exclude if exclude is not None else []
        self.is_int = is_int
        
    def __call__(self, value):
        try:
            if self.is_int:
                val = int(value)
            else:
                val = float(value)
        except:
            return None
        
        min_check = self.min is None or self.min <= val
        max_check = self.max is None or val <= self.max
        exclude_check = val not in self.exclude
        if min_check and max_check and exclude_check:
            return val
        else:
            return None
        

class ObjectConverter:
    def __init__(self, type: type):
        self.type = type
        
    def __call__(self, value):
        if isinstance(value, self.type):
            return value
        else:
            return None


class ListConverter:
    def __init__(self, type: type):
        self.type = type
        
    def __call__(self, value):
        if not isinstance(value, list):
            return None
        for item in value:
            if not isinstance(item, self.type):
                return None
        return value