#!/usr/bin/env bash
set -euo pipefail

MODE="${1:---working-tree}"

echo "============================================================"
echo " Sudoku Research — Security / Secret Scan"
echo "============================================================"
echo "Mode: ${MODE}"
echo

# ------------------------------------------------------------
# Secret-pattern definitions and scanning are implemented in
# Python. The Bash layer controls repository scope and exit
# status.
# ------------------------------------------------------------

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "[FAIL] Required Python interpreter not found: $PYTHON_BIN"
    exit 1
fi

"$PYTHON_BIN" - "$MODE" <<'PY'
import re
import subprocess
import sys
import tempfile
from pathlib import Path

mode = sys.argv[1]

FORBIDDEN_NAMES = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.jks",
    "*.keystore",
    "credentials.json",
    "credential.json",
    "service-account.json",
    "secrets.json",
    "secret.json",
)

PLACEHOLDER_PREFIXES = (
    "YOUR_",
    "YOUR-",
    "CHANGE_ME",
    "CHANGEME",
    "REPLACE_ME",
    "REPLACE-ME",
    "INSERT_",
    "INSERT-",
    "PLACEHOLDER",
    "EXAMPLE",
    "DUMMY",
)

PATTERNS = [
    (
        "AWS access key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    (
        "AWS temporary access key",
        re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    ),
    (
        "GitHub token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    ),
    (
        "OpenAI-style API key",
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    ),
    (
        "Google API key",
        re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    ),
    (
        "Private key",
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
        ),
    ),
    (
        "Bearer token",
        re.compile(
            r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{20,}"
        ),
    ),
    (
        "JWT",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{10,}"
            r"\.[A-Za-z0-9_-]{10,}"
            r"\.[A-Za-z0-9_-]{10,}\b"
        ),
    ),
    (
        "Generic secret assignment",
        re.compile(
            r"""(?ix)
            \b
            (?:api[_-]?key|access[_-]?token|auth[_-]?token|
               secret[_-]?key|client[_-]?secret|private[_-]?key)
            \b
            \s*[:=]\s*
            ["']?
            (?!YOUR_|YOUR-|CHANGE_ME|CHANGEME|REPLACE_ME|REPLACE-ME|
               INSERT_|INSERT-|PLACEHOLDER|EXAMPLE|DUMMY|
               <|null|none|true|false)
            [A-Za-z0-9_./+=:-]{16,}
            ["']?
            """
        ),
    ),
    (
        "Password assignment",
        re.compile(
            r"""(?ix)
            \bpassword\b
            \s*[:=]\s*
            ["']?
            (?!YOUR_|YOUR-|CHANGE_ME|CHANGEME|REPLACE_ME|REPLACE-ME|
               INSERT_|INSERT-|PLACEHOLDER|EXAMPLE|DUMMY|
               <|null|none|true|false)
            [^\s"'#]{8,}
            ["']?
            """
        ),
    ),
    (
        "Database URL with embedded credentials",
        re.compile(
            r"""(?ix)
            (?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://
            [^\s:@/]+:[^\s@]+@
            """
        ),
    ),
]


def redact(value: str) -> str:
    """Never print the detected credential itself."""
    if len(value) <= 8:
        return "[REDACTED]"
    return value[:4] + "..." + value[-4:] + " [REDACTED]"


def tracked_files():
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [
        item
        for item in result.stdout.decode(
            "utf-8", errors="replace"
        ).split("\0")
        if item
    ]


def forbidden_filename(path: str) -> bool:
    from fnmatch import fnmatch

    name = Path(path).name

    for pattern in FORBIDDEN_NAMES:
        if fnmatch(name, pattern):
            return True

    return False


def scan_text(source: str, text: str):
    findings = []

    for line_number, line in enumerate(
        text.splitlines(), start=1
    ):
        for name, pattern in PATTERNS:
            match = pattern.search(line)

            if match:
                findings.append(
                    (
                        source,
                        line_number,
                        name,
                        redact(match.group(0)),
                    )
                )

    return findings


def scan_working_tree():
    findings = []

    for filename in tracked_files():
        path = Path(filename)

        if forbidden_filename(filename):
            findings.append(
                (
                    filename,
                    0,
                    "Forbidden credential-bearing filename",
                    "[REDACTED]",
                )
            )

        if not path.is_file():
            continue

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            continue

        findings.extend(scan_text(filename, text))

    return findings


