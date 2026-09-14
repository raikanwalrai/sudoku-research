#!/usr/bin/env bash

set -euo pipefail

echo "=================================================="
echo "SPRINT 01 — IMPLEMENTATION"
echo "=================================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo
echo "Repository: $ROOT_DIR"

echo
echo "===== VERIFY PYTHON ENVIRONMENT ====="
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "ERROR: .venv is not activated."
    echo "Run: source .venv/bin/activate"
    exit 1
fi

python --version
pytest --version

echo
echo "===== CREATE SOURCE FILE: board.py ====="

cat > src/sudoku_research/board.py <<'PY'
"""Core mathematical representation of a 9x9 Sudoku board."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


BOARD_SIZE = 9
BOX_SIZE = 3
MIN_VALUE = 0
MAX_VALUE = 9


def _validate_value(value: int) -> None:
    """Validate a Sudoku cell value."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"Sudoku cell values must be integers; got {type(value).__name__}.")
    if not MIN_VALUE <= value <= MAX_VALUE:
        raise ValueError(f"Sudoku cell values must be in 0..9; got {value}.")


def _validate_coordinate(row: int, col: int) -> None:
    """Validate a zero-based board coordinate."""
    if not isinstance(row, int) or not isinstance(col, int):
        raise TypeError("Row and column indices must be integers.")
    if not 0 <= row < BOARD_SIZE:
        raise IndexError(f"Row index must be in 0..8; got {row}.")
    if not 0 <= col < BOARD_SIZE:
        raise IndexError(f"Column index must be in 0..8; got {col}.")


@dataclass(frozen=True)
class Board:
    """Represent a 9x9 Sudoku board.

    Values are integers in 0..9.
    Zero represents an empty cell.
    """

    _cells: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        """Validate board shape and cell domains."""
        if len(self._cells) != BOARD_SIZE:
            raise ValueError("A Sudoku board must contain exactly 9 rows.")

        for row in self._cells:
            if len(row) != BOARD_SIZE:
                raise ValueError("Each Sudoku row must contain exactly 9 cells.")
            for value in row:
                _validate_value(value)

    @classmethod
    def empty(cls) -> Board:
        """Create an empty 9x9 board."""
        return cls(
            tuple(
                tuple(0 for _ in range(BOARD_SIZE))
                for _ in range(BOARD_SIZE)
            )
        )

    @classmethod
    def from_rows(cls, rows: Sequence[Sequence[int]]) -> Board:
        """Create a board from nine rows of nine integer values."""
        materialized = tuple(tuple(row) for row in rows)
        return cls(materialized)

    @classmethod
    def from_flat(cls, values: Iterable[int]) -> Board:
        """Create a board from exactly 81 values in row-major order."""
        materialized = tuple(values)

        if len(materialized) != BOARD_SIZE * BOARD_SIZE:
            raise ValueError("A flattened Sudoku board must contain exactly 81 values.")

        rows = tuple(
            materialized[start:start + BOARD_SIZE]
            for start in range(0, len(materialized), BOARD_SIZE)
        )
        return cls(rows)

    def to_rows(self) -> tuple[tuple[int, ...], ...]:
        """Return the board as a tuple of nine rows."""
        return self._cells

    def to_flat(self) -> tuple[int, ...]:
        """Return the board in row-major flattened form."""
        return tuple(value for row in self._cells for value in row)

    def get(self, row: int, col: int) -> int:
        """Return the value at a zero-based coordinate."""
        _validate_coordinate(row, col)
        return self._cells[row][col]

    def set(self, row: int, col: int, value: int) -> Board:
        """Return a new board with one cell replaced."""
        _validate_coordinate(row, col)
        _validate_value(value)

        rows = [list(current_row) for current_row in self._cells]
        rows[row][col] = value

        return Board.from_rows(rows)

    def copy(self) -> Board:
        """Return an independent Board with identical contents."""
        return Board.from_rows(self._cells)

    def is_complete(self) -> bool:
        """Return True when no cell is empty."""
        return all(value != 0 for value in self.to_flat())
PY

echo
echo "===== CREATE SOURCE FILE: validator.py ====="

cat > src/sudoku_research/validator.py <<'PY'
"""Sudoku constraint validation and candidate computation."""

from __future__ import annotations

from sudoku_research.board import BOARD_SIZE, BOX_SIZE, Board


def _unit_has_no_duplicates(values: tuple[int, ...]) -> bool:
    """Return True when non-zero values contain no duplicates."""
    non_zero = [value for value in values if value != 0]
    return len(non_zero) == len(set(non_zero))


def _row_values(board: Board, row: int) -> tuple[int, ...]:
    """Return one row."""
    return board.to_rows()[row]


