from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Set, Tuple

from .ast import Abs, App, BinaryOp, Expr, NumLit, Var
from .config import DEFAULT_SHORTCUTS_PATH
from .parser import parse
from .substitution import free_vars

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only when PyYAML is missing
    yaml = None


def _validate_shortcuts(
    shortcuts: Dict[str, str],
    source_name: str = "shortcuts",
) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for name, expr in shortcuts.items():
        if not isinstance(name, str):
            raise ValueError(f"{source_name}: shortcut name {name!r} is not a string")
        if not isinstance(expr, str):
            raise ValueError(f"{source_name}: shortcut {name!r} must map to a string")

        key = name.strip()
        value = expr.strip()
        if not key:
            raise ValueError(f"{source_name}: empty shortcut name")
        if not key.isidentifier():
            raise ValueError(f"{source_name}: invalid shortcut identifier {key!r}")
        if not value:
            raise ValueError(f"{source_name}: empty shortcut expression for {key!r}")
        normalized[key] = value

    return normalized


def load_shortcuts(path: str = DEFAULT_SHORTCUTS_PATH) -> Dict[str, str]:
    """
    Loads a YAML mapping from shortcut name to expression.

    Semantics:
    - shortcuts are constants, not textual macros
    - names must be valid identifiers
    """
    p = Path(path)
    if not p.exists():
        return {}

    if yaml is None:
        raise RuntimeError("PyYAML is required to parse shortcuts.yaml (pip install pyyaml)")

    text = p.read_text(encoding="utf-8")
    try:
        data = yaml.load(text, Loader=yaml.BaseLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: invalid YAML: {exc}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping")

    cast_data: Dict[str, str] = {}
    for key, value in data.items():
        cast_data[str(key)] = "" if value is None else str(value)

    return _validate_shortcuts(cast_data, source_name=path)


def build_shortcut_env(
    shortcuts: Dict[str, str],
    require_closed: bool = True,
) -> Dict[str, Expr]:
    shortcuts = _validate_shortcuts(shortcuts, source_name="shortcut env")

    memo: Dict[str, Expr] = {}
    visiting: Set[str] = set()

    def expand_references(expr: Expr, bound: Optional[Set[str]] = None) -> Expr:
        bound_vars = bound or set()
        if isinstance(expr, Var):
            if expr.name in bound_vars:
                return expr
            if expr.name in shortcuts:
                return resolve(expr.name)
            return expr
        if isinstance(expr, Abs):
            new_bound = set(bound_vars)
            new_bound.add(expr.param)
            return Abs(expr.param, expand_references(expr.body, new_bound))
        if isinstance(expr, App):
            return App(
                expand_references(expr.fn, bound_vars),
                expand_references(expr.arg, bound_vars),
            )
        if isinstance(expr, BinaryOp):
            return BinaryOp(
                expr.op,
                expand_references(expr.left, bound_vars),
                expand_references(expr.right, bound_vars),
            )
        if isinstance(expr, NumLit):
            return expr
        raise TypeError(f"Unknown expression type: {type(expr)}")

    def resolve(name: str) -> Expr:
        if name in memo:
            return memo[name]
        if name in visiting:
            chain = " -> ".join([*sorted(visiting), name])
            raise ValueError(f"Cyclic shortcut definition detected: {chain}")

        visiting.add(name)
        parsed = parse(shortcuts[name])
        expanded = expand_references(parsed)
        visiting.remove(name)

        if require_closed:
            unresolved = free_vars(expanded)
            if unresolved:
                raise ValueError(
                    f"Shortcut {name!r} is not closed; unresolved free variables: {sorted(unresolved)}"
                )

        memo[name] = expanded
        return expanded

    for shortcut_name in shortcuts:
        resolve(shortcut_name)
    return memo


def expand_with_shortcuts(
    expr: Expr,
    shortcut_env: Dict[str, Expr],
    bound: Optional[Set[str]] = None,
) -> Tuple[Expr, Set[str]]:
    bound_vars = bound or set()

    if isinstance(expr, Var):
        if expr.name in bound_vars:
            return expr, set()
        if expr.name in shortcut_env:
            return shortcut_env[expr.name], {expr.name}
        return expr, set()

    if isinstance(expr, Abs):
        new_bound = set(bound_vars)
        new_bound.add(expr.param)
        new_body, used = expand_with_shortcuts(expr.body, shortcut_env, new_bound)
        return Abs(expr.param, new_body), used

    if isinstance(expr, App):
        new_fn, used_fn = expand_with_shortcuts(expr.fn, shortcut_env, bound_vars)
        new_arg, used_arg = expand_with_shortcuts(expr.arg, shortcut_env, bound_vars)
        return App(new_fn, new_arg), (used_fn | used_arg)

    if isinstance(expr, BinaryOp):
        new_left, used_left = expand_with_shortcuts(expr.left, shortcut_env, bound_vars)
        new_right, used_right = expand_with_shortcuts(expr.right, shortcut_env, bound_vars)
        return BinaryOp(expr.op, new_left, new_right), (used_left | used_right)

    if isinstance(expr, NumLit):
        return expr, set()

    raise TypeError(f"Unknown expression type: {type(expr)}")
