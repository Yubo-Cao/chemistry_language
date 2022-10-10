from collections import namedtuple
from enum import Enum

Token = namedtuple("Token", ["type", "val", "line", "attr"])


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
