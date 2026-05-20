"""
Smoke test for generate_report.py.

Creates minimal fixture JSON files (score + alpha + geom), runs the report
generator, and verifies that a non-empty .md file was written containing
expected section headers.
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT       = PROJECT_ROOT / "TOOLS" / "generate_report.py"
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR  = PROJECT_ROOT / "SIMULATION" / "results"
SCORES_DIR   = PROJECT_ROOT / "EVALUATION" / "scores"
REPORTS_DIR  = PROJECT_ROOT / "REPORTS"

for d in (AIRCRAFT_DIR, RESULTS_DIR, SCORES_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

STEM = "MODEL_TEST_report"

GEOM = {
    "total_length_m": 5.0, "wing_span_m": 9.8, "wing_area_m2": 4.2,
    "wing_mac_m": 0.44, "wing_taper_ratio": 0.654, "wing_sweep": 1.0,
    "htail_span_m": 1.6, "vtail_height": 0.70,
    "total_wetted_m2": 22.0, "fuse_wetted_m2": 13.0, "wing_wetted_m2": 8.7,
    "x_cg_m": 1.90, "empty_mass_est_kg": 104.5, "V_H": 0.48,
}

ALPHA = {
    "model": f"{STEM}.vsp3", "analysis": "VSPAEROSweep_VLM",
    "reference": {"mtow_kg": 218.0, "wing_area_m2": 4.2, "wing_span_m": 9.8,
                  "wing_mac_m": 0.44, "x_cg_m": 1.90, "engine_power_w": 13423.0},
    "polar": [{"alpha_deg": 4.0, "CL": 0.65, "CD": 0.021, "CM": -0.01, "LD": 31.0}],
    "CL_alpha_per_deg": 0.099, "CL_0": 0.25, "Cm_alpha_per_deg": -0.015,
    "CL_max_vlm": 1.62, "vstall_est_ms": 19.8, "vstall_ok": True,
    "vcruise_75pct_ms": 48.0, "LD_cruise": 26.0, "CD_cruise": 0.023,
    "CL_cruise": 0.62, "longitudinal_stable": True,
}

SCORE = {
    "model": f"{STEM}.vsp3",
    "total_cost": 75.3,
    "stall_cost": 0.0,
    "stability_cost": 12.5,
    "mass_cost": 63.8,
    "cruise_reward": 1.0,
    "stability_source": "cm_alpha_proxy",
    "inputs": {},
}


def main():
    # Write fixtures
    (AIRCRAFT_DIR / f"{STEM}.json").write_text(json.dumps(GEOM))
    (RESULTS_DIR  / f"{STEM}_alpha_sweep.json").write_text(json.dumps(ALPHA))
    (SCORES_DIR   / f"{STEM}_score.json").write_text(json.dumps(SCORE))

    r = subprocess.run(
        [sys.executable, str(SCRIPT), f"AIRCRAFT/{STEM}.json"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    if r.returncode != 0:
        print(f"FAIL: {r.stderr[:300]}"); sys.exit(1)

    out_path = REPORTS_DIR / f"{STEM}_report.md"
    if not out_path.exists():
        print("FAIL: report file not written"); sys.exit(1)

    content = out_path.read_text(encoding="utf-8")
    if len(content) < 500:
        print(f"FAIL: report too short ({len(content)} chars)"); sys.exit(1)

    required_sections = [
        "# Design Report",
        "## Score Summary",
        "## Geometry",
        "## Aerodynamics",
    ]
    for section in required_sections:
        if section not in content:
            print(f"FAIL: missing section '{section}'"); sys.exit(1)

    # Cleanup fixtures
    for p in [(AIRCRAFT_DIR / f"{STEM}.json"),
              (RESULTS_DIR  / f"{STEM}_alpha_sweep.json"),
              (SCORES_DIR   / f"{STEM}_score.json")]:
        p.unlink(missing_ok=True)

    print(f"  Report: {len(content)} chars  sections OK")
    print("PASS  generate_report smoke test")


if __name__ == "__main__":
    main()
