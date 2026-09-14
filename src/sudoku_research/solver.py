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
