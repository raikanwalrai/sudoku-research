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


from dataclasses import replace

import pytest

from sudoku_research.dataset import (
    DatasetRecord,
    build_dataset_records,
    puzzle_hash,
    solution_hash,
)
from sudoku_research.generator import PuzzleRecord, generate_dataset, generate_puzzle


def test_dataset_record_preserves_generator_provenance():
    source = generate_puzzle(seed=12345, target_clues=30)

    record = DatasetRecord.from_puzzle_record(source)

    assert record.puzzle_id == source.puzzle_id
    assert record.generator_seed == source.seed
    assert record.puzzle == source.puzzle
    assert record.solution == source.solution
    assert record.clue_count == source.clue_count
    assert record.removed_count == source.removed_count
    assert record.target_clues == source.target_clues


def test_dataset_record_computes_exact_identity_hashes():
    source = generate_puzzle(seed=12345, target_clues=30)

    record = DatasetRecord.from_puzzle_record(source)

    assert record.puzzle_hash == puzzle_hash(source.puzzle)
    assert record.solution_hash == solution_hash(source.solution)


def test_dataset_record_identity_validation_succeeds_for_untampered_record():
    source = generate_puzzle(seed=12345, target_clues=30)

    record = DatasetRecord.from_puzzle_record(source)

    record.validate_identity()


def test_dataset_record_detects_tampered_puzzle_hash():
    source = generate_puzzle(seed=12345, target_clues=30)

    record = DatasetRecord.from_puzzle_record(source)
    tampered = replace(record, puzzle_hash="0" * 64)

    with pytest.raises(ValueError, match="puzzle_hash"):
        tampered.validate_identity()


def test_dataset_record_detects_tampered_solution_hash():
    source = generate_puzzle(seed=12345, target_clues=30)

    record = DatasetRecord.from_puzzle_record(source)
    tampered = replace(record, solution_hash="0" * 64)

    with pytest.raises(ValueError, match="solution_hash"):
        tampered.validate_identity()


def test_dataset_record_round_trip_preserves_original_record():
    source = generate_puzzle(seed=12345, target_clues=30)

    dataset_record = DatasetRecord.from_puzzle_record(source)
    restored = dataset_record.to_puzzle_record()

    assert restored == source


def test_build_dataset_records_preserves_order():
    source = generate_dataset(size=5, seed=20260915, target_clues=30)

    dataset_records = build_dataset_records(source)

    assert len(dataset_records) == len(source)

    for dataset_record, original in zip(dataset_records, source):
        assert dataset_record.to_puzzle_record() == original


def test_build_dataset_records_is_deterministic():
    source_a = generate_dataset(size=5, seed=20260915, target_clues=30)
    source_b = generate_dataset(size=5, seed=20260915, target_clues=30)

    records_a = build_dataset_records(source_a)
    records_b = build_dataset_records(source_b)

    assert records_a == records_b


def test_build_dataset_records_rejects_non_tuple():
    source = generate_dataset(size=2, seed=20260915, target_clues=30)

    with pytest.raises(
        TypeError,
        match="tuple of PuzzleRecord instances",
    ):
        build_dataset_records(list(source))


def test_build_dataset_records_rejects_invalid_record_type():
    with pytest.raises(TypeError, match="PuzzleRecord"):
        build_dataset_records((object(),))


def test_dataset_records_have_distinct_identity_fields_for_distinct_generated_puzzles():
    source = generate_dataset(size=5, seed=20260915, target_clues=30)

    dataset_records = build_dataset_records(source)

    assert len({record.puzzle_hash for record in dataset_records}) == 5
    assert len({record.solution_hash for record in dataset_records}) == 5


def test_dataset_record_is_immutable():
    source = generate_puzzle(seed=12345, target_clues=30)

    record = DatasetRecord.from_puzzle_record(source)

    with pytest.raises(Exception):
        record.puzzle_hash = "0" * 64
