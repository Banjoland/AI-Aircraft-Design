"""
Diagnostic: lists all result keys available from VSPAEROSweep on the baseline model.
Checks both the outer rid and the first per-alpha sub-result rid_vec[0].
"""
import os
import sys
from pathlib import Path
import openvsp as vsp

PROJECT_ROOT = Path(__file__).resolve().parents[4]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RUNS_DIR = PROJECT_ROOT / "SIMULATION" / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

candidates = sorted(AIRCRAFT_DIR.glob("MODEL_*.vsp3"), key=lambda p: p.stat().st_mtime)
model_path = candidates[-1]
print(f"Model: {model_path.name}", file=sys.stderr)

vsp.ClearVSPModel()
vsp.ReadVSPFile(str(model_path))
vsp.Update()

wing_ids = vsp.FindGeomsWithName("MainWing")

_orig = os.getcwd()
os.chdir(str(RUNS_DIR))
try:
    vsp.SetAnalysisInputDefaults("VSPAEROComputeGeometry")
    vsp.SetIntAnalysisInput("VSPAEROComputeGeometry", "GeomSet",     [vsp.SET_NONE], 0)
    vsp.SetIntAnalysisInput("VSPAEROComputeGeometry", "ThinGeomSet", [vsp.SET_ALL],  0)
    vsp.SetIntAnalysisInput("VSPAEROComputeGeometry", "Symmetry",    [1],            0)
    vsp.ExecAnalysis("VSPAEROComputeGeometry")

    vsp.SetAnalysisInputDefaults("VSPAEROSweep")
    vsp.SetIntAnalysisInput("VSPAEROSweep", "GeomSet",     [vsp.SET_NONE], 0)
    vsp.SetIntAnalysisInput("VSPAEROSweep", "ThinGeomSet", [vsp.SET_ALL],  0)
    vsp.SetIntAnalysisInput("VSPAEROSweep", "RefFlag",     [1],            0)
    vsp.SetIntAnalysisInput("VSPAEROSweep", "Symmetry",    [1],            0)
    vsp.SetIntAnalysisInput("VSPAEROSweep", "WakeNumIter", [3],            0)
    if wing_ids:
        vsp.SetStringAnalysisInput("VSPAEROSweep", "WingID", wing_ids, 0)
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "AlphaStart", [-4.0], 0)
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "AlphaEnd",   [4.0],  0)
    vsp.SetIntAnalysisInput(   "VSPAEROSweep", "AlphaNpts",  [3],    0)  # small sweep for speed
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "MachStart",  [0.15], 0)
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "MachEnd",    [0.15], 0)
    vsp.SetIntAnalysisInput(   "VSPAEROSweep", "MachNpts",   [1],    0)
    rid = vsp.ExecAnalysis("VSPAEROSweep")
finally:
    os.chdir(_orig)

print("=== Outer rid result names ===")
outer_names = vsp.GetAllResultsNames()
print(f"  All result names in store: {outer_names}")

# List keys on the outer rid
print(f"\n  Outer rid data keys:")
for name in ["Alpha", "Beta", "Mach", "CLtot", "CDtot", "CDi", "CDo", "CS",
             "CMx", "CMy", "CMz", "CMl", "CMm", "CMn",
             "Cmy", "CMytot", "CMtot", "CMyb",
             "CL", "CD", "CM", "Cm",
             "CFx", "CFy", "CFz", "CMxyz"]:
    vals = vsp.GetDoubleResults(rid, name)
    if vals:
        print(f"    [{name}] = {vals[:5]}{'...' if len(vals)>5 else ''}")

rid_vec = vsp.GetStringResults(rid, "ResultsVec")
print(f"\n  rid_vec length: {len(rid_vec)}")

if rid_vec:
    print(f"\n=== rid_vec[0] (first alpha-point sub-result) keys ===")
    for name in ["Alpha", "Beta", "Mach", "CLtot", "CDtot", "CDi", "CDo", "CS",
                 "CMx", "CMy", "CMz", "CMl", "CMm", "CMn",
                 "Cmy", "CMytot", "CMtot", "CMyb",
                 "CL", "CD", "CM", "Cm",
                 "CFx", "CFy", "CFz"]:
        vals = vsp.GetDoubleResults(rid_vec[0], name)
        if vals:
            print(f"    [{name}] = {vals[:5]}{'...' if len(vals)>5 else ''}")

    # Also dump full PrintResults for rid and rid_vec[0]
    print("\n=== PrintResults(rid) ===")
    vsp.PrintResults(rid)
    print("\n=== PrintResults(rid_vec[0]) ===")
    vsp.PrintResults(rid_vec[0])
