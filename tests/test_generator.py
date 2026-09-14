"""Tests for reproducible synthetic Sudoku generation."""

from __future__ import annotations

import pytest

from sudoku_research.board import Board
from sudoku_research.generator import (
    PuzzleRecord,
    generate_dataset,
    generate_puzzle,
    generate_solution,
)
from sudoku_research.solver import count_solutions, solve
from sudoku_research.validator import is_valid_partial, is_valid_solution


def test_generate_solution_is_valid() -> None:
    solution = generate_solution(12345)

    assert isinstance(solution, Board)
    assert is_valid_solution(solution)


def test_generate_solution_is_reproducible() -> None:
    first = generate_solution(12345)
    second = generate_solution(12345)

    assert first == second


def test_different_seeds_can_generate_different_solutions() -> None:
    first = generate_solution(12345)
    second = generate_solution(54321)

    assert first != second


def test_generate_puzzle_supports_empirical_lower_boundary() -> None:
    record = generate_puzzle(seed=0, target_clues=25)

    assert record.target_clues == 25
    assert record.clue_count == 25
    assert record.removed_count == 56
    assert is_valid_partial(record.puzzle)
    assert is_valid_solution(record.solution)
    assert count_solutions(record.puzzle, limit=2) == 1
    assert solve(record.puzzle) == record.solution


def test_generate_puzzle_returns_expected_record() -> None:
    record = generate_puzzle(seed=12345, target_clues=40)

    assert isinstance(record, PuzzleRecord)
    assert record.puzzle_id == 0
    assert record.seed == 12345
    assert record.target_clues == 40
    assert record.clue_count == 40
    assert record.removed_count == 41


def test_generated_puzzle_is_valid_partial() -> None:
    record = generate_puzzle(seed=12345, target_clues=40)

    assert is_valid_partial(record.puzzle)
    assert is_valid_solution(record.solution)


def test_generated_puzzle_is_uniquely_solvable() -> None:
    record = generate_puzzle(seed=12345, target_clues=40)

    assert count_solutions(record.puzzle, limit=2) == 1
    assert solve(record.puzzle) == record.solution


def test_puzzle_clues_match_solution() -> None:
    record = generate_puzzle(seed=12345, target_clues=40)

    assert all(
        puzzle_value == 0 or puzzle_value == solution_value
        for puzzle_value, solution_value in zip(
            record.puzzle.to_flat(),
            record.solution.to_flat(),
        )
    )


def test_generate_puzzle_is_reproducible() -> None:
    first = generate_puzzle(seed=12345, target_clues=40)
    second = generate_puzzle(seed=12345, target_clues=40)

    assert first == second


def test_generate_dataset_is_reproducible() -> None:
    first = generate_dataset(size=3, seed=9876, target_clues=40)
    second = generate_dataset(size=3, seed=9876, target_clues=40)

    assert first == second


def test_generate_dataset_assigns_stable_ids() -> None:
    dataset = generate_dataset(size=3, seed=9876, target_clues=40)

    assert [record.puzzle_id for record in dataset] == [0, 1, 2]


def test_generate_dataset_records_are_unique_by_puzzle() -> None:
    dataset = generate_dataset(size=5, seed=9876, target_clues=40)

    puzzles = [record.puzzle.to_flat() for record in dataset]

    assert len(set(puzzles)) == len(puzzles)


def test_generate_dataset_records_have_unique_solutions() -> None:
    dataset = generate_dataset(size=3, seed=9876, target_clues=40)

    for record in dataset:
        assert count_solutions(record.puzzle, limit=2) == 1
        assert solve(record.puzzle) == record.solution


@pytest.mark.parametrize("seed", [0, 1, 2, 99])
def test_multiple_seeds_generate_valid_puzzles(seed: int) -> None:
    record = generate_puzzle(seed=seed, target_clues=40)

    assert is_valid_partial(record.puzzle)
    assert is_valid_solution(record.solution)
    assert count_solutions(record.puzzle, limit=2) == 1
    assert solve(record.puzzle) == record.solution


@pytest.mark.parametrize("target_clues", [24, 16, 1, 0, 82])
def test_invalid_target_clues_rejected(target_clues: int) -> None:
    with pytest.raises(ValueError):
        generate_puzzle(seed=1, target_clues=target_clues)


def test_boolean_target_clues_rejected() -> None:
    with pytest.raises(TypeError):
        generate_puzzle(seed=1, target_clues=True)  # type: ignore[arg-type]


def test_boolean_seed_rejected() -> None:
    with pytest.raises(TypeError):
        generate_solution(True)  # type: ignore[arg-type]


@pytest.mark.parametrize("size", [0, -1])
def test_invalid_dataset_size_rejected(size: int) -> None:
    with pytest.raises(ValueError):
        generate_dataset(size=size)


def test_boolean_dataset_size_rejected() -> None:
    with pytest.raises(TypeError):
        generate_dataset(size=True)  # type: ignore[arg-type]


def test_generated_puzzle_has_expected_flattened_size() -> None:
    record = generate_puzzle(seed=7, target_clues=40)

    assert len(record.puzzle.to_flat()) == 81
    assert len(record.solution.to_flat()) == 81
