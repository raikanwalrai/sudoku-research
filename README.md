# Sudoku Neural-to-Fundamental-Function Research

This repository contains the reproducible research implementation for studying
whether progressively sophisticated neural architectures trained on Sudoku
can learn, expose, or support the discovery of compact underlying structure.

The research progression is:

MLP → CNN → RNN/LSTM/GRU → GNN → Transformer → GPT-style → Hybrid Neural-Constraint

The final research objective is not merely predictive accuracy. The project
investigates whether learned parameters, representations, trajectories, and
constraints can be reverse-engineered into an independently implemented
function, equation, rule system, compact algorithm, or solver.

## Core validation principle

The strongest validation target is an independently implemented function or
solver that operates without the original neural network and correctly maps
entirely unseen Sudoku puzzles to their valid solutions.

## Reproducibility

All experiments must record:

- dataset version
- generator version
- random seeds
- architecture
- hyperparameters
- training history
- model parameters
- internal representations
- attention / activation artifacts where applicable
- evaluation metrics
- software environment

Dataset construction must prevent leakage between train, validation, and test
sets, including leakage caused by multiple puzzle variants derived from the
same completed Sudoku board.

## Current implementation status

### Sprint 01 — Mathematical representation and validator

COMPLETE.

The foundational Sudoku representation and constraint validator are implemented
under `src/sudoku_research/`, with regression tests under `tests/`.

The implementation provides:

- immutable 9×9 board representation
- row-major 81-cell flattening
- cell domain validation for integers 0–9
- explicit rejection of Boolean cell values
- row, column, and 3×3 box constraint validation
- partial-board validation
- complete-solution validation
- legal candidate-value computation

Sprint 01 verification: 20 tests passed, Python compilation passed, and
Board/Validator import and foundational invariant checks passed.

The implementation is generated reproducibly by
`scripts/sprint_01_implementation.sh`.


### Sprint 02 — Exact solver / ground-truth oracle

COMPLETE.

The deterministic exact Sudoku solver is implemented under
`src/sudoku_research/solver.py`, with regression tests under `tests/`.

The implementation provides:

- deterministic depth-first backtracking;
- Minimum Remaining Values (MRV) cell selection;
- deterministic candidate ordering;
- exact solution counting with a configurable stopping limit;
- unique-solution detection;
- unique-solution solving;
- independent solution verification;
- rejection of invalid partial Sudoku boards.

Sprint 02 verification: the complete regression suite passes with 36 tests.
The exact solver is independent of neural models and is designated as the
ground-truth oracle for subsequent dataset generation and neural-model
experiments.

The implementation is generated reproducibly by
`scripts/sprint_02_implementation.sh`.


## Development discipline

The canonical implementation belongs under `src/`.

Tests belong under `tests/`.

Research notes and decisions belong under `research/`.

Generated experiment artifacts belong under `experiments/`, `analysis/`,
`models/`, `reports/`, and `extracted/` as appropriate.

All development is performed through Bash/developer scripts so that the
research environment and repository construction remain reproducible.


### Security and pre-push gate

Security scanning is a mandatory part of the repository workflow. Before
changes are pushed to GitHub, the repository uses the executable Git hook
`.githooks/pre-push` to run the security gate.

The security infrastructure consists of:

- `scripts/security_scan.sh` — repository security and secret scanner.
- `.githooks/pre-push` — automatic pre-push security gate.
- `scripts/install_git_hooks.sh` — installer that configures Git to use
  `.githooks` through `core.hooksPath`.

The pre-push gate performs five checks:

1. security-scanner self-test;
2. working-tree security scan;
3. staged-content security scan;
4. current `HEAD` security scan; and
5. repository-history security scan.

The scanner checks configured credential-bearing filenames and secret
patterns, including AWS credentials, GitHub tokens, OpenAI-style API keys,
Google API keys, private keys, bearer tokens, JWTs, generic credential
assignments, password assignments, and database URLs containing embedded
credentials. Detection output is redacted so that a detected value is not
copied into the scan report.

The scanner also contains synthetic self-tests for its detection rules and
for placeholder exclusion. An empirical synthetic-secret test was performed
against the pre-push hook using representative AWS, OpenAI-style, and
password credentials. The hook correctly blocked the push attempt with a
non-zero exit status, and the synthetic artifact was subsequently removed.

The hook is enabled for this repository with:

    ./scripts/install_git_hooks.sh

