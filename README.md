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

## Development discipline

The canonical implementation belongs under `src/`.

Tests belong under `tests/`.

Research notes and decisions belong under `research/`.

Generated experiment artifacts belong under `experiments/`, `analysis/`,
`models/`, `reports/`, and `extracted/` as appropriate.

All development is performed through Bash/developer scripts so that the
research environment and repository construction remain reproducible.
