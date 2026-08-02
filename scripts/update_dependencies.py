#!/usr/bin/env python3
"""Safely check and update pinned Python dependencies.

Examples:
    python scripts/update_dependencies.py
    python scripts/update_dependencies.py --update streamlit pyarrow
    python scripts/update_dependencies.py --update streamlit --apply
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


PIN_RE = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s;]+)(.*)$")


def canonical_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


@dataclass(frozen=True)
class Pin:
    name: str
    version: str
    suffix: str = ""


def read_pins(path: Path) -> dict[str, Pin]:
    pins: dict[str, Pin] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = PIN_RE.match(raw_line.strip())
        if match:
            pin = Pin(match.group(1), match.group(2), match.group(3))
            pins[canonical_name(pin.name)] = pin
    return pins


def latest_stable_version(package: str, timeout: int = 15) -> str:
    url = f"https://pypi.org/pypi/{package}/json"
    request = urllib.request.Request(url, headers={"User-Agent": "dependency-updater/1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    return str(payload["info"]["version"])


def check_updates(pins: dict[str, Pin]) -> list[tuple[Pin, str | None, str | None]]:
    results: list[tuple[Pin, str | None, str | None]] = []
    for key in sorted(pins):
        pin = pins[key]
        try:
            latest = latest_stable_version(pin.name)
            results.append((pin, latest, None))
        except (OSError, KeyError, ValueError, urllib.error.URLError) as exc:
            results.append((pin, None, str(exc)))
    return results


def run(command: list[str], *, cwd: Path) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def create_tool_venv(directory: Path) -> Path:
    venv_dir = directory / "tools-venv"
    run([sys.executable, "-m", "venv", str(venv_dir)], cwd=directory)
    python = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "pip-tools"], cwd=directory)
    return python


def make_candidate_input(source: Path, destination: Path, selected: set[str]) -> None:
    output: list[str] = []
    for raw_line in source.read_text(encoding="utf-8").splitlines():
        match = PIN_RE.match(raw_line.strip())
        if match and canonical_name(match.group(1)) in selected:
            output.append(f"{match.group(1)}{match.group(3)}")
        else:
            output.append(raw_line)
    destination.write_text("\n".join(output) + "\n", encoding="utf-8")


def update_dependencies(root: Path, packages: list[str], apply: bool) -> int:
    input_path = root / "requirements.in"
    lock_path = root / "requirements.txt"
    source_pins = read_pins(input_path)
    selected = {canonical_name(name) for name in packages}
    unknown = sorted(selected - source_pins.keys())
    if unknown:
        print("Unknown top-level package(s):", ", ".join(unknown), file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="dependency-update-") as temp_name:
        temp_dir = Path(temp_name)
        candidate_input = temp_dir / "requirements.in"
        candidate_lock = temp_dir / "requirements.txt"
        make_candidate_input(input_path, candidate_input, selected)
        tool_python = create_tool_venv(temp_dir)

        command = [
            str(tool_python),
            "-m",
            "piptools",
            "compile",
            "--strip-extras",
            "--upgrade",
            "--output-file",
            str(candidate_lock),
            str(candidate_input),
        ]
        run(command, cwd=root)
        run(
            [sys.executable, "-m", "pip", "install", "--dry-run", "--ignore-installed", "-r", str(candidate_lock)],
            cwd=root,
        )

        resolved = read_pins(candidate_lock)
        new_input = input_path.read_text(encoding="utf-8")
        for key in selected:
            old = source_pins[key]
            new = resolved.get(key)
            if new is None:
                print(f"Resolver did not return {old.name}.", file=sys.stderr)
                return 1
            pattern = re.compile(rf"(?m)^{re.escape(old.name)}==[^\s;]+(.*)$", re.IGNORECASE)
            new_input = pattern.sub(f"{old.name}=={new.version}\\1", new_input)
            print(f"{old.name}: {old.version} -> {new.version}")

        if not apply:
            print("Dry run complete. Re-run with --apply to update requirements.in and requirements.txt.")
            return 0

        backup_dir = root / ".dependency-backups"
        backup_dir.mkdir(exist_ok=True)
        shutil.copy2(input_path, backup_dir / "requirements.in.bak")
        shutil.copy2(lock_path, backup_dir / "requirements.txt.bak")
        input_path.write_text(new_input, encoding="utf-8")
        shutil.copy2(candidate_lock, lock_path)
        print("Updated requirements.in and requirements.txt.")
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--update", nargs="+", metavar="PACKAGE", help="Top-level package(s) to resolve and update")
    parser.add_argument("--apply", action="store_true", help="Write validated updates; otherwise perform a dry run")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    input_path = root / "requirements.in"
    if not input_path.exists():
        print(f"Missing {input_path}", file=sys.stderr)
        return 2

    if args.apply and not args.update:
        print("--apply requires --update PACKAGE ...", file=sys.stderr)
        return 2

    if args.update:
        return update_dependencies(root, args.update, args.apply)

    pins = read_pins(input_path)
    errors = 0
    print(f"Checking {len(pins)} top-level dependencies from {input_path.name}...")
    for pin, latest, error in check_updates(pins):
        if error:
            errors += 1
            print(f"ERROR {pin.name}: {error}")
        elif latest == pin.version:
            print(f"OK    {pin.name}=={pin.version}")
        else:
            print(f"NEW   {pin.name}: {pin.version} -> {latest}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
