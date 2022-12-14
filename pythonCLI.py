import asyncio
import sys
import os
import traceback
from config import config


SCRIPTS_PATH = config('scripts path', default="./")
CONFIG_VARS = config('vars', default={})

# TERMINALS
KEYWORD_NODE = "Keyword"
COMMAND_NODE = "Command"
NUMBER_NODE = "Number"
STRING_NODE = "String"
BOOLEAN_NODE = "Boolean"
VAR_NODE = "Variable"
FUNVAR_NODE = "FunVar"

# NON-TERMINALS
LIST_NODE = "List"
OBJECT_NODE = "Object"
EXPR_NODE = "Expr"

# VARIABLE SET STATE
INITIAL_LET = 0
AWAITING_LET_NAME = 1
AWAITING_LET_EQUAL = 2
AWAITING_LET_VALUE = 3
# VARIABLE GET STATE
INITIAL_GET = 0
AWAITING_GET_NAME = 1
# FUNCTION DEFINE STATE
INITIAL_FUN = 0
AWAITING_FUN_NAME = 1
AWAITING_FUN_EQUALS = 2
AWAITING_FUN_VALUE = 3

SINGLE_TOKENS = ['(', ")", "[", "]", '=']
BOOLEAN_TOKENS = ["true", "false"]


async def ainput(string: str) -> str:
    print(string + ' ', end='', flush=True)
    return await asyncio.get_event_loop().run_in_executor(
        None, sys.stdin.readline)


def _create_command_dict(commands):
    out_dict = {}
    for command in commands:
        out_dict[command.name] = command
    return out_dict


class StackCLI:
    def __init__(self, commands: list, state, end_queue="\n", debug=False):
        self.commands = _create_command_dict(commands)
        self.state = state
        self.debug = debug

        self.end_queue = end_queue

        self.queue = []
        self.queueing = False
        self.running = False

        self.parser = CommandParser([
            "read",
            "wait",
            "do",
            "exit"
        ], self.commands, self.state)
        self.evaluator = CommandEvaluator(self.state, self.commands, self)
        
        temp_evaulator = NoKeywordCommandEvaluator(self.state, self.commands)
        
        for var_name in CONFIG_VARS:
            var_code = CONFIG_VARS[var_name]
            tokens = tokenize(var_code)
            parse_node = self.parser.parse(tokens)
            self.state.last_command_result = None
            var_value = temp_evaulator.evaluate(parse_node)
            self.state.vars[var_name] = Variable(var_code, var_value, self.state.last_command_result != None)

    async def run(self):
        self.running = True
        self.queue = []
        self.queueing = False

        if os.path.exists(os.path.join(SCRIPTS_PATH, "startup.txt")):
            await self.parse_input('read "startup.txt"')

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
            await self.parse_queue()
        except Exception as e:
            if self.debug:
                self.state.send(traceback.format_exc())
            else:
                self.state.send(e)

    async def parse_queue(self):
        while not self.queueing and len(self.queue) > 0:
            input_str = self.queue.pop(0)
            if input_str.startswith("#"):
                continue
            tokens = tokenize(input_str)
            parsed_input = self.parser.parse(tokens)
            # print(parsed_input)
            self.state.last_command_result = None
            eval_obj = await self.evaluator.evaluate(parsed_input)
            if self.state.last_command_result is not None:
                self.state.controller.set_effect(eval_obj)
            elif eval_obj is not None:
                self.state.send(eval_obj)

    async def process_keyword(self, name, args):
        nargs = len(args)
        if (nargs > 0):
            if (name == "wait"):
                await self.process_wait(args, nargs)
            elif (name == "read"):
                self.process_read(args, nargs)
            elif (name == "do"):
                self.queueing = True
            elif (name == "exit"):
                self.running = False
                if "exit" in self.commands:
                    self.commands["exit"].run(self.state, args, nargs)

    async def process_wait(self, args, nargs):
        if (nargs < 2):
            raise Exception("wait takes one argument: TIME")
        if (len(self.queue) <= 0):
            raise Exception("wait can only be used before another command")

        try:
            time = float(args[1])
        except:
            raise Exception(f"Error: {args[1]} is not a valid TIME")

        await asyncio.sleep(time)

    def process_read(self, args, nargs):
        if (nargs < 2):
            raise Exception("read takes one argument: FILENAME")

        filename = args[1]
        try:
            with open(os.path.join(SCRIPTS_PATH, filename), 'r') as file:
                old_queue = self.queue
                self.queue = file.readlines()
                self.queue.extend(old_queue)
        except:
            self.state.send(os.getcwd())
            raise Exception("Invalid file")


