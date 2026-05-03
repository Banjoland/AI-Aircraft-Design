"""
Pod-and-boom aircraft generator.

Creates a single-engine tractor configuration:
  Cockpit Pod + Tail Boom → Main Wing → Horizontal Tail → Vertical Tail → Prop Disk

Saves to AIRCRAFT/MODEL_MM_DD_YYYY_XX.vsp3 (project root).
Prints a JSON summary to stdout.

Run via openvsp-python:
    openvsp-python generate.py
Or via openvsp_runner:
    python -c "from TOOLS.openvsp_runner.runner import run; r=run('generate.py'); print(r.stdout)"
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import openvsp as vsp

# ── Paths ──────────────────────────────────────────────────────────────────────
# generate.py lives at DESIGN/AGENTS/baseline_generator/generate.py
# project root is 3 levels up
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
AIRCRAFT_DIR.mkdir(exist_ok=True)

# ── Spec-derived sizing (SPECIFICATION.md) ─────────────────────────────────────
MTOW_KG   = 218.0                  # max gross weight (SPECIFICATION.md)
MTOW_N    = MTOW_KG * 9.81
RHO_SL    = 1.225                  # kg/m³ sea-level ISA
VSTALL_LIM = 21.0                  # m/s  (SPECIFICATION.md)
CL_MAX    = 1.7                    # conservative clean-wing target

# Minimum wing area to hit stall limit at MTOW
S_MIN_M2 = 2.0 * MTOW_N / (RHO_SL * VSTALL_LIM**2 * CL_MAX)  # approx 4.65 m2

# Mass spec
SKIN_DENSITY   = 6.0               # kg/m²  (SPECIFICATION.md)
ENGINE_MASS_KG = 40.0              # kg
SYSTEMS_MASS_KG = 8.0              # kg  (minimal ultralight landing gear, avionics, controls)
STRUCTURE_FACTOR = 1.0             # skin density is treated as installed shell mass
EMPTY_MASS_SPEC  = 110.0           # kg  (spec limit)

# ── Baseline design parameters ─────────────────────────────────────────────────
P = {
    # Cockpit pod — spec-compliant width, shortened to engine bay + cockpit only
    "fuse_length":      1.6,    # m — pod only (engine bay + cockpit)
    "fuse_max_width":   1.10,   # m — spec-compliant
    "fuse_max_height":  0.75,   # m — reduced from 1.05 for lower wetted area
    "fuse_taper_width":  0.20,   # m — aft pod taper width (blends to boom)
    "fuse_taper_height": 0.20,   # m — aft pod taper height

    # Tail boom (new) — slim structural tube extending aft of pod
    "boom_x":           1.30,   # m — boom starts near aft of pod
    "boom_length":      1.90,   # m — extends to ~3.2 m from nose
    "boom_diameter":    0.12,   # m — slim structural tube

    # Main wing — very high AR for max VLM CL_max per unit wetted area
    "wing_span":        9.8,    # m  (< 15 m limit)
    "wing_root_chord":  0.52,   # m
    "wing_tip_chord":   0.34,   # m  (AR ≈ 22, sailplane-class)
    "wing_sweep":        1.0,   # deg
    "wing_dihedral":     3.0,   # deg
    "wing_twist":        0.0,   # deg washout (removed to recover CL_max)
    "wing_x":            0.65,  # m — moved forward on shorter pod
    "wing_z":            0.0,   # m

    # Horizontal tail — reduced area (~0.43 m²) for lower wetted area / mass
    "htail_span":        1.6,   # m
    "htail_root_chord":  0.30,  # m
    "htail_tip_chord":   0.24,  # m
    "htail_sweep":       8.0,   # deg
    "htail_x":           2.85,  # m — at end of boom (boom_x + boom_length ≈ 3.2 m)
    "htail_z":           0.0,   # m

    # Vertical tail
    "vtail_height":      0.70,  # m
    "vtail_root_chord":  0.40,  # m
    "vtail_tip_chord":   0.20,  # m
    "vtail_sweep":      20.0,   # deg
    "vtail_x":           2.65,  # m

    # Propeller thrust disk
    "prop_diameter":     1.10,  # m  (18 hp engine)
    "prop_x":           -0.05,  # m

    # Airfoil and incidence
    "wing_airfoil":    "NACA4412",  # NACA 4-digit designation (empty string = OpenVSP default)
    "wing_incidence_deg": 0.0,       # deg — wing incidence angle relative to fuselage
}

if len(sys.argv) > 1:
    override_path = Path(sys.argv[1]).resolve()
    overrides = json.loads(override_path.read_text())
    for k, v in overrides.items():
        if k not in P:
            continue
        P[k] = str(v) if isinstance(P[k], str) else float(v)

# ── Helpers ────────────────────────────────────────────────────────────────────
def _set(geom_id, parm, group, value):
    """SetParmVal wrapper; prints a warning instead of hard-failing on bad parm names."""
    parm_id = vsp.FindParm(geom_id, parm, group)
    if parm_id == "":
        print(f"  [warn] parm not found: {group}/{parm} on {vsp.GetGeomName(geom_id)}", file=sys.stderr)
        return
    vsp.SetParmVal(parm_id, value)


# ── Build model ────────────────────────────────────────────────────────────────
vsp.ClearVSPModel()

# ── Cockpit Pod ────────────────────────────────────────────────────────────────
fuse_id = vsp.AddGeom("FUSELAGE")
vsp.SetGeomName(fuse_id, "CockpitPod")
_set(fuse_id, "Length", "Design", P["fuse_length"])

# Widen the mid-section cross-sections to cockpit dimensions, tapering
# the last interior XSec down to boom-like dimensions for a smooth blend.
surf    = vsp.GetXSecSurf(fuse_id, 0)
n_xsec  = vsp.GetNumXSec(surf)
# OpenVSP FUSELAGE default has nose (i=0) and tail (i=n-1) at points.
# Adjust interior XSecs: full cabin width/height except the last which tapers.
for idx in range(1, n_xsec - 1):
    xs = vsp.GetXSec(surf, idx)
    if idx < n_xsec - 2:
        vsp.SetXSecWidth(xs,  P["fuse_max_width"])
        vsp.SetXSecHeight(xs, P["fuse_max_height"])
    else:
        vsp.SetXSecWidth(xs,  P["fuse_taper_width"])
        vsp.SetXSecHeight(xs, P["fuse_taper_height"])
vsp.Update()

# ── Tail Boom ──────────────────────────────────────────────────────────────────
boom_id = vsp.AddGeom("FUSELAGE", fuse_id)
vsp.SetGeomName(boom_id, "TailBoom")
_set(boom_id, "Length", "Design", P["boom_length"])
_set(boom_id, "X_Rel_Location", "XForm", P["boom_x"])

# Set all XSec widths/heights to boom diameter (circular cross-section)
boom_surf  = vsp.GetXSecSurf(boom_id, 0)
boom_nxsec = vsp.GetNumXSec(boom_surf)
for idx in range(boom_nxsec):
    bxs = vsp.GetXSec(boom_surf, idx)
    vsp.SetXSecWidth(bxs,  P["boom_diameter"])
    vsp.SetXSecHeight(bxs, P["boom_diameter"])
vsp.Update()

# ── Main Wing ──────────────────────────────────────────────────────────────────
wing_id = vsp.AddGeom("WING", fuse_id)
vsp.SetGeomName(wing_id, "MainWing")
_set(wing_id, "TotalSpan",  "WingGeom", P["wing_span"])
_set(wing_id, "Root_Chord", "XSec_1",   P["wing_root_chord"])
_set(wing_id, "Tip_Chord",  "XSec_1",   P["wing_tip_chord"])
_set(wing_id, "Sweep",      "XSec_1",   P["wing_sweep"])
_set(wing_id, "Dihedral",   "XSec_1",   P["wing_dihedral"])
_set(wing_id, "Twist",      "XSec_1",   P["wing_twist"])
_set(wing_id, "X_Rel_Location", "XForm", P["wing_x"])
_set(wing_id, "Z_Rel_Location", "XForm", P["wing_z"])
_set(wing_id, "Incidence",      "XSec_1", P["wing_incidence_deg"])
vsp.Update()

# Apply NACA 4-digit airfoil to all wing XSecs (if specified)
_airfoil = P.get("wing_airfoil", "")
if _airfoil and _airfoil.upper().startswith("NACA") and len(_airfoil) >= 8:
    _digits = _airfoil.upper().replace("NACA", "")
    if len(_digits) == 4:
        _cam      = float(_digits[0]) / 100.0
        _cam_loc  = float(_digits[1]) / 10.0 if _digits[1] != "0" else 0.4
        _thick    = float(_digits[2:]) / 100.0
        _wsrf     = vsp.GetXSecSurf(wing_id, 0)
        _nwxs     = vsp.GetNumXSec(_wsrf)
        for _wi in range(_nwxs):
            vsp.ChangeXSecShape(_wsrf, _wi, vsp.XS_FOUR_SERIES)
            _wxs = vsp.GetXSec(_wsrf, _wi)
            for _pid in vsp.GetXSecParmIDs(_wxs):
                _pn = vsp.GetParmName(_pid)
                if _pn == "Camber":
                    vsp.SetParmVal(_pid, _cam)
                elif _pn == "CamberLoc":
                    vsp.SetParmVal(_pid, _cam_loc)
                elif _pn == "ThickChord":
                    vsp.SetParmVal(_pid, _thick)
        vsp.Update()

# ── Horizontal Tail ────────────────────────────────────────────────────────────
htail_id = vsp.AddGeom("WING", fuse_id)
vsp.SetGeomName(htail_id, "HorizTail")
_set(htail_id, "TotalSpan",  "WingGeom", P["htail_span"])
_set(htail_id, "Root_Chord", "XSec_1",   P["htail_root_chord"])
_set(htail_id, "Tip_Chord",  "XSec_1",   P["htail_tip_chord"])
_set(htail_id, "Sweep",      "XSec_1",   P["htail_sweep"])
_set(htail_id, "X_Rel_Location", "XForm", P["htail_x"])
_set(htail_id, "Z_Rel_Location", "XForm", P["htail_z"])
vsp.Update()

# ── Vertical Tail ──────────────────────────────────────────────────────────────
vtail_id = vsp.AddGeom("WING", fuse_id)
vsp.SetGeomName(vtail_id, "VertTail")

# Remove XZ-plane symmetry so only one surface exists
sym_parm = vsp.FindParm(vtail_id, "Sym_Planar_Flag", "Sym")
if sym_parm != "":
    vsp.SetParmVal(sym_parm, 0)

_set(vtail_id, "TotalSpan",  "WingGeom", P["vtail_height"])
_set(vtail_id, "Root_Chord", "XSec_1",   P["vtail_root_chord"])
_set(vtail_id, "Tip_Chord",  "XSec_1",   P["vtail_tip_chord"])
_set(vtail_id, "Sweep",      "XSec_1",   P["vtail_sweep"])

# Rotate 90° around body X-axis → wing spans upward (Z direction)
_set(vtail_id, "X_Rel_Rotation", "XForm", 90.0)
_set(vtail_id, "X_Rel_Location", "XForm", P["vtail_x"])
_set(vtail_id, "Z_Rel_Location", "XForm", 0.0)
vsp.Update()

# ── Propeller Thrust Disk ──────────────────────────────────────────────────────
# Try PROP geom first; fall back to a very thin flat WING disc
prop_id = None
try:
    prop_id = vsp.AddGeom("PROP", fuse_id)
    vsp.SetGeomName(prop_id, "PropDisk")
    # Try group "Design" first, then "PropGeom"
    if vsp.FindParm(prop_id, "Diameter", "Design") != "":
        _set(prop_id, "Diameter", "Design", P["prop_diameter"])
    elif vsp.FindParm(prop_id, "Diameter", "PropGeom") != "":
        _set(prop_id, "Diameter", "PropGeom", P["prop_diameter"])
    _set(prop_id, "X_Rel_Location", "XForm", P["prop_x"])
    vsp.Update()
except Exception as exc:
    print(f"  [warn] PROP geom failed ({exc}); falling back to disc wing", file=sys.stderr)
    if prop_id:
        vsp.DeleteGeom(prop_id)
    prop_id = vsp.AddGeom("WING", fuse_id)
    vsp.SetGeomName(prop_id, "PropDisk")
    _set(prop_id, "TotalSpan",  "WingGeom", P["prop_diameter"])
    _set(prop_id, "Root_Chord", "XSec_1",   0.05)   # very thin chord → disc-like
    _set(prop_id, "Tip_Chord",  "XSec_1",   0.05)
    _set(prop_id, "Sweep",      "XSec_1",   0.0)
    _set(prop_id, "Dihedral",   "XSec_1",   0.0)
    _set(prop_id, "X_Rel_Location", "XForm", P["prop_x"])
    vsp.Update()

# ── Save model ─────────────────────────────────────────────────────────────────
# Filename format: MODEL_MM_DD_YYYY_XX where XX is version count for that date
date_str    = datetime.now().strftime("%m_%d_%Y")
existing    = list(AIRCRAFT_DIR.glob(f"MODEL_{date_str}_*.vsp3"))
version     = len(existing) + 1
out_path    = AIRCRAFT_DIR / f"MODEL_{date_str}_{version:02d}.vsp3"
vsp.WriteVSPFile(str(out_path), 0)

# ── Summary ────────────────────────────────────────────────────────────────────
wing_area   = P["wing_span"] * 0.5 * (P["wing_root_chord"] + P["wing_tip_chord"])
ar          = P["wing_span"] ** 2 / wing_area
wing_mac    = (2.0 / 3.0) * (
    (P["wing_root_chord"] ** 2 + P["wing_root_chord"] * P["wing_tip_chord"] + P["wing_tip_chord"] ** 2)
    / (P["wing_root_chord"] + P["wing_tip_chord"])
)
vstall_est  = (2.0 * MTOW_N / (RHO_SL * wing_area * CL_MAX)) ** 0.5
htail_area  = P["htail_span"] * 0.5 * (P["htail_root_chord"] + P["htail_tip_chord"])
vtail_area  = P["vtail_height"] * 0.5 * (P["vtail_root_chord"] + P["vtail_tip_chord"])

# ── Empty mass estimate ────────────────────────────────────────────────────────
# Wetted area approximations from planform geometry
wing_wetted  = 2.0 * wing_area  * 1.04   # both sides + thickness
htail_wetted = 2.0 * htail_area * 1.02
vtail_wetted = 2.0 * vtail_area * 1.02
import math
# Cockpit pod (trapezoidal average — tapered aft section blends to boom)
fuse_perim_fwd  = math.pi * 0.5 * (P["fuse_max_width"]    + P["fuse_max_height"])
fuse_perim_aft  = math.pi * 0.5 * (P["fuse_taper_width"]  + P["fuse_taper_height"])
fuse_wetted     = 0.5 * (fuse_perim_fwd + fuse_perim_aft) * P["fuse_length"]
# Tail boom (circular tube)
boom_perim   = math.pi * P["boom_diameter"]
boom_wetted  = boom_perim * P["boom_length"]
total_wetted = wing_wetted + htail_wetted + vtail_wetted + fuse_wetted + boom_wetted

skin_mass    = total_wetted * SKIN_DENSITY
empty_mass   = skin_mass * STRUCTURE_FACTOR + ENGINE_MASS_KG + SYSTEMS_MASS_KG

summary = {
    "model_file":           str(out_path),
    "configuration":        "pod_and_boom",
    "wing_area_m2":         round(wing_area, 2),
    "aspect_ratio":         round(ar, 2),
    "wing_mac_m":           round(wing_mac, 3),
    "htail_area_m2":        round(htail_area, 2),
    "vtail_area_m2":        round(vtail_area, 2),
    "prop_diameter_m":      P["prop_diameter"],
    "fuse_length_m":        P["fuse_length"],
    "fuse_max_width_m":     P["fuse_max_width"],
    "fuse_max_height_m":    P["fuse_max_height"],
    "fuse_taper_width_m":   P["fuse_taper_width"],
    "fuse_taper_height_m":  P["fuse_taper_height"],
    "boom_x_m":             P["boom_x"],
    "boom_length_m":        P["boom_length"],
    "boom_diameter_m":      P["boom_diameter"],
    "mtow_kg":              round(MTOW_KG, 1),
    "vstall_est_ms":        round(vstall_est, 2),
    "vstall_limit_ms":      VSTALL_LIM,
    "vstall_margin_ok":     vstall_est < VSTALL_LIM,
    "wingspan_m":           P["wing_span"],
    "wingspan_limit_m":     15.0,
    "wingspan_ok":          P["wing_span"] <= 15.0,
    "s_min_m2":             round(S_MIN_M2, 2),
    "total_wetted_area_m2": round(total_wetted, 2),
    "empty_mass_est_kg":    round(empty_mass, 1),
    "empty_mass_spec_kg":   EMPTY_MASS_SPEC,
    "empty_mass_ok":        empty_mass < EMPTY_MASS_SPEC,
    "wing_airfoil":         P["wing_airfoil"],
    "wing_incidence_deg":   P["wing_incidence_deg"],
}

# Write companion JSON alongside the .vsp3 so score.py can read mass
companion = out_path.with_suffix(".json")
companion.write_text(__import__("json").dumps(summary, indent=2))

print(json.dumps(summary, indent=2))
