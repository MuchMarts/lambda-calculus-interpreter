from __future__ import annotations

from typing import Iterable, List, Optional

from .ast import Abs, App, BinaryOp, Expr, NumLit, Var
from .lexer import tokenize


class Parser:
    def __init__(self, tokens: Iterable[str]):
        self.tokens = list(tokens)
        self.pos = 0

    def parse(self) -> Expr:
        expr = self.parse_expr()
        if self._peek() == "|":
            expr = self.parse_pipe_application(expr)
        if self._peek() is not None:
            raise SyntaxError(f"Unexpected token at end: {self._peek()!r}")
        return expr

    def parse_expr(self) -> Expr:
        return self.parse_addsub()

    def parse_addsub(self) -> Expr:
        left = self.parse_muldiv()
        while self._peek() in {"+", "-"}:
            op = self._consume()
            right = self.parse_muldiv()
            left = BinaryOp(op, left, right)
        return left

    def parse_muldiv(self) -> Expr:
        left = self.parse_application()
        while self._peek() in {"*", "/"}:
            op = self._consume()
            right = self.parse_application()
            left = BinaryOp(op, left, right)
        return left

    def parse_application(self) -> Expr:
        left = self.parse_atom()
        while self._starts_atom(self._peek()):
            right = self.parse_atom()
            left = App(left, right)
        return left

    def parse_atom(self) -> Expr:
        tok = self._peek()
        if tok is None:
            raise SyntaxError("Unexpected end of input")

        if tok == "(":
            self._consume("(")
            expr = self.parse_expr()
            self._consume(")")
            return expr

        if tok == "λ":
            return self.parse_lambda()

        if self._is_number(tok):
            return NumLit(float(self._consume()))

        if tok.isidentifier():
            return Var(self._consume())

        raise SyntaxError(f"Unexpected token: {tok!r}")

    def parse_lambda(self) -> Expr:
        self._consume("λ")

        params: List[str] = []
        while True:
            tok = self._peek()
            if tok is not None and tok.isidentifier():
                params.append(self._consume())
            else:
                break

        if not params:
            raise SyntaxError("Lambda must have at least one parameter")

        self._consume(".")
        body = self.parse_expr()

        expr: Expr = body
        for p in reversed(params):
            expr = Abs(p, expr)
        return expr

    def parse_pipe_application(self, fn_expr: Expr) -> Expr:
        """
        Sugar:
            f | a b c        == (((f a) b) c)
            f | (1+2) x      == ((f (1+2)) x)
            f | a | b        == ((f a) b)

        After '|', arguments are parsed as atoms; wrap complex expressions
        in parentheses.
        """
        self._consume("|")
        args: List[Expr] = []

        while True:
            tok = self._peek()
            if tok is None:
                break
            if tok == "|":
                self._consume("|")
                if self._peek() is None:
                    raise SyntaxError("Expected argument after '|'")
            args.append(self.parse_atom())

        if not args:
            raise SyntaxError("Pipe application requires at least one argument")

        result = fn_expr
        for arg in args:
            result = App(result, arg)
        return result

    def _peek(self) -> Optional[str]:
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def _consume(self, expected: Optional[str] = None) -> str:
        tok = self._peek()
        if tok is None:
            raise SyntaxError("Unexpected end of input")
        if expected is not None and tok != expected:
            raise SyntaxError(f"Expected {expected!r}, found {tok!r}")
        self.pos += 1
        return tok

    @staticmethod
    def _is_number(tok: str) -> bool:
        try:
            float(tok)
            return True
        except ValueError:
            return False

    @staticmethod
    def _starts_atom(tok: Optional[str]) -> bool:
        if tok is None:
            return False
        if tok in {"(", "λ"}:
            return True
        if tok.isidentifier():
            return True
        return Parser._is_number(tok)


def parse(source: str) -> Expr:
    return Parser(tokenize(source)).parse()
