"""Dataset identity and canonical serialization utilities.

Sprint 04A establishes exact, deterministic identity for Sudoku boards.

Canonical representation:
    - row-major order
    - exactly 81 characters
    - each character represents one Sudoku value
    - values are ASCII decimal digits 0 through 9
    - no separators or whitespace

Identity:
    SHA-256 over the ASCII bytes of the canonical representation.
"""

from __future__ import annotations

import hashlib

from .board import Board


BOARD_SIZE = 9
CELL_COUNT = BOARD_SIZE * BOARD_SIZE
SERIALIZED_LENGTH = CELL_COUNT


def serialize_board(board: Board) -> str:
    """Serialize a Sudoku board into its canonical row-major representation.

    The representation contains exactly 81 ASCII decimal characters.

    Args:
        board: Sudoku Board instance.

    Returns:
        Canonical 81-character row-major representation.

    Raises:
        TypeError: If board is not a Board instance.
    """
    if not isinstance(board, Board):
        raise TypeError("board must be a Board instance")

    values = board.to_flat()

    if len(values) != CELL_COUNT:
        raise ValueError(
            f"board must contain exactly {CELL_COUNT} cells"
        )

    serialized = "".join(str(value) for value in values)

    if len(serialized) != SERIALIZED_LENGTH:
        raise ValueError(
            f"canonical serialization must contain exactly "
            f"{SERIALIZED_LENGTH} characters"
        )

    if not serialized.isascii() or not serialized.isdigit():
        raise ValueError("canonical serialization must contain ASCII digits only")

    return serialized


def board_hash(board: Board) -> str:
    """Return the exact SHA-256 identity of a Sudoku board.

    Hash input is the ASCII encoding of ``serialize_board(board)``.

    Returns:
        Lowercase hexadecimal SHA-256 digest.
    """
    canonical = serialize_board(board)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def puzzle_hash(board: Board) -> str:
    """Return the exact identity hash for a puzzle board."""
    return board_hash(board)


def solution_hash(board: Board) -> str:
    """Return the exact identity hash for a complete solution board."""
    return board_hash(board)
