"""
Smoke test for tail_sizing/size.py.

Tests two scenarios:
  A) Standard geometry: checks that output fields exist and SM is plausible
  B) Tail-forward CG (very small SM): should flag htail as under-sized
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPT       = PROJECT_ROOT / "DESIGN" / "AGENTS" / "tail_sizing" / "size.py"
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
AIRCRAFT_DIR.mkdir(parents=True, exist_ok=True)

BASE_GEOM = {
    "total_length_m":     5.0,
    "wing_span_m":        9.8,
    "wing_area_m2":       4.2,
    "wing_mac_m":         0.44,
    "wing_x_m":           1.80,
    "wing_taper_ratio":   0.654,
    "wing_sweep":         1.0,
    "htail_span_m":       1.6,
    "htail_root_chord_m": 0.30,
    "htail_tip_chord_m":  0.24,
    "htail_mac_m":        0.27,
    "htail_x_m":          4.50,
    "vtail_height":       0.70,
    "vtail_root_chord":   0.40,
    "vtail_tip_chord":    0.20,
    "vtail_x_m":          4.30,
    "x_cg_m":             1.85,
    "fuse_max_width_m":   1.10,
}

STEM = "MODEL_TEST_tail"


def _run(geom_dict):
    gf = AIRCRAFT_DIR / f"{STEM}.json"
    gf.write_text(json.dumps(geom_dict))
    r = subprocess.run([sys.executable, str(SCRIPT), str(gf)],
                       capture_output=True, text=True)
    gf.unlink(missing_ok=True)
    if r.returncode != 0:
        return None, r.stderr
    out = SCRIPT.parent / f"{STEM}_tail_size.json"
    if not out.exists():
        return None, "output JSON not written"
    try:
        return json.loads(out.read_text()), ""
    except Exception as exc:
        return None, str(exc)


def main():
    # A — standard geometry
    rep_a, err = _run(BASE_GEOM)
    if rep_a is None:
        print(f"FAIL A: {err[:300]}"); sys.exit(1)

    for section in ["htail", "vtail", "geometry"]:
        if section not in rep_a:
            print(f"FAIL A: missing section '{section}'"); sys.exit(1)

    SM_a = rep_a["htail"]["SM_current_frac"]
    if not (-0.50 < SM_a < 0.80):
        print(f"FAIL A: SM={SM_a:.3f} outside plausible range"); sys.exit(1)

    print(f"  Scenario A (nominal CG): SM={SM_a*100:.1f}%MAC  "
          f"S_h={rep_a['htail']['S_h_current_m2']:.3f}m²  "
          f"htail_ok={rep_a['htail']['htail_ok']}  OK")

    # B — CG very far forward (x_cg = 1.0m): SM will be large → tail over-sized
    geom_b = dict(BASE_GEOM)
    geom_b["x_cg_m"] = 1.0
    rep_b, err = _run(geom_b)
    if rep_b is None:
        print(f"FAIL B: {err[:300]}"); sys.exit(1)

    SM_b = rep_b["htail"]["SM_current_frac"]
    if SM_b <= SM_a:
        print(f"FAIL B: forward CG should give larger SM, got {SM_b:.3f} vs {SM_a:.3f}")
        sys.exit(1)
    print(f"  Scenario B (fwd CG 1.0m): SM={SM_b*100:.1f}%MAC  "
          f"htail_ok={rep_b['htail']['htail_ok']}  OK")

    # C — CG very far aft (x_cg = 2.5m): SM will be small/negative → tail under-sized
    geom_c = dict(BASE_GEOM)
    geom_c["x_cg_m"] = 2.5
    rep_c, err = _run(geom_c)
    if rep_c is None:
        print(f"FAIL C: {err[:300]}"); sys.exit(1)

    SM_c = rep_c["htail"]["SM_current_frac"]
    if SM_c >= SM_a:
        print(f"FAIL C: aft CG should give smaller SM, got {SM_c:.3f} vs {SM_a:.3f}")
        sys.exit(1)
    print(f"  Scenario C (aft CG 2.5m): SM={SM_c*100:.1f}%MAC  "
          f"htail_ok={rep_c['htail']['htail_ok']}  OK")

    # Verify monotonicity: SM_b > SM_a > SM_c
    if not (SM_b > SM_a > SM_c):
        print(f"FAIL monotonicity: SM_b={SM_b:.3f} SM_a={SM_a:.3f} SM_c={SM_c:.3f}")
        sys.exit(1)

    print("PASS  tail_sizing smoke test")


if __name__ == "__main__":
    main()
