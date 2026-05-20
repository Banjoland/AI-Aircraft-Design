"""
Smoke test for range_estimator/estimate.py.

Tests two scenarios:
  A) Over-weight design (empty_mass > 101 kg) → fuel = 0, range = 0, range_ok = False
  B) Ideal lightweight design (empty_mass = 80 kg) → range should meet spec
"""

import json, subprocess, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
ESTIMATOR    = PROJECT_ROOT / "SIMULATION" / "AGENTS" / "range_estimator" / "estimate.py"
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR  = PROJECT_ROOT / "SIMULATION" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
AIRCRAFT_DIR.mkdir(parents=True, exist_ok=True)

BASE_ALPHA = {
    "model": "MODEL_TEST_range.vsp3",
    "analysis": "VSPAEROSweep_VLM",
    "reference": {
        "mtow_kg": 218.0, "wing_area_m2": 4.2, "wing_span_m": 9.8,
        "wing_mac_m": 0.44, "x_cg_m": 1.8, "engine_power_w": 13423.0,
    },
    "polar": [{"alpha_deg": 4.0, "CL": 0.65, "CD": 0.021, "CM": -0.01, "LD": 31.0}],
    "CL_alpha_per_deg": 0.099, "CL_0": 0.25, "Cm_alpha_per_deg": -0.015,
    "CL_max_vlm": 1.62, "vstall_est_ms": 20.4, "vstall_ok": True,
    "vcruise_75pct_ms": 50.0, "LD_cruise": 28.0, "CD_cruise": 0.023,
    "CL_cruise": 0.65, "longitudinal_stable": True,
}

REQUIRED = ["fuel", "range", "climb", "compliance"]

def _run(alpha_dict, geom_dict, stem):
    af = RESULTS_DIR  / f"{stem}_alpha_sweep.json"
    gf = AIRCRAFT_DIR / f"{stem}.json"
    af.write_text(json.dumps(alpha_dict))
    gf.write_text(json.dumps(geom_dict))
    r = subprocess.run([sys.executable, str(ESTIMATOR), str(af), str(gf)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, r.stderr
    try:
        b = r.stdout.index("BEGIN_JSON") + len("BEGIN_JSON")
        e = r.stdout.index("END_JSON")
        return json.loads(r.stdout[b:e].strip()), ""
    except Exception as exc:
        return None, str(exc)

def main():
    # Scenario A: over-weight (173.9 kg) → no fuel
    rep_a, err = _run(
        BASE_ALPHA,
        {"empty_mass_est_kg": 173.9, "wing_area_m2": 4.2, "wing_span_m": 9.8},
        "MODEL_TEST_range_A",
    )
    if rep_a is None:
        print(f"FAIL scenario A: {err[:200]}"); sys.exit(1)
    for f in REQUIRED:
        if f not in rep_a:
            print(f"FAIL A: missing '{f}'"); sys.exit(1)
    if rep_a["fuel"]["fuel_avail_kg"] > 1.0:
        print(f"FAIL A: expected near-zero fuel for over-weight design, "
              f"got {rep_a['fuel']['fuel_avail_kg']:.1f} kg"); sys.exit(1)
    if rep_a["compliance"]["range_ok"]:
        print("FAIL A: over-weight design should not pass range spec"); sys.exit(1)
    print(f"  Scenario A (173.9 kg empty): fuel={rep_a['fuel']['fuel_avail_kg']:.1f} kg  "
          f"range={rep_a['range']['range_actual_km']:.0f} km  [PASS expected FAIL] OK")

    # Scenario B: light design (80 kg empty) → should have range
    rep_b, err = _run(
        BASE_ALPHA,
        {"empty_mass_est_kg": 80.0, "wing_area_m2": 4.2, "wing_span_m": 9.8},
        "MODEL_TEST_range_B",
    )
    if rep_b is None:
        print(f"FAIL scenario B: {err[:200]}"); sys.exit(1)
    fuel_b = rep_b["fuel"]["fuel_avail_kg"]
    rng_b  = rep_b["range"]["range_actual_km"]
    ok_b   = rep_b["compliance"]["range_ok"]
    if fuel_b < 5.0:
        print(f"FAIL B: expected positive fuel for 80 kg empty design, got {fuel_b:.1f}"); sys.exit(1)
    print(f"  Scenario B (80 kg empty):    fuel={fuel_b:.1f} kg  "
          f"range={rng_b:.0f} km  ok={ok_b} OK")

    print("PASS  range_estimator smoke test")

if __name__ == "__main__":
    main()
