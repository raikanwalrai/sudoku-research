"""Reproducible synthetic Sudoku solution and puzzle generation."""

from __future__ import annotations

from dataclasses import dataclass
import random

from sudoku_research.board import BOARD_SIZE, Board
from sudoku_research.solver import count_solutions, solve
from sudoku_research.validator import is_valid_partial, is_valid_solution


@dataclass(frozen=True)
class PuzzleRecord:
    """A reproducibly generated Sudoku puzzle and its ground-truth solution."""

    puzzle_id: int
    seed: int
    puzzle: Board
    solution: Board
    clue_count: int
    removed_count: int
    target_clues: int


def _validate_seed(seed: int) -> None:
    """Validate a generator seed."""
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer.")


def _validate_target_clues(target_clues: int) -> None:
    """Validate a requested number of retained clues."""
    if isinstance(target_clues, bool) or not isinstance(target_clues, int):
        raise TypeError("target_clues must be an integer.")

    if not 25 <= target_clues <= BOARD_SIZE * BOARD_SIZE:
        raise ValueError("target_clues must be in the range 25..81.")


def _validate_dataset_size(size: int) -> None:
    """Validate a requested dataset size."""
    if isinstance(size, bool) or not isinstance(size, int):
        raise TypeError("size must be an integer.")

    if size < 1:
        raise ValueError("size must be at least 1.")


def _generate_solution_with_rng(rng: random.Random) -> Board:
    """Generate a complete valid Sudoku using seeded randomized DFS."""

    board = Board.empty()

    def search(current: Board) -> Board | None:
        # Find the first empty cell in row-major order.
        selected: tuple[int, int] | None = None

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if current.get(row, col) == 0:
                    selected = (row, col)
                    break
            if selected is not None:
                break

        if selected is None:
            return current if is_valid_solution(current) else None

        row, col = selected

        # Candidate values are calculated from the current partial board.
        candidates = set(range(1, BOARD_SIZE + 1))

        for index in range(BOARD_SIZE):
            candidates.discard(current.get(row, index))
            candidates.discard(current.get(index, col))

        box_row = (row // 3) * 3
        box_col = (col // 3) * 3

        for r in range(box_row, box_row + 3):
            for c in range(box_col, box_col + 3):
                candidates.discard(current.get(r, c))

        ordered_candidates = list(candidates)
        rng.shuffle(ordered_candidates)

        for value in ordered_candidates:
            next_board = current.set(row, col, value)

            if not is_valid_partial(next_board):
                continue

            result = search(next_board)

            if result is not None:
                return result

        return None

    result = search(board)

    if result is None:
        raise RuntimeError("Seeded solution generation failed unexpectedly.")

    return result


def generate_solution(seed: int) -> Board:
    """Generate a complete valid Sudoku solution reproducibly from ``seed``.

    The same seed produces the same solution.
    """
    _validate_seed(seed)

    rng = random.Random(seed)
    solution = _generate_solution_with_rng(rng)

    if not is_valid_solution(solution):
        raise RuntimeError("Generator produced an invalid complete solution.")

    return solution


def _remove_clues(
    solution: Board,
    rng: random.Random,
    target_clues: int,
) -> Board:
    """Remove clues while preserving unique solvability."""

    puzzle = solution
    positions = list(range(BOARD_SIZE * BOARD_SIZE))
    rng.shuffle(positions)

    clue_count = BOARD_SIZE * BOARD_SIZE

    for index in positions:
        if clue_count <= target_clues:
            break

        row, col = divmod(index, BOARD_SIZE)

        # This cell is already empty only if a future policy changes this
        # function. Keeping this guard makes the operation explicit.
        if puzzle.get(row, col) == 0:
            continue

        candidate = puzzle.set(row, col, 0)

        if count_solutions(candidate, limit=2) == 1:
            puzzle = candidate
            clue_count -= 1

    return puzzle


def generate_puzzle(seed: int, target_clues: int = 30) -> PuzzleRecord:
    """Generate one uniquely solvable synthetic Sudoku puzzle.

    Args:
        seed: Integer seed controlling all generation randomness.
        target_clues: Desired number of retained clues.

    Returns:
        A ``PuzzleRecord`` containing the puzzle and exact solution.

    Raises:
        TypeError: If ``seed`` or ``target_clues`` has an invalid type.
        ValueError: If ``target_clues`` is outside 25..81.
        RuntimeError: If the requested clue count cannot be reached while
            preserving uniqueness.
    """
    _validate_seed(seed)
    _validate_target_clues(target_clues)

    rng = random.Random(seed)
    solution = _generate_solution_with_rng(rng)
    puzzle = _remove_clues(solution, rng, target_clues)

    clue_count = sum(value != 0 for value in puzzle.to_flat())
    removed_count = BOARD_SIZE * BOARD_SIZE - clue_count

    if clue_count != target_clues:
        raise RuntimeError(
            "Unable to reach the requested target clue count while "
            "preserving unique solvability."
        )

    if not is_valid_solution(solution):
        raise RuntimeError("Generated solution is invalid.")

    if not is_valid_partial(puzzle):
        raise RuntimeError("Generated puzzle is invalid.")

    if count_solutions(puzzle, limit=2) != 1:
        raise RuntimeError("Generated puzzle is not uniquely solvable.")

    oracle_solution = solve(puzzle)

    if oracle_solution != solution:
        raise RuntimeError(
            "Generator solution disagrees with the independent solver oracle."
        )

    if not all(
        puzzle_value == 0 or puzzle_value == solution_value
        for puzzle_value, solution_value in zip(
            puzzle.to_flat(), solution.to_flat()
        )
    ):
        raise RuntimeError("Puzzle contains a clue inconsistent with its solution.")

    return PuzzleRecord(
        puzzle_id=0,
        seed=seed,
        puzzle=puzzle,
        solution=solution,
        clue_count=clue_count,
        removed_count=removed_count,
        target_clues=target_clues,
    )


def generate_dataset(
    size: int,
    seed: int = 0,
    target_clues: int = 30,
) -> tuple[PuzzleRecord, ...]:
    """Generate a reproducible collection of Sudoku puzzle records.

    Puzzle seeds are derived deterministically from the supplied dataset seed.
    Each record receives a stable zero-based ``puzzle_id``.
    """
    _validate_dataset_size(size)
    _validate_seed(seed)
    _validate_target_clues(target_clues)

    dataset_rng = random.Random(seed)
    records: list[PuzzleRecord] = []

    for puzzle_id in range(size):
        puzzle_seed = dataset_rng.randrange(0, 2**63)

        record = generate_puzzle(
            seed=puzzle_seed,
            target_clues=target_clues,
        )

        records.append(
            PuzzleRecord(
                puzzle_id=puzzle_id,
                seed=record.seed,
                puzzle=record.puzzle,
                solution=record.solution,
                clue_count=record.clue_count,
                removed_count=record.removed_count,
                target_clues=record.target_clues,
            )
        )

    return tuple(records)


__all__ = [
    "PuzzleRecord",
    "generate_dataset",
    "generate_puzzle",
    "generate_solution",
]
