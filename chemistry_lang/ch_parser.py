from typing import Optional, List

from chemistry_lang.ch_ast import (
    Assign,
    Binary,
    Call,
    Conversion,
    Grouping,
    Literal,
    Unary,
    Variable,
    Interval,
    Write,
    Exam,
    Redo,
    During,
    Work,
    Submit,
    ExprStmt,
    Block,
)
from chemistry_lang.ch_error import CHError
from chemistry_lang.ch_handler import handler
from chemistry_lang.ch_objs import CHQuantity, CHString, FormulaUnit, Reaction
from chemistry_lang.ch_token import Token, TokenType
from chemistry_lang.ch_ureg import ureg


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Block:
        stmts = []
        while not self.end:
            try:
                stmts.append(self.stmt())
            except CHError:
                self.synchronize()
        return Block(tuple(stmts))

    def synchronize(self):
        """
        This function try to synchronize the parser, i.e., come back
        to next newline or statement so that we won't blow up cascading errors
        to user.
        """
        while (
            not self.match(
                TokenType.SEP,
                TokenType.EXAM,
                TokenType.DOC,
                TokenType.SUBMIT,
                TokenType.FAIL,
                TokenType.REDO,
                TokenType.DURING,
                TokenType.WORK,
            )
            and not self.end
        ):
            self.advance()

    def stmt(self):
        match self.peek.type:
            case TokenType.SEP:
                # Ignore empty newline
                self.sep()
            case TokenType.EXAM:
                return self.exam()
            case TokenType.REDO:
                return self.redo()
            case TokenType.DURING:
                return self.during()
            case TokenType.WORK:
                return self.work()
            case TokenType.SUBMIT:
                return self.submit()
            case _:
                return self.expr_stmt()

    def expr_stmt(self):
        expr = self.expr()
        kw = self.sep()
        return ExprStmt(kw, expr)

    def sep(self):
        return self.expect("Expect newline", TokenType.SEP)

    def submit(self):
        kw = self.expect("Expect 'submit'", TokenType.SUBMIT)
        expr = Literal(None)
        if self.peek.type != TokenType.SEP:
            expr = self.expr()
        self.sep()
        return Submit(kw, expr)

    def work(self):
        work = self.expect("Expect 'work'", TokenType.WORK)
        identifier = self.expect("Expect identifier", TokenType.ID).val
        self.expect("Expect '('", TokenType.LPAREN)
        params = []
        if self.peek.type == TokenType.ID:
            params = self.params()
        self.expect("Expect ')'", TokenType.RPAREN)
        body = self.be()
        self.opt_sep()
        return Work(work, identifier, params, body)

    def params(self):
        msg = "Expect parameter"
        params = [self.expect(msg, TokenType.ID).val]
        while self.match(TokenType.COMMA):
            # Ignore newline between parameters
            self.opt_sep()
            params.append(self.expect(msg, TokenType.ID).val)
            self.opt_sep()
        return params

    def redo(self):
        kw = self.expect("Expect 'redo'", TokenType.REDO)
        identifier = self.expect("Expect identifier", TokenType.ID).val
        self.expect("Expect 'of'", TokenType.OF)
        interval = self.interval()
        body = self.be()
        self.opt_sep()
        return Redo(kw, identifier, interval, body)

    def opt_sep(self):
        if self.match(TokenType.SEP):
            pass

    def during(self):
        kw = self.expect("Expect 'during'", TokenType.DURING)
        cond = self.expr()
        body = self.be()
        self.opt_sep()
        return During(kw, cond, body)

    def exam(self):
        kw = self.expect("Expect 'exam'", TokenType.EXAM)
        cond = self.expr()
        body = self.be()
        makeups = [(kw, cond, body)]
        while kw := self.match(TokenType.MAKEUP):
            cond = self.expr()
            body = self.be()
            makeups.append((kw, cond, body))
        if kw := self.match(TokenType.FAIL):
            body = self.be()
            makeups.append((kw, Literal(True), body))
        result = None
        for kw, cond, body in reversed(makeups):
            result = Exam(kw, cond, body, result)
        self.opt_sep()
        return result

    def be(self):
        # Block or Expression
        if self.match(TokenType.SEP):
            body = self.block()
        else:
            body = self.expr()
        return body

    def block(self):
        self.expect("Expect indent", TokenType.INDENT)
        stmts = []
        while not self.match(TokenType.DEDENT) and not self.end:
            stmts.append(self.stmt())
        return Block(tuple(stmts))

    def expr(self):
        return self.write()

    def write(self):
        expr = self.interval()
        if to := self.match(TokenType.TO):
            path = self.expect("Expect path", TokenType.PATH).val
            expr = Write(expr, to, path)
        return expr

    def interval(self):
        start = self.assign()
        if dots := self.match(TokenType.INTERVAL):
            end = self.assign()
            start = Interval(start, dots, end)
        return start

    def assign(self):
        left = self.or_expr()
        sugar = {
            TokenType.ADDEQ: TokenType.ADD,
            TokenType.SUBEQ: TokenType.SUB,
            TokenType.DIVEQ: TokenType.DIV,
            TokenType.MULEQ: TokenType.MUL,
            TokenType.MODEQ: TokenType.MOD,
            TokenType.MULMULEQ: TokenType.MULMUL,
            TokenType.CARETEQ: TokenType.CARET,
        }
        if op := self.match(*sugar, TokenType.EQ):
            # recursive -> right-associative.
            rvalue = self.expr()
            if not isinstance(left, Variable):
                raise self.error("Invalid left-hand side of assignment", self.peek)
            # de-sugaring
            if op.type != TokenType.EQ:
                rvalue = Binary(left, sugar[op.type], rvalue)
            left = Assign(left.name, rvalue)
        return left

    def binary_parse(self, nonterminal, *operator):
        left = nonterminal()
        while op := self.match(*operator):
            right = nonterminal()
            left = Binary(left, op.type, right)
        return left

    def or_expr(self):
        return self.binary_parse(self.and_expr, TokenType.OR)

    def and_expr(self):
        return self.binary_parse(self.eq, TokenType.AND)

    def eq(self):
        return self.binary_parse(self.cp, TokenType.EQEQ, TokenType.NOEQ)

    def cp(self):
        return self.binary_parse(
            self.term, TokenType.LE, TokenType.GE, TokenType.LT, TokenType.GT
        )

    def term(self):
        return self.binary_parse(self.factor, TokenType.ADD, TokenType.SUB)

    def reactions(self):
        rxns = [self.reaction()]
        while self.match(TokenType.COMMA):
            rxns.append(self.reaction())
        self.expect("Expect ':'", TokenType.COLON)
        return rxns

    def reaction(self):
        reactants = [self.expect("Need at least one reactant", TokenType.FORMULA).val]
        while self.match(TokenType.ADD):
            reactants.append(self.expect("Expect reactant", TokenType.FORMULA).val)
        to = self.expect("Expect '->' after reactants", TokenType.TO)
        products = [self.expect("Need at least one product", TokenType.FORMULA).val]
        while self.match(TokenType.ADD):
            products.append(self.expect("Expect product", TokenType.FORMULA).val)
        return Reaction(reactants, to, products)

    def factor(self):
        left = self.unary()
        while True:
            if op := self.match(TokenType.MUL, TokenType.DIV, TokenType.MOD):
                right = self.unary()
                left = Binary(left, op.type, right)
            elif self.match(TokenType.COLON):
                reactions = self.reactions()
                to = self.expect("Expect '->' after reaction.", TokenType.TO)
                unit = self.expect(
                    "Expect unit or formula after '->'",
                    TokenType.FORMULA,
                    TokenType.UNIT,
                )
                left = Conversion(left, to, unit.val, reactions)
            elif (
                self.peek.type == TokenType.TO and self.peek_next.type != TokenType.PATH
            ):
                while to := self.match(TokenType.TO):
                    left = Conversion(
                        left,
                        to,
                        self.expect(
                            "Expect unit or formula after '->'",
                            TokenType.FORMULA,
                            TokenType.UNIT,
                        ).val,
                        [],
                    )
            else:
                break
        return left

    def unary(self):
        if op := self.match(TokenType.ADD, TokenType.SUB, TokenType.INV, TokenType.NOT):
            expr = self.unary()
            return Unary(op.type, expr)
        return self.exp()

    def exp(self):
        left = self.call()
        if op := self.match(TokenType.CARET, TokenType.MULMUL):
            if self.match(TokenType.LBRACE):
                right = self.expr()
                self.expect("Expect '}'", TokenType.RBRACE)
            else:
                right = self.exp()
            return Binary(left, op.type, right)
        return left

    def call(self):
        callee = self.atom()
        while True:
            if self.match(TokenType.LPAREN):
                args = []
                # Handle 0 arguments case
                if not self.peek.type == TokenType.RPAREN:
                    args.append(self.expr())
                    while self.match(TokenType.COMMA):
                        args.append(self.expr())
                self.expect("Expect ')'", TokenType.RPAREN)
                callee = Call(callee, args)
            else:
                break
        return callee

    def atom(self):
        adv = self.advance()
        match adv.type:
            case TokenType.NUM:
                unit = ureg.dimensionless
                formula = FormulaUnit([])
                if self.match(TokenType.UNIT):
                    unit = self.previous.val
                    if self.match(TokenType.FORMULA):
                        formula = FormulaUnit([self.previous.val])
                elif self.match(TokenType.FORMULA):
                    unit = ureg.gram / ureg.mole
                    formula = FormulaUnit([self.previous.val])
                return Literal(CHQuantity(formula, adv.val, unit))
            case TokenType.PATH:
                return Literal(adv.val)
            case TokenType.STR:
                return Literal(CHString(adv.val, adv.attr["sub"]))
            case TokenType.NA:
                return Literal(None)
            case TokenType.ID:
                return Variable(adv.val)
            case TokenType.PASS:
                return Literal(True)
            case TokenType.FAIL:
                return Literal(False)
            case TokenType.FORMULA:
                return adv.val
            case TokenType.LPAREN:
                expr = self.expr()
                self.expect("Expect ')'", TokenType.RPAREN)
                return Grouping(expr)
            case _:
                self.error("Expect expression.", adv)

    @property
    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def advance(self) -> Token:
        if not self.end:
            self.current += 1
            return self.tokens[self.current - 1]
        else:
            return self.tokens[-1]

    @property
    def peek(self) -> Token:
        return self.tokens[self.current]

    @property
    def peek_next(self) -> Token:
        return (
            self.tokens[self.current + 1]
            if self.current < len(self.tokens) - 1
            else self.tokens[-1]
        )

    def match(self, *tokens: TokenType) -> Optional[Token]:
        if (res := self.peek).type in tokens:
            self.current += 1
            return res
        return None

    @property
    def end(self) -> bool:
        return self.tokens[self.current].type == TokenType.EOF

    def expect(self, msg: str = "Expect {tokens}", *tokens: TokenType) -> Token:
        if self.tokens[self.current].type not in tokens:
            msg = msg.format(tokens=" or ".join(str(token) for token in tokens))
            raise handler.error(msg, self.peek)
        return self.advance()

    def error(self, msg: str, token: Token) -> None:
        return handler.error(msg, token)


def parse(tokens: List[Token]) -> Block:
    parser = Parser(tokens)
    return parser.parse()
