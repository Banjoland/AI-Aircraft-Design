"""
Static margin and neutral point calculator.

Computes the stick-fixed neutral point, static margin, and CG position
from alpha sweep derivatives and geometry metadata.

No OpenVSP API required — plain Python 3.

Run:
    python compute.py
    python compute.py path/to/MODEL_xx_alpha_sweep.json [path/to/MODEL_xx.json]

Output: SIMULATION/results/<model_stem>_static_margin.json

Theory (Nelson "Flight Stability and Automatic Control"):
  SM = -(dCm/dCL) = -(Cm_alpha / CL_alpha)   [dimensionless, fraction of MAC]
  x_NP = x_CG + SM * c_bar                   [neutral point location from nose]
  Positive SM → stable (NP behind CG).
"""

import json
import math
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR  = PROJECT_ROOT / "SIMULATION" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Target static margin range (conventional aircraft) ────────────────────────
SM_MIN  = 0.05   # fraction of MAC — below this is marginally stable
SM_MAX  = 0.30   # above this is over-stable (high trim drag, poor maneuverability)
SM_OPT  = 0.15   # typical target for a light aircraft

# ── Find inputs ────────────────────────────────────────────────────────────────
if len(sys.argv) > 1:
    alpha_path = Path(sys.argv[1]).resolve()
else:
    candidates = sorted(RESULTS_DIR.glob("*_alpha_sweep.json"),
                        key=lambda p: p.stat().st_mtime)
    if not candidates:
        print("ERROR: no *_alpha_sweep.json in SIMULATION/results/", file=sys.stderr)
        sys.exit(1)
    alpha_path = candidates[-1]

model_stem = alpha_path.stem.replace("_alpha_sweep", "")

if len(sys.argv) > 2:
    geom_path = Path(sys.argv[2]).resolve()
else:
    geom_path = AIRCRAFT_DIR / f"{model_stem}.json"

alpha = json.loads(alpha_path.read_text())
geom  = json.loads(geom_path.read_text()) if geom_path.exists() else {}

if not geom:
    print(f"WARN: no geometry JSON ({geom_path.name}); using fallback values", file=sys.stderr)

# ── Extract derivatives ────────────────────────────────────────────────────────
Cm_alpha_deg = float(alpha.get("Cm_alpha_per_deg", 0.0))
CL_alpha_deg = float(alpha.get("CL_alpha_per_deg", 0.1))
stable       = alpha.get("longitudinal_stable", False)

# Reference geometry
wing_mac = float(geom.get("wing_mac_m",
                  alpha["reference"].get("wing_mac_m", 0.44)))
x_cg     = float(geom.get("x_cg_m",
                  alpha["reference"].get("x_cg_m", 1.8)))
wing_x   = float(geom.get("wing_x_m",  1.8))
htail_x  = float(geom.get("htail_x_m", 4.5))
htail_mac = float(geom.get("htail_mac_m", 0.27))
total_length = float(geom.get("total_length_m", 5.0))

# ── Static margin and neutral point ───────────────────────────────────────────
# dCm/dCL = Cm_alpha / CL_alpha  (consistent units — both /deg, ratio is dimensionless)
dCm_dCL = Cm_alpha_deg / CL_alpha_deg if abs(CL_alpha_deg) > 1e-9 else 0.0

# SM_raw = -(dCm/dCL) referenced to the VSPAERO moment origin (x=0, model nose).
# VSPAERO references pitching moments to the model geometric origin unless the
# analysis Xcg parameter is set. Applying the CG-offset correction:
#   SM_true = SM_raw - x_cg / c_bar
SM_raw = -dCm_dCL
SM = SM_raw - (x_cg / wing_mac) if wing_mac > 0 else SM_raw

# Neutral point location from nose (m)
x_NP = x_cg + SM * wing_mac

# ── Wing aerodynamic center (approximate, for context) ─────────────────────────
# For thin wings, AC ≈ 25% MAC from leading edge of MAC
# MAC leading edge location: x_mac_le ≈ wing_x + delta (from sweep geometry)
wing_sweep_deg = float(geom.get("wing_sweep", 1.0))
taper = float(geom.get("wing_taper_ratio", 0.65))
span  = float(geom.get("wing_span_m", geom.get("wingspan_m", 9.8)))

# Spanwise location of MAC: y_mac = (b/6) * (1 + 2*λ)/(1 + λ)
y_mac = (span / 6.0) * (1.0 + 2.0 * taper) / (1.0 + taper)
# Chordwise sweep to MAC LE
x_mac_le = wing_x + y_mac * math.tan(math.radians(wing_sweep_deg))
x_wing_AC = x_mac_le + 0.25 * wing_mac

# ── Fuselage destabilizing contribution (estimated) ──────────────────────────
# Long fuselage ahead of wing adds a destabilizing (nose-up) moment.
# Approximate from Munk formula: dCm/dα_fuse ≈ 2 * k * Vol_nose / (S * c)
# Simplified: just note the fuselage contribution is destabilizing for typical designs.
fuse_nosed_length = wing_x  # fuselage ahead of wing
fuse_note = (f"Fuselage nose length = {fuse_nosed_length:.2f} m ahead of wing. "
             "Long noses add destabilizing fuselage Cmα — tail must compensate.")

