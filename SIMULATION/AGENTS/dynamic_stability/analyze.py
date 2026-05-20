"""
Dynamic stability analyzer — longitudinal and lateral-directional modes.

Computes phugoid, short-period, dutch roll, roll, and spiral mode eigenvalues
from aerodynamic derivatives (alpha/beta sweep) and inertia estimates.

No OpenVSP API required — run with plain Python 3 (requires numpy).

Run:
    python analyze.py
    python analyze.py path/to/MODEL_xx_alpha_sweep.json [path/to/MODEL_xx_inertia.json]

Output: SIMULATION/results/<model_stem>_dynamic_stability.json

References:
  Nelson, R.C. "Flight Stability and Automatic Control", 2nd ed. McGraw-Hill, 1998.
  Etkin, B. & Reid, L.D. "Dynamics of Flight", 3rd ed. Wiley, 1996.
"""

import json
import math
import sys
from pathlib import Path

import numpy as np


class _NpEncoder(json.JSONEncoder):
    """Serialize numpy scalars and arrays to plain Python types."""
    def default(self, obj):
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR  = PROJECT_ROOT / "SIMULATION" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Spec constants ─────────────────────────────────────────────────────────────
MTOW_KG    = 218.0
MTOW_N     = MTOW_KG * 9.81
RHO_SL     = 1.225    # kg/m³
g          = 9.81     # m/s²

# ── Find simulation results ────────────────────────────────────────────────────
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

# Try to load inertia results
if len(sys.argv) > 2:
    inertia_path = Path(sys.argv[2]).resolve()
else:
    inertia_path = RESULTS_DIR / f"{model_stem}_inertia.json"

alpha_data   = json.loads(alpha_path.read_text())
inertia_data = json.loads(inertia_path.read_text()) if inertia_path.exists() else {}

if not inertia_data:
    print(f"WARN: inertia JSON not found ({inertia_path.name}); "
          "using geometric fallbacks for inertia", file=sys.stderr)

# Override MTOW from embedded spec constants if present
if "spec_MTOW_kg" in alpha_data:
    MTOW_KG = float(alpha_data["spec_MTOW_kg"])
    MTOW_N  = MTOW_KG * 9.81

# ── Extract aerodynamic derivatives ───────────────────────────────────────────
V0          = float(alpha_data.get("vcruise_75pct_ms",  50.0))   # trim / cruise speed
_ref        = alpha_data.get("reference", {})
wing_area   = float(_ref.get("wing_area_m2", alpha_data.get("wing_area_m2", 4.2)))
wing_span   = float(_ref.get("wing_span_m",  alpha_data.get("wing_span_m",  9.8)))
wing_mac    = float(_ref.get("wing_mac_m",   alpha_data.get("wing_mac_m",   0.44)))
x_cg        = float(_ref.get("x_cg_m",      alpha_data.get("x_cg_m",       1.8)))

CLalpha_deg = float(alpha_data.get("CL_alpha_per_deg", 0.1))  # /deg
Cmalpha_deg = float(alpha_data.get("Cm_alpha_per_deg", -0.05))  # /deg; negative = stable

# Convert to per-radian
CLalpha = CLalpha_deg * (180.0 / math.pi)
Cmalpha = Cmalpha_deg * (180.0 / math.pi)

# Trim conditions at cruise
qbar   = 0.5 * RHO_SL * V0**2    # dynamic pressure
CL0    = MTOW_N / (qbar * wing_area)  # trim lift coefficient
CD0    = CL0 / max(alpha_data.get("LD_cruise", 15.0), 1.0)  # approximate from L/D

# Alpha at trim (small angle assumption)
CL0_from_polar = float(alpha_data.get("CL_0", 0.3))  # intercept from linear fit
alpha0_rad = (CL0 - CL0_from_polar) / CLalpha if CLalpha > 0 else 0.0

