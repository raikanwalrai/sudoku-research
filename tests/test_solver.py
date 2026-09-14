"""Tests for the exact Sudoku solver/oracle."""

import pytest

from sudoku_research.board import Board
from sudoku_research.solver import (
    count_solutions,
    has_unique_solution,
    solve,
    verify_solution,
)
from sudoku_research.validator import is_valid_solution


VALID_SOLUTION = (
    (5, 3, 4, 6, 7, 8, 9, 1, 2),
    (6, 7, 2, 1, 9, 5, 3, 4, 8),
    (1, 9, 8, 3, 4, 2, 5, 6, 7),
    (8, 5, 9, 7, 6, 1, 4, 2, 3),
    (4, 2, 6, 8, 5, 3, 7, 9, 1),
    (7, 1, 3, 9, 2, 4, 8, 5, 6),
    (9, 6, 1, 5, 3, 7, 2, 8, 4),
    (2, 8, 7, 4, 1, 9, 6, 3, 5),
    (3, 4, 5, 2, 8, 6, 1, 7, 9),
)

UNIQUE_PUZZLE = (
    (5, 3, 0, 0, 7, 0, 0, 0, 0),
    (6, 0, 0, 1, 9, 5, 0, 0, 0),
    (0, 9, 8, 0, 0, 0, 0, 6, 0),
    (8, 0, 0, 0, 6, 0, 0, 0, 3),
    (4, 0, 0, 8, 0, 3, 0, 0, 1),
    (7, 0, 0, 0, 2, 0, 0, 0, 6),
    (0, 6, 0, 0, 0, 0, 2, 8, 0),
    (0, 0, 0, 4, 1, 9, 0, 0, 5),
    (0, 0, 0, 0, 8, 0, 0, 7, 9),
)

# This is a deliberately underconstrained valid partial board.
# It has many completions, so counting with limit=2 must return 2.
MULTIPLE_PUZZLE = (
    (5, 3, 0, 0, 7, 0, 0, 0, 0),
    (6, 0, 0, 1, 9, 5, 0, 0, 0),
    (0, 9, 8, 0, 0, 0, 0, 6, 0),
    (8, 0, 0, 0, 6, 0, 0, 0, 0),
    (4, 0, 0, 8, 0, 3, 0, 0, 0),
    (7, 0, 0, 0, 2, 0, 0, 0, 0),
    (0, 6, 0, 0, 0, 0, 0, 8, 0),
    (0, 0, 0, 4, 1, 9, 0, 0, 0),
    (0, 0, 0, 0, 8, 0, 0, 7, 0),
)

INVALID_PUZZLE = (
    (5, 5, 0, 0, 7, 0, 0, 0, 0),
    (6, 0, 0, 1, 9, 5, 0, 0, 0),
    (0, 9, 8, 0, 0, 0, 0, 6, 0),
    (8, 0, 0, 0, 6, 0, 0, 0, 3),
    (4, 0, 0, 8, 0, 3, 0, 0, 1),
    (7, 0, 0, 0, 2, 0, 0, 0, 6),
    (0, 6, 0, 0, 0, 0, 2, 8, 0),
    (0, 0, 0, 4, 1, 9, 0, 0, 5),
    (0, 0, 0, 0, 8, 0, 0, 7, 9),
)


def test_unique_puzzle_has_one_solution() -> None:
    board = Board.from_rows(UNIQUE_PUZZLE)

    assert count_solutions(board) == 1
    assert has_unique_solution(board)


def test_solve_returns_expected_unique_solution() -> None:
    board = Board.from_rows(UNIQUE_PUZZLE)

    solution = solve(board)

    assert solution is not None
    assert solution.to_rows() == VALID_SOLUTION
    assert is_valid_solution(solution)


def test_solve_is_deterministic() -> None:
    board = Board.from_rows(UNIQUE_PUZZLE)

    first = solve(board)
    second = solve(board)

    assert first is not None
    assert second is not None
    assert first.to_flat() == second.to_flat()


def test_solution_preserves_original_clues() -> None:
    board = Board.from_rows(UNIQUE_PUZZLE)
    solution = solve(board)

    assert solution is not None
    assert verify_solution(board, solution)


def test_complete_valid_board_has_one_solution() -> None:
    board = Board.from_rows(VALID_SOLUTION)

    assert count_solutions(board) == 1
    assert solve(board) == board
    assert has_unique_solution(board)


def test_multiple_solution_puzzle_is_detected() -> None:
    board = Board.from_rows(MULTIPLE_PUZZLE)

    assert count_solutions(board, limit=2) == 2
    assert not has_unique_solution(board)
    assert solve(board) is None


def test_invalid_partial_board_is_rejected() -> None:
    board = Board.from_rows(INVALID_PUZZLE)

    with pytest.raises(ValueError):
        count_solutions(board)

    with pytest.raises(ValueError):
        solve(board)


@pytest.mark.parametrize("limit", [0, -1])
def test_invalid_solution_count_limit_is_rejected(limit: int) -> None:
    with pytest.raises(ValueError):
        count_solutions(Board.empty(), limit=limit)


@pytest.mark.parametrize("limit", [True, False, 2.0, "2"])
def test_invalid_solution_count_limit_type_is_rejected(limit) -> None:
    with pytest.raises(TypeError):
        count_solutions(Board.empty(), limit=limit)


def test_verify_solution_rejects_wrong_solution() -> None:
    puzzle = Board.from_rows(UNIQUE_PUZZLE)
    wrong_solution = Board.from_rows(VALID_SOLUTION).set(0, 0, 6)

    assert not verify_solution(puzzle, wrong_solution)


def test_verify_solution_rejects_solution_that_does_not_preserve_clues() -> None:
    puzzle = Board.from_rows(UNIQUE_PUZZLE)
    changed = Board.from_rows(VALID_SOLUTION).set(0, 0, 4)

    assert not verify_solution(puzzle, changed)


def test_verify_solution_rejects_incomplete_board() -> None:
    puzzle = Board.from_rows(UNIQUE_PUZZLE)

    assert not verify_solution(puzzle, puzzle)
