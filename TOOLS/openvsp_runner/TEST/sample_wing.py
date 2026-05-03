"""
Minimal OpenVSP smoke test: create a single wing and save it to a .vsp3 file.
Run via: openvsp-python sample_wing.py
"""

import openvsp as vsp
from pathlib import Path

out = Path(__file__).parent / "sample_wing.vsp3"

vsp.ClearVSPModel()
wing_id = vsp.AddGeom("WING")
vsp.SetGeomName(wing_id, "SmokeTestWing")

# 10 m span, 1.5 m root chord — arbitrary, just needs to be a valid geometry
vsp.SetParmVal(wing_id, "TotalSpan", "WingGeom", 10.0)
vsp.SetParmVal(wing_id, "Root_Chord", "XSec_1", 1.5)

vsp.Update()
vsp.WriteVSPFile(str(out), 0)

print(f"OK wrote {out}")