# ── Inertia ────────────────────────────────────────────────────────────────────
Iyy = float(inertia_data.get("Iyy_kgm2", 300.0))
Ixx = float(inertia_data.get("Ixx_kgm2", 180.0))
Izz = float(inertia_data.get("Izz_kgm2", 450.0))
Ixz = float(inertia_data.get("Ixz_kgm2", 0.0))
m   = float(inertia_data.get("total_mass_kg", MTOW_KG))

# ── Tail geometry (for Cmq estimation) ────────────────────────────────────────
# Read from companion geometry JSON if available, else derive from alpha results
geom_path = AIRCRAFT_DIR / f"{model_stem}.json"
geom      = json.loads(geom_path.read_text()) if geom_path.exists() else {}

htail_area  = float(geom.get("htail_area_m2",  0.432))
htail_x     = float(geom.get("htail_x_m",       4.5))
htail_mac   = float(geom.get("htail_mac_m",     0.27))
V_H         = float(geom.get("V_H",             0.0))
tail_moment_arm = float(geom.get("tail_moment_arm_m",
                         htail_x + htail_mac*0.25 - x_cg))

if V_H <= 0 and wing_mac > 0:
    V_H = (htail_area * tail_moment_arm) / (wing_area * wing_mac)

# Efficiency factor for horizontal tail
ETA_TAIL = 0.90

# Cmq estimate (pitch-rate damping, tail contribution dominates):
#   Cmq ≈ -2 * η * CLα_tail * V_H * (l_t / c̄)
# CLα_tail ≈ same as wing per Nelson
CLalpha_tail = CLalpha * 0.85   # tail efficiency vs. wing
Cmq = -2.0 * ETA_TAIL * CLalpha_tail * V_H * (tail_moment_arm / wing_mac) if wing_mac > 0 else -10.0

# CmalphaD (pitch damping due to alpha-dot, typically ~0.5 * Cmq in magnitude):
CmalphaD = 0.5 * Cmq  # simplified estimate

# CDalpha (drag change with AoA — small for low alpha):
CDalpha = 2.0 * CL0 / (math.pi * (wing_span**2 / wing_area) * 0.85) if wing_area > 0 else 0.0

# ── LONGITUDINAL DYNAMICS (4-state) ───────────────────────────────────────────
# State vector: [Δu, Δw, Δq, Δθ]
# Where u = forward speed perturbation, w = vertical speed (≈ V0·Δα),
#       q = pitch rate, θ = pitch angle
#
# Dimensional stability derivatives (Nelson notation):
qS_m  = qbar * wing_area / m
qSc   = qbar * wing_area * wing_mac

# Speed derivatives
Xu = -(qS_m / V0) * (2 * CD0)                                      # speed drag
Xw = (qS_m / V0) * (CL0 - CDalpha)                                 # AoA force in x
Zu = -(qS_m / V0) * (2 * CL0)                                      # speed lift (heave)
Zw = -(qS_m / V0) * (CLalpha + CD0)                                # AoA heave force

# Pitch moment derivatives
Mw      = (qSc / (Iyy * V0)) * Cmalpha                             # pitch stiffness
Mq_dim  = (qSc * wing_mac / (2 * Iyy * V0)) * Cmq                 # pitch rate damping
MwDot   = (qSc * wing_mac / (2 * Iyy * V0**2)) * CmalphaD         # alpha-dot coupling

# Coupled Mw+MwDot*Zw and Mq+MwDot*V0 (Nelson Eq 4.38):
Mw_c  = Mw  + MwDot * Zw
Mq_c  = Mq_dim + MwDot * V0
Zu_c  = Zu
Zw_c  = Zw

# Build 4x4 longitudinal A-matrix (stability axes, level flight θ0=0)
A_lon = np.array([
    [Xu,      Xw,      0.0,  -g           ],
    [Zu_c,    Zw_c,    V0,    0.0          ],
    [MwDot*Zu_c + 0.0,  Mw_c, Mq_c, 0.0  ],
    [0.0,     0.0,     1.0,   0.0          ],
])
# Simplify: Mu = 0 (no speed-moment coupling)
A_lon[2, 0] = MwDot * Zu_c   # mu_u contribution through alpha-dot

