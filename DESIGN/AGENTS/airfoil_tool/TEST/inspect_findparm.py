"""Diagnostic: test FindParm vs GetParm with XSec ID."""
import openvsp as vsp

MODEL = r"C:\Users\asgin\OneDrive\Documents\PROJECTS\AI AIRPLANE DESIGN\AIRCRAFT DESIGN 2\AIRCRAFT\MODEL_05_01_2026_62.vsp3"

vsp.ClearVSPModel()
vsp.ReadVSPFile(MODEL)
vsp.Update()

all_geoms = vsp.FindGeoms()
wing_id = ""
for gid in all_geoms:
    if vsp.GetGeomName(gid) == "MainWing":
        wing_id = gid
        break

surf = vsp.GetXSecSurf(wing_id, 0)
vsp.ChangeXSecShape(surf, 0, vsp.XS_FOUR_SERIES)
vsp.Update()
xs = vsp.GetXSec(surf, 0)

print(f"wing_id = {wing_id!r}")
print(f"xs      = {xs!r}")

# Method 1: GetParm(container_id, parm_name, group_name)
print("\n--- vsp.GetParm(xs, name, group) ---")
for pname in ["Camber", "CamberLoc", "ThickChord"]:
    try:
        pid = vsp.GetParm(xs, pname, "XSecCurve")
        print(f"  {pname}: {pid!r}")
    except Exception as e:
        print(f"  {pname}: ERROR {e}")

# Method 2: FindParm with xs
print("\n--- vsp.FindParm(xs, name, group) ---")
for pname in ["Camber", "CamberLoc", "ThickChord"]:
    try:
        pid = vsp.FindParm(xs, pname, "XSecCurve")
        print(f"  {pname}: {pid!r}")
    except Exception as e:
        print(f"  {pname}: ERROR {e}")

# Method 3: FindParm with wing_id
print("\n--- vsp.FindParm(wing_id, name, group) ---")
for pname in ["Camber", "CamberLoc", "ThickChord"]:
    try:
        pid = vsp.FindParm(wing_id, pname, "XSecCurve")
        print(f"  {pname}: {pid!r}")
    except Exception as e:
        print(f"  {pname}: ERROR {e}")

# Method 4: scan GetXSecParmIDs and match by name
print("\n--- scan GetXSecParmIDs ---")
parm_ids = vsp.GetXSecParmIDs(xs)
for pid in parm_ids:
    name  = vsp.GetParmName(pid)
    group = vsp.GetParmGroupName(pid)
    if name in ("Camber", "CamberLoc", "ThickChord"):
        val = vsp.GetParmVal(pid)
        print(f"  {group}/{name} = {val}  (id={pid!r})")
        # try setting it
        vsp.SetParmVal(pid, 0.05)
        vsp.Update()
        val2 = vsp.GetParmVal(pid)
        print(f"  -> set to 0.05, now = {val2}")
