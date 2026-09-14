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
from dataclasses import dataclass

from .board import Board
from .generator import PuzzleRecord


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


@dataclass(frozen=True)
class DatasetRecord:
    """Auditable dataset representation of a generated Sudoku record.

    The record preserves the generator provenance while adding exact
    puzzle and solution identities.
    """

    puzzle_id: int
    generator_seed: int
    puzzle: Board
    solution: Board
    clue_count: int
    removed_count: int
    target_clues: int
    puzzle_hash: str
    solution_hash: str

    @classmethod
    def from_puzzle_record(cls, record: PuzzleRecord) -> "DatasetRecord":
        """Create an auditable dataset record from a generated puzzle."""
        if not isinstance(record, PuzzleRecord):
            raise TypeError("record must be a PuzzleRecord instance")

        return cls(
            puzzle_id=record.puzzle_id,
            generator_seed=record.seed,
            puzzle=record.puzzle,
            solution=record.solution,
            clue_count=record.clue_count,
            removed_count=record.removed_count,
            target_clues=record.target_clues,
            puzzle_hash=puzzle_hash(record.puzzle),
            solution_hash=solution_hash(record.solution),
        )

    def validate_identity(self) -> None:
        """Verify that recorded identities match the stored boards."""
        if self.puzzle_hash != puzzle_hash(self.puzzle):
            raise ValueError("puzzle_hash does not match puzzle contents")

        if self.solution_hash != solution_hash(self.solution):
            raise ValueError("solution_hash does not match solution contents")

    def to_puzzle_record(self) -> PuzzleRecord:
        """Return the underlying Sprint-03 puzzle record."""
        return PuzzleRecord(
            puzzle_id=self.puzzle_id,
            seed=self.generator_seed,
            puzzle=self.puzzle,
            solution=self.solution,
            clue_count=self.clue_count,
            removed_count=self.removed_count,
            target_clues=self.target_clues,
        )


def build_dataset_records(
    records: tuple[PuzzleRecord, ...],
) -> tuple[DatasetRecord, ...]:
    """Convert generated PuzzleRecords into auditable dataset records."""
    if not isinstance(records, tuple):
        raise TypeError("records must be a tuple of PuzzleRecord instances")

    dataset_records = tuple(
        DatasetRecord.from_puzzle_record(record)
        for record in records
    )

    for record in dataset_records:
        record.validate_identity()

    return dataset_records


__all__ = [
    "DatasetRecord",
    "SERIALIZED_LENGTH",
    "board_hash",
    "build_dataset_records",
    "puzzle_hash",
    "serialize_board",
    "solution_hash",
]
