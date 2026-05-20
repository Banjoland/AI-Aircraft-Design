"""
Smoke test for weight_estimator/estimate.py.

Tests three scenarios:
  A) Default spec aircraft (aluminum, 18 hp gasoline2) → empty mass computed
  B) Same aircraft with CFRP → lighter than aluminum
  C) Same aircraft with fabric_tube → lightest option
  D) Higher-power gasoline4 engine → heavier engine group
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
ESTIMATOR    = PROJECT_ROOT / "DESIGN" / "AGENTS" / "weight_estimator" / "estimate.py"
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
AIRCRAFT_DIR.mkdir(parents=True, exist_ok=True)

# Representative geometry matching the default spec aircraft
GEOM = {
    "total_length_m":     5.0,
    "fuse_wetted_m2":     13.2,
    "fuse_max_height_m":  1.10,
    "fuse_max_width_m":   1.10,
    "wing_span_m":        9.8,
    "wing_area_m2":       4.2,
    "wing_taper_ratio":   0.654,
    "wing_sweep":         1.0,
    "wing_tc_root":       0.12,
    "htail_span_m":       1.6,
    "htail_root_chord_m": 0.30,
    "htail_tip_chord_m":  0.24,
    "vtail_height":       0.70,
    "vtail_root_chord":   0.40,
    "vtail_tip_chord":    0.20,
    "empty_mass_est_kg":  110.0,
}

STEM = "MODEL_TEST_weight"


def _run(material, engine, hp):
    gf = AIRCRAFT_DIR / f"{STEM}.json"
    gf.write_text(json.dumps(GEOM))
    r = subprocess.run(
        [sys.executable, str(ESTIMATOR), str(gf),
         "--material", material, "--engine", engine, "--hp", str(hp)],
        capture_output=True, text=True,
    )
    gf.unlink(missing_ok=True)
    if r.returncode != 0:
        return None, r.stderr
    # Read the output JSON
    out_path = ESTIMATOR.parent / f"{STEM}_weight.json"
    if not out_path.exists():
        return None, "output JSON not written"
    try:
        return json.loads(out_path.read_text()), ""
    except Exception as exc:
        return None, str(exc)


def _check(rep, label):
    required = ["components", "empty_mass_kg", "spec_ok", "fuel_capacity_kg"]
    for f in required:
        if f not in rep:
            print(f"FAIL {label}: missing field '{f}'")
            sys.exit(1)
    em = rep["empty_mass_kg"]
    if not (10.0 < em < 300.0):
        print(f"FAIL {label}: empty_mass={em:.1f} kg outside plausible range 10–300 kg")
        sys.exit(1)
    return em


def main():
    # A — Aluminum baseline
    rep_a, err = _run("aluminum", "gasoline2", 18)
    if rep_a is None:
        print(f"FAIL A: {err[:300]}"); sys.exit(1)
    em_a = _check(rep_a, "A")
    print(f"  Scenario A (aluminum,    gasoline2 18hp): empty={em_a:.1f} kg  "
          f"spec_ok={rep_a['spec_ok']}  fuel={rep_a['fuel_capacity_kg']:.1f} kg  OK")

    # B — CFRP: must be lighter than aluminum
    rep_b, err = _run("cfrp", "gasoline2", 18)
    if rep_b is None:
        print(f"FAIL B: {err[:300]}"); sys.exit(1)
    em_b = _check(rep_b, "B")
    if em_b >= em_a:
        print(f"FAIL B: CFRP ({em_b:.1f} kg) should be lighter than aluminum ({em_a:.1f} kg)")
        sys.exit(1)
    print(f"  Scenario B (cfrp,        gasoline2 18hp): empty={em_b:.1f} kg  "
          f"spec_ok={rep_b['spec_ok']}  fuel={rep_b['fuel_capacity_kg']:.1f} kg  OK")

    # C — Fabric/tube: lightest structural option
    rep_c, err = _run("fabric_tube", "gasoline2", 18)
    if rep_c is None:
        print(f"FAIL C: {err[:300]}"); sys.exit(1)
    em_c = _check(rep_c, "C")
    if em_c >= em_b:
        print(f"FAIL C: fabric_tube ({em_c:.1f} kg) should be lighter than cfrp ({em_b:.1f} kg)")
        sys.exit(1)
    print(f"  Scenario C (fabric_tube, gasoline2 18hp): empty={em_c:.1f} kg  "
          f"spec_ok={rep_c['spec_ok']}  fuel={rep_c['fuel_capacity_kg']:.1f} kg  OK")

    # D — Higher HP engine: engine group should be heavier than scenario A
    rep_d, err = _run("aluminum", "gasoline4", 36)
    if rep_d is None:
        print(f"FAIL D: {err[:300]}"); sys.exit(1)
    em_d = _check(rep_d, "D")
    eng_a = rep_a["components"]["engine"] + rep_a["components"]["engine_systems"]
    eng_d = rep_d["components"]["engine"] + rep_d["components"]["engine_systems"]
    if eng_d <= eng_a:
        print(f"FAIL D: 36 hp gasoline4 engine ({eng_d:.1f} kg) should be heavier than "
              f"18 hp gasoline2 ({eng_a:.1f} kg)")
        sys.exit(1)
    print(f"  Scenario D (aluminum,    gasoline4 36hp): empty={em_d:.1f} kg  "
          f"engine_group={eng_d:.1f} kg  OK")

    print("PASS  weight_estimator smoke test")


if __name__ == "__main__":
    main()
