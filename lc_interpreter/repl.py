from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from .ast import Expr
from .evaluator import evaluate_source
from .render import pretty, print_tree, syntax_guide_text
from .shortcuts import build_shortcut_env, load_shortcuts


@dataclass
class SessionState:
    max_steps: int
    trace: bool
    show_tree: bool
    float_precision: Optional[int]
    shortcuts_path: str
    raw_shortcuts: Dict[str, str]
    shortcut_env: Dict[str, Expr]


def parse_precision(value: str) -> Optional[int]:
    raw = value.strip().lower()
    if raw == "raw":
        return None

    precision = int(raw)
    if precision <= 0:
        raise ValueError("precision must be > 0, or use 'raw'")
    return precision


def _parse_on_off(value: str) -> bool:
    val = value.strip().lower()
    if val in {"on", "true", "1", "yes"}:
        return True
    if val in {"off", "false", "0", "no"}:
        return False
    raise ValueError("expected on/off")


def load_shortcut_state(path: str) -> Tuple[Dict[str, str], Dict[str, Expr]]:
    raw = load_shortcuts(path)
    env = build_shortcut_env(raw, require_closed=True)
    return raw, env


def _print_shortcuts_env(
    raw_shortcuts: Dict[str, str],
    shortcut_env: Dict[str, Expr],
    float_precision: Optional[int],
    name: Optional[str] = None,
) -> None:
    if not raw_shortcuts:
        print("No shortcuts loaded")
        return

    if name is not None:
        if name not in shortcut_env:
            print(f"Shortcut {name!r} not found")
            return
        print(f"{name}:\t{pretty(shortcut_env[name], float_precision)}")
        return

    for shortcut_name in sorted(shortcut_env):
        print(f"{shortcut_name}:\t{pretty(shortcut_env[shortcut_name], float_precision)}")


def print_settings(state: SessionState) -> None:
    precision_text = "raw" if state.float_precision is None else str(state.float_precision)
    print(
        "Settings: "
        f"trace={state.trace}, "
        f"tree={state.show_tree}, "
        f"max_steps={state.max_steps}, "
        f"precision={precision_text}, "
        f"shortcuts={state.shortcuts_path} ({len(state.shortcut_env)} loaded)"
    )


def print_syntax() -> None:
    print(syntax_guide_text())


def print_help() -> None:
    print("Commands:")
    print("  syntax            Show language syntax guide")
    print("  env               List all expanded shortcuts")
    print("  env <name>        Show one expanded shortcut")
    print("  reload            Reload shortcuts from shortcuts.yaml")
    print("  trace <on|off>    Enable/disable step trace")
    print("  tree <on|off>     Enable/disable AST tree output")
    print("  precision <N|raw> Floating output precision")
    print("  maxsteps <N>      Step limit before aborting")
    print("  settings          Show current settings")
    print("  help              Show this message")
    print("  quit              Exit REPL")


def _cmd_quit(args: List[str], _state: SessionState) -> bool:
    if args:
        print("Usage: quit")
    return True


def _cmd_help(args: List[str], _state: SessionState) -> bool:
    if args:
        print("Usage: help")
    print_help()
    return False


def _cmd_settings(args: List[str], state: SessionState) -> bool:
    if args:
        print("Usage: settings")
    print_settings(state)
    return False


def _cmd_syntax(args: List[str], _state: SessionState) -> bool:
    if args:
        print("Usage: syntax")
    print_syntax()
    return False


def _cmd_env(args: List[str], state: SessionState) -> bool:
    if len(args) > 1:
        print("Usage: env [name]")
        return False
    name = args[0] if args else None
    _print_shortcuts_env(state.raw_shortcuts, state.shortcut_env, state.float_precision, name)
    return False


def _cmd_reload(args: List[str], state: SessionState) -> bool:
    if args:
        print("Usage: reload")
        return False
    raw, env = load_shortcut_state(state.shortcuts_path)
    state.raw_shortcuts = raw
    state.shortcut_env = env
    print(f"Reloaded {len(env)} shortcuts from {state.shortcuts_path}")
    return False


