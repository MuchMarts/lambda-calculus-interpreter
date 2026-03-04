from __future__ import annotations

from typing import List, Optional

from .ast import Abs, App, BinaryOp, Expr, NumLit, Var
from .config import DEFAULT_FLOAT_PRECISION


def format_number(
    n: float,
    float_precision: Optional[int] = DEFAULT_FLOAT_PRECISION,
) -> str:
    if n.is_integer():
        return str(int(n))
    if float_precision is None:
        return repr(n)
    return format(n, f".{float_precision}g")


def pretty(expr: Expr, float_precision: Optional[int] = DEFAULT_FLOAT_PRECISION) -> str:
    if isinstance(expr, Var):
        return expr.name
    if isinstance(expr, Abs):
        return f"(λ{expr.param}.{pretty(expr.body, float_precision)})"
    if isinstance(expr, App):
        return f"({pretty(expr.fn, float_precision)} {pretty(expr.arg, float_precision)})"
    if isinstance(expr, NumLit):
        return format_number(expr.value, float_precision)
    if isinstance(expr, BinaryOp):
        return f"({pretty(expr.left, float_precision)} {expr.op} {pretty(expr.right, float_precision)})"
    raise TypeError(f"Unknown expression type: {type(expr)}")


def _node_label(expr: Expr, float_precision: Optional[int]) -> str:
    if isinstance(expr, Var):
        return f"Var({expr.name})"
    if isinstance(expr, Abs):
        return f"Abs(param={expr.param})"
    if isinstance(expr, App):
        return "App"
    if isinstance(expr, NumLit):
        return f"NumLit({format_number(expr.value, float_precision)})"
    if isinstance(expr, BinaryOp):
        return f"BinaryOp({expr.op})"
    raise TypeError(f"Unknown expression type: {type(expr)}")


def _children(expr: Expr) -> List[Expr]:
    if isinstance(expr, Var):
        return []
    if isinstance(expr, Abs):
        return [expr.body]
    if isinstance(expr, App):
        return [expr.fn, expr.arg]
    if isinstance(expr, NumLit):
        return []
    if isinstance(expr, BinaryOp):
        return [expr.left, expr.right]
    raise TypeError(f"Unknown expression type: {type(expr)}")


def _print_tree_lines(
    expr: Expr,
    float_precision: Optional[int],
    prefix: str = "",
    is_last: bool = True,
) -> None:
    connector = "`- " if is_last else "|- "
    print(f"{prefix}{connector}{_node_label(expr, float_precision)}")
    kids = _children(expr)
    child_prefix = prefix + ("   " if is_last else "|  ")
    for i, child in enumerate(kids):
        _print_tree_lines(child, float_precision, child_prefix, i == len(kids) - 1)


def print_tree(expr: Expr, float_precision: Optional[int] = DEFAULT_FLOAT_PRECISION) -> None:
    print(_node_label(expr, float_precision))
    kids = _children(expr)
    for i, child in enumerate(kids):
        _print_tree_lines(child, float_precision, "", i == len(kids) - 1)


def syntax_guide_text() -> str:
    lines = [
        "Syntax guide:",
        "  Terms:",
        "    variable:         x, foo, bar_1",
        "    number:           2, 3.14, .5, 10.",
        "    lambda:           Lx. x        (or \\x. x, or λx. x)",
        "    multi-arg lambda: Lx y. x+y    (= Lx. Ly. x+y)",
        "    application:      f x y        (= ((f x) y))",
        "    grouping:         ( ... )",
        "  Arithmetic:",
        "    +, -, *, /",
        "    precedence: * and / bind tighter than + and -",
        "  Shortcuts:",
        "    loaded from shortcuts.yaml",
        "    use by name, e.g. if true one two",
        "  Pipe sugar (argument passing):",
        "    f | a b c         (= (((f a) b) c))",
        "    f | (1+2) x       (= ((f (1+2)) x))",
        "    f | a | b         (= ((f a) b))",
        "    note: after '|', complex arguments should be parenthesized",
    ]
    return "\n".join(lines)
