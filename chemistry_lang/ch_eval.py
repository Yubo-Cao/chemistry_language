from typing import Any

from .ch_handler import handler
from .ch_interpreter import interpreter
from .ch_parser import parse
from .ch_tokenizer import tokenize


def evaluate(code) -> Any:
    tokens = tokenize(code)
    if handler.had_error:
        handler.had_error = False
        return ""
    ast = parse(tokens)
    if handler.had_error:
        handler.had_error = False
        return ""
    return interpreter.evaluate(ast)
