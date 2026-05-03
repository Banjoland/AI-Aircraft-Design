"""
Driver for the openvsp_runner smoke test.

Run from any directory:
    python run_test.py

Acceptance criteria (all must pass):
  1. runner exits 0
  2. sample_wing.vsp3 exists and is non-empty
  3. OpenVSP stdout contains "OK"
  4. Wall time under 60 s
"""

import sys
import time
from pathlib import Path

# Allow running this script directly without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # project root
from TOOLS.openvsp_runner.runner import run

HERE = Path(__file__).parent
SCRIPT = HERE / "sample_wing.py"
OUTPUT = HERE / "sample_wing.vsp3"

def main():
    if OUTPUT.exists():
        OUTPUT.unlink()

    print("Running sample_wing.py via openvsp_runner...")
    t0 = time.monotonic()
    result = run(SCRIPT, cwd=HERE)
    elapsed = time.monotonic() - t0

    print(f"--- stdout ---\n{result.stdout}")
    if result.stderr:
        print(f"--- stderr ---\n{result.stderr}")
    print(f"Return code : {result.returncode}")
    print(f"Elapsed     : {elapsed:.1f}s")

    failures = []
    if result.returncode != 0:
        failures.append(f"Non-zero exit code: {result.returncode}")
    if not OUTPUT.exists() or OUTPUT.stat().st_size == 0:
        failures.append(f"Output file missing or empty: {OUTPUT}")
    if "OK" not in result.stdout:
        failures.append("stdout did not contain 'OK'")
    if elapsed > 60:
        failures.append(f"Wall time {elapsed:.1f}s exceeded 60s limit")

    if failures:
        print("\nFAIL")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"\nPASS  ({OUTPUT.stat().st_size} bytes, {elapsed:.1f}s)")

if __name__ == "__main__":
    main()
