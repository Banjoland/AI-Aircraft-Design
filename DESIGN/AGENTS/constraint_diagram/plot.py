"""
Constraint diagram — T/W vs W/S feasibility plot.

Draws the three key sizing constraints on a thrust-to-weight vs wing-loading axes:

  1. Stall constraint   : W/S <= 0.5 * rho * V_stall^2 * CL_max
                         (vertical line — maximum allowable wing loading)
  2. Cruise constraint  : T/W = q*CD0/(W/S) + (W/S)/(q*pi*e*AR)
                         (engine must supply this T/W at cruise)
  3. Climb constraint   : T/W = RC/V + q*CD0/(W/S) + (W/S)/(q*pi*e*AR)
                         (includes rate-of-climb requirement)

The feasible design space is above the cruise and climb curves and to the LEFT
of the stall line.  The design point is plotted for the current spec.

No OpenVSP API required — plain Python 3 + optional matplotlib.

Usage:
    python plot.py                      # uses SPECIFICATION defaults
    python plot.py path/to/spec.json    # override any spec value

Output: DESIGN/AGENTS/constraint_diagram/constraint_diagram.json
        Printed feasibility table to stdout.
        If matplotlib is available: DESIGN/AGENTS/constraint_diagram/constraint_diagram.png
"""

import json
import math
import sys
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR      = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Default spec ────────────────────────────────────────────────────────────────
SPEC = {
    "MTOW_kg":             218.0,
    "P_engine_hp":          18.0,
    "V_stall_max_ms":       21.0,
    "V_cruise_ms":          54.2,
    "RC_min_ms":             2.5,   # minimum rate of climb (m/s) — ~500 ft/min
    "CL_max":                1.8,   # max lift coefficient (clean stall)
    "CL_max_climb":          1.4,   # CL used during best-climb speed
    "CD0":                   0.025, # parasite drag coefficient
    "e_oswald":              0.80,  # span efficiency
    "AR_design":            22.8,   # aspect ratio of current design
    "eta_prop":              0.75,  # propulsive efficiency at cruise
    "eta_prop_climb":        0.65,  # propulsive efficiency at climb speed
    "rho_sl":                1.225,
    "WS_range_Nm2":         [50, 800],  # W/S sweep range [N/m²]
}

if len(sys.argv) > 1:
    SPEC.update(json.loads(Path(sys.argv[1]).read_text()))

# ── Derived constants ────────────────────────────────────────────────────────────
MTOW_kg    = SPEC["MTOW_kg"]
MTOW_N     = MTOW_kg * 9.81
P_W        = SPEC["P_engine_hp"] * 745.7               # engine power in watts
rho        = SPEC["rho_sl"]
V_stall    = SPEC["V_stall_max_ms"]
V_cruise   = SPEC["V_cruise_ms"]
RC         = SPEC["RC_min_ms"]
CL_max     = SPEC["CL_max"]
CL_cl      = SPEC["CL_max_climb"]
CD0        = SPEC["CD0"]
e          = SPEC["e_oswald"]
AR         = SPEC["AR_design"]
eta_c      = SPEC["eta_prop"]
eta_cl     = SPEC["eta_prop_climb"]

q_cruise   = 0.5 * rho * V_cruise**2    # dynamic pressure at cruise [Pa]
V_cl       = V_cruise * 0.60            # approximate best-climb speed

# ── Stall constraint: maximum W/S ─────────────────────────────────────────────
WS_stall   = 0.5 * rho * V_stall**2 * CL_max   # [N/m²]

# Design point W/S from MTOW and design spec
WS_design  = MTOW_N / (SPEC.get("wing_area_m2", MTOW_N / 500.0))   # fallback W/S

# Engine thrust-to-weight at cruise (available)
# P_avail = T * V / eta_prop  →  T = eta * P / V
T_cruise   = eta_c * P_W / V_cruise
TW_avail   = T_cruise / MTOW_N

# ── Build curves over W/S range ────────────────────────────────────────────────
WS_values  = [SPEC["WS_range_Nm2"][0] + i * 5 for i in
              range(int((SPEC["WS_range_Nm2"][1] - SPEC["WS_range_Nm2"][0]) / 5) + 1)]

cruise_pts = []
climb_pts  = []

for WS in WS_values:
    CL_cr  = WS / q_cruise
    CD_cr  = CD0 + CL_cr**2 / (math.pi * e * AR)
    TW_cr  = (CD_cr / CL_cr)                # T/W required in cruise: D/L = CD/CL

    # Climb: power required = (RC + V*CD/CL) * W  →  T/W = RC/V + CD/CL
    q_cl   = 0.5 * rho * V_cl**2
    CL_clb = WS / q_cl if q_cl > 0 else 99
    CD_clb = CD0 + CL_clb**2 / (math.pi * e * AR)
    TW_clb = RC / V_cl + (CD_clb / CL_clb)

    cruise_pts.append((WS, TW_cr))
    climb_pts.append((WS, TW_clb))

