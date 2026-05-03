"""
Test driver for the design_space_explorer agent.

Verifies that explore.py can parse the active generator and produce a ranked
candidate report without requiring OpenVSP.
"""

import json
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPLORE_PY = Path(__file__).resolve().parent.parent / "explore.py"
OUT_FILE = Path(__file__).resolve().parent / "test_design_space_report.json"


def main():
    if OUT_FILE.exists():
        OUT_FILE.unlink()

    t0 = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(EXPLORE_PY), "--out", str(OUT_FILE)],
        capture_output=True,
        text=True,
        cwd=str(EXPLORE_PY.parent),
    )
    elapsed = time.monotonic() - t0

    failures = []
    if result.returncode != 0:
        failures.append(f"Non-zero exit code: {result.returncode}")
    if not OUT_FILE.exists():
        failures.append("Report file was not created")

    report = None
    try:
        report = json.loads(result.stdout)
    except Exception as exc:
        failures.append(f"Could not parse JSON stdout: {exc}")

    if report:
        candidates = report.get("candidates", [])
        if len(candidates) < 4:
            failures.append(f"Expected at least 4 candidates, got {len(candidates)}")
        if not report.get("recommended_next"):
            failures.append("Missing recommended_next")
        for key in ("latest_model", "best_model", "best_compliant_model", "latest_is_best"):
            if key not in report:
                failures.append(f"Report missing {key}")
        for idx, candidate in enumerate(candidates):
            for key in ("name", "feature", "changes", "estimated_metrics", "constraint_violations"):
                if key not in candidate:
                    failures.append(f"Candidate {idx} missing {key}")

    if elapsed > 5:
        failures.append(f"Wall time {elapsed:.1f}s exceeded 5s limit")

    print(f"Return code : {result.returncode}")
    print(f"Elapsed     : {elapsed:.2f}s")
    if report:
        print(f"Recommended: {report.get('recommended_next')}")
        print(f"Candidates : {len(report.get('candidates', []))}")

    if failures:
        print("\nFAIL")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)

    print("\nPASS")


if __name__ == "__main__":
    main()
