"""
Tail sizing — compute required horizontal and vertical tail areas for a
target static margin and control authority.

Given wing geometry, fuselage layout, and CG location, determines:
  1. Required horizontal tail area (S_h) for a target SM range
  2. Required vertical tail area (S_v) for directional stability
  3. Current tail volume coefficients V_H and V_V
  4. Whether existing tail geometry meets requirements

Reads from AIRCRAFT/<stem>.json (companion geometry file) or CLI args.

Usage:
    python size.py
    python size.py AIRCRAFT/MODEL_xx.json
    python size.py AIRCRAFT/MODEL_xx.json --SM_target 0.15 --SM_min 0.05 --SM_max 0.25

Output: DESIGN/AGENTS/tail_sizing/<stem>_tail_size.json
        Recommendations printed to stdout.

Theory
------
Horizontal tail volume coefficient:
    V_H = S_h * l_h / (S_w * c_bar)

where l_h = tail moment arm (htail AC to wing AC), S_w = wing area, c_bar = wing MAC.

Required tail area for target static margin SM_target:
    SM_target = a_w / a  * (V_H * a_t / a_w - x_cg_mac + x_ac_mac)
    -> V_H_req = (SM_target + x_cg_mac - x_ac_mac) * a / (a_t)
    -> S_h_req = V_H_req * S_w * c_bar / l_h

where:
    a   = dCL/dalpha of complete aircraft [per rad]
    a_w = dCL/dalpha of wing [per rad]
    a_t = dCL/dalpha of horizontal tail [per rad]
    x_cg_mac = CG position as fraction of MAC (measured from LE)
    x_ac_mac = aerodynamic center position (≈ 0.25 for most wings)

Simplified (a ≈ a_w for small tail contribution, a_t ≈ 0.8*a_w):
    V_H_req ≈ (SM_target + x_cg_mac - 0.25) / 0.80 * a_w/a_w
             = (SM_target + x_cg_mac - 0.25) / 0.80

Vertical tail volume coefficient:
    V_V = S_v * l_v / (S_w * b)

Stability derivative:
    Cn_beta_tail = V_V * a_v * (1 - dsigma/dbeta)
    Requirement: Cn_beta >= 0.05 /rad for positive directional stability
"""

import argparse
import json
import math
import sys
from pathlib import Path
from datetime import datetime

# ── Paths ────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR  = PROJECT_ROOT / "SIMULATION" / "results"
OUT_DIR      = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Target stability margins ──────────────────────────────────────────────────────
SM_TARGET  = 0.15   # target static margin (fraction of MAC)
SM_MIN     = 0.05   # minimum acceptable SM
SM_MAX     = 0.25   # maximum acceptable SM (above: over-stable)

# Tail aerodynamic efficiency constants
ETA_TAIL   = 0.90   # tail dynamic pressure ratio (propwash + interference)
CL_ALPHA_2D = 2 * math.pi  # per radian (thin airfoil theory)
# Finite AR correction: a = a0 / (1 + a0/(pi*AR_tail))
def _CL_alpha(AR):
    a0 = CL_ALPHA_2D
    return a0 / (1.0 + a0 / (math.pi * AR))

# Downwash on htail: de/dalpha ≈ 2*CL_alpha_wing / (pi * AR_wing)
def _downwash_gradient(CL_alpha_wing_per_rad, AR_wing):
    return 2.0 * CL_alpha_wing_per_rad / (math.pi * AR_wing)

# Cn_beta requirement for directional stability
CN_BETA_MIN = 0.05   # /rad

# ── Argument parsing ────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Tail sizing tool")
parser.add_argument("geom_json",   nargs="?",        help="AIRCRAFT/<stem>.json path")
parser.add_argument("--SM_target", type=float,       default=SM_TARGET)
parser.add_argument("--SM_min",    type=float,       default=SM_MIN)
parser.add_argument("--SM_max",    type=float,       default=SM_MAX)
args = parser.parse_args()

SM_target = args.SM_target
SM_min    = args.SM_min
SM_max    = args.SM_max

# ── Load geometry ────────────────────────────────────────────────────────────────
if args.geom_json:
    geom_path = Path(args.geom_json)
