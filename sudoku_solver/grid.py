"""Reading puzzles from text and printing grids.

Accepted input (all of these describe the same puzzle)::

    530070000600195000098000060800060003400803001700020006060000280000419005000080079

    5 3 . | . 7 . | . . .          53..7....
    6 . . | 1 9 5 | . . .          6..195...
    . 9 8 | . . . | . 6 .          .98....6.
    ------+-------+------          ...and so on, nine lines
    ...

The rules: ``0`` or ``.`` is a blank, ``1``-``9`` are clues, whitespace and
``|`` are ignored, lines made only of ``-``, ``+`` and ``=`` are ignored, and
so are lines starting with ``#`` (comments). There must be exactly 81 cells.
"""

from collections.abc import Sequence

from .solver import CELLS, SIZE, Grid, InvalidPuzzleError

__all__ = ["parse_grid", "format_grid", "grid_to_line"]

_DECORATION = set("-+=| \t")  # a line made only of these is just a divider
_BLANKS = set("0.")
_DIGITS = set("123456789")


def parse_grid(text: str) -> Grid:
    """Turn puzzle text into a 9x9 grid of ints (0 for blank).

    Only the *format* is checked here: allowed characters and 81 cells in
    total. Clashing clues are caught later by :func:`sudoku_solver.validate`.

    Raises:
        InvalidPuzzleError: with a message saying what is wrong and where.
    """
    cells: list[int] = []
    per_line: list[tuple[int, int]] = []  # (line number, cells on that line)
    for line_no, line in enumerate(text.replace("﻿", "").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or set(stripped) <= _DECORATION:
            continue
        before = len(cells)
        for ch in stripped:
            if ch.isspace() or ch == "|":
                continue
            if ch in _BLANKS:
                cells.append(0)
            elif ch in _DIGITS:
                cells.append(int(ch))
            else:
                raise InvalidPuzzleError(
                    f"unexpected character {ascii(ch)} on line {line_no}; "
                    "use the digits 1-9, and 0 or . for blanks"
                )
        per_line.append((line_no, len(cells) - before))

    if not cells:
        raise InvalidPuzzleError("no puzzle found in the input (expected 81 cells)")
    if len(cells) != CELLS:
        raise InvalidPuzzleError(
            f"expected 81 cells (9 rows of 9) but found {len(cells)}"
        )
    if len(per_line) == SIZE:
        # Written as a 9-line grid: make sure no row is short while another is long.
        for line_no, count in per_line:
            if count != SIZE:
                raise InvalidPuzzleError(f"line {line_no} has {count} cells, expected 9")

    return [cells[r * SIZE : (r + 1) * SIZE] for r in range(SIZE)]


def format_grid(grid: Sequence[Sequence[int]], blank: str = ".") -> str:
    """Draw a grid with box borders, using ``blank`` for empty cells.

    The result is plain ASCII and can be fed straight back to
    :func:`parse_grid`.
    """
    rule = "+" + "+".join(["-" * 7] * 3) + "+"
    lines = [rule]
    for r, row in enumerate(grid):
        cells = [str(value) if value else blank for value in row]
        groups = (" ".join(cells[i : i + 3]) for i in range(0, SIZE, 3))
        lines.append("| " + " | ".join(groups) + " |")
        if r % 3 == 2:
            lines.append(rule)
    return "\n".join(lines)


def grid_to_line(grid: Sequence[Sequence[int]], blank: str = "0") -> str:
    """Write a grid as a single 81-character string, row by row."""
    return "".join(str(value) if value else blank for row in grid for value in row)
