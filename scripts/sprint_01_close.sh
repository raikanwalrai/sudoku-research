#!/usr/bin/env bash

set -euo pipefail

echo "=================================================="
echo "SPRINT 01 — DOCUMENTATION CLOSURE"
echo "=================================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo
echo "Repository: $ROOT_DIR"

echo
echo "===== VERIFY REQUIRED FILES ====="
test -f README.md
test -f research/research_log.tex
test -f src/sudoku_research/board.py
test -f src/sudoku_research/validator.py
test -f tests/test_board.py
test -f tests/test_validator.py
echo "Required files: PASS"

echo
echo "===== UPDATE RESEARCH LOG ====="
python3 - <<'PY'
from pathlib import Path

path = Path("research/research_log.tex")
text = path.read_text()

old_status = (
    "Sprint 01 & Mathematical representation, board, constraints, validator -- pending \\\\"
)

new_status = (
    "Sprint 01 & Mathematical representation, board, constraints, validator -- COMPLETE \\\\"
)

if text.count(old_status) != 1:
    raise SystemExit(
        f"Expected exactly one Sprint 01 pending status; found {text.count(old_status)}"
    )

if "\\section{Sprint 01}" in text:
    raise SystemExit("Sprint 01 research-log section already exists.")

completion = r"""
\section{Sprint 01}

Sprint 01 established the mathematical representation and foundational
constraint-validation layer for Sudoku.

\subsection{Implementation}

The board is represented as a $9\times9$ structure with integer cell values in
the domain $\{0,\ldots,9\}$. The value $0$ represents an empty cell. A
row-major flattened representation contains exactly 81 cells.

The implementation provides an immutable \texttt{Board} abstraction with:

\begin{itemize}
    \item construction from rows;
    \item construction from exactly 81 row-major values;
    \item conversion back to row and flattened representations;
    \item coordinate-based cell access;
    \item functional cell replacement returning a new board;
    \item completeness checking;
    \item validation of board shape and cell-value domain.
\end{itemize}

Boolean values are explicitly rejected even though Python treats
\texttt{bool} as a subclass of \texttt{int}. This preserves the intended
mathematical cell domain.

\subsection{Constraint Validation}

The validator is separated from the board representation. It provides:

\begin{itemize}
    \item partial-board validation;
    \item row constraint validation;
    \item column constraint validation;
    \item $3\times3$ box constraint validation;
    \item complete-solution validation;
    \item legal candidate-value computation for empty cells.
\end{itemize}

A valid partial board contains no duplicate non-zero values in any row,
column, or $3\times3$ box. A valid solution additionally requires every cell
to be populated.

\subsection{Verification}

The Sprint 01 developer implementation script was executed after the final
domain-validation correction.

The resulting verification was:

\begin{itemize}
    \item 20 tests passed;
    \item Python syntax/compile checks passed;
    \item \texttt{Board} import passed;
    \item validator imports passed;
    \item foundational board invariants passed;
    \item \texttt{git diff --check} passed.
\end{itemize}

Sprint 01 therefore establishes the verified representation and validation
foundation required by the exact solver/oracle work in Sprint 02.
"""

text = text.replace(old_status, new_status)

marker = "\\end{document}"
if text.count(marker) != 1:
    raise SystemExit(
        f"Expected exactly one document terminator; found {text.count(marker)}"
    )

text = text.replace(marker, completion + "\n" + marker)

path.write_text(text)
PY

echo "Research log: UPDATED"

echo
echo "===== UPDATE README ====="
python3 - <<'PY'
from pathlib import Path

path = Path("README.md")
text = path.read_text()

heading = "## Current implementation status"

if heading in text:
    raise SystemExit("README implementation-status section already exists.")

section = """## Current implementation status

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

"""

anchor = "## Development discipline"

if text.count(anchor) != 1:
    raise SystemExit(
        f"Expected exactly one README development-discipline section; found {text.count(anchor)}"
    )

text = text.replace(anchor, section + anchor)

path.write_text(text)
PY

echo "README: UPDATED"

echo
echo "=================================================="
echo "SPRINT 01 DOCUMENTATION CLOSURE COMPLETE"
echo "=================================================="
