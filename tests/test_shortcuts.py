import tempfile
import unittest
from pathlib import Path

from lc_interpreter.evaluator import evaluate_source
from lc_interpreter.parser import parse
from lc_interpreter.render import pretty
from lc_interpreter.shortcuts import (
    build_shortcut_env,
    expand_with_shortcuts,
    load_shortcuts,
)


class ShortcutTests(unittest.TestCase):
    def test_closed_shortcut_env(self) -> None:
        env = build_shortcut_env({"id": "(Lx. x)", "apply": "(id id)"})
        expanded, used = expand_with_shortcuts(parse("apply"), env)
        self.assertEqual(used, {"apply"})
        self.assertEqual(pretty(expanded), "((λx.x) (λx.x))")

    def test_open_shortcut_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "not closed"):
            build_shortcut_env({"k": "y"})

    def test_cyclic_shortcuts_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            build_shortcut_env({"a": "b", "b": "a"})

    def test_shortcut_name_power_is_allowed(self) -> None:
        env = build_shortcut_env({"power": "(Lx. x)"})
        expanded, used = expand_with_shortcuts(parse("power"), env)
        self.assertEqual(used, {"power"})
        self.assertEqual(pretty(expanded), "(λx.x)")

    def test_shortcut_expansion_step_label(self) -> None:
        env = build_shortcut_env({"tru": "(Lt. (Lf. t))"})
        _, _, result, steps, expansion_step, _ = evaluate_source(
            "tru",
            shortcut_env=env,
            trace=True,
        )
        self.assertEqual(pretty(result), "(λt.(λf.t))")
        self.assertEqual(steps, [])
        self.assertIn("[σ-shortcuts: tru]", expansion_step or "")

    def test_yaml_loader_parses_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir) / "shortcuts.yaml"
            p.write_text("one: (Lf. (Lx. (f x)))\n", encoding="utf-8")
            loaded = load_shortcuts(str(p))
        self.assertEqual(loaded, {"one": "(Lf. (Lx. (f x)))"})


if __name__ == "__main__":
    unittest.main()
