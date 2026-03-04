from __future__ import annotations

from typing import List, Optional, Set

from .ast import Abs, App, BinaryOp, Expr, NumLit, Var


def free_vars(expr: Expr) -> Set[str]:
    if isinstance(expr, Var):
        return {expr.name}
    if isinstance(expr, Abs):
        return free_vars(expr.body) - {expr.param}
    if isinstance(expr, App):
        return free_vars(expr.fn) | free_vars(expr.arg)
    if isinstance(expr, BinaryOp):
        return free_vars(expr.left) | free_vars(expr.right)
    if isinstance(expr, NumLit):
        return set()
    raise TypeError(f"Unknown expression type: {type(expr)}")


def fresh_name(base: str, avoid: Set[str]) -> str:
    candidate = f"{base}_1"
    while candidate in avoid:
        parts = candidate.rsplit("_", maxsplit=1)
        if len(parts) == 2 and parts[1].isdigit():
            candidate = f"{parts[0]}_{int(parts[1]) + 1}"
        else:
            candidate = f"{candidate}_1"
    return candidate


def rename_bound_occurrences(expr: Expr, old: str, new: str) -> Expr:
    """
    Rename occurrences of `old` that are bound by an outer lambda.

    If an inner lambda binds the same variable name (`old`), traversal stops
    in that subtree to preserve shadowing.
    """
    if isinstance(expr, Var):
        return Var(new) if expr.name == old else expr
    if isinstance(expr, App):
        return App(
            rename_bound_occurrences(expr.fn, old, new),
            rename_bound_occurrences(expr.arg, old, new),
        )
    if isinstance(expr, BinaryOp):
        return BinaryOp(
            expr.op,
            rename_bound_occurrences(expr.left, old, new),
            rename_bound_occurrences(expr.right, old, new),
        )
    if isinstance(expr, NumLit):
        return expr
    if isinstance(expr, Abs):
        if expr.param == old:
            return expr
        return Abs(expr.param, rename_bound_occurrences(expr.body, old, new))
    raise TypeError(f"Unknown expression type: {type(expr)}")


def substitute(
    expr: Expr,
    var: str,
    replacement: Expr,
    alpha_log: Optional[List[str]] = None,
) -> Expr:
    if isinstance(expr, Var):
        return replacement if expr.name == var else expr

    if isinstance(expr, App):
        return App(
            substitute(expr.fn, var, replacement, alpha_log),
            substitute(expr.arg, var, replacement, alpha_log),
        )

    if isinstance(expr, BinaryOp):
        return BinaryOp(
            expr.op,
            substitute(expr.left, var, replacement, alpha_log),
            substitute(expr.right, var, replacement, alpha_log),
        )

    if isinstance(expr, NumLit):
        return expr

    if isinstance(expr, Abs):
        if expr.param == var:
            return expr

        replacement_fv = free_vars(replacement)
        if expr.param in replacement_fv:
            avoid = free_vars(expr.body) | replacement_fv | {var, expr.param}
            new_param = fresh_name(expr.param, avoid)
            renamed_body = rename_bound_occurrences(expr.body, expr.param, new_param)
            if alpha_log is not None:
                alpha_log.append(f"{expr.param}->{new_param}")
            return Abs(new_param, substitute(renamed_body, var, replacement, alpha_log))

        return Abs(expr.param, substitute(expr.body, var, replacement, alpha_log))

    raise TypeError(f"Unknown expression type: {type(expr)}")