def _column_values(board: Board, col: int) -> tuple[int, ...]:
    """Return one column."""
    rows = board.to_rows()
    return tuple(rows[row][col] for row in range(BOARD_SIZE))


def _box_values(board: Board, row: int, col: int) -> tuple[int, ...]:
    """Return the 3x3 box containing a coordinate."""
    box_row = (row // BOX_SIZE) * BOX_SIZE
    box_col = (col // BOX_SIZE) * BOX_SIZE

    rows = board.to_rows()

    return tuple(
        rows[r][c]
        for r in range(box_row, box_row + BOX_SIZE)
        for c in range(box_col, box_col + BOX_SIZE)
    )


def is_valid_partial(board: Board) -> bool:
    """Return True when the partial board violates no Sudoku constraint."""
    for row in range(BOARD_SIZE):
        if not _unit_has_no_duplicates(_row_values(board, row)):
            return False

    for col in range(BOARD_SIZE):
        if not _unit_has_no_duplicates(_column_values(board, col)):
            return False

    for row in range(0, BOARD_SIZE, BOX_SIZE):
        for col in range(0, BOARD_SIZE, BOX_SIZE):
            if not _unit_has_no_duplicates(_box_values(board, row, col)):
                return False

    return True


def is_valid_solution(board: Board) -> bool:
    """Return True only for complete boards satisfying all constraints."""
    return board.is_complete() and is_valid_partial(board)


def candidate_values(board: Board, row: int, col: int) -> frozenset[int]:
    """Return legal candidate values for an empty cell."""
    current = board.get(row, col)

    if current != 0:
        return frozenset()

    row_values = set(_row_values(board, row))
    column_values = set(_column_values(board, col))
    box_values = set(_box_values(board, row, col))

    used = row_values | column_values | box_values

    return frozenset(set(range(1, BOARD_SIZE + 1)) - used)
PY

echo
echo "===== CREATE TEST FILE: test_board.py ====="

cat > tests/test_board.py <<'PY'
"""Tests for the Sudoku Board representation."""

import pytest

from sudoku_research.board import Board


VALID_ROWS = (
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


def test_empty_board() -> None:
    board = Board.empty()

    assert len(board.to_rows()) == 9
    assert len(board.to_flat()) == 81
    assert all(value == 0 for value in board.to_flat())
    assert not board.is_complete()


def test_from_rows_and_round_trip() -> None:
    board = Board.from_rows(VALID_ROWS)

    assert board.to_rows() == VALID_ROWS
    assert Board.from_flat(board.to_flat()).to_rows() == VALID_ROWS


def test_get_and_set_are_deterministic() -> None:
    board = Board.from_rows(VALID_ROWS)

    assert board.get(0, 0) == 5

    updated = board.set(0, 2, 4)

    assert board.get(0, 2) == 0
    assert updated.get(0, 2) == 4


def test_copy_preserves_contents() -> None:
    board = Board.from_rows(VALID_ROWS)
    copied = board.copy()

    assert copied.to_rows() == board.to_rows()
    assert copied is not board


@pytest.mark.parametrize(
    "rows",
    [
        ((0,) * 9,) * 8,
        ((0,) * 8,) * 9,
    ],
)
def test_invalid_row_count_or_width(rows) -> None:
    with pytest.raises(ValueError):
        Board.from_rows(rows)


def test_invalid_flat_length() -> None:
    with pytest.raises(ValueError):
        Board.from_flat([0] * 80)


@pytest.mark.parametrize("value", [-1, 10])
def test_invalid_cell_value(value: int) -> None:
    rows = [list(row) for row in VALID_ROWS]
    rows[0][2] = value

    with pytest.raises(ValueError):
        Board.from_rows(rows)


@pytest.mark.parametrize("value", [True, False])
def test_boolean_cell_value_is_rejected(value: bool) -> None:
    rows = [list(row) for row in VALID_ROWS]
    rows[0][2] = value

    with pytest.raises(TypeError):
        Board.from_rows(rows)


def test_invalid_coordinate() -> None:
    board = Board.empty()

    with pytest.raises(IndexError):
        board.get(9, 0)

    with pytest.raises(IndexError):
        board.get(0, 9)
PY

echo
echo "===== CREATE TEST FILE: test_validator.py ====="

cat > tests/test_validator.py <<'PY'
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
PY

echo
echo "===== SYNTAX CHECK ====="
python -m compileall -q src tests

echo
echo "===== TEST SUITE ====="
pytest -q

echo
echo "===== IMPORT CHECK ====="
python -c "from sudoku_research.board import Board; from sudoku_research.validator import is_valid_partial; print('Board/Validator import: PASS')"

echo
echo "=================================================="
echo "SPRINT 01 IMPLEMENTATION COMPLETE"
echo "=================================================="