# ── Available T/W from engine (converts to T/W at each W/S for constant power) ─
# T = eta * P / V  → constant regardless of W/S at a given speed
# Available T/W = T / (W/S × S) ... but S = W / (W/S) → T/W = T*g / MTOW_N
# For constant power engine: T/W = eta*P/(V*MTOW_N) — same at all W/S
TW_engine_cruise = eta_c * P_W / (V_cruise * MTOW_N)
TW_engine_climb  = eta_cl * P_W / (V_cl    * MTOW_N)

# ── Find feasible W/S range ────────────────────────────────────────────────────
feasible = []
for (WS, tw_cr), (_, tw_cl) in zip(cruise_pts, climb_pts):
    cr_ok    = TW_engine_cruise >= tw_cr
    cl_ok    = TW_engine_climb  >= tw_cl
    stall_ok = WS <= WS_stall
    if cr_ok and cl_ok and stall_ok:
        feasible.append(WS)

# Design point
WS_des_nom = min(WS_stall, 500.0)   # nominal design: at stall limit or 500 N/m²
# Find T/W required at design W/S
def _TW_cruise(WS):
    CL = WS / q_cruise
    CD = CD0 + CL**2 / (math.pi * e * AR)
    return CD / CL

def _TW_climb(WS):
    q = 0.5 * rho * V_cl**2
    CL = WS / q if q > 0 else 99
    CD = CD0 + CL**2 / (math.pi * e * AR)
    return RC / V_cl + CD / CL

TW_req_cruise_des = _TW_cruise(WS_des_nom)
TW_req_climb_des  = _TW_climb(WS_des_nom)
TW_req_des        = max(TW_req_cruise_des, TW_req_climb_des)

design_feasible = (TW_engine_cruise >= TW_req_cruise_des and
                   TW_engine_climb  >= TW_req_climb_des and
                   WS_des_nom <= WS_stall)

# ── Power loading analysis ──────────────────────────────────────────────────────
# At the stall-limited W/S, what T/W is required?
TW_at_stall = _TW_cruise(WS_stall)
# What P/W is needed to achieve that T/W at cruise?
PW_req_cruise = TW_at_stall * V_cruise / eta_c   # [W/N] = m/s
P_req_W       = PW_req_cruise * MTOW_N            # [W]
P_req_hp      = P_req_W / 745.7

# Climb margin
TW_climb_at_stall = _TW_climb(WS_stall)
P_req_climb_W     = TW_climb_at_stall * V_cl / eta_cl * MTOW_N
P_req_climb_hp    = P_req_climb_W / 745.7

# ── Print report ────────────────────────────────────────────────────────────────
SEP = "-" * 62
print(f"\nConstraint Diagram Analysis")
print(SEP)
print(f"  MTOW         : {MTOW_kg:.1f} kg  ({MTOW_N:.0f} N)")
print(f"  Engine       : {SPEC['P_engine_hp']:.0f} hp  ({P_W:.0f} W)")
print(f"  V_stall spec : {V_stall:.1f} m/s")
print(f"  V_cruise     : {V_cruise:.1f} m/s")
print(f"  RC min       : {RC:.1f} m/s  ({RC*196.85:.0f} ft/min)")
print(f"  AR / e       : {AR:.1f} / {e:.2f}")
print(SEP)
print(f"\n  Stall constraint   W/S <= {WS_stall:.1f} N/m²")
print(f"  At W/S = {WS_stall:.0f} N/m² (stall limit):")
print(f"    T/W required (cruise)   = {TW_at_stall:.4f}   "
      f"(needs {P_req_hp:.1f} hp at eta={eta_c:.2f})")
print(f"    T/W required (climb)    = {TW_climb_at_stall:.4f}   "
      f"(needs {P_req_climb_hp:.1f} hp at eta={eta_cl:.2f})")
print(f"    T/W available (engine)  = {TW_engine_cruise:.4f}  (cruise)   "
      f"{TW_engine_climb:.4f}  (climb)")
print()

cruise_limited = TW_engine_cruise < TW_at_stall
climb_limited  = TW_engine_climb  < TW_climb_at_stall

if cruise_limited:
    shortage_hp = P_req_hp - SPEC["P_engine_hp"]
    print(f"  CRUISE: Engine is {shortage_hp:.1f} hp SHORT for cruise at stall-limited W/S.")
