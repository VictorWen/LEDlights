import re
from typing import Union

#TODO: Increase grammar power to include regular languages
#TODO: Change grammar parser to use Earley parser

class ParseState:
    def __init__(self, tokens, index=0):
        self.tokens = tokens
        self.index = index
        self.nodes = []
    
    def __repr__(self):
        return f"(index:{self.index}, node:{self.nodes[-1]})"
    
    def done(self):
        return self.index >= len(self.tokens)
    
    def token(self):
        return self.tokens[self.index]
    
    def next_token(self):
        self.index += 1

    def copy(self):
        state = ParseState(self.tokens.copy())
        state.index = self.index
        state.nodes = [node.copy() for node in self.nodes]
        return state


class ParseNode:
    def __init__(self, type, children=[]):
        self.type = type
        self.children = children
        
    def __repr__(self) -> str:
        lines = self.to_string()
        output = ""
        for line in lines:
            output += line + "\n"
        return output
    
    def to_string(self):
        child_strings = []
        for child in self.children:
            if isinstance(child, ParseNode): child_strings.extend(child.to_string())
            else: child_strings.append(f"'{child}'")
        output = [f"{self.type}("]
        for string in child_strings:
            output.append("  " + string)
        output.append(")")
        return output
    
    def add_child(self, child):
        self.children.append(child)
    
    def copy(self):
        children = []
        for child in self.children:
            if isinstance(child, str):
                children.append(child)
            else:
                children.append(child.copy())
        return ParseNode(self.type, children)


class Grammar:
    def __init__(self) -> None:
        self.symbols = {}
    
    def add_symbol(self, symbol):
        self.symbols[symbol.name] = symbol
        
    def parse(self, tokens, start):
        states = [ParseState(tokens)]
        states[0].nodes = [ParseNode("START")]
        states = start.parse(states)
        done_states = []
        for state in states:
            if state.done(): done_states.append(state)
        return done_states


class Symbol:
    def __init__(self, grammar, name):
        self.grammar = grammar
        self.name = name
        self.grammar.add_symbol(self)
    
    def parse(self, states):
        return []


class TermSymbol(Symbol):
    def __init__(self, grammar, name, regex, exclude=[]):
        super().__init__(grammar, name)
        self.regex = re.compile(regex)
        self.exclude = [re.compile(expr) for expr in exclude]
        
    def parse(self, states: list[ParseState]):
        output_states = []
        for state in states:
            if not state.done() \
            and not self._check_exclude(state.token()) \
            and self.regex.match(state.token()):
                node = ParseNode(self.name, [state.token()])
                copy = state.copy()
                copy.nodes[-1].add_child(node)
                # print(self.name, copy.token())
                copy.next_token()
                output_states.append(copy)
            if self.regex.match(""):
                # node = ParseNode(self.name, [""])
                copy = state.copy()
                # copy.nodes[-1].add_child(node)
                # print(self.name, "EMPTY")
                output_states.append(copy)
        return output_states
    
    def _check_exclude(self, token):
        for x in self.exclude:
            if x.match(token): return True
        return False


class VarSymbol(Symbol):
    def __init__(self, grammar, name):
        super().__init__(grammar, name)
        self.rules = []
    
    def set_rules(self, rules: list[list[Union[Symbol,str]]]):
        for rule in rules:
            for i in range(len(rule)):
                symbol = rule[i]
                if isinstance(symbol, str):
                    rule[i] = TermSymbol(self.grammar, "LITERAL", f"\A{symbol}\Z")
        self.rules = rules
        
    def parse(self, states: list[ParseState]):
        # print(f"Trying {self.name}")
        output_states = []
        for rule in self.rules:
            rule_states = [state.copy() for state in states]
            for state in rule_states: 
                state.nodes.append(ParseNode(self.name))
            for symbol in rule:
                rule_states = symbol.parse(rule_states)
                if len(rule_states) == 0: break
            output_states.extend(rule_states)
        for state in output_states:
            # print(f"Found {self.name}, {state.tokens[state.index:]}")
            top = state.nodes.pop(-1)
            state.nodes[-1].add_child(top)
        return output_states
    
    
class RepeatSymbol(Symbol):
    def __init__(self, grammar, name):
        super().__init__(grammar, name)
        self.min_repeat = 0
        self.sep = None
        self.end = None
    
    def set_rules(self, rules: list[list[Union[Symbol,str]]], min_repeat=0, sep="", end=""):
        for rule in rules:
            for i in range(len(rule)):
                symbol = rule[i]
                if isinstance(symbol, str):
                    rule[i] = TermSymbol(self.grammar, "LITERAL", f"\A{symbol}\Z")
        self.rules = rules
        assert(min_repeat >= 0)
        self.min_repeat = min_repeat
        self.sep = TermSymbol(self.grammar, "SEPARATOR", f"\A{sep}\Z")
        self.end = TermSymbol(self.grammar, "ENDING", f"\A{end}\Z")
        
    def parse(self, states: list[ParseState]):
        # print(f"Trying {self.name}")
        
        output_states = [state.copy() for state in states]
        for state in output_states: 
            state.nodes.append(ParseNode(self.name))
        
        for i in range(self.min_repeat):
            if i > 0:
                output_states = self.sep.parse(output_states)
            output_states = self._parse_repetition(output_states)
                  
        copy = [state.copy() for state in output_states]
        while len(copy) > 0:
            copy = self.sep.parse(copy)
            copy = self._parse_repetition(copy)
            output_states.extend(copy)
            copy = [state.copy() for state in copy]
        
        output_states = self.end.parse(output_states)
        for state in output_states:
            # print(f"Found {self.name}, {state.tokens[state.index:]}")
            top = state.nodes.pop(-1)
            state.nodes[-1].add_child(top)
        return output_states
    
    def _parse_repetition(self, states):
        output_states = []
        
        for rule in self.rules:
            rule_states = [state.copy() for state in states]
            for symbol in rule:
                rule_states = symbol.parse(rule_states)
                if len(rule_states) == 0: break
            output_states.extend(rule_states)
        
        return output_states


