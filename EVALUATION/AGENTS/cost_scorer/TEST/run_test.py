"""
Test driver for the cost_scorer evaluation agent.

Runs score.py on the most recent simulation results and verifies:
  1. Exit code 0
  2. JSON report parseable with all three cost components present
  3. total_cost = stall_cost + stability_cost + mass_cost - cruise_reward
  4. A score JSON written to EVALUATION/scores/
  5. Wall time under 10 s (no OpenVSP — pure Python)
"""

import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCORE_PY     = Path(__file__).parent.parent / "score.py"
SCORES_DIR   = PROJECT_ROOT / "EVALUATION" / "scores"

# score.py is plain Python (no OpenVSP), so we can run it directly
def run_score():
    t0  = time.monotonic()
    res = subprocess.run(
        [sys.executable, str(SCORE_PY)],
        capture_output=True, text=True,
        cwd=str(SCORE_PY.parent),
    )
    return res, time.monotonic() - t0


def main():
    sim_dir = PROJECT_ROOT / "SIMULATION" / "results"
    if not list(sim_dir.glob("*_alpha_sweep.json")):
        print("SKIP: no simulation results found — run alpha_sweep first")
        sys.exit(0)

    print("Running score.py ...")
    result, elapsed = run_score()

    if result.stderr:
        print(f"--- stderr ---\n{result.stderr}")
    print(f"Return code : {result.returncode}")
    print(f"Elapsed     : {elapsed:.1f}s")

    failures = []

    if result.returncode != 0:
        failures.append(f"Non-zero exit code: {result.returncode}")

    report = None
    try:
        report = json.loads(result.stdout)
    except Exception as e:
        failures.append(f"Could not parse JSON output: {e}\nstdout: {result.stdout[:300]}")

    if report:
        print(f"\n--- Score report ---")
        print(f"  Model          : {report.get('model')}")
        print(f"  Stall cost     : {report.get('stall_cost')}  ({report.get('stall_note')})")
        print(f"  Stability cost : {report.get('stability_cost')}  ({report.get('stability_note')})")
        print(f"  Cruise reward  : {report.get('cruise_reward')}  ({report.get('cruise_note')})")
        print(f"  Mass cost      : {report.get('mass_cost')}  ({report.get('mass_note')})")
        print(f"  TOTAL COST     : {report.get('total_cost')}")

        # Arithmetic check
        sc = report.get("stall_cost", 0)
        stab = report.get("stability_cost", 0)
        mass = report.get("mass_cost", 0)
        cr = report.get("cruise_reward", 0)
        tc = report.get("total_cost", 0)
        expected = round(sc + stab + mass - cr, 4)
        if abs(expected - tc) > 0.01:
            failures.append(
                f"total_cost arithmetic mismatch: {sc}+{stab}+{mass}-{cr}={expected} != {tc}"
            )

        for key in ("stall_cost", "stability_cost", "cruise_reward", "mass_cost", "total_cost"):
            if report.get(key) is None:
                failures.append(f"Missing field: {key}")

    score_files = list(SCORES_DIR.glob("*_score.json")) if SCORES_DIR.exists() else []
    if not score_files:
        failures.append("No *_score.json written to EVALUATION/scores/")

    if elapsed > 10:
        failures.append(f"Wall time {elapsed:.1f}s exceeded 10s limit")

    print()
    if failures:
        print("FAIL")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"PASS  ({elapsed:.1f}s)")


if __name__ == "__main__":
    main()
