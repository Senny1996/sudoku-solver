"""The sudoku solver: constraint propagation plus depth-first search.

A puzzle is a 9x9 grid: a list of 9 rows, each a list of 9 ints, where ``0``
means "blank" and ``1``-``9`` are the clues. Every function here accepts any
sequence of sequences and never modifies the grid you pass in.

How it works
------------
Internally each of the 81 cells holds a *candidate mask*, a 9-bit integer in
which bit ``d - 1`` is set when digit ``d`` could still go in that cell.

* **Propagation** applies two rules until nothing changes. If a cell has one
  candidate left, that digit is removed from its 20 peers (same row, column
  or box). If a digit fits in only one cell of a row, column or box, it is
  placed there.
* **Search** is used when propagation stalls: pick the undecided cell with the
  fewest candidates, try each candidate in turn on a copy of the grid,
  propagate, and recurse. A branch that empties a cell is abandoned.

Easy puzzles are finished by propagation alone; the search only does real
work on hard ones.
"""

from collections.abc import Iterator, Sequence
from itertools import islice
from typing import Optional

__all__ = [
    "Grid",
    "SudokuError",
    "InvalidPuzzleError",
    "UnsolvablePuzzleError",
    "validate",
    "is_solved",
    "solve",
    "solutions",
    "count_solutions",
    "has_unique_solution",
]

Grid = list[list[int]]
"""A 9x9 puzzle or solution: 9 rows of 9 ints, with 0 meaning blank."""

SIZE = 9
BOX = 3
CELLS = SIZE * SIZE


class SudokuError(Exception):
    """Base class for everything this package raises on purpose."""


class InvalidPuzzleError(SudokuError):
    """The input is not a well-formed puzzle (wrong shape, bad digit, duplicate clue)."""


class UnsolvablePuzzleError(SudokuError):
    """The puzzle is well-formed but has no solution."""


# --------------------------------------------------------------------------- #
# Board geometry, worked out once when the module is imported.
# Cells are numbered 0-80, row by row.
# --------------------------------------------------------------------------- #

_ROWS = [tuple(r * SIZE + c for c in range(SIZE)) for r in range(SIZE)]
_COLS = [tuple(r * SIZE + c for r in range(SIZE)) for c in range(SIZE)]
_BOXES = [
    tuple(
        (box_row * BOX + r) * SIZE + box_col * BOX + c
        for r in range(BOX)
        for c in range(BOX)
    )
    for box_row in range(BOX)
    for box_col in range(BOX)
]
_UNITS = _ROWS + _COLS + _BOXES
_UNIT_NAMES = (
    [f"row {i}" for i in range(1, SIZE + 1)]
    + [f"column {i}" for i in range(1, SIZE + 1)]
    + [f"box {i}" for i in range(1, SIZE + 1)]
)
_UNITS_OF = [[u for u in _UNITS if cell in u] for cell in range(CELLS)]
_PEERS = [
    tuple(sorted({c for u in _UNITS_OF[cell] for c in u} - {cell}))
    for cell in range(CELLS)
]

_ALL = (1 << SIZE) - 1  # candidate mask with every digit still possible
# For every possible mask: how many candidates it holds, and which single bits.
_COUNT = [bin(mask).count("1") for mask in range(_ALL + 1)]
_BITS = [[1 << d for d in range(SIZE) if mask >> d & 1] for mask in range(_ALL + 1)]


def _label(cell: int) -> str:
    """Human-readable name of a cell, e.g. ``R3C7`` for row 3, column 7."""
    return f"R{cell // SIZE + 1}C{cell % SIZE + 1}"


# --------------------------------------------------------------------------- #
# Checking grids
# --------------------------------------------------------------------------- #


def validate(grid: Sequence[Sequence[int]]) -> None:
    """Raise :class:`InvalidPuzzleError` unless ``grid`` is a legal puzzle.

    Legal means 9 rows of 9 cells, every cell an int from 0 to 9, and no digit
    repeated within a row, column or 3x3 box. A legal puzzle may still be
    unsolvable; this only checks the clues for obvious mistakes.
    """
    if len(grid) != SIZE:
        raise InvalidPuzzleError(f"expected 9 rows but found {len(grid)}")
    for r, row in enumerate(grid, start=1):
        if len(row) != SIZE:
            raise InvalidPuzzleError(f"row {r} has {len(row)} cells, expected 9")
        for c, value in enumerate(row, start=1):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                raise InvalidPuzzleError(
                    f"R{r}C{c} contains {value!r}; use 0 for a blank or a digit from 1 to 9"
                )

    flat = [value for row in grid for value in row]
    for name, unit in zip(_UNIT_NAMES, _UNITS):
        seen: dict[int, int] = {}
        for cell in unit:
            digit = flat[cell]
            if digit == 0:
                continue
            if digit in seen:
                raise InvalidPuzzleError(
                    f"digit {digit} appears twice in {name} "
                    f"(at {_label(seen[digit])} and {_label(cell)})"
                )
            seen[digit] = cell


