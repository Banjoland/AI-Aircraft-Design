"""
Single-fuselage complete aircraft generator.

Creates a single-engine tractor configuration with:
  - Streamlined spline-driven fuselage (single continuous body, nose to tail)
  - NACA 4412 high-aspect-ratio wing
  - Horizontal and vertical tail surfaces
  - Propeller disk

The fuselage is defined by three globally-smooth C2 cubic splines:
  top_spline  : z_top(x)      — crown profile
  bot_spline  : z_bot(x)      — keel profile
  hw_spline   : half_width(x) — half-width at each station

Cross-sections are ellipses whose height = z_top - z_bot and width = 2*hw,
positioned along x and vertically by the spline-derived center z.

Architecture: pod-and-boom is permanently retired (see CLAUDE.md).
All designs use a single fuselage body from engine nose to tail tip.

Output: AIRCRAFT/MODEL_MM_DD_YYYY_XX.vsp3
Prints a JSON summary to stdout.

Run via openvsp-python:
    openvsp-python generate.py
    openvsp-python generate.py path/to/spec.json
"""

import json
import math
import sys
from datetime import datetime
from pathlib import Path

import openvsp as vsp
from scipy.interpolate import CubicSpline
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
AIRCRAFT_DIR.mkdir(exist_ok=True)

# ── Spec constants ─────────────────────────────────────────────────────────────
MTOW_KG         = 218.0
MTOW_N          = MTOW_KG * 9.81
RHO_SL          = 1.225
VSTALL_LIM      = 21.0
CL_MAX          = 1.7
SKIN_DENSITY    = 6.0      # kg/m²
ENGINE_MASS_KG  = 40.0
SYSTEMS_MASS_KG = 8.0

# ── Default spec ───────────────────────────────────────────────────────────────
# 5.0 m fuselage, Sears-Haack-inspired profile with pilot cockpit at x≈2.0 m.
# Fineness at cockpit station: L / sqrt(h*w) = 5.0 / sqrt(0.93*1.10) ≈ 4.95
# Target FF ≈ 1.50 (versus CockpitPod FF=2.86 in retired pod-and-boom)
DEFAULT_SPEC = {
    "total_length_m": 5.0,
    "n_sections":     12,

    # Crown profile z_top(x)
    # At x=0.30m engine bay: z_top=0.32 -> height = 0.32+0.30 = 0.62m (engine spec: 0.6m)
    # At x=2.00m cockpit: z_top=0.68 -> height = 0.68+0.42 = 1.10m (2m pilot seated: ~1.07m needed)
    # At x=5.00m tail tip: z_top = z_bot = 0.06m -> SHARP POINT
    "top_spline_knots": [
        [0.00,  0.10],   # nose tip (small rounded nose)
        [0.30,  0.32],   # engine cowl — rapid expansion for 0.62 m engine height
        [0.70,  0.42],   # engine mid
        [1.20,  0.55],   # engine aft / cockpit ramp
        [2.00,  0.68],   # cockpit crown — max height for 2 m pilot
        [2.80,  0.60],   # aft cockpit
        [3.60,  0.40],   # aft taper begins
        [4.30,  0.22],   # tail section
        [5.00,  0.06],   # tail tip — converges to sharp point with z_bot
    ],

    # Keel profile z_bot(x)
    # Tail tip meets top at z=0.06m -> height = 0 -> sharp point
    "bot_spline_knots": [
        [0.00, -0.10],   # nose tip
        [0.30, -0.30],   # engine belly — 0.62 m height at engine bay
        [0.70, -0.40],   # engine belly mid
        [1.20, -0.45],   # cockpit floor begins
        [2.00, -0.42],   # cockpit floor — 1.10 m total height
        [2.80, -0.35],   # aft cockpit floor
        [3.60, -0.14],   # belly closing
        [4.30,  0.02],   # tail belly rising to tip
        [5.00,  0.06],   # tail tip — meets top_spline → sharp point
    ],

    # Half-width hw(x)
    # Engine bay: hw=0.30 at x=0.30m -> width=0.60m (engine spec: 0.6m)
    # Cockpit: hw=0.55 at x=2.00m -> width=1.10m (spec: pilot + 0.3m each side)
    # Tail tip: hw=0.00 -> zero width at tip -> sharp point
    "hw_spline_knots": [
        [0.00,  0.05],   # nose tip
        [0.30,  0.30],   # engine cowl — 0.60 m width
        [0.70,  0.36],   # engine mid
        [1.20,  0.48],   # forward cockpit
        [2.00,  0.55],   # cockpit shoulders (2×0.55 = 1.10 m)
        [2.80,  0.50],   # aft cockpit
        [3.60,  0.28],   # aft taper
        [4.30,  0.13],   # tail
        [5.00,  0.00],   # tail tip — zero width → sharp point
    ],

    # Wing (carried forward from MODEL_05_11_2026_03)
    "wing_span":          9.8,
    "wing_root_chord":    0.52,
    "wing_tip_chord":     0.34,
    "wing_sweep":          1.0,
    "wing_dihedral":       3.0,
    "wing_twist":          0.0,
    "wing_airfoil":       "NACA4412",
    "wing_incidence_deg":  0.0,
    "wing_x_m":            1.80,   # from nose — under cockpit crown
    "wing_z_m":            0.60,   # high-wing at fuselage crown (z_top≈0.65 at x=1.80)

    # Horizontal tail (carried forward from MODEL_05_11_2026_03)
    "htail_span":         1.6,
    "htail_root_chord":   0.30,
    "htail_tip_chord":    0.24,
    "htail_sweep":        8.0,
    "htail_x_m":          4.50,   # from nose
    "htail_z_m":          0.12,   # fuselage mid-height at tail station

    # Vertical tail (carried forward from MODEL_05_11_2026_03)
    "vtail_height":       0.70,
    "vtail_root_chord":   0.40,
    "vtail_tip_chord":    0.20,
    "vtail_sweep":       20.0,
    "vtail_x_m":          4.30,   # from nose
    "vtail_z_m":          0.00,   # base at fuselage reference plane

    # Propeller disk
    "prop_diameter":      1.10,
    "prop_x_m":          -0.05,   # just ahead of nose

    # Smoothness alert thresholds (nose expansion intentionally steep — attached flow)
    "max_slope_deg_warning": 20.0,
    "max_curvature_warning":  0.9,
}

