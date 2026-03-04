import unittest

from lc_interpreter.parser import parse
from lc_interpreter.render import pretty


class ParserTests(unittest.TestCase):
    def test_pipe_sugar_simple_args(self) -> None:
        direct = parse("((Lx y. x+y) 2 3)")
        piped = parse("Lx y. x+y | 2 3")
        self.assertEqual(pretty(direct), pretty(piped))

    def test_pipe_sugar_parenthesized_complex_arg(self) -> None:
        piped = parse("(Lx. x*2) | (1+2)")
        self.assertEqual(pretty(piped), "((λx.(x * 2)) (1 + 2))")

    def test_pipe_requires_arguments(self) -> None:
        with self.assertRaises(SyntaxError):
            parse("Lx. x |")


if __name__ == "__main__":
    unittest.main()
