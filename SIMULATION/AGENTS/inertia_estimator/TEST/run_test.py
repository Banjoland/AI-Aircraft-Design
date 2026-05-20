"""
Smoke test for inertia_estimator/estimate.py.

Creates a minimal geometry JSON for a known test configuration,
runs the estimator, and validates the output fields and CG location.
"""

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
ESTIMATOR    = PROJECT_ROOT / "SIMULATION" / "AGENTS" / "inertia_estimator" / "estimate.py"
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR  = PROJECT_ROOT / "SIMULATION" / "results"

# ── Minimal geometry JSON (matches generate.py output schema) ──────────────────
TEST_GEOM = {
    "model_file":          str(AIRCRAFT_DIR / "MODEL_TEST_inertia.vsp3"),
    "total_length_m":      5.0,
    "wing_area_m2":        4.214,
    "wing_span_m":         9.8,
    "wing_mac_m":          0.437,
    "wing_x_m":            1.8,
    "htail_area_m2":       0.432,
    "htail_mac_m":         0.270,
    "htail_x_m":           4.5,
    "vtail_area_m2":       0.210,
    "vtail_x_m":           4.3,
    "vtail_root_chord_m":  0.40,
    "fuse_wetted_m2":      10.34,
    "wing_wetted_m2":      8.765,
    "x_engine_m":          0.70,
    "cockpit_x_m":         1.8,
    "empty_mass_est_kg":   170.5,
}

REQUIRED_OUTPUT_FIELDS = [
    "total_mass_kg", "cg_x_m", "cg_y_m", "cg_z_m",
    "Iyy_kgm2", "Ixx_kgm2", "Izz_kgm2", "components",
]

def main():
    # Write temp geometry JSON to AIRCRAFT dir
    AIRCRAFT_DIR.mkdir(parents=True, exist_ok=True)
    geom_path = AIRCRAFT_DIR / "MODEL_TEST_inertia.json"
    geom_path.write_text(json.dumps(TEST_GEOM, indent=2))

    # Run estimator
    result = subprocess.run(
        [sys.executable, str(ESTIMATOR), str(geom_path)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("FAIL: estimator returned non-zero exit code")
        print(result.stderr)
        sys.exit(1)

    # Parse output
    stdout = result.stdout
    try:
        begin = stdout.index("BEGIN_JSON") + len("BEGIN_JSON")
        end   = stdout.index("END_JSON")
        report = json.loads(stdout[begin:end].strip())
    except (ValueError, json.JSONDecodeError) as e:
        print(f"FAIL: could not parse output JSON: {e}")
        print(stdout[:500])
        sys.exit(1)

    # Validate fields
    for field in REQUIRED_OUTPUT_FIELDS:
        if field not in report:
            print(f"FAIL: missing field '{field}'")
            sys.exit(1)

    # Validate ranges
    mass = report["total_mass_kg"]
    if not (100 < mass < 300):
        print(f"FAIL: total_mass_kg = {mass:.1f} out of expected range 100–300 kg")
        sys.exit(1)

    cg_x = report["cg_x_m"]
    if not (0.5 < cg_x < 4.5):
        print(f"FAIL: cg_x_m = {cg_x:.3f} m out of expected range 0.5–4.5 m")
        sys.exit(1)

    Iyy = report["Iyy_kgm2"]
    if not (50 < Iyy < 1500):
        print(f"FAIL: Iyy_kgm2 = {Iyy:.1f} out of expected range 50–1500 kg·m²")
        sys.exit(1)

    Ixx = report["Ixx_kgm2"]
    if not (50 < Ixx < 2000):
        print(f"FAIL: Ixx_kgm2 = {Ixx:.1f} out of expected range 50–2000 kg·m²")
        sys.exit(1)

    out_file = RESULTS_DIR / "MODEL_TEST_inertia_inertia.json"
    if not out_file.exists():
        print(f"FAIL: output file not written to {out_file}")
        sys.exit(1)

    print(f"PASS  total_mass={mass:.1f} kg  cg_x={cg_x:.3f} m  "
          f"Iyy={Iyy:.1f}  Ixx={Ixx:.1f} kg·m²")
    geom_path.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
