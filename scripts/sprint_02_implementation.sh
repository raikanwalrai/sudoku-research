#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "===== Sprint 02: Exact Solver / Oracle ====="
echo "Repository: $REPO_ROOT"
echo

mkdir -p src/sudoku_research tests

cat > src/sudoku_research/solver.py <<'PY'
"""Deterministic exact Sudoku solver and ground-truth oracle."""

from __future__ import annotations

from sudoku_research.board import BOARD_SIZE, Board
from sudoku_research.validator import (
    candidate_values,
    is_valid_partial,
    is_valid_solution,
)


def _select_mrv_cell(board: Board) -> tuple[int, int, frozenset[int]] | None:
    """Select an empty cell using Minimum Remaining Values.

    Returns:
        A tuple ``(row, col, candidates)`` for the empty cell with the
        fewest legal candidates, or ``None`` when the board is complete.

    The scan order is deterministic: row-major order breaks ties.
    """
    best: tuple[int, int, frozenset[int]] | None = None

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board.get(row, col) != 0:
                continue

            candidates = candidate_values(board, row, col)

            if best is None or len(candidates) < len(best[2]):
                best = (row, col, candidates)

                # Zero candidates means immediate contradiction.
                if not candidates:
                    return best

    return best


def _search(
    board: Board,
    solutions: list[Board],
    limit: int,
) -> None:
    """Depth-first exact search, stopping after ``limit`` solutions."""
    if len(solutions) >= limit:
        return

    selected = _select_mrv_cell(board)

    if selected is None:
        if is_valid_solution(board):
            solutions.append(board)
        return

    row, col, candidates = selected

    if not candidates:
        return

    # sorted() makes the oracle deterministic and reproducible.
    for value in sorted(candidates):
        next_board = board.set(row, col, value)

        if not is_valid_partial(next_board):
            continue

        _search(next_board, solutions, limit)

        if len(solutions) >= limit:
            return


def count_solutions(board: Board, limit: int = 2) -> int:
    """Count Sudoku solutions, up to ``limit``.

    Args:
        board: A Sudoku puzzle represented by ``Board``.
        limit: Positive stopping threshold. A value of 2 is sufficient
            to distinguish zero, unique, and multiple solutions.

    Returns:
        The number of solutions found, capped at ``limit``.

    Raises:
        TypeError: If ``limit`` is not an integer or is Boolean.
        ValueError: If ``limit`` is less than 1 or the input board is
            already invalid as a partial Sudoku.
    """
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise TypeError("limit must be an integer.")

    if limit < 1:
        raise ValueError("limit must be at least 1.")

    if not is_valid_partial(board):
        raise ValueError("Cannot solve an invalid partial Sudoku board.")

    solutions: list[Board] = []
    _search(board, solutions, limit)

    return len(solutions)


def has_unique_solution(board: Board) -> bool:
    """Return True exactly when the puzzle has one solution."""
    return count_solutions(board, limit=2) == 1


def solve(board: Board) -> Board | None:
    """Return the unique solution when one exists.

    Returns:
        The unique solved board when exactly one solution exists;
        otherwise ``None``.

    Raises:
        ValueError: If the input board is invalid as a partial Sudoku.
    """
    if not is_valid_partial(board):
        raise ValueError("Cannot solve an invalid partial Sudoku board.")

    solutions: list[Board] = []
    _search(board, solutions, limit=2)

    if len(solutions) == 1:
        return solutions[0]

    return None


def verify_solution(board: Board, solution: Board) -> bool:
    """Verify that ``solution`` is a valid solution of ``board``.

    The solution must:
      1. be a complete valid Sudoku;
      2. preserve every non-zero clue in the original board.
    """
    if not is_valid_solution(solution):
        return False

    puzzle = board.to_flat()
    solved = solution.to_flat()

    return all(
        puzzle[index] == 0 or puzzle[index] == solved[index]
        for index in range(BOARD_SIZE * BOARD_SIZE)
    )
PY

cat > tests/test_solver.py <<'PY'
"""Tests for the exact Sudoku solver/oracle."""

import pytest

from sudoku_research.board import Board
from sudoku_research.solver import (
    count_solutions,
    has_unique_solution,
    solve,
    verify_solution,
)
from sudoku_research.validator import is_valid_solution


VALID_SOLUTION = (
    (5, 3, 4, 6, 7, 8, 9, 1, 2),
    (6, 7, 2, 1, 9, 5, 3, 4, 8),
    (1, 9, 8, 3, 4, 2, 5, 6, 7),
    (8, 5, 9, 7, 6, 1, 4, 2, 3),
    (4, 2, 6, 8, 5, 3, 7, 9, 1),
    (7, 1, 3, 9, 2, 4, 8, 5, 6),
    (9, 6, 1, 5, 3, 7, 2, 8, 4),
    (2, 8, 7, 4, 1, 9, 6, 3, 5),
    (3, 4, 5, 2, 8, 6, 1, 7, 9),
)