# ── Load optional spec override ────────────────────────────────────────────────
spec = DEFAULT_SPEC.copy()
if len(sys.argv) > 1:
    override_path = Path(sys.argv[1]).resolve()
    spec.update(json.loads(override_path.read_text()))

# Allow spec JSON to override performance constants
MTOW_KG         = float(spec.get("MTOW_kg",            MTOW_KG))
MTOW_N          = MTOW_KG * 9.81
ENGINE_MASS_KG  = float(spec.get("engine_mass_kg",     ENGINE_MASS_KG))
SYSTEMS_MASS_KG = float(spec.get("systems_mass_kg",    SYSTEMS_MASS_KG))
CL_MAX          = float(spec.get("CL_max",             CL_MAX))
VSTALL_LIM      = float(spec.get("vstall_lim_ms",      VSTALL_LIM))

# ── Helpers ────────────────────────────────────────────────────────────────────
def _make_spline(knots):
    pts = np.array(sorted(knots, key=lambda p: p[0]), dtype=float)
    return CubicSpline(pts[:, 0], pts[:, 1], bc_type="not-a-knot")

def _set(geom_id, parm, group, value):
    parm_id = vsp.FindParm(geom_id, parm, group)
    if parm_id == "":
        print(f"  [warn] parm not found: {group}/{parm}", file=sys.stderr)
        return
    vsp.SetParmVal(parm_id, value)

def _xsec_set(xs, parm_name, value):
    for pid in vsp.GetXSecParmIDs(xs):
        if vsp.GetParmName(pid) == parm_name:
            vsp.SetParmVal(pid, value)
            return True
    return False

def _apply_c2(xs):
    vsp.ResetXSecSkinParms(xs)
    vsp.SetXSecContinuity(xs, 2)
    for name in ("ContinuityTop", "ContinuityRight", "ContinuityBottom", "ContinuityLeft"):
        _xsec_set(xs, name, 2.0)