def scan_head():
    findings = []

    for filename in tracked_files():
        if forbidden_filename(filename):
            findings.append(
                (
                    f"HEAD:{filename}",
                    0,
                    "Forbidden credential-bearing filename",
                    "[REDACTED]",
                )
            )

        result = subprocess.run(
            ["git", "show", f"HEAD:{filename}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

        if result.returncode != 0:
            continue

        text = result.stdout.decode(
            "utf-8", errors="replace"
        )

        findings.extend(
            scan_text(f"HEAD:{filename}", text)
        )

    return findings


def scan_staged():
    findings = []

    result = subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--binary",
            "--no-ext-diff",
            "--unified=0",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    text = result.stdout.decode(
        "utf-8", errors="replace"
    )

    findings.extend(
        scan_text("STAGED DIFF", text)
    )

    # Also inspect staged filenames.
    names = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode(
        "utf-8", errors="replace"
    ).split("\0")

    for filename in names:
        if filename and forbidden_filename(filename):
            findings.append(
                (
                    f"STAGED:{filename}",
                    0,
                    "Forbidden credential-bearing filename",
                    "[REDACTED]",
                )
            )

    return findings


def scan_history():
    findings = []

    commits = subprocess.run(
        ["git", "rev-list", "--all"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode().splitlines()

    for commit in commits:
        filenames = subprocess.run(
            [
                "git",
                "ls-tree",
                "-r",
                "--name-only",
                commit,
            ],
            check=True,
            stdout=subprocess.PIPE,
        ).stdout.decode(
            "utf-8", errors="replace"
        ).splitlines()

        for filename in filenames:
            if forbidden_filename(filename):
                findings.append(
                    (
                        f"{commit[:12]}:{filename}",
                        0,
                        "Forbidden credential-bearing filename",
                        "[REDACTED]",
                    )
                )

            result = subprocess.run(
                ["git", "show", f"{commit}:{filename}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )

            if result.returncode != 0:
                continue

            text = result.stdout.decode(
                "utf-8", errors="replace"
            )

            findings.extend(
                scan_text(
                    f"{commit[:12]}:{filename}",
                    text,
                )
            )

    return findings


def print_findings(findings):
    print()

    for source, line_number, name, value in findings:
        if line_number:
            location = f"{source}:{line_number}"
        else:
            location = source

        print(f"[FAIL] {name}")
        print(f"       Location: {location}")
        print(f"       Match:    {value}")
        print()


def run_scan():
    if mode == "--working-tree":
        return scan_working_tree()

    if mode == "--staged":
        return scan_staged()

    if mode == "--head":
        return scan_head()

    if mode == "--history":
        return scan_history()

    print("[FAIL] Unknown mode:", mode)
    print(
        "       Valid modes: "
        "--working-tree, --staged, --head, --history, --self-test"
    )
    sys.exit(2)


def self_test():
    synthetic_cases = {
        "AWS access key": "AKIA" + "0" * 16,
        "AWS temporary access key": "ASIA" + "0" * 16,
        "GitHub token": "ghp_" + "A" * 36,
        "OpenAI-style API key": "sk-" + "A" * 30,
        "Google API key": "AIza" + "A" * 35,
        "Private key": (
            "-----BEGIN "
            + "RSA "
            + "PRIVATE KEY-----"
        ),
        "Bearer token": "Bearer " + "A" * 30,
        "JWT": (
            "eyJ" + "A" * 20
            + "."
            + "B" * 20
            + "."
            + "C" * 20
        ),
        "Generic secret assignment": (
            "api_key = " + "A" * 24
        ),
        "Password assignment": (
            "password = " + "A" * 12
        ),
        "Database URL with embedded credentials": (
            "postgres"
            + "ql://"
            + "fakeuser"
            + ":"
            + "fakepassword"
            + "@"
            + "example.invalid/db"
        ),
    }

    failed = False

    for expected_name, value in synthetic_cases.items():
        matched = False

        for pattern_name, pattern in PATTERNS:
            if pattern_name == expected_name and pattern.search(value):
                matched = True
                break

        if matched:
            print(
                f"[PASS] Self-test detects: {expected_name}"
            )
        else:
            print(
                f"[FAIL] Self-test does not detect: "
                f"{expected_name}"
            )
            failed = True

    # Verify placeholders are not treated as secrets.
    safe_placeholders = (
        "api_key = YOUR_API_KEY_HERE",
        "password = CHANGE_ME",
        "secret_key = <REPLACE_ME>",
    )

    for value in safe_placeholders:
        matched = any(
            pattern.search(value)
            for _, pattern in PATTERNS
        )

        if matched:
            print(
                f"[FAIL] Placeholder incorrectly detected: "
                f"{value}"
            )
            failed = True
        else:
            print(
                "[PASS] Placeholder correctly ignored"
            )

    # Verify redaction does not return the complete value.
    secret = "AKIA" + "0" * 16
    redacted = redact(secret)

    if redacted == secret or secret in redacted:
        print("[FAIL] Redaction test failed")
        failed = True
    else:
        print("[PASS] Detection output is redacted")

    if failed:
        print()
        print("SECURITY SCANNER SELF-TEST FAILED")
        return 1

    print()
    print("SECURITY SCANNER SELF-TEST PASSED")
    return 0


if mode == "--self-test":
    sys.exit(self_test())

findings = run_scan()

if findings:
    print_findings(findings)
    print("============================================================")
    print(" SECURITY SCAN FAILED")
    print(f" Findings: {len(findings)}")
    print("============================================================")
    sys.exit(1)

print("[PASS] No configured secret patterns detected")
print("============================================================")
print(" SECURITY SCAN PASSED")
print("============================================================")
PY
