from __future__ import annotations

from typing import List, Optional, Tuple

from .ast import Abs, App, BinaryOp, Expr, NumLit, StepInfo
from .substitution import substitute

# Evaluates numeric operations
def _eval_binary(op: str, left: float, right: float) -> Tuple[float, str]:
    if op == "+":
        return left + right, "δ+"
    if op == "-":
        return left - right, "δ-"
    if op == "*":
        return left * right, "δ*"
    if op == "/":
        if right == 0:
            raise ZeroDivisionError("Division by zero")
        return left / right, "δ/"
    raise ValueError(f"Unsupported operator: {op}")


def reduce_once(expr: Expr) -> tuple[Expr, bool, Optional[StepInfo]]:
    if isinstance(expr, App):
        if isinstance(expr.fn, Abs):
            alpha_log: List[str] = []
            reduced = substitute(expr.fn.body, expr.fn.param, expr.arg, alpha_log)
            if alpha_log:
                return reduced, True, StepInfo("β", f"alpha: {', '.join(alpha_log)}")
            return reduced, True, StepInfo("β")

        new_fn, changed, info = reduce_once(expr.fn)
        if changed:
            return App(new_fn, expr.arg), True, info

        new_arg, changed, info = reduce_once(expr.arg)
        if changed:
            return App(expr.fn, new_arg), True, info

        return expr, False, None

    if isinstance(expr, BinaryOp):
        if isinstance(expr.left, NumLit) and isinstance(expr.right, NumLit):
            value, rule = _eval_binary(expr.op, expr.left.value, expr.right.value)
            return NumLit(value), True, StepInfo(rule)

        new_left, changed, info = reduce_once(expr.left)
        if changed:
            return BinaryOp(expr.op, new_left, expr.right), True, info

        new_right, changed, info = reduce_once(expr.right)
        if changed:
            return BinaryOp(expr.op, expr.left, new_right), True, info

        return expr, False, None

    if isinstance(expr, Abs):
        new_body, changed, info = reduce_once(expr.body)
        if changed:
            return Abs(expr.param, new_body), True, info
        return expr, False, None

    return expr, False, None
