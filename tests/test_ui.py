import unittest

from lc_interpreter.render import syntax_guide_text


class SyntaxGuideTests(unittest.TestCase):
    def test_syntax_guide_mentions_pipe(self) -> None:
        guide = syntax_guide_text()
        self.assertIn("Pipe sugar", guide)
        self.assertIn("f | a b c", guide)


if __name__ == "__main__":
    unittest.main()
