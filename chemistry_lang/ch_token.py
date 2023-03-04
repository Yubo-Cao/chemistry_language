from enum import Enum
from typing import NamedTuple, Any


class TokenType(Enum):
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    COLON = ":"
    QUEST = "?"
    COMMA = ","
    DOT = "."
    SUB = "-"
    SUBEQ = "-="
    ADD = "+"
    ADDEQ = "+="
    DIV = "/"
    DIVEQ = "/="
    MUL = "*"
    MULEQ = "*="
    MOD = "%"
    MODEQ = "%="
    INV = "~"
    MULMUL = "**"
    MULMULEQ = "**="
    CARET = "^"
    CARETEQ = "^="
    INTERVAL = "..."

    SEP = "\n"

    UNDERSCORE = "_"
    TO = "->"

    NOT = "!"
    NOEQ = "!="

    EQ = "="
    EQEQ = "=="

    GE = ">="
    GT = ">"

    LE = "<="
    LT = "<"

    AND = "&&"
    ANDEQ = "&&="
    OR = "||"
    OREQ = "||="

    PATH = "path"
    PIPE = "|"

    ID = "identifier"
    STR = "string"
    NUM = "number"

    NA = "na"
    EXAM = "exam"
    DONE = "done"
    SUBMIT = "submit"
    PASS = "pass"
    FAIL = "fail"
    REDO = "redo"
    DURING = "during"
    MAKEUP = "makeup"
    OF = "of"
    WORK = "work"
    DOC = "doc"

    UNIT = "unit"
    FORMULA = "formula"

    EOF = ""

    INDENT = "indent"
    DEDENT = "dedent"


class Token(NamedTuple):
    type: TokenType
    val: Any = None
    line: int = 1
    attr: Any = None
