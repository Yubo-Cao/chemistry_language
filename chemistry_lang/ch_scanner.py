from decimal import Decimal
from functools import partial
from itertools import groupby
from pathlib import Path
from typing import Any, Callable, Literal, cast, Optional

from ch_base import shared_lazy_loading
from ch_error import CHError
from ch_handler import handler
from ch_objs import Element, SubFormula, Formula
from ch_periodic_table import periodic_table
from ch_token import Token, TokenType
from ch_ureg import ureg


class Scanner:
    WHITESPACE = {" ": 1, "\t": 4}

    KEYWORDS = {
        "na": TokenType.NA,
        "exam": TokenType.EXAM,
        "done": TokenType.DONE,
        "submit": TokenType.SUBMIT,
        "pass": TokenType.PASS,
        "fail": TokenType.FAIL,
        "redo": TokenType.REDO,
        "during": TokenType.DURING,
        "makeup": TokenType.MAKEUP,
        "of": TokenType.OF,
        "work": TokenType.WORK,
        "doc": TokenType.DOC,
    }

    def __init__(self, input_string: str):
        self.input = input_string.strip()
        self.current = 0
        self.start = 0
        self.line = 1
        self.start_of_line = True
        self.indent_stack: list[int] = []
        self.tokens: list[Token] = []

    def error(self, message: str):
        handler.error(message, self.line)

    def expect(self, message: str, predicate: Callable[[], Any] | str):
        if callable(predicate):
            result = predicate()
            if not result:
                return handler.error(message, self.line)
            return result
        else:
            if self.match(predicate):
                return True
            return handler.error(message, self.line)

    @shared_lazy_loading
    def chem_start_letter(self):
        return {
            first_letter: set(v[1] if len(v) > 1 else "" for v in rest)
            for first_letter, rest in groupby(
                sorted(periodic_table.periodic_table.keys()),
                key=lambda element: element[0],
            )
        }

    # A series of helper method to help scan tokens

    @property
    def end(self) -> bool:
        return self.current >= len(self.input)

    @property
    def previous(self) -> str:
        return self.input[self.current - 1] if self.current > 0 else ""

    @property
    def peek(self) -> str:
        return self.input[self.current] if not self.end else ""

    def advance(self) -> str:
        if not self.end:
            self.current += 1
            return self.input[self.current - 1]
        return ""

    def match(self, *char: str) -> str:
        if self.peek in char:
            result = self.peek
            self.current += 1
            return result
        return ""

    def proceed(self):
        self.start = self.current

    def add_token(
            self, token_type: TokenType, value: Any = None, attr: Any = None
    ) -> None:
        self.tokens.append(Token(token_type, value, self.line, attr))

    def scan_tokens(self) -> list[Token]:
        while not self.end:
            self.scan_token()
            self.start = self.current
        if self.input[-1] != "\n":
            self.add_token(TokenType.SEP)
        while self.indent_stack:
            self.add_token(TokenType.DEDENT, self.indent_stack.pop())
        self.add_token(TokenType.EOF)
        return self.tokens

    # Real scanning methods start here.

    def scan_token(self) -> None:
        self.indent()

        # Consume a character and start checking for a token.
        prev = self.advance()
        match prev:
            # Already handled by indent. Ignored
            case " " | "\t":
                pass
            # One character tokens
            case "(" | ")" | "{" | "}" | "," | "_" | "?" | ":" | "~":
                return self.add_token(TokenType(prev))
            # Two character tokens which may optionally be followed by '=' as short
            # hand of a x= b => a = a x b, where x in any operators listed below
            case "+" | "!" | "%" | "<" | ">" | "=" | "^" | "/":
                if self.match("="):
                    self.add_token(TokenType(prev + "="))
                else:
                    self.add_token(TokenType(prev))
            case "-":
                if self.match(">"):
                    self.add_token(TokenType(prev + ">"))
                elif self.match("="):
                    self.add_token(TokenType(prev + "="))
                else:
                    self.add_token(TokenType(prev))
            # Three character tokens. **, **=, and *
            case "*":
                if self.match("*"):
                    if self.match("="):
                        self.add_token(TokenType.MULMULEQ)
                    else:
                        self.add_token(TokenType.MULMUL)
                else:
                    self.add_token(TokenType.MUL)
            # '&&' and '||'
            case "&":
                self.expect("Expect '&' to be followed by '&'", "&")
                self.add_token(TokenType.AND)
            # '||' serve as or. However, '|' are used to quote paths
            case "|":
                if self.match("|"):
                    self.add_token(TokenType.OR)
                else:
                    if not self.path():
                        handler.error("Invalid character '|'", self.line)
            # '\r' is ignored. So we discarded user of macOS
            case "\n":
                self.start_of_line = True
                self.line += 1
                self.add_token(TokenType.SEP)
            # digits
            case "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "0":
                self.add_token(TokenType.NUM, self.number())
            # chemical element
            case "V" | "N" | "X" | "B" | "K" | "W" | "U" | "G" | "M" | "P" | "S" | "Y" | "A" | "T" | "E" | "F" | "Z" | "O" | "D" | "H" | "R" | "C" | "L" | "I":
                # since formula ->  ( element ( subscript )? ( superscript )? )+.
                # giving element a flag about whether first letter is already checked
                # it a little ponderous, we use backtrack the first letter
                self.current -= 1
                formula = self.formula()
                if formula:
                    self.add_token(TokenType.FORMULA, formula)
                elif not self.id():
                    self.path()
            # escaped identifier
            case "`":
                self.expect("Expect identifier", self.id)
            # string
            case '"' | "'":
                self.string()
            # comment i.e. post script
            case "p":
                if self.match("s"):
                    self.ps()
                elif not self.id():
                    self.path()
            # substituted string
            case "s":
                if self.match('"') or self.match("'"):
                    self.start += 1
                    self.string(sub=True)
                elif not self.id():
                    self.path()
                # since start with s, it is impossible to be docstring
            # interval. but we don't have OOP, so dot itself is not legit
            case ".":
                if self.match(".") and self.match("."):
                    self.add_token(TokenType.INTERVAL)
                else:
                    handler.error("Invalid character '.'", self.line)
            # default, identifier or path
            case _:
                if prev.isalpha():
                    if self.id():
                        if self.tokens[-1].type == TokenType.DOC:
                            self.tokens.pop(-1)
                            self.docstring()
                        return
                    else:
                        self.path()
                        return
                handler.error(f"Invalid character {prev!r}", self.line)

    def docstring(self):
        done_idx = self.input.find("done", self.current)
        raw_done = done_idx
        if done_idx == -1:
            handler.error("Unterminated docstring", self.line)
        else:
            self.between(predicate=lambda c: c.isspace())
            done_idx -= 1
            line_offset = 0

            while self.input[done_idx].isspace():
                if self.input[done_idx] == "\n":
                    line_offset += 1
                done_idx -= 1

            lines = self.input[self.current: done_idx + 1].split("\n")

            min_white_space = min(self.count_white_space(line) for line in lines)
            docstring = "\n".join(line[min_white_space:] for line in lines)

            self.add_token(TokenType.STR, docstring, attr={"sub": True})

            self.line += line_offset
            self.current = raw_done + 4

    @staticmethod
    def count_white_space(line):
        idx = len(line) - len(line.lstrip())
        return sum(
            map(
                lambda x: 1 if line[x] == " " else (4 if line[x] == "\t" else 0),
                range(idx),
            )
        )

    def id(self) -> bool:
        """
        The id function is used to match identifiers. It is a function that takes in
        a string and returns true if the string is an identifier, false otherwise.


        :param self: Access the instance variables of the class
        :return: The identifier
        """

        # User can use "`" to quote anything and make it an identifier
        if self.previous == "`":
            self.between("`")
            self.expect(
                "Expect '`' to be followed by '`'. Unterminated identifier.", "`"
            )
            self.add_token(
                TokenType.ID,
                self.input[self.start + 1: self.current - 1].replace("\\`", "`"),
            )
        # If they do not quote, we assume it is an identifier. If it is followed by
        # a '\', it is a path. Otherwise, it is a keyword, unit, or finally, an
        # identifier that user may use.
        else:
            backtrack = self.current
            self.between(predicate=lambda x: x.isalnum() or x == "_")

            if self.peek == "\\":
                self.current = backtrack
                return False

            identifier = self.input[self.start: self.current]

            if identifier in self.KEYWORDS:
                self.add_token(TokenType(identifier), identifier)
            elif identifier in ureg:
                self.add_token(TokenType.UNIT, ureg(identifier).units)
            else:
                self.add_token(TokenType.ID, identifier)
        return True

    def between(
            self,
            start: str = "",
            end: str = cast(str, ...),
            predicate: Callable = cast(Callable, ...),
            escapable: bool = True,
    ):
        """
        The between function is a helper function that allows we to parse:
            - a quoted substring
            - a paired substring, support nested
            - a customized predicate, e.g., isalpha, isalnum, etc.
        Index current will terminate on first ending character, or first character that
        does not pass predicate.

        :param self: Access the class properties
        :param start:str: Define the start of a string
        :param end:str: Allow the between function to be used for both matching and non-matching braces
        :param predicate:Callable: Check if the current character is valid
        :param escapable:bool: Determine whether the parser should treat backslashes as escape characters
        :return: The string between two other strings
        """

        end = cast(str, start if end is ... else end)
        if predicate is not ...:
            while not self.end and predicate(self.peek):
                if self.peek == "\n":
                    self.line += 1
                self.advance()
        elif end == start:
            while (
                    self.peek != start or self.previous == "\\"
                    if escapable
                    else self.peek != start
            ) and not self.end:
                if self.peek == "\n":
                    self.line += 1
                self.advance()
        else:
            stack = [start]
            while not self.end:
                if self.peek == "\n":
                    self.line += 1
                if self.peek == start and not escapable or not self.previous == "\\":
                    stack.append(start)
                elif self.peek == end and not escapable or not self.previous == "\\":
                    if stack.pop() != start:
                        handler.error(f"Unmatched braces. Expect '{end}'", self.line)
                if not stack:
                    break
                self.current += 1
            if stack:
                handler.error(f"Unmatched braces. Expect '{end}'", self.line)

    def number(self):
        while self.peek.isdigit() or self.peek == "_":
            self.advance()
        if self.peek == "." and self.input[self.current + 1].isdigit():
            self.match(".")
            while self.peek.isdigit() or self.peek == "_":
                self.advance()
            if self.match("e", "E"):
                self.match("+", "-")
                while self.peek.isdigit():
                    self.advance()

        # Decimal handles float/integer very well. So we piggyback on it.
        num = self.input[self.start: self.current]
        try:
            return Decimal(num) if num else ""
        except CHError:
            handler.error("Invalid number {}".format(num), self.line)

    def string(self, sub: bool = False):
        pair = self.previous
        self.between(pair)
        self.expect(f"Unterminated string literal. Expect '{pair}'", pair)

        self.add_token(
            TokenType.STR,
            self.input[self.start + 1: self.current - 1],
            {"sub": sub},
        )

    def ps(self):
        self.between(predicate=lambda c: c != "\n")
        self.add_token(TokenType.SEP)
        self.current += 1
        self.line += 1
        self.start_of_line = True

    def is_path_char(self, c: str):
        return not c.isspace() and c not in '<>"/|?*(){}'

    def path(self) -> bool:
        if self.previous == "|":
            self.between("|")
            self.expect("Unterminated path", "|")
            self.add_token(TokenType.PATH, Path(self.input[self.start + 1: self.current - 1]))
            return True
        else:
            self.between(self.is_path_char)
            end = self.current

            # We require a path to contain either, a drive name, e.g., C:, or at least one slash, e.g., \
            # doing so meet the design requirement of a path.
            if self.start != self.current and (
                    "\\" in (res := self.input[self.start: end]) or ":" in res
            ):
                self.add_token(TokenType.PATH, Path(self.input[self.start: end]))
                return True
        return False

    def element_name(self):
        backtrack = self.current
        start = self.match(*self.chem_start_letter.keys())
        matched = (
                self.match(*(sec := self.chem_start_letter.get(start, {}))) or "" in sec
        )
        if not matched:
            self.current = backtrack
            return ""
        else:
            return self.input[self.start: self.current]

    def script(self, start: Literal["_", "^"] = "_", default: Decimal = None):
        if self.match(start):
            self.start += 1
            if self.match("{"):
                self.start += 1
                while self.peek != "}" and not self.end:
                    self.advance()
                self.expect(
                    "Unterminated {'sub' if start == '_' else 'super'}script", "}"
                )
                return self.input[self.start: self.current - 1]
            else:
                # Subscript and superscript have infinite significance
                return self.expect(f"Expect number after '{start}'", self.number)
        else:
            return self.number() or default

    def element(self) -> Optional[Element]:
        name = self.element_name()
        if not name:
            return None
        self.proceed()
        subscript = self.script(default=Decimal(1))
        self.proceed()
        superscript = self.script("^", default=Decimal(0))
        self.proceed()
        return Element(name, subscript, superscript)

    def formula(self) -> Formula:
        """
        It parses a chemical formula
        :return: A Compound object
        """
        result = self._formula()
        if result is None:
            return None
        else:
            return Formula(result)
    
    def _formula(self) -> Optional[list[SubFormula | Element]]:
        """
        Implementation detail of formula
        """

        current_backtrack = self.current
        start_backtrack = self.start

        elements: list[Element | SubFormula] = []
        while not self.end:
            if self.match("("):
                self.proceed()
                formula = self._formula()
                self.expect(
                    "Expect ')'. Unmatched '(' at {line}", partial(self.match, ")")
                )
                self.proceed()
                subscript = self.expect(
                    "Expect number after parenthesis at line {line}", self.script
                )
                self.proceed()
                superscript = self.script("^", default=Decimal(0))
                elements.append(SubFormula(tuple(formula), subscript, superscript))
            elif self.peek == ")":
                return elements
            elif self.peek in self.chem_start_letter:
                element = self.element()
                if element is None:
                    break
                elements.append(cast(Element, element))
            else:
                break

        # it must an identifier since compound does not munch maximum
        if self.peek.isalnum() or self.peek == "_":
            self.current = current_backtrack
            self.start = start_backtrack
            return None

        return elements

    def indent(self) -> None:
        """
        The indent function is responsible for keeping track of the current indentation
        level. It does this by adding a DEDENT token to the token stream if we
        encounter an indentation that is less than or equal to our current level. If we
        encounter an indentation greater than our current level, then it adds that new
        """

        if self.start_of_line:
            depth = 0
            while (d := Scanner.WHITESPACE.get(self.peek, 0)) and not self.end:
                self.current += 1
                depth += d
            self.start = self.current
            self.start_of_line = False

            while self.indent_stack and self.indent_stack[-1] > depth:
                self.add_token(TokenType.DEDENT, self.indent_stack.pop())

            if depth != 0 and (
                    not self.indent_stack
                    or self.indent_stack
                    and depth > self.indent_stack[-1]
            ):
                self.indent_stack.append(depth)
                self.add_token(TokenType.INDENT, depth)
