from grammar import ParseNode
from typing import Callable


class ControlState:
    controller = None
    send = print
    vars = {}
    commands = {}
    last_command_result = None
    
    def copy(self):
        copy = ControlState()
        copy.controller = self.controller
        copy.send = self.send
        copy.vars = self.vars.copy()
        copy.commands = self.commands.copy()
        return copy


class Evaluator:
    def __init__(self, 
                transformers: dict[str, Callable[[ControlState, list], any]], 
                preprocessors: dict[str, Callable[[ControlState, ParseNode], None]] = None):
        self.transformers = transformers
        self.preprocessors = preprocessors if preprocessors is not None else {}
        
    def evaluate(self, context: ControlState, parse_root: ParseNode):
        node_type = parse_root.type
        if node_type not in self.transformers:
            raise Exception(f"No transformer for type {node_type}")
        if node_type in self.preprocessors:
            context = self.preprocessors[node_type](context, parse_root)
        children = []
        for child in parse_root.children:
            if isinstance(child, ParseNode):
                val = self.evaluate(context, child)
                if val is not None:
                    children.append(val)
            else:
                children.append(child)
        return self.transformers[node_type](context, children)



def IdentityTransformer(context, children):
    if len(children) > 0:
        return children[0]
    else:
        return None

def PopTransformer(context, children):
    if len(children) > 0:
        return children[-1]
    else:
        return None

def DestroyerTransformer(context, children):
    return None

def ArrayTransformer(context, children):
    return children


def KeywordTransformer(context, children):
    if children[0] == "let":
        context.vars[children[1]] = children[3]
    elif children[0] == "get":
        context.send(context.vars[children[1]])
    elif children[0] == "read":
        pass
    elif children[0] == "wait":
        pass
    elif children[0] == "exit":
        pass
    else:
        raise Exception(f"Invalid keyword {children[0]}")
    return None


def StringTransformer(context, children):
    assert children[0] == "\"" and children[2] == "\""
    return children[1]

def NumberTransformer(context, children):
    return float(children[0])

def BoolTransformer(context, children):
    return True if children[0] == "true" else False

def ListTransformer(context, children):
    assert children[0] == "[" and children[2] == "]"
    return children[1]

def NameTransformer(context, children):
    name = children[0]
    if name in context.vars:
        return context.vars[name]
    elif name in context.commands:
        context.commands[name].run(context, 1, [name])
        result = context.last_command_result
        return result if result is not None else []
    else:
        raise Exception(f"Undefined symbol {name}")
    

def FunCallTransformer(context, children):
    name = children[0]
    args = children[1]
    if name not in context.commands:
        raise Exception(f"Command {name} not found")
    context.commands[name].run(context, len(args) + 1, [name] + args)
    result = context.last_command_result
    return result if result is not None else []


def ExprTransformer(context, children):
    # print(children)
    if children[0] == "(" and children[-1] == ")":
        return children[1]
    else:
        return IdentityTransformer(context, children)
    

def ScopeTransformer(context, children):
    assert children[0] == "{" and children[-1] == "}"
    return children[1]    

def ScopePreprocessor(context, parse_root):
    print("HERE")
    scoped_context = context.copy()
    return scoped_context



transformers = {
    "START": IdentityTransformer,
    "COMMANDS": PopTransformer,
    "COMMAND": IdentityTransformer,
    "LITERAL": IdentityTransformer,
    "CHARS": IdentityTransformer,
    
    "VAR_NAME": IdentityTransformer,
    "FUN_NAME": IdentityTransformer,
    "FUN_ARG": IdentityTransformer,
    
    "NEW_LINE": DestroyerTransformer,
    "SEPARATOR": DestroyerTransformer,
    
    "MULTI_LINE_FUN_CALL": FunCallTransformer,
    "MULTI_LINE_FUN_ARGS": ArrayTransformer,
    "FUN_CALL": FunCallTransformer,
    "FUN_ARGS": ArrayTransformer,
    
    "KEYWORD": KeywordTransformer,
    
    "STRING": StringTransformer,
    "NUMBER": NumberTransformer,
    "BOOL": BoolTransformer,
    "NAME": NameTransformer,
    
    "LIST": ListTransformer,
    "LIST_ELEMENTS": ArrayTransformer,
    
    "EXPR": ExprTransformer,
    "SCOPE": ScopeTransformer,
}

preprocessors = {
    "SCOPE": ScopePreprocessor,
}



if __name__ == "__main__":
    import grammar as gram
    
    import sys
    sys.path.append('../')
    from command_builder import CommandBuilder, CommandArgument, ObjectConverter, NumberConverter
    from effects.effects import ColorAdapter, WipeEffect, BaseEffect
    from colors import RainbowColorSelector
    
    rainbow = CommandBuilder("rainbow", lambda: ColorAdapter(RainbowColorSelector())).set_description(
        "Display a rainbow"
    )
    wipe = wipe = CommandBuilder("wipe", WipeEffect, [
        CommandArgument("EFFECT", "EFFECT", ObjectConverter(BaseEffect), "Effect to use"),
        CommandArgument("TIME", "NUMBER!=0", NumberConverter(exclude=[0]), "The period to complete a full wipe")
    ]).set_description("Fill strip with a color changing over time using the given effect")
    
    context = ControlState()
    context.vars["TEST"] = "HELLO WORLD"
    context.commands["rainbow"] = rainbow
    context.commands["wipe"] = wipe
    
    evaluator = Evaluator(transformers, preprocessors)
    # parsings = gram.grammar.parse(['[', '(', "wipe", "\n", 
    #                                     "rainbow", "-321", ')', '\n', 
    #                                '-3', ']'], gram.EXPR)
    parsings = gram.grammar.parse([
        'let', 'time', '=', '2', '\n',
        'let', 'earth', '=', '{', '\n',
        'let', 'color', '=', 'rainbow', '\n', 
        'let', 'time', '=', '1', '\n', 
        'wipe', 'color', 'time',
        # 'let', 'body', '=', 'pbody', '100', '\n',
        # 'let', 'effects', '=', '[', '(', 'force', '"', 'Gravity', '"', '1', ')', ']', '\n',
        # 'let', 'isCollidable', '=', 'false', '\n',
        # 'particle', 'color', ':', 'color', 'body', ':', 'body', 'size', 'effects', 'isCollidable', ':', 'isCollidable', '\n',
        '}', '\n',
        'time', '\n'
    ], gram.COMMANDS)
    # parsings = gram.grammar.parse(["let", "TEST", "=", "wipe", "rainbow", "3"], gram.KEYWORD)
    print(parsings)
    for parsing in parsings:
        print(evaluator.evaluate(context, parsing.nodes[0]))
        
    parsings = gram.grammar.parse(["earth", "\n"], gram.COMMANDS)
    print(parsings)
    for parsing in parsings:
        print(evaluator.evaluate(context, parsing.nodes[0]).period)