from dataclasses import replace

import pytest

from sudoku_research.dataset import (
    DatasetRecord,
    puzzle_hash,
    solution_hash,
)
from sudoku_research.generator import generate_puzzle
from sudoku_research.leakage import (
    LeakageReport,
    audit_split_leakage,
    find_exact_duplicates,
    find_solution_duplicates,
)


def make_record(seed: int, target_clues: int = 30) -> DatasetRecord:
    """Generate one deterministic DatasetRecord for testing."""
    puzzle = generate_puzzle(seed=seed, target_clues=target_clues)
    return DatasetRecord.from_puzzle_record(puzzle)


def test_clean_partitions_have_no_leakage():
    left = (make_record(1001), make_record(1002))
    right = (make_record(2001), make_record(2002))

    report = audit_split_leakage(left, right)

    assert isinstance(report, LeakageReport)
    assert report.puzzle_overlap == frozenset()
    assert report.solution_overlap == frozenset()
    assert report.has_puzzle_leakage is False
    assert report.has_solution_leakage is False
    assert report.has_leakage is False


def test_exact_puzzle_copy_is_detected():
    shared = make_record(3001)

    left = (shared,)
    right = (shared,)

    report = audit_split_leakage(left, right)

    assert report.puzzle_overlap == frozenset({shared.puzzle_hash})
    assert report.has_puzzle_leakage is True
    assert report.has_leakage is True


def test_different_puzzles_with_same_solution_are_solution_leakage():
    source = generate_puzzle(seed=4001, target_clues=30)

    solution = source.solution
    puzzle_a = source.puzzle

    # Start from the known-good Sprint-03 puzzle and remove additional
    # clues one at a time.  Each candidate is accepted only when the
    # exact Sprint-02 solver confirms that the resulting puzzle still
    # has exactly one solution.
    from sudoku_research.board import Board
    from sudoku_research.solver import count_solutions, solve

    candidate_values = list(puzzle_a.to_flat())

    for index in range(81):
        if candidate_values[index] == 0:
            continue

        original_value = candidate_values[index]
        candidate_values[index] = 0

        candidate = Board.from_flat(candidate_values)

        if count_solutions(candidate, limit=2) == 1:
            continue

        candidate_values[index] = original_value

    puzzle_b = Board.from_flat(candidate_values)

    assert puzzle_b != puzzle_a
    assert count_solutions(puzzle_b, limit=2) == 1
    assert solve(puzzle_b) == solution

    original = DatasetRecord.from_puzzle_record(source)

    clue_count = sum(value != 0 for value in puzzle_b.to_flat())

    alternate = DatasetRecord(
        puzzle_id=999,
        generator_seed=source.seed,
        puzzle=puzzle_b,
        solution=solution,
        clue_count=clue_count,
        removed_count=81 - clue_count,
        target_clues=clue_count,
        puzzle_hash=puzzle_hash(puzzle_b),
        solution_hash=solution_hash(solution),
    )

    left = (original,)
    right = (alternate,)

    report = audit_split_leakage(left, right)

    assert report.puzzle_overlap == frozenset()
    assert report.solution_overlap == frozenset(
        {original.solution_hash}
    )
    assert report.has_puzzle_leakage is False
    assert report.has_solution_leakage is True
    assert report.has_leakage is True


def test_exact_duplicate_puzzles_inside_partition_are_detected():
    record = make_record(5001)

    duplicates = find_exact_duplicates((record, record))

    assert duplicates == frozenset({record.puzzle_hash})


def test_exact_duplicate_puzzles_inside_partition_are_not_reported_when_unique():
    records = (
        make_record(5101),
        make_record(5102),
        make_record(5103),
    )

    duplicates = find_exact_duplicates(records)

    assert duplicates == frozenset()


def test_duplicate_solutions_inside_partition_are_detected():
    record = make_record(5201)

    duplicates = find_solution_duplicates((record, record))

    assert duplicates == frozenset({record.solution_hash})


def test_duplicate_solutions_inside_partition_are_not_reported_when_unique():
    records = (
        make_record(5301),
        make_record(5302),
        make_record(5303),
    )

    duplicates = find_solution_duplicates(records)

    assert duplicates == frozenset()


def test_empty_partitions_are_valid_and_clean():
    report = audit_split_leakage((), ())

    assert report.puzzle_overlap == frozenset()
    assert report.solution_overlap == frozenset()
    assert report.has_leakage is False


def test_leakage_report_is_immutable():
    report = LeakageReport(
        left_puzzle_duplicates=frozenset(),
        right_puzzle_duplicates=frozenset(),
        left_solution_duplicates=frozenset(),
        right_solution_duplicates=frozenset(),
        puzzle_overlap=frozenset({"puzzle"}),
        solution_overlap=frozenset({"solution"}),
    )

    with pytest.raises(Exception):
        report.puzzle_overlap = frozenset()


