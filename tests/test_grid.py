"""Tests for reading and printing puzzles (sudoku_solver.grid)."""

import pytest
from puzzles import EASY, EASY_SOLUTION

from sudoku_solver import InvalidPuzzleError, format_grid, grid_to_line, parse_grid

EASY_GRID = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

NINE_LINES_DOTS = """\
53..7....
6..195...
.98....6.
8...6...3
4..8.3..1
7...2...6
.6....28.
...419..5
....8..79
"""

SPACED_WITH_BORDERS = """\
5 3 . | . 7 . | . . .
6 . . | 1 9 5 | . . .
. 9 8 | . . . | . 6 .
------+-------+------
8 . . | . 6 . | . . 3
4 . . | 8 . 3 | . . 1
7 . . | . 2 . | . . 6
------+-------+------
. 6 . | . . . | 2 8 .
. . . | 4 1 9 | . . 5
. . . | . 8 . | . 7 9
"""

BOXED = """\
+-------+-------+-------+
| 5 3 . | . 7 . | . . . |
| 6 . . | 1 9 5 | . . . |
| . 9 8 | . . . | . 6 . |
+-------+-------+-------+
| 8 . . | . 6 . | . . 3 |
| 4 . . | 8 . 3 | . . 1 |
| 7 . . | . 2 . | . . 6 |
+-------+-------+-------+
| . 6 . | . . . | 2 8 . |
| . . . | 4 1 9 | . . 5 |
| . . . | . 8 . | . 7 9 |
+-------+-------+-------+
"""


# --- the accepted input formats -------------------------------------------


def test_one_line_with_zeros():
    assert parse_grid(EASY) == EASY_GRID


def test_one_line_with_dots():
    assert parse_grid(EASY.replace("0", ".")) == EASY_GRID


def test_mixed_zeros_and_dots():
    assert parse_grid(EASY.replace("0", ".", 10)) == EASY_GRID


@pytest.mark.parametrize(
    "text",
    [NINE_LINES_DOTS, NINE_LINES_DOTS.replace(".", "0"), SPACED_WITH_BORDERS, BOXED],
    ids=["nine-lines-dots", "nine-lines-zeros", "spaced-with-borders", "boxed"],
)
def test_nine_line_grid_formats(text):
    assert parse_grid(text) == EASY_GRID


def test_whitespace_and_line_breaks_are_ignored():
    chunks = [EASY[i : i + 7] for i in range(0, 81, 7)]
    assert parse_grid(" \n\t".join(chunks)) == EASY_GRID
    assert parse_grid("  " + EASY + "\r\n\r\n") == EASY_GRID


def test_windows_line_endings_and_byte_order_mark():
    assert parse_grid("﻿" + NINE_LINES_DOTS.replace("\n", "\r\n")) == EASY_GRID


def test_comment_lines_are_skipped():
    assert parse_grid("# the Wikipedia puzzle\n" + NINE_LINES_DOTS + "\n   # done\n") == EASY_GRID


# --- malformed input -------------------------------------------------------


def test_bad_character_is_reported_with_its_line():
    text = NINE_LINES_DOTS.replace("98", "9x", 1)
    with pytest.raises(InvalidPuzzleError, match=r"unexpected character 'x' on line 3"):
        parse_grid(text)


def test_non_ascii_characters_are_reported_safely():
    with pytest.raises(InvalidPuzzleError, match=r"unexpected character '\\u0663'"):
        parse_grid("٣" + EASY[1:])  # an Arabic-Indic digit three


def test_too_few_cells():
    with pytest.raises(InvalidPuzzleError, match="expected 81 cells .* found 80"):
        parse_grid(EASY[:-1])


def test_too_many_cells():
    with pytest.raises(InvalidPuzzleError, match="found 82"):
        parse_grid(EASY + "0")


def test_empty_input():
    for text in ["", "   \n\n", "# only a comment\n"]:
        with pytest.raises(InvalidPuzzleError, match="no puzzle found"):
            parse_grid(text)


def test_nine_lines_with_one_short_row_and_one_long_row():
    lines = NINE_LINES_DOTS.splitlines()
    lines[0] = lines[0][:-1]  # 8 cells
    lines[1] += "."  # 10 cells; the total is still 81
    with pytest.raises(InvalidPuzzleError, match="line 1 has 8 cells"):
        parse_grid("\n".join(lines))


# --- output ----------------------------------------------------------------


def test_format_grid_layout():
    assert format_grid(EASY_GRID) + "\n" == BOXED


def test_format_grid_blank_character():
    assert "_" in format_grid(EASY_GRID, blank="_")
    assert "." not in format_grid(EASY_GRID, blank="_")


def test_formatted_grid_can_be_parsed_again():
    assert parse_grid(format_grid(EASY_GRID)) == EASY_GRID


def test_grid_to_line():
    assert grid_to_line(EASY_GRID) == EASY
    assert grid_to_line(EASY_GRID, blank=".") == EASY.replace("0", ".")
    assert grid_to_line(parse_grid(EASY_SOLUTION)) == EASY_SOLUTION
