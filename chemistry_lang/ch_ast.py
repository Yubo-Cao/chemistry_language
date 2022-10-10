from dataclasses import field
from pathlib import Path
from typing import Any, NamedTuple

from pint import Unit

from ch_objs import FormulaUnit, Reaction
from ch_token import Token, TokenType


class Expr:
    """
    Abstract base class for expression.
    """


class Write(NamedTuple):
    expr: Expr
    to: Token
    path: Path

    def __str__(self):
        return f"{self.expr!s} -> {self.path!s}"


class Interval(NamedTuple):
    start: Any
    dots: Token
    end: Any

    def __str__(self):
        return f"{self.start!s} ... {self.end!s}"


class Binary(NamedTuple):
    left: "Unary"
    op: TokenType
    right: "Unary"

    def __str__(self):
        return f"{self.left!s} {self.op.value} {self.right!s}"


class Unary(NamedTuple):
    op: Token
    right: "Unary"

    def __str__(self):
        return f"{self.op}{self.right}"


class Grouping(NamedTuple):
    expr: Expr

    def __str__(self):
        return f"({self.expr})"


class Conversion(NamedTuple):
    value: Expr
    to: Token
    unit: Unit | FormulaUnit
    reaction: list[Reaction] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.value!s} -> {self.unit!s}"


class Literal(NamedTuple):
    value: Any

    def __str__(self) -> str:
        return str(self.value)


class Call(NamedTuple):
    callee: Expr  # Specfically, it evaluate to a CHWork
    args: list[str]

    def __str__(self) -> str:
        return f"{self.callee!s}({', '.join(map(str, self.args))})"


class Variable(NamedTuple):
    name: str

    def __str__(self) -> str:
        return self.name


class Assign(NamedTuple):
    name: str
    val: Any

    def __str__(self) -> str:
        return f"{self.name!s} = {self.val!s}"


# All those ast nodes get a token field to store keyword, as we want to
# report error to line.

# Actually, nothing is statement. Everything evaluate to a value. However
# newline is a separator, so some kind of expression-y and statement-y mixture
# is presented, as follows


class Block(NamedTuple):
    body: tuple[Expr]

    def __str__(self) -> str:
        return "\n" + "\n".join(map(lambda stmt: " " * 4 + str(stmt), self.body)) + "\n"


class Exam(NamedTuple):
    kw: Token
    cond: Expr
    pass_stmt: Block | Expr
    fail_stmt: Block | Expr

    def __str__(self) -> str:
        return f"exam {self.cond!s} {self.pass_stmt!s}" + (
            (" fail " + str(self.fail_stmt)) if self.fail_stmt else ""
        )


class During(NamedTuple):
    kw: Token
    cond: Expr
    body: Block | Expr

    def __str__(self) -> str:
        return f"during {self.cond!s} {self.body!s}"


class Work(NamedTuple):
    kw: Token
    identifier: str
    params: list[str]
    body: Block | Expr

    def __str__(self) -> str:
        return f"work {self.identifier!s}({', '.join(self.params)}) {self.body!s}"


class Submit(NamedTuple):
    kw: Token
    expr: Expr

    def __str__(self) -> str:
        return f"submit {self.expr!s}"


class ExprStmt(NamedTuple):
    kw: Token
    expr: Expr

    def __str__(self) -> str:
        return str(self.expr)


class Redo(NamedTuple):
    kw: Token
    identifier: str
    interval: Interval
    body: Block | Expr

    def __str__(self) -> str:
        return f"redo {self.identifier!s} of {self.interval!s} {self.body!s}"
