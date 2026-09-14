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
