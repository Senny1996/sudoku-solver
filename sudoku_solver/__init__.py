"""A small, readable sudoku solver."""

__version__ = "0.1.0"

from .grid import format_grid, grid_to_line, parse_grid
from .solver import (
    Grid,
    InvalidPuzzleError,
    SudokuError,
    UnsolvablePuzzleError,
    count_solutions,
    has_unique_solution,
    is_solved,
    solutions,
    solve,
    validate,
)

__all__ = [
    "__version__",
    "Grid",
    "InvalidPuzzleError",
    "SudokuError",
    "UnsolvablePuzzleError",
    "count_solutions",
    "format_grid",
    "grid_to_line",
    "has_unique_solution",
    "is_solved",
    "parse_grid",
    "solutions",
    "solve",
    "validate",
]
