"""
Smoke test for dynamic_stability/analyze.py.

Creates minimal alpha_sweep and inertia JSON fixtures and validates
that the analyzer produces eigenvalues, mode classifications, and
a finite stability cost.
"""

import json
import math
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
ANALYZER     = PROJECT_ROOT / "SIMULATION" / "AGENTS" / "dynamic_stability" / "analyze.py"
RESULTS_DIR  = PROJECT_ROOT / "SIMULATION" / "results"
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
AIRCRAFT_DIR.mkdir(parents=True, exist_ok=True)

# ── Fixture: alpha sweep (statically stable aircraft) ─────────────────────────
ALPHA_SWEEP = {
    "model": "MODEL_TEST_dynstab.vsp3",
    "analysis": "VSPAEROSweep_VLM",
    "mach": 0.15,
    "reference": {
        "mtow_kg": 218.0,
        "wing_area_m2": 4.214,
        "wing_span_m": 9.8,
        "wing_mac_m": 0.437,
        "x_cg_m": 1.82,
        "engine_power_w": 13423.0,
    },
    "polar": [
        {"alpha_deg": -4.0, "CL": -0.15, "CD": 0.012, "CM": 0.08, "LD": -12.5},
        {"alpha_deg": -2.0, "CL":  0.05, "CD": 0.010, "CM": 0.06, "LD":  5.0},
        {"alpha_deg":  0.0, "CL":  0.25, "CD": 0.012, "CM": 0.04, "LD": 20.8},
        {"alpha_deg":  2.0, "CL":  0.45, "CD": 0.015, "CM": 0.02, "LD": 30.0},
        {"alpha_deg":  4.0, "CL":  0.65, "CD": 0.021, "CM": -0.01,"LD": 31.0},
        {"alpha_deg":  6.0, "CL":  0.85, "CD": 0.031, "CM": -0.04,"LD": 27.4},
        {"alpha_deg":  8.0, "CL":  1.05, "CD": 0.046, "CM": -0.07,"LD": 22.8},
        {"alpha_deg": 10.0, "CL":  1.22, "CD": 0.065, "CM": -0.10,"LD": 18.8},
        {"alpha_deg": 12.0, "CL":  1.38, "CD": 0.090, "CM": -0.13,"LD": 15.3},
        {"alpha_deg": 14.0, "CL":  1.51, "CD": 0.120, "CM": -0.16,"LD": 12.6},
        {"alpha_deg": 16.0, "CL":  1.62, "CD": 0.158, "CM": -0.19,"LD": 10.3},
    ],
    "CL_alpha_per_deg": 0.0990,
    "CL_0": 0.25,
    "Cm_alpha_per_deg": -0.0150,
    "Cm_0": 0.04,
    "CL_max_vlm": 1.62,
    "vstall_est_ms": 20.4,
    "vstall_ok": True,
    "vcruise_75pct_ms": 50.0,
    "LD_cruise": 28.0,
    "longitudinal_stable": True,
}

# ── Fixture: inertia ──────────────────────────────────────────────────────────
INERTIA = {
    "model": "MODEL_TEST_dynstab.vsp3",
    "total_mass_kg": 218.0,
    "cg_x_m": 1.82,
    "cg_y_m": 0.0,
    "cg_z_m": -0.05,
    "Iyy_kgm2": 310.0,
    "Ixx_kgm2": 185.0,
    "Izz_kgm2": 480.0,
    "Ixz_kgm2": 0.0,
}

# ── Fixture: geometry companion (for Cmq and V_H) ─────────────────────────────
GEOM = {
    "wing_area_m2": 4.214,
    "wing_span_m": 9.8,
    "wing_mac_m": 0.437,
    "wing_taper_ratio": 0.654,
    "wing_sweep": 1.0,
    "wing_x_m": 1.80,
    "htail_area_m2": 0.432,
    "htail_mac_m": 0.270,
    "htail_x_m": 4.50,
    "vtail_area_m2": 0.210,
    "vtail_x_m": 4.30,
    "vtail_root_chord_m": 0.40,
    "tail_moment_arm_m": 2.64,
    "V_H": 0.48,
    "engine_bay_start_m": 0.30,
    "engine_bay_end_m": 1.10,
    "x_engine_m": 0.70,
    "x_cg_m": 1.82,
}

REQUIRED = ["stability_cost", "stability_status", "min_eigenvalue_dist",
            "longitudinal", "lateral", "trim", "derivatives", "inertia"]

def main():
    stem = "MODEL_TEST_dynstab"

    # Write fixtures
    alpha_file   = RESULTS_DIR / f"{stem}_alpha_sweep.json"
    inertia_file = RESULTS_DIR / f"{stem}_inertia.json"
    geom_file    = AIRCRAFT_DIR / f"{stem}.json"

    alpha_file.write_text(json.dumps(ALPHA_SWEEP, indent=2))
    inertia_file.write_text(json.dumps(INERTIA, indent=2))
    geom_file.write_text(json.dumps(GEOM, indent=2))

    # Run analyzer
    result = subprocess.run(
        [sys.executable, str(ANALYZER), str(alpha_file), str(inertia_file)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("FAIL: analyzer returned non-zero exit code")
        print(result.stderr[:500])
        sys.exit(1)

    stdout = result.stdout
    try:
        begin = stdout.index("BEGIN_JSON") + len("BEGIN_JSON")
        end   = stdout.index("END_JSON")
        report = json.loads(stdout[begin:end].strip())
    except (ValueError, json.JSONDecodeError) as e:
        print(f"FAIL: could not parse output JSON: {e}")
        print(stdout[:800])
        sys.exit(1)

    for field in REQUIRED:
        if field not in report:
            print(f"FAIL: missing field '{field}'")
            sys.exit(1)

    # Stability status should be "stable" for our fixture (Cm_alpha < 0)
    if report["stability_status"] != "stable":
        print(f"FAIL: expected stability_status='stable', got '{report['stability_status']}'")
        sys.exit(1)

    # Stability cost should be finite and > 0
    sc = report["stability_cost"]
    if not (0 < sc < 100):
        print(f"FAIL: stability_cost = {sc:.4f} not in (0, 100)")
        sys.exit(1)

    # Longitudinal modes should include a phugoid
    lon_modes = report["longitudinal"]["modes"]
    names = [m.get("name", "") for m in lon_modes]
    if "phugoid" not in names:
        print(f"FAIL: phugoid mode not identified; modes = {names}")
        sys.exit(1)

    # All longitudinal modes stable
    if not report["longitudinal"]["all_stable"]:
        print("FAIL: longitudinal modes reported as unstable for a stable fixture")
        sys.exit(1)

    # Output file exists
    out_file = RESULTS_DIR / f"{stem}_dynamic_stability.json"
    if not out_file.exists():
        print(f"FAIL: output file not written: {out_file}")
        sys.exit(1)

    print(f"PASS  stability_cost={sc:.4f}  modes={names}  "
          f"lon_stable={report['longitudinal']['all_stable']}")

    # Clean up fixtures
    for p in [alpha_file, inertia_file, geom_file]:
        p.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