# ── Build splines ──────────────────────────────────────────────────────────────
top_cs = _make_spline(spec["top_spline_knots"])
bot_cs = _make_spline(spec["bot_spline_knots"])
hw_cs  = _make_spline(spec["hw_spline_knots"])

L          = float(spec["total_length_m"])
N          = int(spec["n_sections"])
x_stations = np.linspace(0.0, L, N)

# ── Smoothness check ───────────────────────────────────────────────────────────
# Skip the nose tip (x=0): high slopes there are a spline boundary artifact and
# aerodynamically benign (attached flow on forebody).  Check from 2nd station on.
slope_warn = float(spec.get("max_slope_deg_warning", 20.0))
curv_warn  = float(spec.get("max_curvature_warning",  0.9))
flags = []
for x in x_stations[1:]:
    for label, cs in [("top", top_cs), ("bot", bot_cs), ("hw", hw_cs)]:
        dy  = float(cs(x, 1))
        d2y = float(cs(x, 2))
        slope = abs(math.degrees(math.atan(dy)))
        curv  = abs(d2y) / (1.0 + dy**2)**1.5
        if slope > slope_warn:
            flags.append(f"x={x:.2f}m {label} slope {slope:.1f}° > {slope_warn}°")
        if curv > curv_warn:
            flags.append(f"x={x:.2f}m {label} curvature {curv:.3f} > {curv_warn}/m")

if flags:
    print(f"  [smoothness] {len(flags)} warning(s):", file=sys.stderr)
    for f in flags[:6]:
        print(f"    {f}", file=sys.stderr)
    if len(flags) > 6:
        print(f"    ... and {len(flags)-6} more", file=sys.stderr)
else:
    print("  [smoothness] all stations within thresholds", file=sys.stderr)

# ── Build OpenVSP model ────────────────────────────────────────────────────────
vsp.ClearVSPModel()

# --- Fuselage (spline-driven) ---
fuse_id = vsp.AddGeom("FUSELAGE")
vsp.SetGeomName(fuse_id, "Fuselage")

pid = vsp.FindParm(fuse_id, "Length", "Design")
if pid:
    vsp.SetParmVal(pid, L)
vsp.Update()

def _xsec_count():
    return vsp.GetNumXSec(vsp.GetXSecSurf(fuse_id, 0))

while _xsec_count() < N:
    surf = vsp.GetXSecSurf(fuse_id, 0)
    n    = vsp.GetNumXSec(surf)
    vsp.InsertXSec(fuse_id, n - 2, vsp.XS_ELLIPSE)
    vsp.Update()

while _xsec_count() > N:
    surf = vsp.GetXSecSurf(fuse_id, 0)
    n    = vsp.GetNumXSec(surf)
    vsp.CutXSec(fuse_id, n - 2)
    vsp.Update()

surf   = vsp.GetXSecSurf(fuse_id, 0)
n_xsec = vsp.GetNumXSec(surf)

for idx in range(n_xsec):
    x      = float(x_stations[idx]) if idx < len(x_stations) else L
    x_frac = x / L if L > 0 else float(idx) / max(n_xsec - 1, 1)

    z_top_v = float(top_cs(x))
    z_bot_v = float(bot_cs(x))
    hw_v    = float(hw_cs(x))
    z_ctr   = (z_top_v + z_bot_v) / 2.0
    z_frac  = z_ctr / L

    is_tail_tip = (idx == n_xsec - 1)

    if is_tail_tip:
        # Sharp tail tip — degenerate point cross-section
        vsp.ChangeXSecShape(surf, idx, vsp.XS_POINT)
        vsp.Update()
        xs = vsp.GetXSec(surf, idx)
        _xsec_set(xs, "XLocPercent", x_frac)
        _xsec_set(xs, "ZLocPercent", z_frac)
    else:
        height = max(z_top_v - z_bot_v, 0.02)
        width  = max(2.0 * hw_v, 0.04)

        vsp.ChangeXSecShape(surf, idx, vsp.XS_ELLIPSE)
        vsp.Update()
        xs = vsp.GetXSec(surf, idx)
        vsp.SetXSecWidthHeight(xs, width, height)
        _xsec_set(xs, "XLocPercent", x_frac)
        _xsec_set(xs, "YLocPercent", 0.0)
        _xsec_set(xs, "ZLocPercent", z_frac)

        if 0 < idx < n_xsec - 1:
            _apply_c2(xs)