def tokenize(input_str):
    input_str = input_str.strip()
    words = []
    i = 0
    built_word = ""
    while i < len(input_str):
        c = input_str[i]
        if c == '"':
            if len(built_word) > 0:
                raise Exception("Invalid '\"' placement")
            i += 1
            quoted_str = ""
            while i < len(input_str) and input_str[i] != '"':
                quoted_str += input_str[i]
                i += 1
            if i + 1 == len(input_str) and input_str[i] != '"':
                raise Exception("Unmatched '\"'")
            words.append(f'"{quoted_str}"')
        elif c == "=":
            if len(built_word) > 0:
                words.append(built_word)
                built_word = ""
            words.append("=")
            words.append(input_str[i+1:].strip())
            break
        elif c in SINGLE_TOKENS:
            if len(built_word) > 0:
                words.append(built_word)
                built_word = ""
            words.append(input_str[i])
        elif c == ' ':
            if len(built_word) > 0:
                words.append(built_word)
                built_word = ""
        else:
            built_word += c
        i += 1
    if len(built_word) > 0:
        words.append(built_word)
    return words


class Variable:
    def __init__(self, var_code, var_value, is_command=False):
        self.code = var_code
        self.value = var_value
        self.is_command = is_command


class ParseNode:
    def __init__(self, type=None, value=None, children=[]):
        self.type = type
        self.value = value
        self.children = children

        self.is_leaf = len(children) == 0

    def __repr__(self):
        if not self.is_leaf:
            return f"{self.type} {self.children}"
        else:
            return f"{self.type} {self.value}"

    def append_child(self, child):
        self.children.append(child)
        self.is_leaf = True


