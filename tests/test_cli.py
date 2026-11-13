"""Tests for the command-line tool (sudoku_solver.cli)."""

import io
import subprocess
import sys
from pathlib import Path

import pytest
from puzzles import (
    DUPLICATE_IN_ROW,
    EASY,
    EASY_SOLUTION,
    HARD,
    HARD_SOLUTION,
    TWO_SOLUTIONS,
    UNSOLVABLE_DEEP,
    UNSOLVABLE_SIMPLE,
)

from sudoku_solver import format_grid, parse_grid
from sudoku_solver.cli import main

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def puzzle_file(tmp_path):
    """Return a function that writes puzzle text to a temp file and gives its path."""

    def write(text):
        path = tmp_path / "puzzle.txt"
        path.write_text(text, encoding="utf-8")
        return str(path)

    return write


def test_solves_a_file_and_prints_the_grid(puzzle_file, capsys):
    assert main([puzzle_file(EASY)]) == 0
    captured = capsys.readouterr()
    assert captured.out == format_grid(parse_grid(EASY_SOLUTION)) + "\n"
    assert captured.err == ""


def test_solves_a_hard_puzzle(puzzle_file, capsys):
    assert main([puzzle_file(HARD), "--oneline"]) == 0
    assert capsys.readouterr().out == HARD_SOLUTION + "\n"


def test_reads_standard_input_when_no_file_is_given(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(EASY))
    assert main([]) == 0
    assert capsys.readouterr().out == format_grid(parse_grid(EASY_SOLUTION)) + "\n"


def test_dash_means_standard_input(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(EASY.replace("0", ".")))
    assert main(["-", "--oneline"]) == 0
    assert capsys.readouterr().out == EASY_SOLUTION + "\n"


def test_output_can_be_fed_back_in(puzzle_file, capsys):
    main([puzzle_file(EASY)])
    solved_text = capsys.readouterr().out
    assert main([puzzle_file(solved_text), "--oneline"]) == 0
    assert capsys.readouterr().out == EASY_SOLUTION + "\n"


def test_invalid_puzzle_exits_1_with_a_helpful_message(puzzle_file, capsys):
    assert main([puzzle_file(DUPLICATE_IN_ROW)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid puzzle" in captured.err
    assert "digit 5 appears twice in row 1" in captured.err


def test_bad_character_exits_1(puzzle_file, capsys):
    assert main([puzzle_file(EASY.replace("9", "x", 1))]) == 1
    assert "unexpected character 'x'" in capsys.readouterr().err


def test_wrong_size_exits_1(puzzle_file, capsys):
    assert main([puzzle_file(EASY[:-3])]) == 1
    assert "expected 81 cells" in capsys.readouterr().err


@pytest.mark.parametrize("line", [UNSOLVABLE_SIMPLE, UNSOLVABLE_DEEP])
def test_unsolvable_puzzle_exits_3(puzzle_file, capsys, line):
    assert main([puzzle_file(line)]) == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "no solution" in captured.err


def test_missing_file_exits_1(tmp_path, capsys):
    assert main([str(tmp_path / "nope.txt")]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "cannot read" in captured.err


def test_file_that_is_not_utf8_text_exits_1(tmp_path, capsys):
    # What Windows PowerShell 5 writes for `command > file.txt`.
    path = tmp_path / "utf16.txt"
    path.write_text(EASY, encoding="utf-16")
    assert main([str(path)]) == 1
    assert "not UTF-8" in capsys.readouterr().err


def test_utf8_file_with_byte_order_mark_is_fine(tmp_path, capsys):
    path = tmp_path / "bom.txt"
    path.write_text(EASY, encoding="utf-8-sig")
    assert main([str(path), "--oneline"]) == 0
    assert capsys.readouterr().out == EASY_SOLUTION + "\n"


def test_unique_flag_on_a_proper_puzzle(puzzle_file, capsys):
    assert main([puzzle_file(EASY), "--unique"]) == 0
    captured = capsys.readouterr()
    assert captured.out == format_grid(parse_grid(EASY_SOLUTION)) + "\n"
    assert "unique" in captured.err


def test_unique_flag_on_a_puzzle_with_two_solutions(puzzle_file, capsys):
    assert main([puzzle_file(TWO_SOLUTIONS), "--unique"]) == 4
    captured = capsys.readouterr()
    assert captured.out.startswith("+-------+")  # the first solution is still shown
    assert "more than one solution" in captured.err


def test_without_unique_flag_two_solutions_is_not_an_error(puzzle_file):
    assert main([puzzle_file(TWO_SOLUTIONS)]) == 0


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as info:
        main(["--version"])
    assert info.value.code == 0
    assert capsys.readouterr().out.startswith("sudoku-solver ")


def test_unknown_option_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as info:
        main(["--bogus"])
    assert info.value.code == 2


def test_runs_as_a_module(tmp_path):
    path = tmp_path / "puzzle.txt"
    path.write_text(EASY, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "sudoku_solver", str(path), "--oneline"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == EASY_SOLUTION
