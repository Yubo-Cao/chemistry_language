from typing import Any

from chemistry_lang.ch_handler import handler
from chemistry_lang.ch_interpreter import interpreter
from chemistry_lang.ch_parser import parse
from chemistry_lang.ch_tokenizer import tokenize


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
