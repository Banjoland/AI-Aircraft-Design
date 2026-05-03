"""
Thin subprocess wrapper around the OpenVSP-bundled Python launcher.

Usage (as a module):
    from TOOLS.openvsp_runner.runner import run
    result = run("my_script.py", cwd="/some/dir")
    print(result.stdout)

Usage (CLI):
    python runner.py path/to/script.py [script args...]
"""

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

OPENVSP_LAUNCHER = Path(
    r"C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd"
)


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    elapsed_s: float

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run(script_path: str | Path, cwd: str | Path | None = None, timeout: int = 300, args: list[str] | None = None) -> RunResult:
    """Invoke an OpenVSP Python script via the bundled launcher and return its output."""
    script_path = Path(script_path).resolve()
    if not OPENVSP_LAUNCHER.exists():
        raise FileNotFoundError(f"OpenVSP launcher not found: {OPENVSP_LAUNCHER}")
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    t0 = time.monotonic()
    proc = subprocess.run(
        [str(OPENVSP_LAUNCHER), str(script_path), *(args or [])],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else str(script_path.parent),
        timeout=timeout,
    )
    elapsed = time.monotonic() - t0

    return RunResult(
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        elapsed_s=elapsed,
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python runner.py <script.py>", file=sys.stderr)
        sys.exit(1)

    result = run(sys.argv[1], args=sys.argv[2:])
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    sys.exit(result.returncode)
