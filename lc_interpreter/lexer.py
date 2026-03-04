from __future__ import annotations

from typing import List


def tokenize(source: str) -> List[str]:
    # Convert lambda calculus expression string into a list of tokens
    tokens: List[str] = []
    i = 0
    while i < len(source):
        c = source[i]
        if c.isspace():
            i += 1
        elif c in "().+-*/|":
            tokens.append(c)
            i += 1
        elif c in "\\L":  # allow both \ and L as lambda symbols
            tokens.append("λ")
            i += 1
        elif c.isdigit() or c == ".":
            j = i
            seen_dot = False
            seen_digit = False
            while j < len(source):
                ch = source[j]
                if ch.isdigit():
                    seen_digit = True
                    j += 1
                    continue
                if ch == ".":
                    if seen_dot:
                        break
                    seen_dot = True
                    j += 1
                    continue
                break

            raw = source[i:j]
            if not seen_digit or raw == ".":
                raise SyntaxError(f"Invalid numeric literal: {raw!r}")
            tokens.append(raw)
            i = j
        elif c.isalpha() or c == "_":
            j = i
            while j < len(source) and (source[j].isalnum() or source[j] == "_"):
                j += 1
            tokens.append(source[i:j])
            i = j
        else:
            raise SyntaxError(f"Unexpected character: {c!r}")
    return tokens
