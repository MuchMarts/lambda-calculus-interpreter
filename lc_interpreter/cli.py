from __future__ import annotations

import argparse
from typing import Dict, List, Optional

from .ast import Expr
from .config import DEFAULT_FLOAT_PRECISION, DEFAULT_SHORTCUTS_PATH
from .evaluator import evaluate_source
from .repl import (
    SessionState,
    load_shortcut_state,
    parse_precision,
    print_evaluation,
    print_syntax,
    run_repl,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lambda calculus interpreter")
    parser.add_argument(
        "expression",
        nargs="?",
        help="Expression to evaluate. If omitted, REPL starts.",
    )
    parser.add_argument(
        "--syntax",
        action="store_true",
        help="Print syntax guide and exit.",
    )
    parser.add_argument(
        "--repl",
        action="store_true",
        help="Force REPL mode even when an expression is provided.",
    )
    parser.add_argument(
        "--shortcuts",
        default=DEFAULT_SHORTCUTS_PATH,
        help="Path to shortcuts YAML file.",
    )
    parser.add_argument(
        "--no-shortcuts",
        action="store_true",
        help="Disable shortcut loading.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=1000,
        help="Max reduction steps before aborting.",
    )
    parser.add_argument(
        "--tree",
        action="store_true",
        help="Print AST tree for the expanded expression.",
    )
    parser.add_argument(
        "--trace",
        dest="trace",
        action="store_true",
        default=True,
        help="Print reduction trace (default: on).",
    )
    parser.add_argument(
        "--no-trace",
        dest="trace",
        action="store_false",
        help="Disable reduction trace.",
    )
    parser.add_argument(
        "--precision",
        default=str(DEFAULT_FLOAT_PRECISION),
        help="Floating output precision (integer) or 'raw'.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.syntax:
        print_syntax()
        return 0

    if args.max_steps <= 0:
        parser.error("--max-steps must be > 0")

    try:
        float_precision = parse_precision(args.precision)
    except ValueError as exc:
        parser.error(f"--precision: {exc}")

    if args.no_shortcuts:
        raw_shortcuts: Dict[str, str] = {}
        shortcut_env: Dict[str, Expr] = {}
    else:
        raw_shortcuts, shortcut_env = load_shortcut_state(args.shortcuts)

    state = SessionState(
        max_steps=args.max_steps,
        trace=args.trace,
        show_tree=args.tree,
        float_precision=float_precision,
        shortcuts_path=args.shortcuts,
        raw_shortcuts=raw_shortcuts,
        shortcut_env=shortcut_env,
    )

    if args.repl or args.expression is None:
        run_repl(state)
        return 0

    parsed, expanded, result, steps, expansion_step, used = evaluate_source(
        args.expression,
        shortcut_env=state.shortcut_env,
        max_steps=state.max_steps,
        trace=state.trace,
        float_precision=state.float_precision,
    )
    print_evaluation(
        source=args.expression,
        parsed=parsed,
        expanded=expanded,
        result=result,
        steps=steps,
        expansion_step=expansion_step,
        used_shortcuts=used,
        trace=state.trace,
        show_tree=state.show_tree,
        float_precision=state.float_precision,
    )
    return 0