eigs_lon = np.linalg.eigvals(A_lon)

# ── Classify longitudinal modes ───────────────────────────────────────────────
# Phugoid: eigenvalue pair with small imaginary part (slow, lightly damped)
# Short-period: eigenvalue pair with large imaginary part (fast, well damped)

def _classify_modes(eigs, label):
    """Classify complex eigenvalue pairs into named modes."""
    modes = []
    used  = set()
    eigs_list = sorted(eigs, key=lambda e: abs(e.imag))
    for i, lam in enumerate(eigs_list):
        if i in used:
            continue
        # Find conjugate pair
        pair_idx = None
        for j, other in enumerate(eigs_list):
            if j != i and j not in used and abs(lam - other.conjugate()) < 1e-6:
                pair_idx = j
                break
        if pair_idx is not None:
            used.add(i)
            used.add(pair_idx)
            sigma = lam.real
            omega = abs(lam.imag)
            omega_n = abs(lam)           # natural frequency
            zeta    = -sigma / omega_n if omega_n > 1e-9 else 0.0
            T_half  = -math.log(2) / sigma if sigma < 0 else math.inf
            T_double = math.log(2) / sigma if sigma > 0 else math.inf
            modes.append({
                "type": "oscillatory",
                "sigma": round(sigma, 5),
                "omega_rad_s": round(omega, 5),
                "omega_n_rad_s": round(omega_n, 5),
                "zeta": round(zeta, 4),
                "period_s": round(2*math.pi / omega, 3) if omega > 1e-9 else None,
                "T_half_s": round(T_half, 2) if T_half < 1e6 else None,
                "T_double_s": round(T_double, 2) if T_double < 1e6 else None,
                "stable": sigma < 0,
                "dist_from_origin": round(omega_n, 5),
            })
        else:
            used.add(i)
            sigma = lam.real
            T_half   = -math.log(2) / sigma if sigma < 0 else math.inf
            T_double =  math.log(2) / sigma if sigma > 0 else math.inf
            modes.append({
                "type": "aperiodic",
                "sigma": round(sigma, 5),
                "T_half_s":   round(T_half, 2)   if T_half < 1e6   else None,
                "T_double_s": round(T_double, 2) if T_double < 1e6 else None,
                "stable": sigma < 0,
                "dist_from_origin": round(abs(sigma), 5),
            })
    return modes

lon_modes = _classify_modes(eigs_lon, "longitudinal")
lon_modes_sorted = sorted(lon_modes, key=lambda m: m.get("omega_n_rad_s", abs(m["sigma"])))

# Label phugoid (slowest oscillatory) and short-period (fastest oscillatory)
osc_modes = [mode for mode in lon_modes_sorted if mode["type"] == "oscillatory"]
if len(osc_modes) >= 2:
    osc_modes[0]["name"] = "phugoid"
    osc_modes[1]["name"] = "short_period"
elif len(osc_modes) == 1:
    osc_modes[0]["name"] = "phugoid_or_short_period"
for mode in lon_modes_sorted:
    if mode["type"] == "aperiodic" and "name" not in mode:
        mode["name"] = "aperiodic_lon"

# ── LATERAL-DIRECTIONAL DYNAMICS (4-state) ────────────────────────────────────
# State vector: [Δβ, Δp, Δr, Δφ]
# Lateral derivatives from beta sweep if available:

beta_path = RESULTS_DIR / f"{model_stem}_beta_sweep.json"
beta_data = json.loads(beta_path.read_text()) if beta_path.exists() else {}

CY_beta = float(beta_data.get("CY_beta_per_deg", -0.20)) * (180.0/math.pi)
Cl_beta = float(beta_data.get("Cl_beta_per_deg", -0.04)) * (180.0/math.pi)
Cn_beta = float(beta_data.get("Cn_beta_per_deg",  0.05)) * (180.0/math.pi)