else:
    print(f"  CRUISE: Engine has surplus T/W for cruise at stall-limited W/S. OK")

if climb_limited:
    shortage_hp = P_req_climb_hp - SPEC["P_engine_hp"]
    print(f"  CLIMB:  Engine is {shortage_hp:.1f} hp SHORT for {RC:.1f} m/s climb.")
else:
    print(f"  CLIMB:  Engine meets {RC:.1f} m/s climb at stall-limited W/S. OK")

print()
if feasible:
    print(f"  Feasible W/S range: {min(feasible):.0f} – {max(feasible):.0f} N/m²")
else:
    print("  NO FEASIBLE DESIGN POINT exists with current engine power.")
    # Find minimum power required
    min_hp_needed = max(P_req_hp, P_req_climb_hp)
    print(f"  Minimum engine power to close design: {min_hp_needed:.1f} hp")

print(SEP + "\n")

# ── Optional plot ──────────────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("Agg")   # non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    fig, ax = plt.subplots(figsize=(9, 6))

    ws = [p[0] for p in cruise_pts]
    tw_cr = [p[1] for p in cruise_pts]
    tw_cl = [p[1] for p in climb_pts]

    ax.plot(ws, tw_cr, "b-",  lw=2, label="T/W required — cruise")
    ax.plot(ws, tw_cl, "g--", lw=2, label=f"T/W required — climb ({RC:.1f} m/s)")
    ax.axvline(WS_stall, color="r", lw=2, ls=":", label=f"Stall limit ({WS_stall:.0f} N/m²)")
    ax.axhline(TW_engine_cruise, color="orange", lw=1.5, ls="-.",
               label=f"T/W available cruise ({SPEC['P_engine_hp']:.0f} hp, eta={eta_c:.2f})")
    ax.axhline(TW_engine_climb, color="purple", lw=1.5, ls="--",
               label=f"T/W available climb (eta={eta_cl:.2f})")

    # Shade feasible region
    ws_arr = ws
    feasible_region_x = [x for x in ws_arr if x <= WS_stall]
    if feasible_region_x:
        ax.fill_betweenx(
            [0, max(TW_engine_cruise, TW_engine_climb) * 1.5],
            0, WS_stall,
            alpha=0.07, color="green", label="Stall-feasible zone"
        )

    ax.set_xlabel("Wing Loading W/S  [N/m²]", fontsize=12)
    ax.set_ylabel("Thrust-to-Weight  T/W  [-]", fontsize=12)
    ax.set_title(
        f"Constraint Diagram — MTOW={MTOW_kg:.0f} kg, {SPEC['P_engine_hp']:.0f} hp, "
        f"AR={AR:.1f}",
        fontsize=13
    )
    ax.set_xlim(SPEC["WS_range_Nm2"])
    ax.set_ylim(0, min(0.40, max(tw_cr + tw_cl) * 1.5))
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3)

    png_path = OUT_DIR / "constraint_diagram.png"
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
    print(f"Plot saved: {png_path.relative_to(PROJECT_ROOT)}")
except ImportError:
    print("  (matplotlib not available — skipping plot)")
except Exception as exc:
    print(f"  (plot error: {exc})")

# ── Write JSON ──────────────────────────────────────────────────────────────────
out = {
    "timestamp":          datetime.now().isoformat(),
    "spec":               SPEC,
    "stall_limit_WS_Nm2": round(WS_stall, 1),
    "TW_avail_cruise":    round(TW_engine_cruise, 5),
    "TW_avail_climb":     round(TW_engine_climb, 5),
    "TW_req_cruise_at_stall": round(TW_at_stall, 5),
    "TW_req_climb_at_stall":  round(TW_climb_at_stall, 5),
    "P_req_cruise_hp":    round(P_req_hp, 2),
    "P_req_climb_hp":     round(P_req_climb_hp, 2),
    "cruise_deficit_hp":  round(max(0, P_req_hp - SPEC["P_engine_hp"]), 2),
    "climb_deficit_hp":   round(max(0, P_req_climb_hp - SPEC["P_engine_hp"]), 2),
    "feasible_WS_range":  [min(feasible), max(feasible)] if feasible else [],
    "design_feasible":    design_feasible,
    "sweep": [
        {"WS_Nm2": ws, "TW_cruise": round(tc, 6), "TW_climb": round(tl, 6)}
        for (ws, tc), (_, tl) in zip(cruise_pts, climb_pts)
    ],
}
out_path = OUT_DIR / "constraint_diagram.json"
out_path.write_text(json.dumps(out, indent=2))
print(f"Wrote: {out_path.relative_to(PROJECT_ROOT)}")