def _cmd_trace(args: List[str], state: SessionState) -> bool:
    if len(args) != 1:
        print("Usage: trace <on|off>")
        return False
    state.trace = _parse_on_off(args[0])
    print(f"Trace set to {state.trace}")
    return False


def _cmd_tree(args: List[str], state: SessionState) -> bool:
    if len(args) != 1:
        print("Usage: tree <on|off>")
        return False
    state.show_tree = _parse_on_off(args[0])
    print(f"Tree output set to {state.show_tree}")
    return False


def _cmd_precision(args: List[str], state: SessionState) -> bool:
    if len(args) != 1:
        print("Usage: precision <N|raw>")
        return False
    state.float_precision = parse_precision(args[0])
    label = "raw" if state.float_precision is None else str(state.float_precision)
    print(f"Precision set to {label}")
    return False


def _cmd_maxsteps(args: List[str], state: SessionState) -> bool:
    if len(args) != 1:
        print("Usage: maxsteps <N>")
        return False
    value = int(args[0])
    if value <= 0:
        raise ValueError("maxsteps must be > 0")
    state.max_steps = value
    print(f"max_steps set to {state.max_steps}")
    return False


COMMAND_HANDLERS: Dict[str, Callable[[List[str], SessionState], bool]] = {
    "quit": _cmd_quit,
    "help": _cmd_help,
    "settings": _cmd_settings,
    "syntax": _cmd_syntax,
    "env": _cmd_env,
    "reload": _cmd_reload,
    "trace": _cmd_trace,
    "tree": _cmd_tree,
    "precision": _cmd_precision,
    "maxsteps": _cmd_maxsteps,
}


COMMAND_ALIASES: Dict[str, str] = {
    "exit": "quit",
}


def handle_repl_command(line: str, state: SessionState) -> Tuple[bool, bool]:
    stripped = line.strip()
    if not stripped:
        return True, False

    command_text = stripped[1:].strip() if stripped.startswith(":") else stripped
    parts = command_text.split()
    if not parts:
        return True, False

    command = parts[0].lower()
    args = parts[1:]

    command = COMMAND_ALIASES.get(command, command)

    if command not in COMMAND_HANDLERS and not stripped.startswith(":"):
        return False, False

    try:
        handler = COMMAND_HANDLERS.get(command)
        if handler is None:
            print(f"Unknown command: {command}")
            return True, False
        should_exit = handler(args, state)
        return True, should_exit

    except Exception as exc:
        print(f"Command error: {exc}")
        return True, False


def print_evaluation(
    source: str,
    parsed: Expr,
    expanded: Expr,
    result: Expr,
    steps: List[str],
    expansion_step: Optional[str],
    used_shortcuts: set[str],
    trace: bool,
    show_tree: bool,
    float_precision: Optional[int],
) -> None:
    print("Input:", source)
    print("Pretty (parsed):", pretty(parsed, float_precision))

    if used_shortcuts:
        print("Shortcuts used:", ", ".join(sorted(used_shortcuts)))
    if expansion_step:
        print("Expansion step:")
        print(expansion_step)

    print("Pretty (expanded):", pretty(expanded, float_precision))

    if show_tree:
        print("Tree:")
        print_tree(expanded, float_precision)

    if trace:
        print("Reduction steps:")
        if not steps:
            print("0. [normal form] no reduction needed")
        else:
            for step in steps:
                print(step)

    print("Reduced:", pretty(result, float_precision))


def run_repl(state: SessionState) -> None:
    print("Lambda calculus REPL. Type 'help' for commands.")
    print_settings(state)

    while True:
        try:
            line = input("λ> ").strip()
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue

        handled, should_exit = handle_repl_command(line, state)
        if should_exit:
            break
        if handled:
            continue

        try:
            parsed, expanded, result, steps, expansion_step, used = evaluate_source(
                line,
                shortcut_env=state.shortcut_env,
                max_steps=state.max_steps,
                trace=state.trace,
                float_precision=state.float_precision,
            )
            print_evaluation(
                source=line,
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
        except Exception as exc:
            print(f"Error: {exc}")