if not beta_data:
    print("WARN: beta sweep results not found; lateral derivatives are estimated", file=sys.stderr)
    # Rough geometric estimates if no beta sweep
    AR = wing_span**2 / wing_area if wing_area > 0 else 10.0
    CY_beta = -0.20  # approximate from vertical tail contribution
    Cl_beta = -0.02 * AR / (10.0)   # dihedral effect estimate
    Cn_beta = 0.05   # positive = weathercock stability

# Rate derivatives estimated from geometry (no rate sweep available from VSPAERO)
# References: Roskam Vol. VI appendix tables, approximate engineering values
AR   = wing_span**2 / wing_area if wing_area > 0 else 10.0
taper = float(geom.get("wing_taper_ratio", 0.65))
sweep_rad = math.radians(float(geom.get("wing_sweep", 1.0)) if geom else 1.0)

# Roll damping: Clp ≈ -(CLalpha/8) * (1 + 3λ)/(1 + λ) for untapered → simplified
Clp = -CLalpha / (4.0 * AR) * (1.0 + 3.0*taper) / (1.0 + taper)

# Yaw-roll cross derivative: Clr ≈ CL0/4  (Etkin approximation)
Clr = CL0 / 4.0

# Yaw damping: Cnr ≈ -0.5 * V_T² * (AR_vtail / AR) * CDvtail ... simplified:
# Use: Cnr ≈ -2 * Cn_beta * (l_t / b)²  (yaw damping proportional to vtail volume)
vtail_height = float(geom.get("vtail_area_m2", 0.21) / max(float(geom.get("vtail_root_chord_m", 0.40)), 0.1)) if geom else 0.7
l_t_lateral  = abs(float(geom.get("vtail_x_m", 4.3)) + float(geom.get("vtail_root_chord_m", 0.40))*0.25 - x_cg) if geom else 2.5
Cnr = -2.0 * Cn_beta * (l_t_lateral / wing_span)**2 * (wing_span**2 / wing_area)

# Cross yaw-roll: Cnp ≈ -CL0/8  (Etkin)
Cnp = -CL0 / 8.0

# Yaw from roll rate: Clr is already set; Cnr_from_Clr is small, skip.

# Convert to dimensional form
qS_Ixx = qbar * wing_area / Ixx
qS_Izz = qbar * wing_area / Izz
b      = wing_span

Yb_dim = qbar * wing_area * CY_beta / m
Lb_dim = qbar * wing_area * b * Cl_beta / Ixx
Nb_dim = qbar * wing_area * b * Cn_beta / Izz
Lp_dim = qbar * wing_area * b**2 * Clp / (2 * Ixx * V0)
Lr_dim = qbar * wing_area * b**2 * Clr / (2 * Ixx * V0)
Np_dim = qbar * wing_area * b**2 * Cnp / (2 * Izz * V0)
Nr_dim = qbar * wing_area * b**2 * Cnr / (2 * Izz * V0)

# 4x4 lateral A-matrix  (θ0 ≈ 0, so tan(θ0) ≈ 0)
A_lat = np.array([
    [Yb_dim/V0,   0.0,  -1.0,   g/V0    ],
    [Lb_dim,      Lp_dim, Lr_dim, 0.0   ],
    [Nb_dim,      Np_dim, Nr_dim, 0.0   ],
    [0.0,         1.0,    0.0,    0.0   ],
])

eigs_lat = np.linalg.eigvals(A_lat)

lat_modes = _classify_modes(eigs_lat, "lateral")
lat_modes_sorted = sorted(lat_modes, key=lambda md: md.get("omega_n_rad_s", abs(md["sigma"])))

# Label lateral modes: dutch roll (oscillatory), roll (large negative real),
# spiral (small real, may be slightly positive)
lat_osc  = [md for md in lat_modes_sorted if md["type"] == "oscillatory"]
lat_aper = sorted([md for md in lat_modes_sorted if md["type"] == "aperiodic"],
                  key=lambda md: md["sigma"])

if lat_osc:
    lat_osc[0]["name"] = "dutch_roll"
