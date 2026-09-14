"""Exact identity-based leakage detection for Sudoku datasets.

Sprint 04C defines leakage at two exact-identity levels:

1. Exact puzzle leakage:
       puzzle_hash overlap between dataset partitions.

2. Exact solution-family leakage:
       solution_hash overlap between dataset partitions.

The audit also reports duplicate identities within each partition.

Structural equivalence under Sudoku symmetries is deliberately outside
the scope of this module and will be addressed separately.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dataset import DatasetRecord


@dataclass(frozen=True)
class LeakageReport:
    """Structured result of an exact-identity leakage audit.

    The report distinguishes:

    - duplicate puzzle identities within the left partition;
    - duplicate puzzle identities within the right partition;
    - duplicate solution identities within the left partition;
    - duplicate solution identities within the right partition;
    - exact puzzle identities shared by both partitions;
    - exact solution identities shared by both partitions.
    """

    left_puzzle_duplicates: frozenset[str]
    right_puzzle_duplicates: frozenset[str]
    left_solution_duplicates: frozenset[str]
    right_solution_duplicates: frozenset[str]
    puzzle_overlap: frozenset[str]
    solution_overlap: frozenset[str]

    @property
    def has_left_duplicates(self) -> bool:
        """Return whether the left partition contains duplicates."""
        return bool(
            self.left_puzzle_duplicates
            or self.left_solution_duplicates
        )

    @property
    def has_right_duplicates(self) -> bool:
        """Return whether the right partition contains duplicates."""
        return bool(
            self.right_puzzle_duplicates
            or self.right_solution_duplicates
        )

    @property
    def has_puzzle_leakage(self) -> bool:
        """Return whether exact puzzle identities overlap."""
        return bool(self.puzzle_overlap)

    @property
    def has_solution_leakage(self) -> bool:
        """Return whether exact solution identities overlap."""
        return bool(self.solution_overlap)

    @property
    def has_leakage(self) -> bool:
        """Return whether any exact cross-partition leakage exists."""
        return self.has_puzzle_leakage or self.has_solution_leakage

    @property
    def is_clean(self) -> bool:
        """Return whether both partitions are internally and externally clean."""
        return not (
            self.has_left_duplicates
            or self.has_right_duplicates
            or self.has_leakage
        )


def _validate_records(
    records: tuple[DatasetRecord, ...],
    name: str,
) -> None:
    """Validate the type of a dataset partition."""
    if not isinstance(records, tuple):
        raise TypeError(
            f"{name} must be a tuple of DatasetRecord instances"
        )

    for record in records:
        if not isinstance(record, DatasetRecord):
            raise TypeError(
                f"{name} must contain only DatasetRecord instances"
            )


def _duplicate_hashes(
    records: tuple[DatasetRecord, ...],
    attribute: str,
) -> frozenset[str]:
    """Return identities occurring more than once in a partition."""
    counts: dict[str, int] = {}

    for record in records:
        digest = getattr(record, attribute)
        counts[digest] = counts.get(digest, 0) + 1

    return frozenset(
        digest
        for digest, count in counts.items()
        if count > 1
    )


def _hash_set(
    records: tuple[DatasetRecord, ...],
    attribute: str,
) -> set[str]:
    """Extract a set of exact identity hashes from dataset records."""
    return {getattr(record, attribute) for record in records}


def find_exact_duplicates(
    records: tuple[DatasetRecord, ...],
) -> frozenset[str]:
    """Return exact puzzle hashes occurring more than once."""
    _validate_records(records, "records")
    return _duplicate_hashes(records, "puzzle_hash")


def find_solution_duplicates(
    records: tuple[DatasetRecord, ...],
) -> frozenset[str]:
    """Return solution hashes occurring more than once."""
    _validate_records(records, "records")
    return _duplicate_hashes(records, "solution_hash")


def audit_split_leakage(
    left: tuple[DatasetRecord, ...],
    right: tuple[DatasetRecord, ...],
) -> LeakageReport:
    """Audit two dataset partitions for exact identity leakage.

    The audit reports both within-partition duplicates and
    cross-partition overlap.

    Args:
        left: First dataset partition.
        right: Second dataset partition.

    Returns:
        LeakageReport containing duplicate and overlap identities.

    Raises:
        TypeError: If either partition is not a tuple of DatasetRecord
            instances.
    """
    _validate_records(left, "left")
    _validate_records(right, "right")

    left_puzzles = _hash_set(left, "puzzle_hash")
    right_puzzles = _hash_set(right, "puzzle_hash")

    left_solutions = _hash_set(left, "solution_hash")
    right_solutions = _hash_set(right, "solution_hash")

    return LeakageReport(
        left_puzzle_duplicates=find_exact_duplicates(left),
        right_puzzle_duplicates=find_exact_duplicates(right),
        left_solution_duplicates=find_solution_duplicates(left),
        right_solution_duplicates=find_solution_duplicates(right),
        puzzle_overlap=frozenset(left_puzzles & right_puzzles),
        solution_overlap=frozenset(left_solutions & right_solutions),
    )


__all__ = [
    "LeakageReport",
    "audit_split_leakage",
    "find_exact_duplicates",
    "find_solution_duplicates",
]
