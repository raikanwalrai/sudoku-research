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
