import unittest

from lc_interpreter.evaluator import evaluate_source
from lc_interpreter.render import pretty
from lc_interpreter.shortcuts import build_shortcut_env, load_shortcuts


class ExtendedEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.shortcut_env = build_shortcut_env(load_shortcuts("shortcuts.yaml"))

    def test_if_shortcut_evaluates_boolean_branches(self) -> None:
        _, _, when_true, _, _, _ = evaluate_source(
            "if true 1 2",
            shortcut_env=self.shortcut_env,
            trace=False,
        )
        _, _, when_false, _, _, _ = evaluate_source(
            "if false 1 2",
            shortcut_env=self.shortcut_env,
            trace=False,
        )
        self.assertEqual(pretty(when_true), "1")
        self.assertEqual(pretty(when_false), "2")

    def test_pair_shortcuts_select_expected_components(self) -> None:
        _, _, first_value, _, _, _ = evaluate_source(
            "first (pair 1 2)",
            shortcut_env=self.shortcut_env,
            trace=False,
        )
        _, _, second_value, _, _, _ = evaluate_source(
            "second (pair 1 2)",
            shortcut_env=self.shortcut_env,
            trace=False,
        )
        self.assertEqual(pretty(first_value), "1")
        self.assertEqual(pretty(second_value), "2")

    def test_church_plus_normalizes_to_five(self) -> None:
        _, _, result, _, _, used = evaluate_source(
            "plus two three (Lx. x+1) 0",
            shortcut_env=self.shortcut_env,
            trace=False,
        )
        self.assertEqual(pretty(result), "5")
        self.assertEqual(used, {"plus", "two", "three"})

    def test_leftmost_outermost_handles_divergent_argument(self) -> None:
        expr = "(Lx. 1) ((Ly. (y y)) (Ly. (y y)))"

        _, _, result, _, _, _ = evaluate_source(
            expr,
            shortcut_env=self.shortcut_env,
            max_steps=40,
            trace=False,
        )
        self.assertEqual(pretty(result), "1")


if __name__ == "__main__":
    unittest.main()
