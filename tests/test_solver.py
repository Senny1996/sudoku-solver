"""Tests for the solving logic (sudoku_solver.solver)."""

import pytest
from puzzles import (
    DUPLICATE_IN_ROW,
    EASY,
    EASY_SOLUTION,
    FEW_CLUES,
    HARD,
    HARD_SOLUTION,
    TWO_SOLUTIONS,
    UNSOLVABLE_DEEP,
    UNSOLVABLE_SIMPLE,
)

from sudoku_solver import (
    InvalidPuzzleError,
    UnsolvablePuzzleError,
    count_solutions,
    grid_to_line,
    has_unique_solution,
    is_solved,
    parse_grid,
    solutions,
    solve,
    validate,
)


def blank_grid():
    return [[0] * 9 for _ in range(9)]


def keeps_clues(puzzle, solution):
    return all(
        clue in (0, answer)
        for puzzle_row, solution_row in zip(puzzle, solution)
        for clue, answer in zip(puzzle_row, solution_row)
    )


# --- solving ---------------------------------------------------------------


def test_already_solved_grid_comes_back_unchanged():
    grid = parse_grid(EASY_SOLUTION)
    assert is_solved(grid)
    assert solve(grid) == grid


def test_easy_puzzle():
    puzzle = parse_grid(EASY)
    solution = solve(puzzle)
    assert grid_to_line(solution) == EASY_SOLUTION
    assert is_solved(solution)


def test_hard_puzzle_needing_search():
    puzzle = parse_grid(HARD)
    solution = solve(puzzle)
    assert grid_to_line(solution) == HARD_SOLUTION
    assert is_solved(solution)
    assert keeps_clues(puzzle, solution)


def test_sparse_puzzle():
    puzzle = parse_grid(FEW_CLUES)
    solution = solve(puzzle)
    assert is_solved(solution)
    assert keeps_clues(puzzle, solution)


def test_empty_grid_gets_filled_in():
    solution = solve(blank_grid())
    assert is_solved(solution)


def test_solve_does_not_modify_its_input():
    puzzle = parse_grid(HARD)
    before = [row[:] for row in puzzle]
    solve(puzzle)
    assert puzzle == before


def test_accepts_tuples_as_well_as_lists():
    puzzle = tuple(tuple(row) for row in parse_grid(EASY))
    assert grid_to_line(solve(puzzle)) == EASY_SOLUTION


def test_is_solved_rejects_puzzles_and_broken_grids():
    assert not is_solved(parse_grid(EASY))  # still has blanks
    broken = parse_grid(EASY_SOLUTION)
    broken[0][0], broken[0][1] = broken[0][1], broken[0][0]  # swap two cells
    assert not is_solved(broken)
    assert not is_solved([[1] * 9])  # wrong shape


# --- invalid puzzles -------------------------------------------------------


def test_duplicate_digit_in_a_row():
    grid = blank_grid()
    grid[0][0] = grid[0][8] = 4
    with pytest.raises(InvalidPuzzleError, match=r"digit 4 appears twice in row 1 \(at R1C1 and R1C9\)"):
        validate(grid)
    with pytest.raises(InvalidPuzzleError):
        solve(grid)


def test_duplicate_digit_in_a_column():
    grid = blank_grid()
    grid[0][2] = grid[8][2] = 7
    with pytest.raises(InvalidPuzzleError, match=r"digit 7 appears twice in column 3"):
        solve(grid)


def test_duplicate_digit_in_a_box():
    grid = blank_grid()
    grid[0][0] = grid[2][2] = 9  # different row and column, same box
    with pytest.raises(InvalidPuzzleError, match=r"digit 9 appears twice in box 1"):
        solve(grid)


def test_duplicate_from_a_real_puzzle():
    with pytest.raises(InvalidPuzzleError, match="row 1"):
        solve(parse_grid(DUPLICATE_IN_ROW))


def test_wrong_number_of_rows():
    with pytest.raises(InvalidPuzzleError, match="expected 9 rows but found 8"):
        solve(blank_grid()[:8])


def test_wrong_row_length():
    grid = blank_grid()
    grid[4] = [0] * 8
    with pytest.raises(InvalidPuzzleError, match="row 5 has 8 cells"):
        solve(grid)


@pytest.mark.parametrize("bad", [10, -1, "5", 5.0, None, True])
def test_cell_values_must_be_ints_from_0_to_9(bad):
    grid = blank_grid()
    grid[2][3] = bad
    with pytest.raises(InvalidPuzzleError, match="R3C4"):
        solve(grid)


def test_invalid_puzzle_is_reported_when_solutions_is_called_not_when_iterated():
    grid = blank_grid()
    grid[0][0] = grid[0][1] = 1
    with pytest.raises(InvalidPuzzleError):
        solutions(grid)


# --- unsolvable puzzles ----------------------------------------------------


@pytest.mark.parametrize("line", [UNSOLVABLE_SIMPLE, UNSOLVABLE_DEEP])
def test_unsolvable_puzzle_is_reported(line):
    puzzle = parse_grid(line)
    validate(puzzle)  # legal clues: it is the puzzle as a whole that fails
    with pytest.raises(UnsolvablePuzzleError, match="no solution"):
        solve(puzzle)
    assert list(solutions(puzzle)) == []
    assert count_solutions(puzzle) == 0
    assert not has_unique_solution(puzzle)


# --- uniqueness ------------------------------------------------------------


@pytest.mark.parametrize("line", [EASY, HARD, FEW_CLUES])
def test_proper_puzzles_have_exactly_one_solution(line):
    puzzle = parse_grid(line)
    assert count_solutions(puzzle, limit=10) == 1
    assert has_unique_solution(puzzle)


def test_puzzle_with_two_solutions():
    puzzle = parse_grid(TWO_SOLUTIONS)
    assert count_solutions(puzzle, limit=10) == 2
    assert not has_unique_solution(puzzle)
    first, second = solutions(puzzle)
    assert first != second
    for solution in (first, second):
        assert is_solved(solution)
        assert keeps_clues(puzzle, solution)
    # solve() still gives one of them.
    assert solve(puzzle) in (first, second)


def test_empty_grid_is_not_unique_and_the_count_respects_the_limit():
    assert count_solutions(blank_grid(), limit=5) == 5
    assert not has_unique_solution(blank_grid())