class CommandParser:
    def __init__(self, keywords, commands, state, fun_vars=[]):
        self.keywords = keywords
        self.commands = commands
        self.state = state
        self.variables = state.vars
        self.fun_vars = fun_vars

    def parse(self, tokens):
        root = ParseNode(type=OBJECT_NODE)
        stack = []

        self.is_first_token = True
        self.variable_set_state = INITIAL_LET
        self.variable_get_state = INITIAL_GET
        self.variable_fun_state = INITIAL_FUN

        for token in tokens:
            self.process_token(token, stack)
            self.is_first_token = False

        self.check_for_errors(stack)

        root.children = stack
        root.is_leaf = False
        return root

    def check_for_errors(self, stack):
        if '(' in stack:
            raise Exception("Unmatched '('")
        if '[' in stack:
            raise Exception("Unmatched '['")
        if self.variable_set_state != 0:
            raise Exception(
                "Unfinished set variable expression. Usage: let VAR_NAME = EXPRESSION")
        if self.variable_get_state != 0:
            raise Exception(
                "Unfinished get variable expression. Usage: get VAR_NAME")
        if self.variable_fun_state != 0:
            raise Exception(
                "Unfinished fun variable expression. Usage: fun FUN_NAME <VAR1> <VAR2> ... = EXPRESSION")

    def process_token(self, token, stack):
        if (self._check_state_machines(token, stack)): 
            pass
        elif token == "(":
            stack.append('(')
        elif token == ")":
            self.parse_parentheses(stack)
        elif token == "[":
            stack.append('[')
        elif token == "]":
            self.parse_brackets(stack)
        else:
            terminal = self.create_terminal_node(token)
            stack.append(terminal)

    def parse_parentheses(self, stack):
        k = len(stack) - 1
        while k >= 0 and stack[k] != '(':
            k -= 1
        if (k < 0):
            raise Exception("Unmatched ')'")
        arguments = stack[k+1:]
        for _ in range(k, len(stack)):
            stack.pop(-1)

        if len(arguments) == 0:
            raise Exception(f"Invalid object token length")

        object_node = ParseNode(type=OBJECT_NODE, children=arguments)
        stack.append(object_node)

    def parse_brackets(self, stack):
        k = len(stack) - 1
        while k >= 0 and stack[k] != '[':
            k -= 1
        if (k < 0):
            raise Exception("Unmatched ']'")
        arguments = stack[k+1:]
        for _ in range(k, len(stack)):
            stack.pop(-1)
        list_node = ParseNode(type=LIST_NODE, children=arguments)
        stack.append(list_node)

    def create_terminal_node(self, token):
        if len(token) >= 2 and token.startswith('"') and token.endswith('"'):
            return ParseNode(type=STRING_NODE, value=token[1:len(token)-1])
        elif token[0].isdigit() or \
            token[0] == "-" and len(token) >= 2 and \
                (token[1] == "." or token[1].isdigit()):
            try:
                value = float(token)
                return ParseNode(type=NUMBER_NODE, value=value)
            except ValueError:
                raise Exception(f"{token} is not a valid number")
        elif token in BOOLEAN_TOKENS:
            return ParseNode(type=BOOLEAN_NODE, value=(token==BOOLEAN_TOKENS[0]))
        elif token in self.fun_vars:
            return ParseNode(type=FUNVAR_NODE, value=token)
        elif token in self.keywords:
            return ParseNode(type=KEYWORD_NODE, value=token)
        elif token in self.commands:
            return ParseNode(type=COMMAND_NODE, value=token)
        elif token in self.variables:
            return ParseNode(type=VAR_NODE, value=token)
        else:
            raise Exception(f"{token} is an undefined symbol")
        
    def _check_is_valid_var_name(self, token):
        if not token.isalpha() or len(token) < 1:
            raise Exception(f"Invalid variable name: {token}")
        if token in self.keywords or token in self.commands or token in BOOLEAN_TOKENS:
            raise Exception(
                f"Invalid variable name: {token} is already a reserved value")
            
    def _check_state_machines(self, token, stack):
        if token == "let":
            if not self.is_first_token:
                raise Exception(
                    "'let' can only be used at the beginning of an expression")
            self.variable_set_state = AWAITING_LET_NAME
            return True
        elif token == "get":
            if not self.is_first_token:
                raise Exception(
                    "'get' can only be used at the beginning of an expression")
            self.variable_get_state = AWAITING_GET_NAME
            return True
        elif token == "fun":
            if not self.is_first_token:
                raise Exception(
                    "'fun' can only be used at the beginning of an expression")
            self.variable_fun_state = AWAITING_FUN_NAME
            return True
        elif self._update_state_machines(token, stack):
            return True
        return False

    def _update_state_machines(self, token, stack):
        if self.variable_set_state != INITIAL_LET:
            self._update_variable_set_state(token, stack)
            return True
        elif self.variable_get_state != INITIAL_GET:
            self._update_variable_get_state(token, stack)
            return True
        elif self.variable_fun_state != INITIAL_FUN:
            self._update_variable_fun_state(token, stack)
            return True
        return False

    def _update_variable_set_state(self, token, stack):
        if self.variable_set_state == AWAITING_LET_NAME:
            self.variable_set_state = AWAITING_LET_EQUAL
            self._check_is_valid_var_name(token)
            stack.append(token)
        elif self.variable_set_state == AWAITING_LET_EQUAL:
            if token != '=':
                raise Exception(f"Expecting '=' after 'let {stack.pop(-1)}'")
            self.variable_set_state = AWAITING_LET_VALUE
        elif self.variable_set_state == AWAITING_LET_VALUE:
            self.variable_set_state = INITIAL_LET
            var_name = stack.pop(-1)
            tokens = tokenize(token)
            temp_parser = CommandParser({}, self.commands, self.state)
            parse_node = temp_parser.parse(tokens)
            temp_eval = NoKeywordCommandEvaluator(self.state, self.commands)
            self.state.last_command_result = None
            var_value = temp_eval.evaluate(parse_node)
            self.variables[var_name] = Variable(token, var_value, is_command=self.state.last_command_result != None)
    
    def _update_variable_get_state(self, token, stack):
        if self.variable_get_state == AWAITING_GET_NAME:
            self.variable_get_state = INITIAL_GET
            if token in self.variables:
                self.state.send(self.variables[token].code)
            else:
                raise Exception(f"Undefined variable name: {token}")
            
    def _update_variable_fun_state(self, token, stack):
        if self.variable_fun_state == AWAITING_FUN_NAME:
            self.variable_fun_state = AWAITING_FUN_EQUALS
            self._check_is_valid_var_name(token)
            stack.append(token)
        elif self.variable_fun_state == AWAITING_FUN_EQUALS:
            if token != '=':
                if not token.isalpha() or len(token) < 1:
                    raise Exception(f"Invalid variable name: {token}")
                stack.append(token)
            else:
                self.variable_fun_state = AWAITING_FUN_VALUE
        elif self.variable_fun_state == AWAITING_FUN_VALUE:
            self.variable_fun_state = INITIAL_FUN
            fun_vars = stack[1:]
            fun_name = stack[0]
            stack.clear()
            self.commands[fun_name] = FunctionCommand(self, code=token, var_names=fun_vars)