@pytest.mark.parametrize(
    "function",
    [
        find_exact_duplicates,
        find_solution_duplicates,
    ],
)
def test_duplicate_detectors_reject_non_tuple(function):
    with pytest.raises(TypeError, match="tuple"):
        function([])


def test_split_audit_rejects_non_tuple_left_partition():
    with pytest.raises(TypeError, match="left"):
        audit_split_leakage([], ())


def test_split_audit_rejects_non_tuple_right_partition():
    with pytest.raises(TypeError, match="right"):
        audit_split_leakage((), [])


def test_split_audit_rejects_invalid_record_inside_partition():
    with pytest.raises(TypeError, match="DatasetRecord"):
        audit_split_leakage((object(),), ())


def test_duplicate_detector_rejects_invalid_record_inside_partition():
    with pytest.raises(TypeError, match="DatasetRecord"):
        find_exact_duplicates((object(),))


def test_tampered_hash_cannot_hide_actual_puzzle_identity():
    record = make_record(5401)

    tampered = replace(record, puzzle_hash="0" * 64)

    with pytest.raises(ValueError, match="puzzle_hash"):
        tampered.validate_identity()


def test_clean_report_has_no_internal_duplicates():
    left = (make_record(6001), make_record(6002))
    right = (make_record(6003), make_record(6004))

    report = audit_split_leakage(left, right)

    assert report.left_puzzle_duplicates == frozenset()
    assert report.right_puzzle_duplicates == frozenset()
    assert report.left_solution_duplicates == frozenset()
    assert report.right_solution_duplicates == frozenset()
    assert report.has_left_duplicates is False
    assert report.has_right_duplicates is False
    assert report.is_clean is True


def test_left_partition_duplicates_are_reported():
    record = make_record(6101)

    report = audit_split_leakage(
        (record, record),
        (),
    )

    assert report.left_puzzle_duplicates == frozenset(
        {record.puzzle_hash}
    )
    assert report.left_solution_duplicates == frozenset(
        {record.solution_hash}
    )
    assert report.right_puzzle_duplicates == frozenset()
    assert report.right_solution_duplicates == frozenset()
    assert report.has_left_duplicates is True
    assert report.has_right_duplicates is False
    assert report.has_leakage is False
    assert report.is_clean is False


def test_right_partition_duplicates_are_reported():
    record = make_record(6201)

    report = audit_split_leakage(
        (),
        (record, record),
    )

    assert report.left_puzzle_duplicates == frozenset()
    assert report.left_solution_duplicates == frozenset()
    assert report.right_puzzle_duplicates == frozenset(
        {record.puzzle_hash}
    )
    assert report.right_solution_duplicates == frozenset(
        {record.solution_hash}
    )
    assert report.has_left_duplicates is False
    assert report.has_right_duplicates is True
    assert report.has_leakage is False
    assert report.is_clean is False


def test_cross_partition_puzzle_leakage_does_not_create_internal_duplicates():
    record = make_record(6301)

    report = audit_split_leakage(
        (record,),
        (record,),
    )

    assert report.left_puzzle_duplicates == frozenset()
    assert report.right_puzzle_duplicates == frozenset()
    assert report.left_solution_duplicates == frozenset()
    assert report.right_solution_duplicates == frozenset()
    assert report.puzzle_overlap == frozenset({record.puzzle_hash})
    assert report.solution_overlap == frozenset({record.solution_hash})
    assert report.has_left_duplicates is False
    assert report.has_right_duplicates is False
    assert report.has_leakage is True
    assert report.is_clean is False


def test_leakage_report_is_clean_only_when_all_categories_are_clear():
    clean = LeakageReport(
        left_puzzle_duplicates=frozenset(),
        right_puzzle_duplicates=frozenset(),
        left_solution_duplicates=frozenset(),
        right_solution_duplicates=frozenset(),
        puzzle_overlap=frozenset(),
        solution_overlap=frozenset(),
    )

    assert clean.is_clean is True
    assert clean.has_leakage is False


def test_leakage_report_with_internal_duplicates_is_not_clean():
    report = LeakageReport(
        left_puzzle_duplicates=frozenset({"puzzle"}),
        right_puzzle_duplicates=frozenset(),
        left_solution_duplicates=frozenset(),
        right_solution_duplicates=frozenset(),
        puzzle_overlap=frozenset(),
        solution_overlap=frozenset(),
    )

    assert report.has_left_duplicates is True
    assert report.has_right_duplicates is False
    assert report.has_leakage is False
    assert report.is_clean is False
