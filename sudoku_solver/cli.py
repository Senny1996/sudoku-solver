"""Command-line interface: ``sudoku-solver [FILE]``."""

import argparse
import sys
from collections.abc import Sequence
from itertools import islice
from typing import Optional

from . import __version__
from .grid import format_grid, grid_to_line, parse_grid
from .solver import InvalidPuzzleError, solutions

EXIT_OK = 0
EXIT_INVALID = 1  # unreadable input, malformed puzzle, clashing clues
# 2 is argparse's own "bad command line" status.
EXIT_UNSOLVABLE = 3
EXIT_NOT_UNIQUE = 4  # only with --unique

_PROG = "sudoku-solver"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_PROG,
        description=(
            "Solve a sudoku. The puzzle is 81 cells, written as one line or as "
            "nine rows, using 0 or . for blanks."
        ),
        epilog=(
            "exit status: 0 solved, 1 invalid or unreadable puzzle, "
            "2 bad command line, 3 no solution, 4 more than one solution (--unique only)"
        ),
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="file containing the puzzle; omit or use - to read standard input",
    )
    parser.add_argument(
        "--oneline",
        action="store_true",
        help="print the solution as one 81-digit line instead of a grid",
    )
    parser.add_argument(
        "--unique",
        action="store_true",
        help="also check that the puzzle has exactly one solution (exit 4 if it has more)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _read_text(path: str) -> str:
    if path == "-":
        if sys.stdin.isatty():
            print(
                "Reading the puzzle from standard input. Paste it, then press "
                "Ctrl+Z and Enter (Windows) or Ctrl+D (Linux/macOS).",
                file=sys.stderr,
            )
        return sys.stdin.read()
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _fail(message: str, status: int) -> int:
    print(f"{_PROG}: {message}", file=sys.stderr)
    return status


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the command line tool and return its exit status."""
    args = _build_parser().parse_args(argv)

    try:
        text = _read_text(args.file)
    except UnicodeDecodeError:
        return _fail(
            f"cannot read {args.file!r}: it is not UTF-8 text "
            "(save the puzzle as a plain text file)",
            EXIT_INVALID,
        )
    except OSError as exc:
        reason = exc.strerror or str(exc)
        return _fail(f"cannot read {args.file!r}: {reason}", EXIT_INVALID)

    try:
        grid = parse_grid(text)
        found = list(islice(solutions(grid), 2 if args.unique else 1))
    except InvalidPuzzleError as exc:
        return _fail(f"invalid puzzle: {exc}", EXIT_INVALID)

    if not found:
        return _fail(
            "this puzzle has no solution (the clues cannot all be satisfied together)",
            EXIT_UNSOLVABLE,
        )

    print(grid_to_line(found[0]) if args.oneline else format_grid(found[0]))
    sys.stdout.flush()  # keep the grid ahead of any message on stderr

    if args.unique:
        if len(found) > 1:
            return _fail(
                "this puzzle has more than one solution; the grid shown is just the first one found",
                EXIT_NOT_UNIQUE,
            )
        print(f"{_PROG}: the solution is unique", file=sys.stderr)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
