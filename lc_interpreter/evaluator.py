from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from .ast import Expr
from .config import DEFAULT_FLOAT_PRECISION
from .parser import parse
from .reduction import reduce_once
from .render import pretty
from .shortcuts import expand_with_shortcuts


def evaluate(
    expr: Expr,
    max_steps: int = 1000,
) -> Expr:
    current = expr
    for _ in range(max_steps):
        current, changed, _ = reduce_once(current)
        if not changed:
            return current
    raise RuntimeError("Maximum reduction steps exceeded")


def evaluate_with_trace(
    expr: Expr,
    max_steps: int = 1000,
    float_precision: Optional[int] = DEFAULT_FLOAT_PRECISION,
) -> Tuple[Expr, List[str]]:
    trace: List[str] = []
    current = expr
    for i in range(1, max_steps + 1):
        next_expr, changed, info = reduce_once(current)
        if not changed:
            return current, trace

        label = info.rule if info is not None else "?"
        if info is not None and info.detail:
            label = f"{label} ({info.detail})"
        trace.append(
            f"{i}. [{label}] {pretty(current, float_precision)} -> {pretty(next_expr, float_precision)}"
        )
        current = next_expr

    raise RuntimeError("Maximum reduction steps exceeded")


def evaluate_source(
    source: str,
    shortcut_env: Optional[Dict[str, Expr]] = None,
    max_steps: int = 1000,
    trace: bool = True,
    float_precision: Optional[int] = DEFAULT_FLOAT_PRECISION,
) -> Tuple[Expr, Expr, Expr, List[str], Optional[str], Set[str]]:
    parsed = parse(source)
    expanded, used_shortcuts = expand_with_shortcuts(parsed, shortcut_env or {})

    expansion_step: Optional[str] = None
    if used_shortcuts:
        parsed_text = pretty(parsed, float_precision)
        expanded_text = pretty(expanded, float_precision)
        if parsed_text != expanded_text:
            expansion_step = (
                f"0. [σ-shortcuts: {', '.join(sorted(used_shortcuts))}] "
                f"{parsed_text} -> {expanded_text}"
            )

    if trace:
        result, steps = evaluate_with_trace(
            expanded,
            max_steps=max_steps,
            float_precision=float_precision,
        )
    else:
        result = evaluate(expanded, max_steps=max_steps)
        steps = []

    return parsed, expanded, result, steps, expansion_step, used_shortcuts