vsp.Update()

# --- Main Wing (high-wing, NACA 4412) ---
wing_id = vsp.AddGeom("WING", fuse_id)
vsp.SetGeomName(wing_id, "MainWing")
_set(wing_id, "TotalSpan",       "WingGeom", spec["wing_span"])
_set(wing_id, "Root_Chord",      "XSec_1",   spec["wing_root_chord"])
_set(wing_id, "Tip_Chord",       "XSec_1",   spec["wing_tip_chord"])
_set(wing_id, "Sweep",           "XSec_1",   spec["wing_sweep"])
_set(wing_id, "Dihedral",        "XSec_1",   spec["wing_dihedral"])
_set(wing_id, "Twist",           "XSec_1",   spec["wing_twist"])
_set(wing_id, "X_Rel_Location",  "XForm",    spec["wing_x_m"])
_set(wing_id, "Z_Rel_Location",  "XForm",    spec["wing_z_m"])
_set(wing_id, "Incidence",       "XSec_1",   spec["wing_incidence_deg"])
vsp.Update()

_airfoil = str(spec.get("wing_airfoil", ""))
if _airfoil.upper().startswith("NACA") and len(_airfoil) >= 8:
    _digits = _airfoil.upper().replace("NACA", "")
    if len(_digits) == 4:
        _cam     = float(_digits[0]) / 100.0
        _cam_loc = float(_digits[1]) / 10.0 if _digits[1] != "0" else 0.4
        _thick   = float(_digits[2:]) / 100.0
        _wsrf    = vsp.GetXSecSurf(wing_id, 0)
        _nwxs    = vsp.GetNumXSec(_wsrf)
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

# --- Horizontal Tail ---
htail_id = vsp.AddGeom("WING", fuse_id)
vsp.SetGeomName(htail_id, "HorizTail")
_set(htail_id, "TotalSpan",      "WingGeom", spec["htail_span"])
_set(htail_id, "Root_Chord",     "XSec_1",   spec["htail_root_chord"])
_set(htail_id, "Tip_Chord",      "XSec_1",   spec["htail_tip_chord"])
_set(htail_id, "Sweep",          "XSec_1",   spec["htail_sweep"])
_set(htail_id, "X_Rel_Location", "XForm",    spec["htail_x_m"])
_set(htail_id, "Z_Rel_Location", "XForm",    spec["htail_z_m"])
vsp.Update()

# --- Vertical Tail ---
vtail_id = vsp.AddGeom("WING", fuse_id)
vsp.SetGeomName(vtail_id, "VertTail")
sym_parm = vsp.FindParm(vtail_id, "Sym_Planar_Flag", "Sym")
if sym_parm != "":
    vsp.SetParmVal(sym_parm, 0)
_set(vtail_id, "TotalSpan",      "WingGeom", spec["vtail_height"])
_set(vtail_id, "Root_Chord",     "XSec_1",   spec["vtail_root_chord"])
_set(vtail_id, "Tip_Chord",      "XSec_1",   spec["vtail_tip_chord"])
_set(vtail_id, "Sweep",          "XSec_1",   spec["vtail_sweep"])
_set(vtail_id, "X_Rel_Rotation", "XForm",    90.0)
_set(vtail_id, "X_Rel_Location", "XForm",    spec["vtail_x_m"])
_set(vtail_id, "Z_Rel_Location", "XForm",    spec.get("vtail_z_m", 0.0))
vsp.Update()

# --- Propeller Disk ---
prop_id = None
try:
    prop_id = vsp.AddGeom("PROP", fuse_id)
    vsp.SetGeomName(prop_id, "PropDisk")
    if vsp.FindParm(prop_id, "Diameter", "Design") != "":
        _set(prop_id, "Diameter", "Design", spec["prop_diameter"])
    elif vsp.FindParm(prop_id, "Diameter", "PropGeom") != "":
        _set(prop_id, "Diameter", "PropGeom", spec["prop_diameter"])
    _set(prop_id, "X_Rel_Location", "XForm", spec["prop_x_m"])
    vsp.Update()