UNIQUE_PUZZLE = (
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

# This is a deliberately underconstrained valid partial board.
# It has many completions, so counting with limit=2 must return 2.
MULTIPLE_PUZZLE = (
    (5, 3, 0, 0, 7, 0, 0, 0, 0),
    (6, 0, 0, 1, 9, 5, 0, 0, 0),
    (0, 9, 8, 0, 0, 0, 0, 6, 0),
    (8, 0, 0, 0, 6, 0, 0, 0, 0),
    (4, 0, 0, 8, 0, 3, 0, 0, 0),
    (7, 0, 0, 0, 2, 0, 0, 0, 0),
    (0, 6, 0, 0, 0, 0, 0, 8, 0),
    (0, 0, 0, 4, 1, 9, 0, 0, 0),
    (0, 0, 0, 0, 8, 0, 0, 7, 0),
)

INVALID_PUZZLE = (
    (5, 5, 0, 0, 7, 0, 0, 0, 0),
    (6, 0, 0, 1, 9, 5, 0, 0, 0),
    (0, 9, 8, 0, 0, 0, 0, 6, 0),
    (8, 0, 0, 0, 6, 0, 0, 0, 3),
    (4, 0, 0, 8, 0, 3, 0, 0, 1),
    (7, 0, 0, 0, 2, 0, 0, 0, 6),
    (0, 6, 0, 0, 0, 0, 2, 8, 0),
    (0, 0, 0, 4, 1, 9, 0, 0, 5),
    (0, 0, 0, 0, 8, 0, 0, 7, 9),
)


def test_unique_puzzle_has_one_solution() -> None:
    board = Board.from_rows(UNIQUE_PUZZLE)

    assert count_solutions(board) == 1
    assert has_unique_solution(board)


def test_solve_returns_expected_unique_solution() -> None:
    board = Board.from_rows(UNIQUE_PUZZLE)

    solution = solve(board)

    assert solution is not None
    assert solution.to_rows() == VALID_SOLUTION
    assert is_valid_solution(solution)


def test_solve_is_deterministic() -> None:
    board = Board.from_rows(UNIQUE_PUZZLE)

    first = solve(board)
    second = solve(board)

    assert first is not None
    assert second is not None
    assert first.to_flat() == second.to_flat()


def test_solution_preserves_original_clues() -> None:
    board = Board.from_rows(UNIQUE_PUZZLE)
    solution = solve(board)

    assert solution is not None
    assert verify_solution(board, solution)


def test_complete_valid_board_has_one_solution() -> None:
    board = Board.from_rows(VALID_SOLUTION)

    assert count_solutions(board) == 1
    assert solve(board) == board
    assert has_unique_solution(board)


def test_multiple_solution_puzzle_is_detected() -> None:
    board = Board.from_rows(MULTIPLE_PUZZLE)

    assert count_solutions(board, limit=2) == 2
    assert not has_unique_solution(board)
    assert solve(board) is None


def test_invalid_partial_board_is_rejected() -> None:
    board = Board.from_rows(INVALID_PUZZLE)

    with pytest.raises(ValueError):
        count_solutions(board)

    with pytest.raises(ValueError):
        solve(board)


@pytest.mark.parametrize("limit", [0, -1])
def test_invalid_solution_count_limit_is_rejected(limit: int) -> None:
    with pytest.raises(ValueError):
        count_solutions(Board.empty(), limit=limit)


@pytest.mark.parametrize("limit", [True, False, 2.0, "2"])
def test_invalid_solution_count_limit_type_is_rejected(limit) -> None:
    with pytest.raises(TypeError):
        count_solutions(Board.empty(), limit=limit)


def test_verify_solution_rejects_wrong_solution() -> None:
    puzzle = Board.from_rows(UNIQUE_PUZZLE)
    wrong_solution = Board.from_rows(VALID_SOLUTION).set(0, 0, 6)

    assert not verify_solution(puzzle, wrong_solution)


def test_verify_solution_rejects_solution_that_does_not_preserve_clues() -> None:
    puzzle = Board.from_rows(UNIQUE_PUZZLE)
    changed = Board.from_rows(VALID_SOLUTION).set(0, 0, 4)

    assert not verify_solution(puzzle, changed)


def test_verify_solution_rejects_incomplete_board() -> None:
    puzzle = Board.from_rows(UNIQUE_PUZZLE)

    assert not verify_solution(puzzle, puzzle)
PY

echo "===== COMPILE CHECK ====="
python -m compileall -q src tests
echo "PASS"

echo
echo "===== TESTS ====="
pytest -q

echo
echo "===== IMPORT CHECK ====="
python - <<'PY'
from sudoku_research.board import Board
from sudoku_research.solver import (
    count_solutions,
    has_unique_solution,
    solve,
    verify_solution,
)

board = Board.empty()

assert count_solutions(board, limit=1) == 1
assert not has_unique_solution(board)

solution = solve(board)
assert solution is None

print("Solver imports and basic oracle checks: PASS")
PY

echo
echo "===== SPRINT 02 IMPLEMENTATION COMPLETE ====="
