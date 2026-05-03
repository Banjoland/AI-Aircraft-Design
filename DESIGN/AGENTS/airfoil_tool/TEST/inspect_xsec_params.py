"""
Diagnostic: inspect XSec parameter names after ChangeXSecShape(XS_FOUR_SERIES).
Run via: openvsp-python TEST/inspect_xsec_params.py
"""
import sys
from pathlib import Path

import openvsp as vsp

MODEL = Path(r"C:\Users\asgin\OneDrive\Documents\PROJECTS\AI AIRPLANE DESIGN\AIRCRAFT DESIGN 2\AIRCRAFT\MODEL_05_01_2026_62.vsp3")

vsp.ClearVSPModel()
vsp.ReadVSPFile(str(MODEL))
vsp.Update()

all_geoms = vsp.FindGeoms()
wing_id = ""
for gid in all_geoms:
    if vsp.GetGeomName(gid) == "MainWing":
        wing_id = gid
        break

print(f"wing_id: {wing_id}", flush=True)
surf = vsp.GetXSecSurf(wing_id, 0)
n = vsp.GetNumXSec(surf)
print(f"n_xsec: {n}", flush=True)

for i in range(min(n, 2)):
    vsp.ChangeXSecShape(surf, i, vsp.XS_FOUR_SERIES)
    vsp.Update()
    xs = vsp.GetXSec(surf, i)
    print(f"\nXSec {i} id: {xs}", flush=True)

    try:
        parm_ids = vsp.GetXSecParmIDs(xs)
        print(f"  parm count: {len(parm_ids)}", flush=True)
        for pid in parm_ids:
            name  = vsp.GetParmName(pid)
            group = vsp.GetParmGroupName(pid)
            val   = vsp.GetParmVal(pid)
            print(f"  {group}/{name} = {val}", flush=True)
    except Exception as e:
        print(f"  GetXSecParmIDs failed: {e}", flush=True)

    # Also try GetGeomParmIDs on the wing itself
    print(f"\n  Wing parms (XSecCurve group):", flush=True)
    try:
        wing_parms = vsp.GetGeomParmIDs(wing_id)
        for pid in wing_parms:
            group = vsp.GetParmGroupName(pid)
            name  = vsp.GetParmName(pid)
            if "Camber" in name or "Thick" in name or group == "XSecCurve":
                val = vsp.GetParmVal(pid)
                print(f"  {group}/{name} = {val}", flush=True)
    except Exception as e:
        print(f"  GetGeomParmIDs failed: {e}", flush=True)