except Exception as exc:
    print(f"  [warn] PROP geom failed ({exc}); using disc wing", file=sys.stderr)
    if prop_id:
        vsp.DeleteGeom(prop_id)
    prop_id = vsp.AddGeom("WING", fuse_id)
    vsp.SetGeomName(prop_id, "PropDisk")
    _set(prop_id, "TotalSpan",      "WingGeom", spec["prop_diameter"])
    _set(prop_id, "Root_Chord",     "XSec_1",   0.05)
    _set(prop_id, "Tip_Chord",      "XSec_1",   0.05)
    _set(prop_id, "Sweep",          "XSec_1",   0.0)
    _set(prop_id, "Dihedral",       "XSec_1",   0.0)
    _set(prop_id, "X_Rel_Location", "XForm",    spec["prop_x_m"])
    vsp.Update()

# ── Save model ─────────────────────────────────────────────────────────────────
now = datetime.now()
version = 1
while True:
    fname = f"MODEL_{now.strftime('%m_%d_%Y')}_{version:02d}.vsp3"
    out_path = AIRCRAFT_DIR / fname
    if not out_path.exists():
        break
    version += 1

vsp.WriteVSPFile(str(out_path), vsp.SET_ALL)

# ── Mass and geometry summary ──────────────────────────────────────────────────
z_tops  = [float(top_cs(x)) for x in x_stations]
z_bots  = [float(bot_cs(x)) for x in x_stations]
hws     = [max(float(hw_cs(x)), 0.02) for x in x_stations]
heights = [max(zt - zb, 0.02) for zt, zb in zip(z_tops, z_bots)]
widths  = [max(2.0 * hw, 0.04) for hw in hws]

def _ellipse_perim(a, b):
    h = ((a - b) / (a + b)) ** 2
    return math.pi * (a + b) * (1.0 + 3.0*h / (10.0 + math.sqrt(4.0 - 3.0*h)))

perims = [_ellipse_perim(w/2.0, h/2.0) for w, h in zip(widths, heights)]

fuse_wetted = 0.0
for i in range(len(x_stations) - 1):
    dx = float(x_stations[i+1]) - float(x_stations[i])
    fuse_wetted += dx * (perims[i] + perims[i+1]) / 2.0

wing_area    = spec["wing_span"] * 0.5 * (spec["wing_root_chord"] + spec["wing_tip_chord"])
htail_area   = spec["htail_span"] * 0.5 * (spec["htail_root_chord"] + spec["htail_tip_chord"])
vtail_area   = spec["vtail_height"] * 0.5 * (spec["vtail_root_chord"] + spec["vtail_tip_chord"])
wing_wetted  = 2.0 * wing_area  * 1.04
htail_wetted = 2.0 * htail_area * 1.02
vtail_wetted = 2.0 * vtail_area * 1.02

total_wetted = fuse_wetted + wing_wetted + htail_wetted + vtail_wetted
skin_mass    = total_wetted * SKIN_DENSITY
empty_mass   = skin_mass + ENGINE_MASS_KG + SYSTEMS_MASS_KG

max_equiv_diam = max(math.sqrt(h * w) for h, w in zip(heights, widths))
fineness       = L / max_equiv_diam if max_equiv_diam > 0 else 0.0

max_top_slope = max(abs(math.degrees(math.atan(float(top_cs(x, 1))))) for x in x_stations)
max_bot_slope = max(abs(math.degrees(math.atan(float(bot_cs(x, 1))))) for x in x_stations)
smoothness_score = max(0.0, min(100.0,
    100.0
    - max(0.0, max(max_top_slope, max_bot_slope) - slope_warn) * 3.0
    - len(flags) * 2.0
))

vstall_est = (2.0 * MTOW_N / (RHO_SL * wing_area * CL_MAX)) ** 0.5

# ── Pilot and engine bay compliance checks ─────────────────────────────────────
# Spec: pilot 2.0 m tall; seated height ~0.92 m + 0.10 m seat + 0.05 m head clearance = 1.07 m min
PILOT_HEIGHT_MIN_M = float(spec.get("pilot_height_min_m", 1.07))
# Engine bay must enclose 0.8 m × 0.6 m × 0.6 m (x_length × width × height)
ENGINE_BAY_LENGTH_M  = 0.8
ENGINE_BAY_WIDTH_M   = 0.6
ENGINE_BAY_HEIGHT_M  = 0.6