def is_solved(grid: Sequence[Sequence[int]]) -> bool:
    """Return True if ``grid`` is a complete, correct sudoku solution."""
    try:
        validate(grid)
    except InvalidPuzzleError:
        return False
    return all(value != 0 for row in grid for value in row)


# --------------------------------------------------------------------------- #
# Propagation and search
# --------------------------------------------------------------------------- #


def _eliminate(cands: list[int], cell: int, bit: int) -> bool:
    """Remove one candidate from a cell and follow the consequences.

    Returns False if that leads to a contradiction (a cell or a unit left
    with nowhere to put a digit). ``cands`` is modified in place, so callers
    that need to backtrack must pass a copy.
    """
    work = [(cell, bit)]
    while work:
        cell, bit = work.pop()
        if not cands[cell] & bit:
            continue  # already eliminated
        cands[cell] &= ~bit
        left = cands[cell]
        if left == 0:
            return False  # this cell has no possible digit
        if _COUNT[left] == 1:
            # Naked single: the last remaining digit cannot appear in any peer.
            work.extend((peer, left) for peer in _PEERS[cell])
        for unit in _UNITS_OF[cell]:
            places = [c for c in unit if cands[c] & bit]
            if not places:
                return False  # this digit has nowhere to go in the unit
            if len(places) == 1:
                # Hidden single: the digit must go in the only cell that can hold it.
                target = places[0]
                work.extend((target, other) for other in _BITS[cands[target] & ~bit])
    return True


def _assign(cands: list[int], cell: int, bit: int) -> bool:
    """Fix ``cell`` to the digit ``bit`` by eliminating its other candidates."""
    return all(_eliminate(cands, cell, other) for other in _BITS[cands[cell] & ~bit])


def _initial_candidates(grid: Sequence[Sequence[int]]) -> Optional[list[int]]:
    """Candidate masks after applying the clues, or None if they contradict."""
    cands = [_ALL] * CELLS
    for r, row in enumerate(grid):
        for c, digit in enumerate(row):
            if digit and not _assign(cands, r * SIZE + c, 1 << (digit - 1)):
                return None
    return cands


def _search(cands: list[int]) -> Iterator[list[int]]:
    """Yield the candidate masks of every complete solution below ``cands``."""
    # Branch on the undecided cell with the fewest candidates: it gives the
    # smallest fan-out, and a wrong guess there is refuted quickly.
    best, best_count = -1, SIZE + 1
    for cell in range(CELLS):
        count = _COUNT[cands[cell]]
        if 1 < count < best_count:
            best, best_count = cell, count
            if count == 2:
                break
    if best < 0:
        yield cands  # every cell has exactly one candidate left
        return
    for bit in _BITS[cands[best]]:
        trial = cands[:]
        if _assign(trial, best, bit):
            yield from _search(trial)


def _to_grid(cands: list[int]) -> Grid:
    """Turn fully-decided candidate masks into a grid of digits."""
    # A mask with only bit d-1 set has bit_length() == d.
    return [[cands[r * SIZE + c].bit_length() for c in range(SIZE)] for r in range(SIZE)]


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def solutions(grid: Sequence[Sequence[int]]) -> Iterator[Grid]:
    """Lazily yield every solution of ``grid``.

    The puzzle is validated immediately (``InvalidPuzzleError`` is raised by
    this call, not later). A puzzle with no solution yields nothing. Use
    :func:`itertools.islice` to stop after the first few; a nearly empty grid
    has an astronomical number of solutions.
    """
    validate(grid)
    cands = _initial_candidates(grid)
    if cands is None:
        return iter(())
    return (_to_grid(final) for final in _search(cands))


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Return a solution of ``grid`` as a new grid.

    If the puzzle has several solutions, one of them is returned; use
    :func:`has_unique_solution` to find out whether that is the only one.

    Raises:
        InvalidPuzzleError: the grid is malformed or repeats a digit in a
            row, column or box.
        UnsolvablePuzzleError: the clues are legal but cannot be completed.
    """
    for solution in solutions(grid):
        return solution
    raise UnsolvablePuzzleError("this puzzle has no solution")


def count_solutions(grid: Sequence[Sequence[int]], limit: int = 2) -> int:
    """Count the solutions of ``grid``, stopping once ``limit`` are found.

    The cap matters: counting every solution of a sparse puzzle would take
    practically forever. Raises ``InvalidPuzzleError`` like :func:`solve`.
    """
    return sum(1 for _ in islice(solutions(grid), limit))


def has_unique_solution(grid: Sequence[Sequence[int]]) -> bool:
    """Return True if ``grid`` has exactly one solution (as a proper puzzle should)."""
    return count_solutions(grid, limit=2) == 1
