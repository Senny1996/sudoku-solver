# sudoku-solver

A small, readable sudoku solver in pure Python, with a command-line tool.

- Solves any 9x9 puzzle, including very hard ones, in milliseconds.
- Reports clearly when a puzzle is **invalid** (bad characters, wrong size, a digit repeated in a row, column or box) or **unsolvable**.
- Can check that a puzzle has **exactly one solution**, as a proper puzzle should.
- No dependencies. Written for Python 3.9 or newer (tested on 3.13 and 3.14).

## Install

```bash
git clone https://github.com/YOUR-USERNAME/sudoku-solver.git
cd sudoku-solver
python -m venv .venv
```

Activate the virtual environment (`.venv\Scripts\Activate.ps1` in Windows PowerShell, `source .venv/bin/activate` on macOS and Linux), then:

```bash
pip install -e .
```

This installs the `sudoku-solver` command. (`python -m sudoku_solver` works too, even without installing, if you run it from the project folder.)

## Use it from the command line

Put a puzzle in a text file: 81 cells, with `0` or `.` for blanks. The file can be a single line or nine lines (see [Input formats](#input-formats)). Several are in the [`examples/`](examples) folder.

```console
$ sudoku-solver examples/easy.txt
+-------+-------+-------+
| 5 3 4 | 6 7 8 | 9 1 2 |
| 6 7 2 | 1 9 5 | 3 4 8 |
| 1 9 8 | 3 4 2 | 5 6 7 |
+-------+-------+-------+
| 8 5 9 | 7 6 1 | 4 2 3 |
| 4 2 6 | 8 5 3 | 7 9 1 |
| 7 1 3 | 9 2 4 | 8 5 6 |
+-------+-------+-------+
| 9 6 1 | 5 3 7 | 2 8 4 |
| 2 8 7 | 4 1 9 | 6 3 5 |
| 3 4 5 | 2 8 6 | 1 7 9 |
+-------+-------+-------+
```

Read from standard input by leaving out the file name, and print the answer as one line with `--oneline`:

```console
$ cat examples/hard.txt | sudoku-solver --oneline
812753649943682175675491283154237896369845721287169534521974368438526917796318452
```

(`cat` works in PowerShell too. You can also pipe a plain string: `"53..7...." | sudoku-solver` is fine, as long as you give the whole puzzle.)

Add `--unique` to also check the puzzle has only one solution. The solution is printed as usual, and the verdict goes to the error stream. A puzzle with two solutions exits with status 4:

```console
$ sudoku-solver --unique --oneline examples/easy.txt
534678912672195348198342567859761423426853791713924856961537284287419635345286179
sudoku-solver: the solution is unique

$ sudoku-solver --unique --oneline examples/multiple-solutions.txt
534678912672195348198342567859761423426853791713924856961537284287419635345286179
sudoku-solver: this puzzle has more than one solution; the grid shown is just the first one found
```

### When something is wrong

Problems go to standard error with a non-zero exit status, so the tool is safe to use in scripts.

```console
$ sudoku-solver examples/invalid.txt
sudoku-solver: invalid puzzle: digit 5 appears twice in row 1 (at R1C1 and R1C3)
$ echo $?
1

$ sudoku-solver examples/unsolvable.txt
sudoku-solver: this puzzle has no solution (the clues cannot all be satisfied together)
$ echo $?
3

$ sudoku-solver examples/nope.txt
sudoku-solver: cannot read 'examples/nope.txt': No such file or directory
```

(`R1C3` means row 1, column 3.)

| Exit status | Meaning |
| ----------- | ------- |
| 0 | Solved |
| 1 | The input is unreadable, malformed, or breaks the rules (bad character, not 81 cells, repeated digit) |
| 2 | Bad command line (for example an unknown option) |
| 3 | The puzzle is valid but has no solution |
| 4 | With `--unique` only: the puzzle has more than one solution (the first one found is still printed) |

### Input formats

All of these are the same puzzle. `0` and `.` both mean a blank; whitespace is ignored.

```text
530070000600195000098000060800060003400803001700020006060000280000419005000080079
```

```text
53..7....
6..195...
.98....6.
8...6...3
4..8.3..1
7...2...6
.6....28.
...419..5
....8..79
```

```text
5 3 . | . 7 . | . . .
6 . . | 1 9 5 | . . .
. 9 8 | . . . | . 6 .
------+-------+------
8 . . | . 6 . | . . 3
...
```

The solver's own output (with the `+-------+` borders) can be fed straight back in. Lines starting with `#` are comments. Exactly 81 cells are required, and a nine-line puzzle must have 9 cells on every line. Files must be plain UTF-8 text. In Windows PowerShell 5, `>` writes UTF-16 and the tool will tell you so; use `Out-File -Encoding utf8` or PowerShell 7.

## Use it from Python

```python
from sudoku_solver import (
    InvalidPuzzleError, UnsolvablePuzzleError,
    format_grid, has_unique_solution, parse_grid, solve,
)

puzzle = parse_grid("""
    53..7....
    6..195...
    .98....6.
    8...6...3
    4..8.3..1
    7...2...6
    .6....28.
    ...419..5
    ....8..79
""")

try:
    solution = solve(puzzle)      # a new 9x9 list of lists; `puzzle` is untouched
except InvalidPuzzleError as err:
    print("Bad puzzle:", err)
except UnsolvablePuzzleError:
    print("No solution")
else:
    print(format_grid(solution))
    print("unique:", has_unique_solution(puzzle))
```

Output:

```text
+-------+-------+-------+
| 5 3 4 | 6 7 8 | 9 1 2 |
| 6 7 2 | 1 9 5 | 3 4 8 |
| 1 9 8 | 3 4 2 | 5 6 7 |
+-------+-------+-------+
| 8 5 9 | 7 6 1 | 4 2 3 |
| 4 2 6 | 8 5 3 | 7 9 1 |
| 7 1 3 | 9 2 4 | 8 5 6 |
+-------+-------+-------+
| 9 6 1 | 5 3 7 | 2 8 4 |
| 2 8 7 | 4 1 9 | 6 3 5 |
| 3 4 5 | 2 8 6 | 1 7 9 |
+-------+-------+-------+
unique: True
```

A grid is a list of 9 lists of 9 ints, with `0` for a blank. The main functions:

| Function | What it does |
| -------- | ------------ |
| `parse_grid(text)` | Text in any of the formats above to a grid |
| `solve(grid)` | Returns a solution; raises `InvalidPuzzleError` or `UnsolvablePuzzleError` |
| `validate(grid)` | Raises `InvalidPuzzleError` if the shape, a value, or a repeated digit is wrong |
| `is_solved(grid)` | True for a complete, correct grid |
| `solutions(grid)` | Lazily yields every solution |
| `count_solutions(grid, limit=2)` | Number of solutions, stopping at `limit` |
| `has_unique_solution(grid)` | True if there is exactly one solution |
| `format_grid(grid)`, `grid_to_line(grid)` | Draw a grid, or write it as 81 characters |

## How it works

Every cell keeps a set of the digits that could still go there, stored as a 9-bit number. Two rules shrink those sets until nothing changes: when a cell is down to one digit, that digit is removed from the other 20 cells in its row, column and box; and when a digit has only one possible cell left in a row, column or box, it is placed there. That alone finishes easy puzzles, and it also notices contradictions, such as a cell with no digits left.

When those rules stall, the solver picks the undecided cell with the fewest candidates, tries each of them in turn on a copy of the board, applies the rules again, and recurses. A branch that hits a contradiction is dropped. Choosing the most constrained cell keeps the search tree small, which is why a puzzle billed as the world's hardest ([`examples/hard.txt`](examples/hard.txt)) still solves in milliseconds. Asking for a second solution just keeps the same search going, which is how `--unique` works. The code is in [`sudoku_solver/solver.py`](sudoku_solver/solver.py).

## Run the tests

```bash
pip install -e ".[dev]"
pytest
```

```text
============================= test session starts =============================
collected 73 items

tests\test_cli.py ...................                                    [ 26%]
tests\test_examples.py ......                                            [ 34%]
tests\test_grid.py ....................                                  [ 61%]
tests\test_solver.py ............................                        [100%]

============================= 73 passed in 0.93s ==============================
```

The tests cover solved, easy, hard and sparse puzzles, invalid and unsolvable ones, puzzles with two solutions, every input format, and the command-line exit statuses. They were run on Python 3.13 and 3.14.

## Project layout

```text
sudoku_solver/
    solver.py     the algorithm and the error types
    grid.py       reading puzzles from text, printing grids
    cli.py        the sudoku-solver command
examples/         sample puzzles, including invalid, unsolvable and ambiguous ones
tests/            pytest tests
```

## Licence

[MIT](LICENSE).