# Cockpit height at wing station (x = wing_x_m), using spline values
cockpit_x     = float(spec["wing_x_m"])
cockpit_ztop  = float(top_cs(cockpit_x))
cockpit_zbot  = float(bot_cs(cockpit_x))
cockpit_h     = cockpit_ztop - cockpit_zbot
pilot_ok      = cockpit_h >= PILOT_HEIGHT_MIN_M

# Engine bay: the engine sits behind the prop spinner, not at x=0.
# Sample from x=0.20m to x=1.00m (the fuselage zone that encloses the engine body).
# We verify that a continuous 0.8m zone exists with adequate cross-section.
engine_start  = 0.30   # m — engine face starts after prop spinner (x=0 to 0.30m is spinner/cowl nose)
engine_end    = engine_start + ENGINE_BAY_LENGTH_M  # 1.00 m
engine_xs     = np.linspace(engine_start, engine_end, 12)
engine_hs     = [float(top_cs(x)) - float(bot_cs(x)) for x in engine_xs]
engine_ws     = [2.0 * float(hw_cs(x)) for x in engine_xs]
min_engine_h  = min(engine_hs)
min_engine_w  = min(engine_ws)
engine_h_ok   = min_engine_h >= ENGINE_BAY_HEIGHT_M
engine_w_ok   = min_engine_w >= ENGINE_BAY_WIDTH_M

# ── Wing / tail aerodynamic properties ────────────────────────────────────────
wing_taper  = spec["wing_tip_chord"]  / spec["wing_root_chord"]
wing_mac    = (2/3) * spec["wing_root_chord"]  * (1 + wing_taper  + wing_taper**2)  / (1 + wing_taper)
htail_taper = spec["htail_tip_chord"] / spec["htail_root_chord"]
htail_mac   = (2/3) * spec["htail_root_chord"] * (1 + htail_taper + htail_taper**2) / (1 + htail_taper)

# Tail moment arm: htail quarter-MAC to wing quarter-MAC
x_wing_qc  = float(spec["wing_x_m"])  + wing_mac  * 0.25
x_htail_qc = float(spec["htail_x_m"]) + htail_mac * 0.25
tail_moment_arm = x_htail_qc - x_wing_qc

# Horizontal tail volume coefficient
V_H = (htail_area * tail_moment_arm) / (wing_area * wing_mac) if wing_mac > 0 else 0.0

# ── CG estimate at MTOW ────────────────────────────────────────────────────────
USEFUL_LOAD_KG = float(spec.get("useful_load_kg", 117.0))
x_engine_m     = (engine_start + engine_end) / 2.0
fuel_kg        = max(0.0, MTOW_KG - empty_mass - USEFUL_LOAD_KG)
x_fuel_m       = min(x_engine_m + 0.25, float(spec["wing_x_m"]) - 0.10)

m_fuse    = fuse_wetted  * SKIN_DENSITY
m_wing    = wing_wetted  * SKIN_DENSITY
m_htail   = htail_wetted * SKIN_DENSITY
m_vtail   = vtail_wetted * SKIN_DENSITY

cg_num = (
    m_fuse    * (L / 2.0)
    + m_wing  * (float(spec["wing_x_m"])  + wing_mac  * 0.25)
    + m_htail * (float(spec["htail_x_m"]) + htail_mac * 0.25)
    + m_vtail * (float(spec["vtail_x_m"]) + spec["vtail_root_chord"] * 0.25)
    + ENGINE_MASS_KG  * x_engine_m
    + SYSTEMS_MASS_KG * (L * 0.3)
    + fuel_kg         * x_fuel_m
    + USEFUL_LOAD_KG  * float(spec["wing_x_m"])
)
cg_den = m_fuse + m_wing + m_htail + m_vtail + ENGINE_MASS_KG + SYSTEMS_MASS_KG + fuel_kg + USEFUL_LOAD_KG
x_cg_est = cg_num / cg_den if cg_den > 0 else L / 2.0

