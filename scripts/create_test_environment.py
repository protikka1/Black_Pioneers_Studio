#!/usr/bin/env python3
"""Create and validate an isolated test environment for this project."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run(command: list[str], *, cwd: Path) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def environment_python(environment: Path) -> Path:
    if sys.platform == "win32":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (default: detected from this script)",
    )
    parser.add_argument(
        "--environment",
        type=Path,
        default=Path(".venv-test"),
        help="Virtual environment path, relative to the repository root by default",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Remove and rebuild the selected test environment",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run pytest after setup and validation",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    environment = args.environment
    if not environment.is_absolute():
        environment = root / environment
    environment = environment.resolve()

    required = [root / "requirements.txt", root / "requirements-dev.in"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print("Missing required file(s): " + ", ".join(missing), file=sys.stderr)
        return 2

    if environment == root or root not in environment.parents:
        print("The test environment must be inside the repository.", file=sys.stderr)
        return 2

    if args.recreate and environment.exists():
        print(f"Removing test environment: {environment}")
        shutil.rmtree(environment)

    if not environment.exists():
        run([sys.executable, "-m", "venv", str(environment)], cwd=root)

    python = environment_python(environment)
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"], cwd=root)
    run([str(python), "-m", "pip", "install", "-r", "requirements.txt"], cwd=root)
    run([str(python), "-m", "pip", "install", "-r", "requirements-dev.in"], cwd=root)
    run([str(python), "-m", "pip", "check"], cwd=root)
    run(
        [
            str(python),
            "-m",
            "py_compile",
            "app.py",
            "database/connection.py",
            "database/migrations.py",
        ],
        cwd=root,
    )

    if args.run_tests:
        run([str(python), "-m", "pytest", "-q"], cwd=root)

    print(f"Test environment ready: {environment}")
    print(f"Python executable: {python}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
