"""
Smoke test for constraint_diagram/plot.py.

Tests two scenarios:
  A) Default 18 hp spec — should show engine deficit for cruise
  B) 80 hp engine       — should find a feasible design point
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPT       = PROJECT_ROOT / "DESIGN" / "AGENTS" / "constraint_diagram" / "plot.py"
OUT_JSON     = SCRIPT.parent / "constraint_diagram.json"


def _run(override_dict):
    import tempfile, os
    spec_file = Path(tempfile.mktemp(suffix=".json"))
    spec_file.write_text(json.dumps(override_dict))
    r = subprocess.run([sys.executable, str(SCRIPT), str(spec_file)],
                       capture_output=True, text=True)
    spec_file.unlink(missing_ok=True)
    if r.returncode != 0:
        return None, r.stderr
    if not OUT_JSON.exists():
        return None, "output JSON not written"
    try:
        return json.loads(OUT_JSON.read_text()), ""
    except Exception as exc:
        return None, str(exc)


def main():
    # A — 18 hp: expect engine deficit for cruise
    rep_a, err = _run({"P_engine_hp": 18.0, "MTOW_kg": 218.0})
    if rep_a is None:
        print(f"FAIL A: {err[:300]}"); sys.exit(1)

    req = ["stall_limit_WS_Nm2", "TW_avail_cruise", "TW_req_cruise_at_stall",
           "P_req_cruise_hp", "cruise_deficit_hp"]
    for f in req:
        if f not in rep_a:
            print(f"FAIL A: missing '{f}'"); sys.exit(1)

    stall_ws = rep_a["stall_limit_WS_Nm2"]
    if not (200 < stall_ws < 600):
        print(f"FAIL A: stall W/S={stall_ws:.1f} outside plausible range"); sys.exit(1)

    print(f"  Scenario A (18 hp): stall_WS={stall_ws:.0f} N/m²  "
          f"P_req_cruise={rep_a['P_req_cruise_hp']:.1f} hp  "
          f"deficit={rep_a['cruise_deficit_hp']:.1f} hp  OK")

    # B — 80 hp: should find feasible region
    rep_b, err = _run({"P_engine_hp": 80.0, "MTOW_kg": 218.0})
    if rep_b is None:
        print(f"FAIL B: {err[:300]}"); sys.exit(1)

    # With 80 hp the design should be feasible
    if rep_b["cruise_deficit_hp"] > 0:
        print(f"FAIL B: 80 hp should be sufficient for cruise, "
              f"but deficit={rep_b['cruise_deficit_hp']:.1f} hp"); sys.exit(1)

    print(f"  Scenario B (80 hp): feasible={rep_b['design_feasible']}  "
          f"P_req_cruise={rep_b['P_req_cruise_hp']:.1f} hp  deficit=0  OK")

    # C — stall W/S must decrease if CL_max increases
    rep_c, err = _run({"P_engine_hp": 18.0, "CL_max": 2.4, "MTOW_kg": 218.0})
    if rep_c is None:
        print(f"FAIL C: {err[:300]}"); sys.exit(1)
    if rep_c["stall_limit_WS_Nm2"] <= stall_ws:
        print(f"FAIL C: higher CL_max should raise stall W/S limit"); sys.exit(1)
    print(f"  Scenario C (CL_max=2.4): stall_WS={rep_c['stall_limit_WS_Nm2']:.0f} N/m²  "
          f"(was {stall_ws:.0f}) OK")

    print("PASS  constraint_diagram smoke test")


if __name__ == "__main__":
    main()
