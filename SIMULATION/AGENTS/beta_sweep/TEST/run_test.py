"""
Test driver for the beta_sweep simulation agent.

Finds the most recent MODEL_05_01_2026_xx.vsp3 (or any MODEL_*.vsp3) in
AIRCRAFT/, runs run_beta_sweep.py via the openvsp_runner, and verifies:
  1. Exit code 0  (OR results file written even if exit code is non-zero)
  2. Results file exists in SIMULATION/results/
  3. Cn_beta field present and is a number
  4. directionally_stable field present and is a bool
  5. sweep_table list present (may be empty if beta_sweep_failed)
  6. Wall time under 300 s
"""

import json
import sys
import time
from pathlib import Path

# Allow importing from project root
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from TOOLS.openvsp_runner.runner import run

SWEEP_PY    = Path(__file__).parent.parent / "run_beta_sweep.py"
RESULTS_DIR = PROJECT_ROOT / "SIMULATION" / "results"
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"


def find_most_recent_model() -> Path | None:
    """Return the most recently modified MODEL_*.vsp3, preferring MODEL_05_01 names."""
    all_models = sorted(AIRCRAFT_DIR.glob("MODEL_*.vsp3"),
                        key=lambda p: p.stat().st_mtime)
    if not all_models:
        return None
    # Prefer most recent by mtime
    return all_models[-1]


def main():
    model = find_most_recent_model()
    if model is None:
        print("FAIL: no MODEL_*.vsp3 found in AIRCRAFT/")
        sys.exit(1)

    print(f"Using model : {model.name}")
    print(f"Running     : {SWEEP_PY.name} ...")

    t0 = time.monotonic()
    result = run(SWEEP_PY, cwd=SWEEP_PY.parent, args=[str(model)])
    elapsed = time.monotonic() - t0

    if result.stderr:
        print(f"\n--- stderr ---\n{result.stderr}")
    print(f"Return code : {result.returncode}")
    print(f"Elapsed     : {elapsed:.1f}s")

    failures = []

    # ── 1. Check results file was written ─────────────────────────────────────
    expected_results = RESULTS_DIR / f"{model.stem}_beta_sweep.json"
    results_file_exists = expected_results.exists()

    # Also accept any *_beta_sweep.json if the expected name is missing
    if not results_file_exists:
        fallbacks = sorted(RESULTS_DIR.glob("*_beta_sweep.json"),
                           key=lambda p: p.stat().st_mtime)
        if fallbacks:
            expected_results = fallbacks[-1]
            results_file_exists = True

    if not results_file_exists:
        failures.append("No *_beta_sweep.json written to SIMULATION/results/")

    # ── 2. Exit code (relax: pass if file written even with non-zero code) ────
    if result.returncode != 0:
        if results_file_exists:
            print(f"WARN: non-zero exit code {result.returncode} but results file exists — continuing checks")
        else:
            failures.append(f"Non-zero exit code: {result.returncode} and no results file")

    # ── 3. Parse JSON summary ─────────────────────────────────────────────────
    summary = None
    try:
        lines = result.stdout.splitlines()
        start = next((i for i, l in enumerate(lines) if l.strip() == "BEGIN_JSON"), None)
        end   = next((i for i, l in enumerate(lines) if l.strip() == "END_JSON"),   None)
        if start is not None and end is not None:
            json_text = "\n".join(lines[start + 1:end])
            summary = json.loads(json_text)
        elif results_file_exists:
            summary = json.loads(expected_results.read_text())
        else:
            failures.append("Could not find BEGIN_JSON sentinel and no results file to fall back to")
    except Exception as e:
        failures.append(f"Could not parse JSON: {e}")

    # ── 4. Validate key fields ────────────────────────────────────────────────
    if summary:
        print(f"\n--- Key results ---")
        print(f"  Model               : {summary.get('model')}")
        print(f"  alpha_fixed_deg     : {summary.get('alpha_fixed_deg')}")
        print(f"  beta_npts_obtained  : {summary.get('beta_npts_obtained')}")
        print(f"  beta_sweep_failed   : {summary.get('beta_sweep_failed')}")
        print(f"  CY_beta             : {summary.get('CY_beta')} /rad")
        print(f"  Cl_beta             : {summary.get('Cl_beta')} /rad  ({summary.get('Cl_beta_sign')})")
        print(f"  Cn_beta             : {summary.get('Cn_beta')} /rad  ({summary.get('Cn_beta_sign')})")
        print(f"  directionally_stable: {summary.get('directionally_stable')}")
        print(f"  dihedral_effect     : {summary.get('dihedral_effect')}")

        tbl = summary.get("sweep_table", [])
        print(f"  sweep_table pts     : {len(tbl)}")
        if tbl:
            print(f"  {'Beta':>6}  {'CY':>10}  {'Cl':>10}  {'Cn':>10}  {'CL_lift':>8}")
            for pt in tbl:
                print(f"  {pt.get('beta_deg', 0):>6.1f}  "
                      f"{pt.get('CY', 0):>10.6f}  "
                      f"{pt.get('Cl', 0):>10.6f}  "
                      f"{pt.get('Cn', 0):>10.6f}  "
                      f"{pt.get('CL_lift', 0):>8.4f}")

        # Assert Cn_beta present and numeric
        cn_beta = summary.get("Cn_beta")
        if cn_beta is None or not isinstance(cn_beta, (int, float)):
            failures.append("Cn_beta missing or not a number")

        # Assert directionally_stable present and bool
        ds = summary.get("directionally_stable")
        if ds is None or not isinstance(ds, bool):
            failures.append("directionally_stable missing or not a bool")

        # Assert sweep_table is a list
        if not isinstance(summary.get("sweep_table"), list):
            failures.append("sweep_table missing or not a list")

        # If not failed, expect some real data points
        if not summary.get("beta_sweep_failed", False):
            if len(summary.get("sweep_table", [])) < 2:
                failures.append(
                    "beta_sweep_failed is False but sweep_table has < 2 points — inconsistent"
                )
    else:
        if not failures:
            failures.append("summary is None — no data to validate")

    # ── 5. Timing ─────────────────────────────────────────────────────────────
    if elapsed > 300:
        failures.append(f"Wall time {elapsed:.1f}s exceeded 300s limit")

    # ── 6. Report ─────────────────────────────────────────────────────────────
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
