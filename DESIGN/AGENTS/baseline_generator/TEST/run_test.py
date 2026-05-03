"""
Test driver for the baseline_generator agent.

Runs generate.py via openvsp_runner and verifies:
  1. Exit code 0
  2. A MODEL_*.vsp3 file appears in AIRCRAFT/
  3. The JSON summary has vstall_margin_ok=True and wingspan_ok=True
  4. Wall time under 60 s
"""

import json
import sys
import time
from pathlib import Path

# project root is 4 levels up from TEST/
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from TOOLS.openvsp_runner.runner import run

GENERATE_PY  = Path(__file__).parent.parent / "generate.py"
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"


def main():
    # Snapshot existing models before test
    before = set(AIRCRAFT_DIR.glob("MODEL_*.vsp3")) if AIRCRAFT_DIR.exists() else set()

    print(f"Running generate.py ...")
    t0     = time.monotonic()
    result = run(GENERATE_PY, cwd=GENERATE_PY.parent)
    elapsed = time.monotonic() - t0

    print(f"--- stdout ---\n{result.stdout}")
    if result.stderr:
        print(f"--- stderr ---\n{result.stderr}")
    print(f"Return code : {result.returncode}")
    print(f"Elapsed     : {elapsed:.1f}s")

    failures = []

    if result.returncode != 0:
        failures.append(f"Non-zero exit code: {result.returncode}")

    # Check a new model file appeared
    after   = set(AIRCRAFT_DIR.glob("MODEL_*.vsp3")) if AIRCRAFT_DIR.exists() else set()
    new_files = after - before
    if not new_files:
        failures.append("No MODEL_*.vsp3 file created in AIRCRAFT/")
    else:
        model_path = list(new_files)[0]
        print(f"Model file  : {model_path.name}  ({model_path.stat().st_size:,} bytes)")
        if model_path.stat().st_size == 0:
            failures.append("Model file is empty")

    # Parse and validate JSON summary
    try:
        summary = json.loads(result.stdout)
        if not summary.get("vstall_margin_ok"):
            failures.append(
                f"Stall speed {summary.get('vstall_est_ms')} m/s exceeds limit "
                f"{summary.get('vstall_limit_ms')} m/s"
            )
        if not summary.get("wingspan_ok"):
            failures.append(
                f"Wingspan {summary.get('wingspan_m')} m exceeds 15 m limit"
            )
    except Exception as e:
        failures.append(f"Could not parse JSON summary: {e}")

    if elapsed > 60:
        failures.append(f"Wall time {elapsed:.1f}s exceeded 60s limit")

    if failures:
        print("\nFAIL")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"\nPASS  ({elapsed:.1f}s)")


if __name__ == "__main__":
    main()
