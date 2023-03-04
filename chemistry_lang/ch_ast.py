from dataclasses import field, dataclass
from pathlib import Path
from typing import Any

from pint import Unit

from .objs import FormulaUnit, Reaction
from .ch_token import Token, TokenType


class Expr:
    """
    Abstract base class for expression.
    """


@dataclass(frozen=True)
class Write(Expr):
    expr: Expr
    to: Token
    path: Path

    def __str__(self):
        return f"{self.expr!s} -> {self.path!s}"


@dataclass(frozen=True)
class Interval(Expr):
    start: Any
    dots: Token
    end: Any

    def __str__(self):
        return f"{self.start!s} ... {self.end!s}"


@dataclass(frozen=True)
class Binary(Expr):
    left: Expr
    op: TokenType
    right: Expr

    def __str__(self):
        return f"{self.left!s} {self.op.value} {self.right!s}"


@dataclass(frozen=True)
class Unary(Expr):
    op: Token
    right: Expr

    def __str__(self):
        return f"{self.op}{self.right}"


@dataclass(frozen=True)
class Grouping(Expr):
    expr: Expr

    def __str__(self):
        return f"({self.expr})"


@dataclass(frozen=True)
class Conversion(Expr):
    value: Expr
    to: Token
    unit: Unit | FormulaUnit
    reaction: list[Reaction] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.value!s} -> {self.unit!s}"


@dataclass(frozen=True)
class Literal(Expr):
    value: Any

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Call(Expr):
    callee: Expr
    args: list[Expr]

    def __str__(self) -> str:
        return f"{self.callee!s}({', '.join(map(str, self.args))})"


@dataclass(frozen=True)
class Variable(Expr):
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Assign(Expr):
    name: str
    val: Any

    def __str__(self) -> str:
        return f"{self.name!s} = {self.val!s}"


# All those ast nodes get a token field to store keyword, as we want to
# report error to line.

# Actually, nothing is statement. Everything evaluate to a value. However,
# newline is a separator, so some kind of expression-y and statement-y mixture
# is presented, as follows


class Stmt:
    """
    Abstract base class for statement.
    """


@dataclass(frozen=True)
class Block(Stmt):
    body: tuple[Stmt, ...]

    def __str__(self) -> str:
        return "\n" + "\n".join(map(lambda stmt: " " * 4 + str(stmt), self.body)) + "\n"


@dataclass(frozen=True)
class Exam(Stmt):
    kw: Token
    cond: Expr
    pass_stmt: Block | Stmt
    fail_stmt: Block | Stmt

    def __str__(self) -> str:
        return f"exam {self.cond!s} {self.pass_stmt!s}" + (
            (" fail " + str(self.fail_stmt)) if self.fail_stmt else ""
        )


@dataclass(frozen=True)
class During(Stmt):
    kw: Token
    cond: Expr
    body: Block | Expr

    def __str__(self) -> str:
        return f"during {self.cond!s} {self.body!s}"


@dataclass(frozen=True)
class Work(Stmt):
    kw: Token
    identifier: str
    params: list[str]
    body: Block | Expr

    def __str__(self) -> str:
        return f"work {self.identifier!s}({', '.join(self.params)}) {self.body!s}"


@dataclass(frozen=True)
class Submit(Stmt):
    kw: Token
    expr: Expr

    def __str__(self) -> str:
        return f"submit {self.expr!s}"


@dataclass(frozen=True)
class ExprStmt(Stmt):
    kw: Token  # new line token
    expr: Expr

    def __str__(self) -> str:
        return str(self.expr)


@dataclass(frozen=True)
class Redo(Stmt):
    kw: Token
    identifier: str
    interval: Interval
    body: Block | Expr

    def __str__(self) -> str:
        return f"redo {self.identifier!s} of {self.interval!s} {self.body!s}"
