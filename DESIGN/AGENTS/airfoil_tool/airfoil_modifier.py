"""
Airfoil Modifier — applies a NACA 4-digit airfoil to the MainWing of an OpenVSP model.

MUST be run via the OpenVSP Python launcher (requires `import openvsp as vsp`):

    "C:\\Users\\asgin\\OneDrive\\Documents\\ENGINEERING\\AERO\\OpenVSP-3.49.0-win64\\openvsp-python.cmd" airfoil_modifier.py NACA2412
    "C:\\Users\\asgin\\OneDrive\\Documents\\ENGINEERING\\AERO\\OpenVSP-3.49.0-win64\\openvsp-python.cmd" airfoil_modifier.py NACA2412 <path_to_model.vsp3>

If no model path is given, the most-recently-modified .vsp3 in AIRCRAFT/ is used.

Output:
  - New model file: AIRCRAFT/MODEL_MM_DD_YYYY_XX.vsp3
  - Companion JSON: same stem with .json extension
  - Prints JSON summary wrapped in BEGIN_JSON / END_JSON sentinels to stdout
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import openvsp as vsp

# ── Paths ──────────────────────────────────────────────────────────────────────
# airfoil_modifier.py lives at DESIGN/AGENTS/airfoil_tool/airfoil_modifier.py
# project root is 3 levels up
_HERE = Path(__file__).resolve()
PROJECT_ROOT = _HERE.parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
AIRCRAFT_DIR.mkdir(exist_ok=True)


# ── Argument parsing ───────────────────────────────────────────────────────────
def usage():
    print("Usage: openvsp-python airfoil_modifier.py NACAXXXX [model_path]", file=sys.stderr)
    print("  NACAXXXX  — NACA 4-digit designation, e.g. NACA2412", file=sys.stderr)
    print("  model_path — optional path to source .vsp3 (default: latest in AIRCRAFT/)", file=sys.stderr)
    sys.exit(1)


if len(sys.argv) < 2:
    usage()

naca_arg = sys.argv[1].strip().upper()
if not naca_arg.startswith("NACA"):
    # Allow bare 4-digit form, e.g. "2412"
    naca_arg = "NACA" + naca_arg

# Validate: must be NACA followed by exactly 4 digits
m = re.fullmatch(r"NACA(\d{4})", naca_arg)
if m is None:
    print(f"[error] '{naca_arg}' is not a valid NACA 4-digit designation (e.g. NACA2412)", file=sys.stderr)
    sys.exit(1)

digits = m.group(1)          # e.g. "2412"
d1 = int(digits[0])          # max camber × 100  (e.g. 2 → 0.02)
d2 = int(digits[1])          # camber location × 10  (e.g. 4 → 0.4)
d34 = int(digits[2:])        # thickness × 100  (e.g. 12 → 0.12)

camber      = d1 / 100.0     # e.g. 0.02
camber_loc  = d2 / 10.0      # e.g. 0.40
thickness   = d34 / 100.0    # e.g. 0.12

# Special case: symmetric airfoils (d1==0) still need a non-zero camber_loc
# to avoid a divide-by-zero in some solver code; use 0.4 (standard).
if d1 == 0:
    camber_loc = 0.4

print(f"[airfoil_modifier] Applying {naca_arg}: "
      f"camber={camber}, camber_loc={camber_loc}, thickness={thickness}",
      file=sys.stderr)

# ── Source model ───────────────────────────────────────────────────────────────
if len(sys.argv) >= 3:
    src_path = Path(sys.argv[2]).resolve()
    if not src_path.exists():
        print(f"[error] Model file not found: {src_path}", file=sys.stderr)
        sys.exit(1)
else:
    candidates = sorted(AIRCRAFT_DIR.glob("*.vsp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        print(f"[error] No .vsp3 files found in {AIRCRAFT_DIR}", file=sys.stderr)
        sys.exit(1)
    src_path = candidates[0]
    print(f"[airfoil_modifier] Using latest model: {src_path}", file=sys.stderr)

# ── Load companion JSON (to carry forward all fields) ──────────────────────────
src_json_path = src_path.with_suffix(".json")
if src_json_path.exists():
    src_meta = json.loads(src_json_path.read_text())
else:
    src_meta = {}
    print(f"[warn] No companion JSON found at {src_json_path}; starting with empty metadata.", file=sys.stderr)

# ── Load model ─────────────────────────────────────────────────────────────────
print(f"[airfoil_modifier] Loading: {src_path}", file=sys.stderr)
vsp.ClearVSPModel()
vsp.ReadVSPFile(str(src_path))
vsp.Update()

# ── Find MainWing ──────────────────────────────────────────────────────────────
all_geoms = vsp.FindGeoms()
wing_id = ""
for gid in all_geoms:
    if vsp.GetGeomName(gid) == "MainWing":
        wing_id = gid
        break

if wing_id == "":
    print("[error] 'MainWing' geom not found in model.  Available geoms:", file=sys.stderr)
    for gid in all_geoms:
        print(f"  - {vsp.GetGeomName(gid)}", file=sys.stderr)
    sys.exit(1)

print(f"[airfoil_modifier] Found MainWing: {wing_id}", file=sys.stderr)

# ── Modify XSec shapes to NACA 4-series ────────────────────────────────────────
# WING geoms have (at least) one XSec surface at index 0.
surf = vsp.GetXSecSurf(wing_id, 0)
n_xsec = vsp.GetNumXSec(surf)
print(f"[airfoil_modifier] Wing XSec surface has {n_xsec} sections", file=sys.stderr)

def _set_xsec_parm(xs, parm_name, value, xsec_index):
    """
    Set a parameter on an XSec cross-section curve.

    NOTE: vsp.FindParm() and vsp.GetParm() do NOT work with XSec IDs — they
    require a geom ID or parm container ID.  The correct approach for XSec
    parameters is to scan vsp.GetXSecParmIDs(xs) and match by name + group.
    """
    parm_ids = vsp.GetXSecParmIDs(xs)
    for pid in parm_ids:
        if vsp.GetParmName(pid) == parm_name and vsp.GetParmGroupName(pid) == "XSecCurve":
            vsp.SetParmVal(pid, value)
            return True
    print(f"  [warn] XSec {xsec_index}: '{parm_name}' not found in XSecCurve — skipping",
          file=sys.stderr)
    return False


changed = 0
params_set = {}   # xsec_index -> {parm: actual_value}

for i in range(n_xsec):
    # Change the cross-section shape to NACA 4-series (XS_FOUR_SERIES)
    vsp.ChangeXSecShape(surf, i, vsp.XS_FOUR_SERIES)
    vsp.Update()

    xs = vsp.GetXSec(surf, i)

    # Set NACA 4-series parameters via XSec parm scan (FindParm does not
    # work for XSec curve parameters — must use GetXSecParmIDs).
    ok_camber  = _set_xsec_parm(xs, "Camber",     camber,     i)
    ok_loc     = _set_xsec_parm(xs, "CamberLoc",  camber_loc, i)
    ok_thick   = _set_xsec_parm(xs, "ThickChord", thickness,  i)

    vsp.Update()

    # Read back actual values (clamped by VSP's parm limits)
    actual = {}
    for pid in vsp.GetXSecParmIDs(xs):
        n = vsp.GetParmName(pid)
        g = vsp.GetParmGroupName(pid)
        if g == "XSecCurve" and n in ("Camber", "CamberLoc", "ThickChord"):
            actual[n] = round(vsp.GetParmVal(pid), 6)

    params_set[i] = actual
    changed += 1
    status = "ok" if (ok_camber and ok_loc and ok_thick) else "partial"
    print(f"  [{status}] XSec {i}: {naca_arg}  actual={actual}", file=sys.stderr)

print(f"[airfoil_modifier] Modified {changed}/{n_xsec} XSecs", file=sys.stderr)

# ── Save new model ─────────────────────────────────────────────────────────────
date_str = datetime.now().strftime("%m_%d_%Y")
existing = list(AIRCRAFT_DIR.glob(f"MODEL_{date_str}_*.vsp3"))
version  = len(existing) + 1
out_path = AIRCRAFT_DIR / f"MODEL_{date_str}_{version:02d}.vsp3"

vsp.WriteVSPFile(str(out_path), 0)
print(f"[airfoil_modifier] Saved new model: {out_path}", file=sys.stderr)

# ── Build companion JSON ───────────────────────────────────────────────────────
# Start from source metadata, then overwrite airfoil fields
out_meta = dict(src_meta)
out_meta["model_file"]           = str(out_path)
out_meta["source_model"]         = str(src_path)
out_meta["airfoil_designation"]  = naca_arg
out_meta["airfoil_camber"]       = camber
out_meta["airfoil_camber_loc"]   = camber_loc
out_meta["airfoil_thickness"]    = thickness
out_meta["xsecs_modified"]       = changed
out_meta["xsecs_params"]         = params_set

out_json_path = out_path.with_suffix(".json")
out_json_path.write_text(json.dumps(out_meta, indent=2))
print(f"[airfoil_modifier] Companion JSON: {out_json_path}", file=sys.stderr)

# ── Print sentinel-wrapped summary ────────────────────────────────────────────
summary = {
    "model_file":          str(out_path),
    "source_model":        str(src_path),
    "airfoil_designation": naca_arg,
    "airfoil_camber":      camber,
    "airfoil_camber_loc":  camber_loc,
    "airfoil_thickness":   thickness,
    "xsecs_modified":      changed,
    "xsecs_params":        params_set,
}

print("BEGIN_JSON")
print(json.dumps(summary, indent=2))
print("END_JSON")
