import unittest

from lc_interpreter.evaluator import evaluate
from lc_interpreter.parser import parse
from lc_interpreter.render import pretty


class ReducerTests(unittest.TestCase):
    def test_operator_precedence(self) -> None:
        self.assertEqual(pretty(evaluate(parse("1+2*3"))), "7")
        self.assertEqual(pretty(evaluate(parse("(1+2)*3"))), "9")
        self.assertEqual(pretty(evaluate(parse("7/2"))), "3.5")

    def test_alpha_conversion_in_beta(self) -> None:
        result = evaluate(parse("(Lx. Ly. x) y"))
        self.assertEqual(pretty(result), "(λy_1.y)")

    def test_division_by_zero(self) -> None:
        with self.assertRaises(ZeroDivisionError):
            evaluate(parse("1/0"))

    def test_pipe_sugar_evaluates(self) -> None:
        self.assertEqual(pretty(evaluate(parse("Lx y.x+y | 2 3"))), "5")


if __name__ == "__main__":
    unittest.main()