which configures:

    core.hooksPath=.githooks

The security scanner is deliberately pattern-based. Passing the scanner
does not constitute a mathematical or cryptographic guarantee that no
secret exists. It is a reproducibility and repository-hygiene control that
must be combined with appropriate handling of credentials and other
sensitive material.

### Sprint 03 — Synthetic Sudoku Generator

**Objective:** Build a reproducible synthetic Sudoku generator that produces
complete valid solutions and partially revealed puzzles with exactly one
solution.

The generator must produce a pair

    (X, S)

where `S` is a complete valid 9x9 Sudoku solution and `X` is obtained by
controlled clue removal from `S`.

The following invariants are mandatory:

1. `S` is a valid complete Sudoku solution.
2. `X` is a valid partial Sudoku.
3. Every non-zero clue in `X` agrees with `S`.
4. `count_solutions(X, 2) == 1`.
5. `solve(X) == S`.
6. Generation is reproducible from an explicit seed and generation
   parameters.
7. Sprint 03 uses only synthetically generated Sudoku instances and does
   not depend on external Sudoku datasets.

The initial generation strategy is randomized deterministic backtracking
for complete solutions followed by controlled clue removal. Python's
standard-library `random.Random(seed)` is used so that the random state is
explicit and reproducible.

The validated operating range of the current greedy clue-removal
generator is 25--81 retained clues. Requests below 25 clues are rejected
because the current algorithm does not provide a reliable sparse-puzzle
generation method. This is an implementation scope boundary, not a claim
that uniquely solvable Sudoku puzzles below 25 clues cannot exist.

Difficulty optimization is intentionally deferred. Sprint 03 prioritizes
validity, uniqueness, reproducibility, and traceability. Dataset splitting
and formal leakage-prevention procedures are deferred to Sprint 04.

Generated datasets are not committed to Git by default. The repository
stores generator code, tests, metadata specifications, and reproducibility
information rather than large generated artifacts.

Planned implementation files:

    src/sudoku_research/generator.py
    tests/test_generator.py
    scripts/sprint_03_implementation.sh
    scripts/sprint_03_close.sh

### Sprint 04 — Dataset Engineering and Leakage Prevention

**Objective:** Build a reproducible dataset engineering pipeline that converts
synthetically generated Sudoku records into deterministic, auditable
train/validation/test datasets while explicitly detecting information leakage.

The dataset unit is a generated pair

    (X, S)

together with provenance metadata. `X` is the partially revealed Sudoku
instance and `S` is its unique complete solution.

Sprint 04 establishes three related identity concepts:

1. **Puzzle identity:** exact identity of the serialized partial board `X`.
2. **Solution identity:** exact identity of the serialized complete solution `S`.
3. **Structural identity:** a future extension for Sudoku-preserving
   transformations and symmetry-aware canonicalization.

For exact identity, each board is deterministically serialized in row-major
order and assigned a SHA-256 identity hash. The hashes are used for dataset
identity, duplicate detection, provenance, and leakage auditing.

The primary experimental split is performed at the complete-solution level,
rather than independently at the puzzle-row level. Consequently, puzzles
associated with the same exact solution must not be distributed across
different primary splits.

The primary leakage requirements are:

    H(X_train) ∩ H(X_validation) = ∅
    H(X_train) ∩ H(X_test)       = ∅
    H(X_validation) ∩ H(X_test) = ∅

and, for the primary solution-family split:

    H(S_train) ∩ H(S_validation) = ∅
    H(S_train) ∩ H(S_test)       = ∅
    H(S_validation) ∩ H(S_test) = ∅

Dataset generation and splitting must be reproducible from explicit seeds
and generation parameters. The resulting manifest must record dataset
version, generator provenance, dataset seed, split seed, record counts,
clue-count distributions, identity counts, and leakage-audit results.

Generated datasets remain excluded from Git by default. Sprint 04 stores
dataset engineering code, tests, specifications, manifests or metadata
required for reproducibility, and leakage-audit logic rather than large
generated datasets.

Structural/symmetry-aware canonicalization is treated as a distinct
capability and must not be silently conflated with exact identity. Any
future symmetry-aware leakage policy must be explicitly specified and
validated.

Planned implementation files:

    src/sudoku_research/dataset.py
    src/sudoku_research/leakage.py
    tests/test_dataset.py
    tests/test_leakage.py
    scripts/sprint_04_implementation.sh
    scripts/sprint_04_close.sh