grammar = Grammar()

KEYWORDS = [
    "let",
    "get",
    "read",
    "wait",
    "exit",
    "true",
    "false"
]

CHARS = TermSymbol(grammar, "CHARS", r".*")
BOOL = TermSymbol(grammar, "BOOL", r"\A(false|true)\Z")
NUMBER = TermSymbol(grammar, "NUMBER", r"\A[+-]?((\d+\.?\d*)|(\d*\.?\d+))\Z")
NAME = TermSymbol(grammar, "NAME", r"\A[A-Za-z]\w*\Z", exclude=KEYWORDS)
VAR_NAME = TermSymbol(grammar, "VAR_NAME", r"\A[A-Za-z]\w*\Z", exclude=KEYWORDS)
FUN_NAME = TermSymbol(grammar, "FUN_NAME", r"\A[A-Za-z]\w*\Z", exclude=KEYWORDS)
NEW_LINE = TermSymbol(grammar, "NEW_LINE", r"\A\n*\Z")
REQ_NEW_LINE = TermSymbol(grammar, "NEW_LINE", r"\A\n+\Z")

COMMANDS = RepeatSymbol(grammar, "COMMANDS")
SCOPE = VarSymbol(grammar, "SCOPE")

COMMAND = VarSymbol(grammar, "COMMAND")
KEYWORD = VarSymbol(grammar, "KEYWORD")
EXPR = VarSymbol(grammar, "EXPR")

MULTI_LINE_FUN_CALL = VarSymbol(grammar, "MULTI_LINE_FUN_CALL")
FUN_CALL = VarSymbol(grammar, "FUN_CALL")
FUN_VARS = RepeatSymbol(grammar, "FUN_VARS")
FUN_ARGS = RepeatSymbol(grammar, "FUN_ARGS")
MULTI_LINE_FUN_ARGS = RepeatSymbol(grammar, "MULTI_LINE_FUN_ARGS")
FUN_ARG = VarSymbol(grammar, "FUN_ARG")

STRING = VarSymbol(grammar, "STRING")
LIST = VarSymbol(grammar, "LIST")
LIST_ELEMENTS = RepeatSymbol(grammar, "LIST_ELEMENTS")


COMMANDS.set_rules([
    [COMMAND, REQ_NEW_LINE]
], min_repeat=1)

COMMAND.set_rules([
    [KEYWORD],
    [EXPR],
    [FUN_CALL]
])

KEYWORD.set_rules([
    ["let", VAR_NAME, "=", EXPR],
    ["let", VAR_NAME, "=", FUN_CALL],
    ["get", VAR_NAME],
    ["read", STRING],
    ["wait", NUMBER],
    ["exit"]
])

EXPR.set_rules([
    ["\(", NEW_LINE, EXPR, NEW_LINE, "\)"],
    ["\(", NEW_LINE, MULTI_LINE_FUN_CALL, NEW_LINE, "\)"],
    [SCOPE],
    [STRING],
    [NUMBER],
    [BOOL],
    [LIST],
    [NAME],
])

SCOPE.set_rules([
    ["{", NEW_LINE, COMMANDS, "}"],
    ["{", NEW_LINE, COMMAND, "}"],
    ["{", NEW_LINE, COMMANDS, COMMAND, "}"],
])

MULTI_LINE_FUN_CALL.set_rules([
    [FUN_NAME, NEW_LINE, MULTI_LINE_FUN_ARGS]
])

FUN_CALL.set_rules([
    [FUN_NAME, FUN_ARGS]
])

FUN_VARS.set_rules([
    [VAR_NAME]
], min_repeat=0)

FUN_ARGS.set_rules([
    [FUN_ARG]
], min_repeat=1)

MULTI_LINE_FUN_ARGS.set_rules([
    [FUN_ARG],
], min_repeat=1, sep=r"\n*")

FUN_ARG.set_rules([
    [VAR_NAME, ":", EXPR],
    [EXPR]
])


STRING.set_rules([
    ["\"", CHARS, "\""]
])

LIST.set_rules([
    ["\[", NEW_LINE, LIST_ELEMENTS, NEW_LINE,"\]"]
])

LIST_ELEMENTS.set_rules([
    [EXPR]
], min_repeat=0, sep=r"\n*")


if __name__ == "__main__":
    # print(grammar.parse([
    #     "exit",
    # ], COMMANDS))
    print(grammar.parse([
        "[", "TEST", "TEST", "\n\n", "TEST", "]",
    ], LIST))
    # print(grammar.parse([
    #     'let', 'earth', '=', '{', '\n',
    #     'let', 'color', '=', 'gradient', 'BLUE', 'CLEAR', '\n',
    #     'let', 'body', '=', 'pbody', '100', '\n',
    #     'let', 'effects', '=', '[', '(', 'force', '"', 'Gravity', '"', '1', ')', ']', '\n',
    #     'let', 'isCollidable', '=', 'false', '\n',
    #     'particle', 'color', ':', 'color', 'body', ':', 'body', 'size', 'effects', 'isCollidable', ':', 'isCollidable', '\n',
    #     '}', '\n'
    # ], COMMANDS))