if len(lat_aper) >= 1:
    most_neg = min(lat_aper, key=lambda md: md["sigma"])
    most_neg["name"] = "roll_mode"
if len(lat_aper) >= 2:
    for md in lat_aper:
        if "name" not in md:
            md["name"] = "spiral_mode"

# ── Stability cost (eigenvalue distance from origin) ──────────────────────────
# All longitudinal modes must be stable (sigma < 0)
# cost = 1 / min(|lambda|) if all stable, else 100
lon_all_stable = all(md["stable"] for md in lon_modes_sorted)
lat_all_stable = all(md["stable"] for md in lat_modes_sorted)

lon_dists = [md["dist_from_origin"] for md in lon_modes_sorted if md["dist_from_origin"] > 1e-9]
lat_dists = [md["dist_from_origin"] for md in lat_modes_sorted if md["dist_from_origin"] > 1e-9]
all_dists = lon_dists + lat_dists

if lon_all_stable and all_dists:
    min_dist = min(all_dists)
    stability_cost = 1.0 / min_dist
    stability_status = "stable"
else:
    min_dist = 0.0
    stability_cost = 100.0
    stability_status = "UNSTABLE"

# ── Approximate phugoid / short-period natural estimates for sanity check ─────
# Phugoid: omega_p ≈ sqrt(2)*g/V0, zeta_p ≈ 1/(sqrt(2)*L/D)
LD = alpha_data.get("LD_cruise", 15.0)
omega_p_approx = math.sqrt(2) * g / V0
zeta_p_approx  = 1.0 / (math.sqrt(2) * max(LD, 1.0))

# ── Write results ──────────────────────────────────────────────────────────────
report = {
    "model":         model_stem + ".vsp3",
    "analysis":      "dynamic_stability",
    "trim": {
        "V_cruise_ms":   round(V0, 2),
        "qbar_Pa":       round(qbar, 2),
        "CL0":           round(CL0, 4),
        "CD0":           round(CD0, 6),
        "alpha0_deg":    round(math.degrees(alpha0_rad), 3),
    },
    "derivatives": {
        "CLalpha_per_rad":  round(CLalpha, 4),
        "Cmalpha_per_rad":  round(Cmalpha, 4),
        "Cmq":              round(Cmq, 4),
        "V_H":              round(V_H, 4),
        "tail_moment_arm_m": round(tail_moment_arm, 3),
        "CY_beta_per_rad":  round(CY_beta, 4),
        "Cl_beta_per_rad":  round(Cl_beta, 4),
        "Cn_beta_per_rad":  round(Cn_beta, 4),
        "lateral_from_beta_sweep": bool(beta_data),
    },
    "inertia": {
        "mass_kg":    round(m, 1),
        "Iyy_kgm2":  round(Iyy, 2),
        "Ixx_kgm2":  round(Ixx, 2),
        "Izz_kgm2":  round(Izz, 2),
        "x_cg_m":    round(x_cg, 3),
    },
    "longitudinal": {
        "A_matrix":  A_lon.tolist(),
        "modes":     lon_modes_sorted,
        "all_stable": lon_all_stable,
    },
    "lateral": {
        "A_matrix":  A_lat.tolist(),
        "modes":     lat_modes_sorted,
        "all_stable": lat_all_stable,
    },
    "stability_cost":   round(stability_cost, 4),
    "stability_status": stability_status,
    "min_eigenvalue_dist": round(min_dist, 5),
    "phugoid_approx": {
        "omega_n_approx_rad_s": round(omega_p_approx, 4),
        "zeta_approx":          round(zeta_p_approx,  4),
    },
}

out_file = RESULTS_DIR / f"{model_stem}_dynamic_stability.json"
out_file.write_text(json.dumps(report, indent=2, cls=_NpEncoder))

print(f"RESULTS_FILE:{out_file}")
print("BEGIN_JSON")
print(json.dumps(report, indent=2, cls=_NpEncoder))
print("END_JSON")