class CommandEvaluator():
    def __init__(self, state, command_dict, cli_controller=None, fun_vars={}):
        self.state = state
        self.commands = command_dict
        self.cli_controller = cli_controller
        self.fun_vars = fun_vars

    async def evaluate(self, parse_root: ParseNode):
        parse_type = parse_root.type
        if parse_type == OBJECT_NODE:
            return await self.eval_object(parse_root)
        elif parse_type == LIST_NODE:
            return await self.eval_list(parse_root)
        elif parse_type == FUNVAR_NODE:
            return self.eval_funvar(parse_root)
        elif parse_type == VAR_NODE:
            return self.eval_var(parse_root)
        elif parse_type == KEYWORD_NODE:
            return await self.eval_keyword(parse_root.value, [parse_root.value])
        elif parse_type == COMMAND_NODE:
            return self.eval_command(parse_root.value, [parse_root.value])
        else:
            return parse_root.value

    async def eval_object(self, object_node):
        if len(object_node.children) < 1:
            return None

        primary = object_node.children[0]
        obj_type = primary.type
        obj_value = primary.value

        if len(object_node.children) == 1:
            return await self.evaluate(primary)
        elif obj_type not in [KEYWORD_NODE, COMMAND_NODE, OBJECT_NODE]:
            raise Exception("Non command-like objects cannot have arguments")
        elif obj_type == OBJECT_NODE:
            children = object_node.children[1:]
            primary.children += children
            return await self.eval_object(primary)
        else:
            eval_args = [obj_value]
            for child in object_node.children[1:]:
                eval_args.append(await self.evaluate(child))

            if obj_type == KEYWORD_NODE:
                return await self.eval_keyword(obj_value, eval_args)
            if obj_type == COMMAND_NODE:
                return self.eval_command(obj_value, eval_args)

    async def eval_list(self, list_node):
        eval_children = []
        for child in list_node.children:
            eval_children.append(await self.evaluate(child))
        self.state.last_command_result = None
        return eval_children

    def eval_funvar(self, funvar):
        funvar_name = funvar.value
        if funvar_name not in self.fun_vars:
            raise Exception(f"Unknown function variable {funvar_name}")
        else:
            return self.fun_vars[funvar_name]
        
    def eval_var(self, var_node):
        if var_node.value not in self.state.vars:
            raise Exception(f"Unknown variable {var_node.value}")
        var = self.state.vars[var_node.value]
        if var.is_command:
            value = var.value.clone()
            self.state.last_command_result = value
            return value
        return var.value

    async def eval_keyword(self, keyword_name, args):
        if self.cli_controller is not None:
            await self.cli_controller.process_keyword(keyword_name, args)
        return None

    def eval_command(self, command_name, args):
        command = self.commands[command_name]
        self.state.last_command_result = None
        command.run(self.state, len(args), args)
        return self.state.last_command_result


