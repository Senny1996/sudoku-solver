"""Keeps the files in examples/ honest: each does what its name says."""

from pathlib import Path

import pytest

from sudoku_solver import (
    InvalidPuzzleError,
    UnsolvablePuzzleError,
    has_unique_solution,
    is_solved,
    parse_grid,
    solve,
)

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def load(name):
    return parse_grid((EXAMPLES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", ["easy.txt", "hard.txt", "grid-format.txt"])
def test_good_examples_have_one_solution(name):
    puzzle = load(name)
    assert has_unique_solution(puzzle)
    assert is_solved(solve(puzzle))


def test_invalid_example():
    with pytest.raises(InvalidPuzzleError):
        solve(load("invalid.txt"))


def test_unsolvable_example():
    with pytest.raises(UnsolvablePuzzleError):
        solve(load("unsolvable.txt"))


def test_multiple_solutions_example():
    puzzle = load("multiple-solutions.txt")
    assert is_solved(solve(puzzle))
    assert not has_unique_solution(puzzle)
