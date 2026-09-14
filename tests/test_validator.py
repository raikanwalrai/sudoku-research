"""Tests for Sudoku constraints and candidate computation."""

from sudoku_research.board import Board
from sudoku_research.validator import (
    candidate_values,
    is_valid_partial,
    is_valid_solution,
)


VALID_PARTIAL = (
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


def test_valid_partial_board() -> None:
    board = Board.from_rows(VALID_PARTIAL)

    assert is_valid_partial(board)
    assert not is_valid_solution(board)


def test_valid_solution() -> None:
    board = Board.from_rows(VALID_SOLUTION)

    assert is_valid_partial(board)
    assert is_valid_solution(board)


def test_duplicate_in_row_is_invalid() -> None:
    rows = [list(row) for row in VALID_PARTIAL]
    rows[0][2] = 5

    assert not is_valid_partial(Board.from_rows(rows))


def test_duplicate_in_column_is_invalid() -> None:
    rows = [list(row) for row in VALID_PARTIAL]
    rows[2][0] = 6

    assert not is_valid_partial(Board.from_rows(rows))


def test_duplicate_in_box_is_invalid() -> None:
    rows = [list(row) for row in VALID_PARTIAL]
    rows[1][2] = 5

    assert not is_valid_partial(Board.from_rows(rows))


def test_candidate_values() -> None:
    board = Board.from_rows(VALID_PARTIAL)

    assert candidate_values(board, 0, 2) == frozenset({1, 2, 4})


def test_candidate_values_for_occupied_cell_are_empty() -> None:
    board = Board.from_rows(VALID_PARTIAL)

    assert candidate_values(board, 0, 0) == frozenset()


def test_valid_solution_requires_completeness() -> None:
    board = Board.from_rows(VALID_PARTIAL)

    assert not is_valid_solution(board)
