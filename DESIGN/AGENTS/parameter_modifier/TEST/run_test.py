"""
Test driver for parameter_modifier.

No OpenVSP run is performed. The test verifies listing, valid override creation,
and invalid parameter rejection.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
AGENT_DIR = HERE.parent
PROJECT_ROOT = HERE.parents[3]
SCRIPT = AGENT_DIR / "make_override.py"


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )


def fail(message: str, proc: subprocess.CompletedProcess[str] | None = None) -> int:
    print(f"FAIL: {message}")
    if proc is not None:
        print(proc.stdout)
        print(proc.stderr)
    return 1


def extract_override_path(stdout: str) -> Path | None:
    for line in stdout.splitlines():
        if line.startswith("OVERRIDE_FILE:"):
            return Path(line.split(":", 1)[1].strip())
    return None


def main() -> int:
    listed = run(["--list"])
    if listed.returncode != 0:
        return fail("--list failed", listed)
    listing = json.loads(listed.stdout)
    if "wingspan" not in listing:
        return fail("--list did not include wingspan")

    valid = run(["wingspan", "--set", "wing_span=10.0"])
    if valid.returncode != 0:
        return fail("valid override failed", valid)
    override_path = extract_override_path(valid.stdout)
    if override_path is None or not override_path.exists():
        return fail("override file was not written", valid)
    override = json.loads(override_path.read_text(encoding="utf-8"))
    if override.get("wing_span") != 10.0:
        return fail(f"unexpected override content: {override}")

    invalid = run(["wingspan", "--set", "wing_root_chord=0.5"])
    if invalid.returncode == 0:
        return fail("invalid parameter was accepted", invalid)

    print(f"OVERRIDE_FILE:{override_path}")
    print("PASS: parameter_modifier created and validated override files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