class FunctionCommand():
    def __init__(self, parser, code, var_names):
        self.parser = parser
        self.code = code
        self.var_names = var_names
        
        temp_parser = CommandParser(self.parser.keywords, self.parser.commands, self.parser.state, fun_vars=self.var_names)
        tokens = tokenize(self.code)
        self.root_node = temp_parser.parse(tokens)
        
    def run(self, state, nargs, args):
        fun_vars = {}
        for i in range(1, nargs):
            fun_vars[self.var_names[i - 1]] = args[i]
        evaluator = NoKeywordCommandEvaluator(self.parser.state, self.parser.commands, fun_vars=fun_vars)
        state.last_command_result = evaluator.evaluate(self.root_node)


class NoKeywordCommandEvaluator:
    def __init__(self, state, command_dict, fun_vars={}):
        self.state = state
        self.commands = command_dict
        self.fun_vars = fun_vars

    def evaluate(self, parse_root: ParseNode):
        self.state.last_command_result = None
        parse_type = parse_root.type
        if parse_type == OBJECT_NODE:
            return self.eval_object(parse_root)
        elif parse_type == LIST_NODE:
            return self.eval_list(parse_root)
        elif parse_type == FUNVAR_NODE:
            return self.eval_funvar(parse_root)
        elif parse_type == VAR_NODE:
            return self.eval_var(parse_root)
        elif parse_type == KEYWORD_NODE:
            raise Exception("Cannot use keywords")
        elif parse_type == COMMAND_NODE:
            return self.eval_command(parse_root.value, [parse_root.value])
        else:
            return parse_root.value

    def eval_object(self, object_node):
        if len(object_node.children) < 1:
            return None

        primary = object_node.children[0]
        obj_type = primary.type
        obj_value = primary.value

        if len(object_node.children) == 1:
            return self.evaluate(primary)
        elif obj_type not in [KEYWORD_NODE, COMMAND_NODE, OBJECT_NODE]:
            raise Exception("Non command-like objects cannot have arguments")
        elif obj_type == OBJECT_NODE:
            children = object_node.children[1:]
            primary.children += children
            return self.eval_object(primary)
        else:
            eval_args = [obj_value]
            for child in object_node.children[1:]:
                eval_args.append(self.evaluate(child))

            if obj_type == KEYWORD_NODE:
                raise Exception("Cannot use keywords")
            if obj_type == COMMAND_NODE:
                return self.eval_command(obj_value, eval_args)

    def eval_list(self, list_node):
        eval_children = []
        for child in list_node.children:
            eval_children.append(self.evaluate(child))
        self.state.last_command_result = None
        return eval_children

    def eval_funvar(self, funvar):
        funvar_name = funvar.value
        if funvar_name not in self.fun_vars:
            raise Exception(f"Unknown function variable {funvar_name}")
        else:
            return self.fun_vars[funvar_name]
    
    def eval_var(self, var_node):
        if var_node.value not in self.state.vars:
            raise Exception(f"Unknown variable {var_node.value}")
        var = self.state.vars[var_node.value]
        if var.is_command:
            value = var.value.clone()
            self.state.last_command_result = value
            return value
        else:
            return var.value

    def eval_command(self, command_name, args):
        command = self.commands[command_name]
        self.state.last_command_result = None
        command.run(self.state, len(args), args)
        return self.state.last_command_result

if __name__ == "__main__":
    keywords = ["test", "exit"]
    commands = ["fill", "rainbow"]

    parser = CommandParser(keywords, commands, {})
    result = parser.parse(["exit", "-.1", '"test"', 'test',
                           '(', 'fill',  '3', ')', '[', '1', '3', '"string"', ']'])
    print(result)

    result = parser.parse(['rainbow', '(', 'rainbow', '0.0', ')'])
    print(result)

    try:
        result = parser.parse(['rainbow', '(', 'rainbow', '0.0'])
        print(result)
    except Exception as e:
        print(e)

    test_str = 'exit -.1 "test" test (fill 3) [ 1 3 "string "]  '
    tokens = tokenize(test_str)
    print(tokens)
    print(parser.parse(tokens))
