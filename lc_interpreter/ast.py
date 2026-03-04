from __future__ import annotations

from dataclasses import dataclass


class Expr:
    """Base class for all lambda calculus expressions."""


# Core lambda calculus expressions
@dataclass(frozen=True)
class Var(Expr):
    name: str

@dataclass(frozen=True)
class Abs(Expr):
    param: str
    body: Expr

@dataclass(frozen=True)
class App(Expr):
    fn: Expr
    arg: Expr

# Custom literals, used to handle math expressions
@dataclass(frozen=True)
class NumLit(Expr):
    value: float

@dataclass(frozen=True)
class BinaryOp(Expr):
    op: str
    left: Expr
    right: Expr

# Step information for reduction steps
@dataclass(frozen=True)
class StepInfo:
    rule: str
    detail: str = ""
