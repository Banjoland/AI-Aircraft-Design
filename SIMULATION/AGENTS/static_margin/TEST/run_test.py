"""
Smoke test for static_margin/compute.py.

Tests a stable aircraft fixture and verifies SM, x_NP, and status fields.
"""

import json, subprocess, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPT       = PROJECT_ROOT / "SIMULATION" / "AGENTS" / "static_margin" / "compute.py"
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR  = PROJECT_ROOT / "SIMULATION" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
AIRCRAFT_DIR.mkdir(parents=True, exist_ok=True)

ALPHA = {
    "model": "MODEL_TEST_sm.vsp3",
    "reference": {
        "wing_area_m2": 4.214, "wing_span_m": 9.8,
        "wing_mac_m": 0.437, "x_cg_m": 1.82,
    },
    "CL_alpha_per_deg": 0.099,
    "Cm_alpha_per_deg": -0.015,
    "longitudinal_stable": True,
    "vcruise_75pct_ms": 50.0,
    "LD_cruise": 28.0,
}
GEOM = {
    "wing_mac_m": 0.437, "x_cg_m": 1.82, "wing_x_m": 1.8,
    "htail_x_m": 4.5, "htail_mac_m": 0.270,
    "wing_taper_ratio": 0.654, "wing_sweep": 1.0,
    "wing_span_m": 9.8, "total_length_m": 5.0,
    "V_H": 0.48, "tail_moment_arm_m": 2.64,
}

REQUIRED = ["derivatives", "geometry", "static_margin", "cg_limits", "recommendations"]

def main():
    stem = "MODEL_TEST_sm"
    af = RESULTS_DIR  / f"{stem}_alpha_sweep.json"
    gf = AIRCRAFT_DIR / f"{stem}.json"
    af.write_text(json.dumps(ALPHA))
    gf.write_text(json.dumps(GEOM))

    r = subprocess.run([sys.executable, str(SCRIPT), str(af), str(gf)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL: non-zero exit"); print(r.stderr[:300]); sys.exit(1)

    try:
        b = r.stdout.index("BEGIN_JSON") + len("BEGIN_JSON")
        e = r.stdout.index("END_JSON")
        rep = json.loads(r.stdout[b:e].strip())
    except Exception as exc:
        print(f"FAIL: parse error {exc}"); sys.exit(1)

    for f in REQUIRED:
        if f not in rep:
            print(f"FAIL: missing '{f}'"); sys.exit(1)

    SM = rep["static_margin"]["SM"]
    status = rep["static_margin"]["SM_status"]
    x_NP = rep["static_margin"]["x_NP_m"]

    # Expected SM = -(−0.015/0.099) ≈ 0.152
    expected_SM = 0.015 / 0.099
    if abs(SM - expected_SM) > 0.01:
        print(f"FAIL: SM={SM:.4f}, expected ≈{expected_SM:.4f}"); sys.exit(1)

    if status not in ("GOOD", "MARGINAL", "OVER_STABLE", "UNSTABLE"):
        print(f"FAIL: unexpected SM_status '{status}'"); sys.exit(1)

    if x_NP <= 1.82:
        print(f"FAIL: x_NP={x_NP:.3f} should be behind x_CG=1.82 for stable aircraft")
        sys.exit(1)

    print(f"PASS  SM={SM:.4f} ({SM*100:.1f}% MAC)  x_NP={x_NP:.3f} m  status={status}")

    for p in [af, gf]:
        p.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
