"""
Two-spline fuselage generator.

Defines the entire fuselage shape from three globally-smooth C2 cubic splines:
  top_spline    : z_top(x)      — top z-coordinate of fuselage cross-section
  bot_spline    : z_bot(x)      — bottom z-coordinate
  hw_spline     : half_width(x) — half-width at each station

A cross-section at position x is an ellipse with:
  height   = z_top(x) - z_bot(x)
  z_center = (z_top(x) + z_bot(x)) / 2
  width    = 2 * half_width(x)

Because the entire shape is driven by three splines, changing a single control
point ripples smoothly through all sections (global C2 continuity).

The generator checks slope and curvature at every sampled station and flags
any region that may cause boundary-layer separation or high form drag.

Output: AIRCRAFT/MODEL_MM_DD_YYYY_XX.vsp3

Usage:
    openvsp-python generate.py                    # default streamlined design
    openvsp-python generate.py path/to/spec.json  # custom spline control points
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

# ── Default spline design (streamlined single-pilot tractor) ──────────────────
# Control points: [x_m, z_m] for top/bot; [x_m, hw_m] for half-width.
# Profile targets Sears-Haack-inspired shape:
#   - Small rounded nose
#   - Max section near 35-40% of length
#   - Long gentle aft taper (slope < 12°)
#   - Meets at a rounded tail tip (not a mathematical point)
DEFAULT_SPEC = {
    "total_length_m": 5.5,
    "n_sections": 12,

    # Top profile z_top(x): engine cowl low, rises through cockpit, tapers aft
    "top_spline_knots": [
        [0.00,  0.20],   # nose tip
        [0.80,  0.40],   # engine cowl
        [1.60,  0.52],   # engine bay
        [2.50,  0.86],   # forward cockpit ramp
        [3.00,  1.02],   # cockpit crown / CG
        [3.40,  1.06],   # wing saddle
        [4.20,  0.92],   # aft taper begins
        [4.80,  0.78],   # tail fairing
        [5.50,  0.62]    # tail tip
    ],

    # Bottom profile z_bot(x): relatively flat, engine low at nose
    "bot_spline_knots": [
        [0.00, -0.18],   # nose tip
        [0.80, -0.38],   # engine cowl belly
        [1.60, -0.44],   # engine bay bottom
        [2.50, -0.44],   # forward belly
        [3.00, -0.40],   # cockpit floor
        [3.40, -0.28],   # belly taper begins
        [4.20,  0.02],   # belly closes
        [4.80,  0.24],   # aft belly
        [5.50,  0.62]    # tail tip (meets top)
    ],

    # Half-width w(x): widest near cockpit, tapers to a small tail
    "hw_spline_knots": [
        [0.00,  0.18],   # nose
        [0.80,  0.34],   # engine cowl
        [1.60,  0.46],   # engine bay
        [2.50,  0.52],   # forward cabin
        [3.00,  0.55],   # cockpit (shoulder + clearance)
        [3.40,  0.52],   # wing saddle
        [4.20,  0.38],   # aft taper
        [4.80,  0.26],   # tail section
        [5.50,  0.10]    # tail tip
    ],

    # Companion metadata (not used by generator geometry — recorded in JSON)
    "wing_x_m":   3.00,
    "wing_z_m":   1.06,
    "htail_x_m":  5.00,
    "htail_z_m":  0.72,
    "vtail_x_m":  4.90,
    "x_cg_m":     3.00,
    "pilot_x_m":  3.00,

    # Alert thresholds for smoothness checks
    "max_slope_deg_warning":  14.0,   # flag if profile slope exceeds this
    "max_curvature_warning":   0.7,   # 1/m — flag if curvature exceeds this
}

# ── Load spec override ─────────────────────────────────────────────────────────
spec = DEFAULT_SPEC.copy()
if len(sys.argv) > 1:
    override_path = Path(sys.argv[1]).resolve()
    overrides = json.loads(override_path.read_text())
    spec.update(overrides)

# ── Helpers ────────────────────────────────────────────────────────────────────
def _make_spline(knots):
    pts = np.array(sorted(knots, key=lambda p: p[0]), dtype=float)
    return CubicSpline(pts[:, 0], pts[:, 1], bc_type="not-a-knot")

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

L    = float(spec["total_length_m"])
N    = int(spec["n_sections"])
# Evenly-spaced stations from 0 to L
x_stations = np.linspace(0.0, L, N)

# ── Smoothness check ───────────────────────────────────────────────────────────
slope_warn = float(spec.get("max_slope_deg_warning", 14.0))
curv_warn  = float(spec.get("max_curvature_warning",  0.7))

flags = []
for x in x_stations:
    for label, cs in [("top", top_cs), ("bot", bot_cs), ("hw", hw_cs)]:
        dy   = float(cs(x, 1))
        d2y  = float(cs(x, 2))
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

fuse_id = vsp.AddGeom("FUSELAGE")
vsp.SetGeomName(fuse_id, "SplineFuselage")

# Set fuselage length
pid = vsp.FindParm(fuse_id, "Length", "Design")
if pid:
    vsp.SetParmVal(pid, L)
vsp.Update()

# ── Ensure correct number of XSec ─────────────────────────────────────────────
def _xsec_count():
    return vsp.GetNumXSec(vsp.GetXSecSurf(fuse_id, 0))

# Add sections until we have enough
while _xsec_count() < N:
    surf = vsp.GetXSecSurf(fuse_id, 0)
    n    = vsp.GetNumXSec(surf)
    vsp.InsertXSec(fuse_id, n - 2, vsp.XS_ELLIPSE)   # insert before last
    vsp.Update()

# Remove excess sections
while _xsec_count() > N:
    surf = vsp.GetXSecSurf(fuse_id, 0)
    n    = vsp.GetNumXSec(surf)
    vsp.CutXSec(fuse_id, n - 2)   # remove second-to-last
    vsp.Update()

# ── Set each cross-section from splines ───────────────────────────────────────
surf    = vsp.GetXSecSurf(fuse_id, 0)
n_xsec  = vsp.GetNumXSec(surf)

for idx in range(n_xsec):
    x = float(x_stations[idx]) if idx < len(x_stations) else L

    z_top = float(top_cs(x))
    z_bot = float(bot_cs(x))
    hw    = max(float(hw_cs(x)), 0.02)

    height  = max(z_top - z_bot, 0.02)
    width   = max(2.0 * hw, 0.04)
    z_ctr   = (z_top + z_bot) / 2.0
    x_frac  = x / L if L > 0 else 0.0
    z_frac  = z_ctr / L

    # Set ellipse shape
    vsp.ChangeXSecShape(surf, idx, vsp.XS_ELLIPSE)
    vsp.Update()
    xs = vsp.GetXSec(surf, idx)
    vsp.SetXSecWidthHeight(xs, width, height)

    # Position along fuselage
    _xsec_set(xs, "XLocPercent", x_frac)
    _xsec_set(xs, "YLocPercent", 0.0)
    _xsec_set(xs, "ZLocPercent", z_frac)

    # C2 skinning on interior sections
    if 0 < idx < n_xsec - 1:
        _apply_c2(xs)

vsp.Update()

# ── Smoothness summary metrics ─────────────────────────────────────────────────
z_tops  = [float(top_cs(x)) for x in x_stations]
z_bots  = [float(bot_cs(x)) for x in x_stations]
hws     = [max(float(hw_cs(x)), 0.02) for x in x_stations]
heights = [max(zt - zb, 0.02) for zt, zb in zip(z_tops, z_bots)]
widths  = [max(2.0 * hw, 0.04) for hw in hws]

max_equiv_diam = max(math.sqrt(h * w) for h, w in zip(heights, widths))
fineness       = L / max_equiv_diam if max_equiv_diam > 0 else 0.0

max_top_slope = max(
    abs(math.degrees(math.atan(float(top_cs(x, 1))))) for x in x_stations
)
max_bot_slope = max(
    abs(math.degrees(math.atan(float(bot_cs(x, 1))))) for x in x_stations
)

smoothness_score = max(0.0, min(100.0,
    100.0
    - max(0.0, max(max_top_slope, max_bot_slope) - slope_warn) * 3.0
    - len(flags) * 2.0
))

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

# ── Companion JSON ─────────────────────────────────────────────────────────────
summary = {
    "model_file":             str(out_path),
    "configuration":          "two_spline_fuselage",
    "generator":              "two_spline_fuselage/generate.py",
    "total_length_m":         round(L, 2),
    "n_sections":             n_xsec,
    "max_equiv_diam_m":       round(max_equiv_diam, 3),
    "fineness_ratio":         round(fineness, 2),
    "max_top_slope_deg":      round(max_top_slope, 2),
    "max_bot_slope_deg":      round(max_bot_slope, 2),
    "smoothness_score":       round(smoothness_score, 1),
    "smoothness_flag_count":  len(flags),
    "smoothness_flags":       flags[:10],
    "top_spline_knots":       spec["top_spline_knots"],
    "bot_spline_knots":       spec["bot_spline_knots"],
    "hw_spline_knots":        spec["hw_spline_knots"],
    "x_cg_m":                 spec.get("x_cg_m", 3.00),
    "pilot_x_m":              spec.get("pilot_x_m", 3.00),
    "wing_x_m":               spec.get("wing_x_m", 3.00),
    "wing_z_m":               spec.get("wing_z_m", 1.06),
    "htail_x_m":              spec.get("htail_x_m", 5.00),
    "vtail_x_m":              spec.get("vtail_x_m", 4.90),
}

json_path = out_path.with_suffix(".json")
json_path.write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
print(f"\nWrote: {out_path}", file=sys.stderr)
