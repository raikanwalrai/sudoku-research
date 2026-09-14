"""Tests for Sprint 04A canonical Sudoku identity."""

from __future__ import annotations

import hashlib

import pytest

from sudoku_research.board import Board
from sudoku_research.dataset import (
    SERIALIZED_LENGTH,
    board_hash,
    puzzle_hash,
    serialize_board,
    solution_hash,
)


KNOWN_BOARD = Board(
    (
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
)


def test_serialization_is_row_major():
    serialized = serialize_board(KNOWN_BOARD)

    assert serialized == (
        "530070000"
        "600195000"
        "098000060"
        "800060003"
        "400803001"
        "700020006"
        "060000280"
        "000419005"
        "000080079"
    )


def test_serialization_has_exact_length():
    assert len(serialize_board(KNOWN_BOARD)) == SERIALIZED_LENGTH == 81


def test_serialization_contains_only_ascii_digits():
    serialized = serialize_board(KNOWN_BOARD)

    assert serialized.isascii()
    assert serialized.isdigit()


def test_serialization_is_deterministic():
    assert serialize_board(KNOWN_BOARD) == serialize_board(KNOWN_BOARD)


def test_hash_matches_direct_sha256():
    serialized = serialize_board(KNOWN_BOARD)

    expected = hashlib.sha256(serialized.encode("ascii")).hexdigest()

    assert board_hash(KNOWN_BOARD) == expected


def test_hash_is_lowercase_hex_sha256():
    digest = board_hash(KNOWN_BOARD)

    assert len(digest) == 64
    assert digest == digest.lower()

    int(digest, 16)


def test_identical_boards_have_identical_hashes():
    board_copy = Board.from_rows(KNOWN_BOARD.to_rows())

    assert serialize_board(KNOWN_BOARD) == serialize_board(board_copy)
    assert board_hash(KNOWN_BOARD) == board_hash(board_copy)


def test_different_boards_have_different_exact_identities():
    rows = [list(row) for row in KNOWN_BOARD.to_rows()]
    rows[0][2] = 4

    different_board = Board(tuple(tuple(row) for row in rows))

    assert serialize_board(KNOWN_BOARD) != serialize_board(different_board)
    assert board_hash(KNOWN_BOARD) != board_hash(different_board)


def test_puzzle_and_solution_hash_functions_use_exact_identity():
    assert puzzle_hash(KNOWN_BOARD) == board_hash(KNOWN_BOARD)
    assert solution_hash(KNOWN_BOARD) == board_hash(KNOWN_BOARD)


def test_non_board_is_rejected():
    with pytest.raises(TypeError):
        serialize_board(tuple(KNOWN_BOARD.to_rows()))  # type: ignore[arg-type]


def test_hash_rejects_non_board():
    with pytest.raises(TypeError):
        board_hash(tuple(KNOWN_BOARD.to_rows()))  # type: ignore[arg-type]
