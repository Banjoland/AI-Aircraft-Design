"""
Test driver for the alpha_sweep simulation agent.

Runs run_sweep.py via openvsp_runner on the most recent AIRCRAFT model and verifies:
  1. Exit code 0
  2. JSON summary parseable with a 'polar' list of at least 5 points
  3. Cm_alpha_per_deg is present (sign may vary but must be a number)
  4. vstall_est_ms is present
  5. vcruise_75pct_ms > vstall_est_ms (sanity)
  6. A results JSON file written to SIMULATION/results/
  7. Wall time under 300 s
"""

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from TOOLS.openvsp_runner.runner import run

SWEEP_PY    = Path(__file__).parent.parent / "run_sweep.py"
RESULTS_DIR = PROJECT_ROOT / "SIMULATION" / "results"


def main():
    print("Running run_sweep.py ...")
    t0     = time.monotonic()
    result = run(SWEEP_PY, cwd=SWEEP_PY.parent)
    elapsed = time.monotonic() - t0

    if result.stderr:
        print(f"--- stderr ---\n{result.stderr}")
    print(f"Return code : {result.returncode}")
    print(f"Elapsed     : {elapsed:.1f}s")

    failures = []

    if result.returncode != 0:
        failures.append(f"Non-zero exit code: {result.returncode}")

    # Extract JSON from between BEGIN_JSON / END_JSON sentinels in stdout.
    # (vspaero.exe also writes to stdout so we cannot parse the whole stream.)
    summary = None
    try:
        lines = result.stdout.splitlines()
        start = next((i for i, l in enumerate(lines) if l.strip() == "BEGIN_JSON"), None)
        end   = next((i for i, l in enumerate(lines) if l.strip() == "END_JSON"),   None)
        if start is not None and end is not None:
            json_text = "\n".join(lines[start+1:end])
            summary = json.loads(json_text)
        else:
            # Fallback: read from results file directly
            candidates = sorted(RESULTS_DIR.glob("*_alpha_sweep.json"),
                                 key=lambda p: p.stat().st_mtime)
            if candidates:
                summary = json.loads(candidates[-1].read_text())
            else:
                failures.append("Could not find BEGIN_JSON sentinel or results file")
    except Exception as e:
        failures.append(f"Could not parse JSON: {e}")

    if summary:
        print(f"\n--- Key results ---")
        print(f"  Model       : {summary.get('model')}")
        print(f"  Cm_alpha    : {summary.get('Cm_alpha_per_deg')} /deg  ({summary.get('Cm_alpha_sign')})")
        print(f"  V_stall est : {summary.get('vstall_est_ms')} m/s  (limit {summary.get('vstall_limit_ms')})")
        print(f"  V_cruise    : {summary.get('vcruise_75pct_ms')} m/s  (L/D={summary.get('LD_cruise')})")
        print(f"  Stable      : {summary.get('longitudinal_stable')}")
        polar = summary.get("polar", [])
        print(f"  Polar pts   : {len(polar)}")
        if polar:
            print(f"  {'Alpha':>6}  {'CL':>8}  {'CD':>8}  {'CM':>8}  {'L/D':>6}")
            for pt in polar:
                print(f"  {pt['alpha_deg']:>6.1f}  {pt['CL']:>8.4f}  {pt['CD']:>8.6f}  {pt['CM']:>8.4f}  {pt['LD']:>6.1f}")

    if summary:
        polar = summary.get("polar", [])
        if len(polar) < 5:
            failures.append(f"Polar has only {len(polar)} points (expected ≥ 5)")

        cm_alpha = summary.get("Cm_alpha_per_deg")
        if cm_alpha is None or not isinstance(cm_alpha, (int, float)):
            failures.append("Cm_alpha_per_deg missing or not a number")

        vstall = summary.get("vstall_est_ms")
        vcruise = summary.get("vcruise_75pct_ms")
        if vstall is None:
            failures.append("vstall_est_ms missing")
        if vcruise is None:
            failures.append("vcruise_75pct_ms missing")
        if vstall and vcruise and vcruise <= vstall:
            failures.append(f"vcruise ({vcruise}) ≤ vstall ({vstall}) — physically wrong")

    # Check results file written
    result_files = list(RESULTS_DIR.glob("*_alpha_sweep.json")) if RESULTS_DIR.exists() else []
    if not result_files:
        failures.append("No *_alpha_sweep.json written to SIMULATION/results/")

    if elapsed > 300:
        failures.append(f"Wall time {elapsed:.1f}s exceeded 300s limit")

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