# ── CG sensitivity: how much does CG shift affect SM? ─────────────────────────
# If CG moves aft by Δx, SM decreases by Δx/c_bar MAC lengths
# Acceptable CG range: SM stays between SM_MIN and SM_MAX
delta_cg_fwd   = (SM - SM_MIN) * wing_mac   # how far CG can move aft before instability
delta_cg_aft   = (SM_MAX - SM) * wing_mac   # how far CG can move forward before over-stability

cg_limit_fwd = x_cg + delta_cg_fwd   # aftmost acceptable CG
cg_limit_aft = x_cg - delta_cg_aft   # forward most acceptable CG

# ── SM assessment ──────────────────────────────────────────────────────────────
if not stable or Cm_alpha_deg >= 0:
    sm_status = "UNSTABLE"
    sm_note   = "Cm_alpha ≥ 0: aircraft is longitudinally unstable."
elif SM < SM_MIN:
    sm_status = "MARGINAL"
    sm_note   = f"SM = {SM:.3f} MAC (< {SM_MIN:.2f} min): marginally stable."
elif SM > SM_MAX:
    sm_status = "OVER_STABLE"
    sm_note   = (f"SM = {SM:.3f} MAC (> {SM_MAX:.2f} max): over-stable. "
                 "High trim drag and reduced cruise efficiency.")
else:
    sm_status = "GOOD"
    sm_note   = f"SM = {SM:.3f} MAC: within recommended range {SM_MIN:.2f}–{SM_MAX:.2f}."

# ── Helper ─────────────────────────────────────────────────────────────────────
def _build_recs(SM, status, x_NP, x_CG, c_bar, V_H):
    recs = []
    if status == "UNSTABLE":
        recs.append("Move CG forward or increase tail volume to achieve stability.")
    elif status == "MARGINAL":
        delta = (SM_OPT - SM) * c_bar
        recs.append(f"Move CG forward by {delta:.3f} m to reach optimal SM={SM_OPT:.2f}.")
    elif status == "OVER_STABLE":
        delta = (SM - SM_OPT) * c_bar
        recs.append(f"Move CG aft by {delta:.3f} m to reach optimal SM={SM_OPT:.2f}.")
        recs.append("Alternatively reduce tail volume (smaller horizontal tail area or shorter moment arm).")
    if V_H < 0.35:
        recs.append(f"Increase horizontal tail volume (V_H={V_H:.3f} < 0.35). "
                    "Options: increase htail area, increase tail moment arm, or move htail aft.")
    return recs


# ── Tail volume check ──────────────────────────────────────────────────────────
V_H = float(geom.get("V_H", 0.0))
_htail_qc = (htail_x + htail_mac * 0.25) - (wing_x + wing_mac * 0.25)
tail_moment_arm = float(geom.get("tail_moment_arm_m", _htail_qc))

# Minimum tail volume for 5% SM (empirical for light aircraft): V_H ~ 0.35–0.45
V_H_note = ("adequate" if V_H >= 0.35
            else f"V_H = {V_H:.3f} is below typical minimum of 0.35 for light aircraft")

# ── Report ────────────────────────────────────────────────────────────────────
report = {
    "model":       model_stem + ".vsp3",
    "derivatives": {
        "Cm_alpha_per_deg": round(Cm_alpha_deg, 5),
        "CL_alpha_per_deg": round(CL_alpha_deg, 5),
        "dCm_dCL":          round(dCm_dCL, 5),
    },
    "geometry": {
        "wing_mac_m":        round(wing_mac, 4),
        "x_cg_m":            round(x_cg, 4),
        "x_wing_AC_m":       round(x_wing_AC, 4),
        "x_htail_m":         round(htail_x, 2),
        "total_length_m":    round(total_length, 2),
        "V_H":               round(V_H, 4),
        "tail_moment_arm_m": round(tail_moment_arm, 3),
    },
    "static_margin": {
        "SM":           round(SM, 4),
        "SM_pct_mac":   round(SM * 100, 1),
        "x_NP_m":       round(x_NP, 4),
        "x_CG_m":       round(x_cg, 4),
        "NP_behind_CG_m": round(x_NP - x_cg, 4),
        "SM_status":    sm_status,
        "SM_note":      sm_note,
    },
    "cg_limits": {
        "cg_aft_limit_m":  round(cg_limit_fwd, 4),
        "cg_fwd_limit_m":  round(cg_limit_aft, 4),
        "cg_range_m":      round(delta_cg_fwd + delta_cg_aft, 4),
        "note": (f"CG may move aft by {delta_cg_fwd:.3f} m or forward by "
                 f"{delta_cg_aft:.3f} m from current position before SM exits "
                 f"[{SM_MIN:.2f}, {SM_MAX:.2f}] range."),
    },
    "V_H_assessment": V_H_note,
    "fuse_note": fuse_note,
    "recommendations": _build_recs(SM, sm_status, x_NP, x_cg, wing_mac, V_H),
}

out_file = RESULTS_DIR / f"{model_stem}_static_margin.json"
out_file.write_text(json.dumps(report, indent=2))

print(f"RESULTS_FILE:{out_file}")
print("BEGIN_JSON")
print(json.dumps(report, indent=2))
print("END_JSON")
