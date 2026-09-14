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