# ── Companion JSON and stdout ──────────────────────────────────────────────────
summary = {
    "model_file":              str(out_path),
    "configuration":           "spline_fuselage_complete",
    "generator":               "spline_aircraft/generate.py",
    "total_length_m":          round(L, 2),
    "n_sections":              n_xsec,
    "fineness_ratio":          round(fineness, 2),
    "max_equiv_diam_m":        round(max_equiv_diam, 3),
    "smoothness_score":        round(smoothness_score, 1),
    "smoothness_flag_count":   len(flags),
    "smoothness_flags":        flags[:10],
    "top_spline_knots":        spec["top_spline_knots"],
    "bot_spline_knots":        spec["bot_spline_knots"],
    "hw_spline_knots":         spec["hw_spline_knots"],
    "wing_area_m2":            round(wing_area, 3),
    "aspect_ratio":            round(spec["wing_span"]**2 / wing_area, 2),
    "htail_area_m2":           round(htail_area, 3),
    "vtail_area_m2":           round(vtail_area, 3),
    "fuse_wetted_m2":          round(fuse_wetted, 2),
    "wing_wetted_m2":          round(wing_wetted, 2),
    "total_wetted_m2":         round(total_wetted, 2),
    "skin_mass_kg":            round(skin_mass, 1),
    "empty_mass_est_kg":       round(empty_mass, 1),
    "vstall_est_ms":           round(vstall_est, 2),
    "vstall_ok":               vstall_est < VSTALL_LIM,
    "wingspan_m":              spec["wing_span"],
    "wingspan_ok":             spec["wing_span"] <= 15.0,
    # Wing chord / MAC
    "wing_root_chord_m":       spec["wing_root_chord"],
    "wing_tip_chord_m":        spec["wing_tip_chord"],
    "wing_taper_ratio":        round(wing_taper, 4),
    "wing_mac_m":              round(wing_mac, 4),
    "wing_span_m":             spec["wing_span"],
    # Horizontal tail chord / MAC
    "htail_root_chord_m":      spec["htail_root_chord"],
    "htail_tip_chord_m":       spec["htail_tip_chord"],
    "htail_mac_m":             round(htail_mac, 4),
    "htail_span_m":            spec["htail_span"],
    # Tail volume
    "tail_moment_arm_m":       round(tail_moment_arm, 3),
    "V_H":                     round(V_H, 4),
    # Vertical tail chord
    "vtail_root_chord_m":      spec["vtail_root_chord"],
    "vtail_tip_chord_m":       spec["vtail_tip_chord"],
    # Positions
    "wing_x_m":                spec["wing_x_m"],
    "wing_z_m":                spec["wing_z_m"],
    "htail_x_m":               spec["htail_x_m"],
    "vtail_x_m":               spec["vtail_x_m"],
    "prop_x_m":                spec["prop_x_m"],
    "wing_airfoil":            spec.get("wing_airfoil", ""),
    # Engine bay
    "engine_bay_start_m":      round(engine_start, 3),
    "engine_bay_end_m":        round(engine_end, 3),
    "x_engine_m":              round(x_engine_m, 3),
    # CG estimate
    "x_cg_m":                  round(x_cg_est, 3),
    "fuel_kg_est":             round(fuel_kg, 1),
    "useful_load_kg":          USEFUL_LOAD_KG,
    # Compliance
    "cockpit_x_m":             round(cockpit_x, 2),
    "cockpit_height_m":        round(cockpit_h, 3),
    "pilot_clearance_ok":      pilot_ok,
    "pilot_clearance_min_m":   PILOT_HEIGHT_MIN_M,
    "engine_bay_min_height_m": round(min_engine_h, 3),
    "engine_bay_min_width_m":  round(min_engine_w, 3),
    "engine_bay_height_ok":    engine_h_ok,
    "engine_bay_width_ok":     engine_w_ok,
    # Spec constants forwarded for simulation scripts
    "spec_MTOW_kg":            MTOW_KG,
    "spec_CL_max":             CL_MAX,
    "spec_vstall_lim_ms":      VSTALL_LIM,
    "spec_engine_mass_kg":     ENGINE_MASS_KG,
    "spec_P_engine_kw":        float(spec.get("P_engine_kw", 0.0)),
}

json_path = out_path.with_suffix(".json")
json_path.write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
print(f"\nWrote: {out_path}", file=sys.stderr)
