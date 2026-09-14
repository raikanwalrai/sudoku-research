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