else:
    candidates = sorted(AIRCRAFT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    candidates = [p for p in candidates if "TEST" not in p.name.upper()]
    if not candidates:
        print("ERROR: no geometry JSON found in AIRCRAFT/", file=sys.stderr)
        sys.exit(1)
    geom_path = candidates[-1]

geom = {}
if geom_path.exists():
    try:
        geom = json.loads(geom_path.read_text())
    except Exception as e:
        print(f"WARN: could not parse {geom_path}: {e}", file=sys.stderr)

model_stem = geom_path.stem

# Also load alpha_sweep for CL_alpha if available
alpha_json = RESULTS_DIR / f"{model_stem}_alpha_sweep.json"
alpha = {}
if alpha_json.exists():
    try:
        alpha = json.loads(alpha_json.read_text())
    except Exception:
        pass

# ── Extract geometry ─────────────────────────────────────────────────────────────
def _g(key, default):
    return geom.get(key, default)

wing_span      = _g("wing_span_m",         9.8)
wing_area      = _g("wing_area_m2",         4.2)
wing_mac       = _g("wing_mac_m",           0.44)
wing_x         = _g("wing_x_m",             1.80)   # leading edge x
wing_taper     = _g("wing_taper_ratio",     0.65)
wing_sweep     = _g("wing_sweep",            1.0)   # deg, half-chord

htail_span     = _g("htail_span_m",         1.6)
htail_root_c   = _g("htail_root_chord_m",   0.30)
htail_tip_c    = _g("htail_tip_chord_m",    0.24)
htail_x        = _g("htail_x_m",            4.50)
htail_mac      = _g("htail_mac_m",          (htail_root_c + htail_tip_c) / 2)

vtail_height   = _g("vtail_height",         0.70)
vtail_root_c   = _g("vtail_root_chord",     0.40)
vtail_tip_c    = _g("vtail_tip_chord",      0.20)
vtail_x        = _g("vtail_x_m",            4.30)
vtail_mac      = (vtail_root_c + vtail_tip_c) / 2

x_cg           = _g("x_cg_m",              1.80)
fuse_len       = _g("total_length_m",       5.0)

# Use CL_alpha from alpha_sweep if available, else estimate
CL_alpha_wing  = alpha.get("CL_alpha_per_deg", 0.099) * math.degrees(1)  # /deg -> /rad

# ── Derived geometry ──────────────────────────────────────────────────────────────
AR_wing  = wing_span**2 / wing_area
AR_htail = htail_span**2 / (htail_span * htail_mac)

# Aerodynamic center of wing (25% MAC from LE of MAC)
# x_ac = wing_x + MAC_LE_offset + 0.25 * MAC
# For tapered wing: LE of MAC is at wing_x + 0.25*wing_span*(1-taper)/(1+taper) * tan_sweep
# Simplified: assume wing AC at wing_x + 0.25*wing_mac
x_ac_wing = wing_x + 0.25 * wing_mac

# CG position as fraction of MAC
x_cg_frac = (x_cg - (x_ac_wing - 0.25 * wing_mac)) / wing_mac

# Horizontal tail AC
x_ac_htail = htail_x + 0.25 * htail_mac

# Moment arms
l_h = x_ac_htail - x_ac_wing    # htail moment arm (between ACs)
l_v = vtail_x + 0.25 * vtail_mac - x_ac_wing  # vtail moment arm

# Current tail areas
S_h_current = htail_span * (htail_root_c + htail_tip_c) / 2.0
S_v_current = vtail_height * (vtail_root_c + vtail_tip_c) / 2.0

# Current tail volume coefficients
V_H_current = (S_h_current * l_h) / (wing_area * wing_mac) if l_h > 0 else 0.0
V_V_current = (S_v_current * l_v) / (wing_area * wing_span) if l_v > 0 else 0.0

# ── Required horizontal tail: target SM ────────────────────────────────────────────
# Tail CL_alpha (finite AR correction)
a_t = _CL_alpha(AR_htail)  # /rad

# Wing CL_alpha (use from alpha_sweep or estimate)
a_w = CL_alpha_wing  # /rad

# Downwash gradient at tail
de_dalpha = _downwash_gradient(a_w, AR_wing)
eff_tail  = ETA_TAIL * (1.0 - de_dalpha)   # effective tail contribution factor

# Required V_H for each margin target
def _V_H_required(SM):
    # SM = x_np_frac - x_cg_frac
    # x_np_frac = 0.25 + V_H * a_t * eff_tail / a_w
    # -> V_H = (SM + x_cg_frac - 0.25) * a_w / (a_t * eff_tail)
    numerator   = (SM + x_cg_frac - 0.25) * a_w
    denominator = a_t * eff_tail
    return numerator / denominator if denominator > 0 else 99.0

V_H_req_target = _V_H_required(SM_target)
V_H_req_min    = _V_H_required(SM_min)
V_H_req_max    = _V_H_required(SM_max)

# Required S_h for target V_H
def _S_h_required(V_H):
    if l_h <= 0:
        return 0.0
    return V_H * wing_area * wing_mac / l_h

S_h_req_target = _S_h_required(V_H_req_target)
S_h_req_min    = _S_h_required(V_H_req_min)
S_h_req_max    = _S_h_required(V_H_req_max)

# Current SM from current V_H
SM_current = (0.25 + V_H_current * a_t * eff_tail / a_w) - x_cg_frac

# ── Required vertical tail: directional stability ──────────────────────────────────
# Cn_beta = V_V * a_v * eta_v * (1 - sigma_beta)
# Using a_v = CL_alpha of vtail, sigma_beta ≈ 0.10 (fuselage sidewash)
a_v       = _CL_alpha(vtail_height / vtail_mac if vtail_mac > 0 else 1.5)
sigma_b   = 0.10   # approximate sidewash factor

# Fuselage destabilizing contribution (Cn_beta_fuse < 0)
# Simplified: Cn_beta_fuse ≈ -2 * Vol_fuse / (S_w * b)  (Multhopp)
D_eff     = _g("fuse_max_width_m", 1.1)    # max fuselage width
Cn_beta_fuse = -2.0 * (D_eff**2 * fuse_len) / (wing_area * wing_span) * 0.12

# Required V_V for Cn_beta = CN_BETA_MIN
Cn_beta_tail_req = CN_BETA_MIN - Cn_beta_fuse
V_V_required     = Cn_beta_tail_req / (a_v * ETA_TAIL * (1.0 - sigma_b))

S_v_required = (V_V_required * wing_area * wing_span / l_v) if l_v > 0 else 0.0

# Current Cn_beta
Cn_beta_current = V_V_current * a_v * ETA_TAIL * (1.0 - sigma_b) + Cn_beta_fuse

# ── Tail root chord recommendations for fixed span ─────────────────────────────────
# If S_h needs adjustment, what root chord change is needed for fixed span?
delta_S_h = S_h_req_target - S_h_current
new_htail_root_c = htail_root_c + delta_S_h / (htail_span * 0.75)  # rough

delta_S_v = S_v_required - S_v_current
new_vtail_root_c = vtail_root_c + delta_S_v / (vtail_height * 0.75)

# ── Assessment ─────────────────────────────────────────────────────────────────────
htail_ok = S_h_req_min <= S_h_current <= S_h_req_max
vtail_ok = S_v_current >= S_v_required
sm_ok    = SM_min <= SM_current <= SM_max

SEP = "-" * 64
print(f"\nTail Sizing: {model_stem}")
print(SEP)
print(f"  Wing: span={wing_span:.2f}m  area={wing_area:.3f}m²  MAC={wing_mac:.3f}m  "
      f"AR={AR_wing:.1f}")
print(f"  x_CG={x_cg:.3f}m  x_AC_wing={x_ac_wing:.3f}m  "
      f"x_CG_frac_MAC={x_cg_frac:.3f}")
print(f"  l_h={l_h:.3f}m  l_v={l_v:.3f}m")
print(SEP)

print(f"\n  HORIZONTAL TAIL")
print(f"    Current:  S_h={S_h_current:.4f} m²  V_H={V_H_current:.4f}  SM={SM_current*100:.1f}%MAC")
print(f"    Required for SM={SM_target*100:.0f}%: "
      f"S_h={S_h_req_target:.4f} m²  V_H={V_H_req_target:.4f}")
print(f"    Acceptable range [SM {SM_min*100:.0f}–{SM_max*100:.0f}%]: "
      f"S_h = {S_h_req_min:.4f} – {S_h_req_max:.4f} m²")

if htail_ok and sm_ok:
    print(f"    Status: OK  (current S_h is within acceptable range)")
elif S_h_current < S_h_req_min:
    inc = S_h_req_target - S_h_current
    print(f"    Status: UNDER-SIZED — increase S_h by {inc:.4f} m²")
    print(f"    Suggestion: increase htail root chord from "
          f"{htail_root_c:.3f}m -> {new_htail_root_c:.3f}m (span unchanged)")
elif S_h_current > S_h_req_max:
    dec = S_h_current - S_h_req_target
    print(f"    Status: OVER-SIZED — reduce S_h by {dec:.4f} m²  (excess trim drag)")
    print(f"    Suggestion: reduce htail root chord from "
          f"{htail_root_c:.3f}m -> {new_htail_root_c:.3f}m (span unchanged)")

print(f"\n  VERTICAL TAIL")
print(f"    Current:  S_v={S_v_current:.4f} m²  V_V={V_V_current:.4f}  "
      f"Cn_beta={Cn_beta_current:.4f}/rad")
print(f"    Required: S_v={S_v_required:.4f} m²  V_V={V_V_required:.4f}  "
      f"Cn_beta>={CN_BETA_MIN:.4f}/rad")

if vtail_ok:
    print(f"    Status: OK")
else:
    inc = S_v_required - S_v_current
    print(f"    Status: UNDER-SIZED — increase S_v by {inc:.4f} m²")
    print(f"    Suggestion: increase vtail root chord from "
          f"{vtail_root_c:.3f}m -> {new_vtail_root_c:.3f}m (height unchanged)")

print(SEP + "\n")

# ── Write JSON ──────────────────────────────────────────────────────────────────
report = {
    "model":     model_stem + ".vsp3",
    "timestamp": datetime.now().isoformat(),
    "geometry": {
        "wing_span_m":      wing_span,
        "wing_area_m2":     wing_area,
        "wing_mac_m":       wing_mac,
        "AR_wing":          round(AR_wing, 2),
        "x_cg_m":           x_cg,
        "x_ac_wing_m":      round(x_ac_wing, 4),
        "x_cg_frac_mac":    round(x_cg_frac, 4),
        "l_h_m":            round(l_h, 4),
        "l_v_m":            round(l_v, 4),
    },
    "htail": {
        "S_h_current_m2":   round(S_h_current, 4),
        "V_H_current":      round(V_H_current, 5),
        "SM_current_frac":  round(SM_current, 4),
        "SM_current_pct":   round(SM_current * 100, 2),
        "S_h_req_min_m2":   round(S_h_req_min, 4),
        "S_h_req_target_m2":round(S_h_req_target, 4),
        "S_h_req_max_m2":   round(S_h_req_max, 4),
        "V_H_req_target":   round(V_H_req_target, 5),
        "htail_ok":         htail_ok and sm_ok,
        "delta_S_h_m2":     round(S_h_req_target - S_h_current, 4),
        "new_htail_root_chord_m": round(new_htail_root_c, 3) if not (htail_ok and sm_ok) else htail_root_c,
    },
    "vtail": {
        "S_v_current_m2":   round(S_v_current, 4),
        "V_V_current":      round(V_V_current, 5),
        "Cn_beta_current":  round(Cn_beta_current, 5),
        "S_v_required_m2":  round(S_v_required, 4),
        "V_V_required":     round(V_V_required, 5),
        "Cn_beta_fuse":     round(Cn_beta_fuse, 5),
        "vtail_ok":         vtail_ok,
        "delta_S_v_m2":     round(S_v_required - S_v_current, 4),
        "new_vtail_root_chord_m": round(new_vtail_root_c, 3) if not vtail_ok else vtail_root_c,
    },
    "stability_targets": {
        "SM_target": SM_target, "SM_min": SM_min, "SM_max": SM_max,
    },
}

out_path = OUT_DIR / f"{model_stem}_tail_size.json"
out_path.write_text(json.dumps(report, indent=2))
print(f"Wrote: {out_path.relative_to(PROJECT_ROOT)}")
