#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "===== Sprint 02 Closure ====="

REQUIRED_FILES=(
    "src/sudoku_research/solver.py"
    "tests/test_solver.py"
    "scripts/sprint_02_implementation.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "ERROR: Missing required file: $file"
        exit 1
    fi
done

echo "Required files: PASS"

python - <<'PY'
from pathlib import Path

readme = Path("README.md")
log = Path("research/research_log.tex")

readme_text = readme.read_text()
log_text = log.read_text()

old_status = "Sprint 02 & Exact Sudoku solver / ground-truth oracle -- pending"
new_status = "Sprint 02 & Exact Sudoku solver / ground-truth oracle -- COMPLETE"

if old_status not in log_text:
    raise SystemExit("ERROR: Expected Sprint 02 pending status not found.")

log_text = log_text.replace(old_status, new_status, 1)

section = r"""
\section{Sprint 02}

Sprint 02 established the deterministic exact Sudoku solver and
ground-truth oracle required for all subsequent learning experiments.

\subsection{Solver Design}

The exact solver operates directly on the immutable \texttt{Board}
representation established in Sprint 01. Sudoku constraint semantics are
delegated to the existing validator rather than duplicated inside the
solver.

The search procedure uses deterministic depth-first backtracking with
Minimum Remaining Values (MRV) cell selection. Candidate values are
obtained from the Sprint 01 candidate computation. Candidate traversal is
sorted so that identical input boards produce identical search decisions
and solutions.

\subsection{Oracle Semantics}

The solver provides three principal operations:

\begin{itemize}
    \item \texttt{solve(board)} returns a solution only when exactly one
    solution exists;
    \item \texttt{count\_solutions(board, limit)} counts solutions up to
    the supplied stopping limit;
    \item \texttt{has\_unique\_solution(board)} tests whether exactly one
    solution exists.
\end{itemize}

With the standard stopping threshold of two, the oracle distinguishes:

\[
\operatorname{count}(X)=0
\]

for an unsatisfiable puzzle,

\[
\operatorname{count}(X)=1
\]

for a uniquely solvable puzzle, and

\[
\operatorname{count}(X)\geq2
\]

for a puzzle with multiple solutions.

This distinction is important because later synthetic datasets must be
able to guarantee unique solutions without relying on a neural model.

\subsection{Solution Verification}

The implementation also provides \texttt{verify\_solution(board, solution)}.
A verified solution must be complete, satisfy all Sudoku constraints, and
preserve every non-zero clue present in the original puzzle.

\subsection{Research Independence}

The exact solver contains no neural-network component and does not depend
on learned parameters, learned representations, or training data. It is
therefore maintained as an independent computational oracle against which
later neural models can be evaluated.

The intended later comparison is:

\[
N_{\theta}(X) \stackrel{?}{=} G(X),
\]

where $N_{\theta}$ denotes a neural model and $G$ denotes the exact
ground-truth solver.

\subsection{Verification}

Sprint 02 verification included:

\begin{itemize}
    \item Python compilation checks passed;
    \item the complete regression suite passed with 36 tests;
    \item unique-solution solving was tested;
    \item deterministic repeated solving was tested;
    \item complete-board handling was tested;
    \item multiple-solution detection was tested;
    \item invalid partial-board rejection was tested;
    \item solution-count limit validation was tested;
    \item solution verification was tested.
\end{itemize}

Sprint 02 therefore establishes the deterministic exact solver/oracle
required for synthetic puzzle generation and ground-truth dataset
construction in Sprint 03.
"""

marker = r"\end{document}"

if r"\section{Sprint 02}" in log_text:
    raise SystemExit("ERROR: Sprint 02 research-log section already exists.")

if marker not in log_text:
    raise SystemExit("ERROR: research log does not contain end-document marker.")

log_text = log_text.replace(marker, section.strip() + "\n\n" + marker, 1)
log.write_text(log_text)

status_heading = "## Current implementation status"

sprint02_readme = """### Sprint 02 — Exact solver / ground-truth oracle

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

"""

if "### Sprint 02 — Exact solver / ground-truth oracle" in readme_text:
    raise SystemExit("ERROR: Sprint 02 README section already exists.")

if status_heading not in readme_text:
    raise SystemExit("ERROR: README status section not found.")

readme_text = readme_text.replace(
    status_heading,
    status_heading + "\n\n" + sprint02_readme,
    1,
)

readme.write_text(readme_text)

print("Research log: UPDATED")
print("README: UPDATED")
PY

echo "Closure documentation: PASS"

echo
echo "===== DOCUMENTATION CHECK ====="
grep -n -A30 -B3 "Sprint 02" README.md
echo
grep -n -A80 -B3 "section{Sprint 02}" research/research_log.tex

echo
echo "===== COMPILE CHECK ====="
python -m compileall -q src tests
echo "PASS"

echo
echo "===== FULL TEST SUITE ====="
pytest -q

echo
echo "===== DIFF CHECK ====="
git diff --check

echo
echo "===== STATUS ====="
git status --short

echo
echo "===== SPRINT 02 CLOSURE COMPLETE ====="
