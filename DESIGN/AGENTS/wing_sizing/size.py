"""
Wing sizer — back-calculates wing parameters from performance requirements.

Given MTOW, engine power, stall speed limit, and cruise speed target,
finds the wing area and aspect ratio that satisfy both constraints simultaneously.

Also sweeps aspect ratio vs span to show trade-offs.

No OpenVSP API required — plain Python 3.

Run:
    python size.py
    python size.py path/to/spec_override.json

Output: DESIGN/wing_sizing_<timestamp>.json  (printed to stdout as JSON)

Equations:
    Stall:  S_min = 2 * MTOW_N / (rho * V_stall^2 * CL_max)
    Cruise: At 75% power level flight:
            D * V_cruise = 0.75 * P_engine
            D = 0.5 * rho * V^2 * S * CD
            CD = CD0 + CL^2 / (pi * e * AR)
            CL = 2 * MTOW_N / (rho * V^2 * S)
    Solve numerically for S that satisfies both constraints at the chosen AR.
"""

import json
import math
import sys
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DESIGN_DIR   = PROJECT_ROOT / "DESIGN"

# ── Default spec (SPECIFICATION.md) ───────────────────────────────────────────
DEFAULT = {
    "MTOW_kg":          218.0,
    "P_engine_hp":       18.0,
    "V_stall_max_ms":    21.0,
    "V_cruise_target_ms": 54.2,
    "CL_max":             1.8,    # achievable with NACA 44xx at max AoA
    "CD0":                0.025,  # parasite drag coefficient estimate
    "e_oswald":           0.80,   # span efficiency factor
    "AR_range":           [6, 8, 10, 12, 14, 16, 18, 20],
    "rho_sl":             1.225,
    "power_fraction":     0.75,   # cruise at 75% power
}

if len(sys.argv) > 1:
    override = json.loads(Path(sys.argv[1]).read_text())
    DEFAULT.update(override)

spec = DEFAULT

# ── Derived constants ──────────────────────────────────────────────────────────
MTOW_N    = spec["MTOW_kg"] * 9.81
P_avail   = spec["P_engine_hp"] * 745.7 * spec["power_fraction"]
rho       = spec["rho_sl"]
V_stall   = spec["V_stall_max_ms"]
V_cruise  = spec["V_cruise_target_ms"]
CL_max    = spec["CL_max"]
CD0       = spec["CD0"]
e         = spec["e_oswald"]

# ── Stall constraint: minimum wing area ───────────────────────────────────────
S_min_stall = 2.0 * MTOW_N / (rho * V_stall**2 * CL_max)

# ── Cruise constraint: solve for S at each AR ─────────────────────────────────
# P_avail = D * V = 0.5 * rho * V^3 * S * CD
# CD = CD0 + CL^2 / (pi * e * AR) where CL = 2W/(rho*V^2*S)
# → CD = CD0 + (2W)^2 / (rho^2 * V^4 * S^2 * pi * e * AR)
# P_avail = 0.5 * rho * V^3 * S * [CD0 + 4*W^2 / (rho^2*V^4*S^2*pi*e*AR)]
# P_avail = 0.5*rho*V^3*S*CD0  +  2*W^2/(rho*V*S*pi*e*AR)
# Multiply through by S:
#   P_avail * S = 0.5*rho*V^3*CD0*S^2  +  2*W^2/(rho*V*pi*e*AR)
# Quadratic in S: A*S^2 - P*S + B = 0
#   A = 0.5*rho*V^3*CD0
#   B = 2*W^2/(rho*V*pi*e*AR)
#   solution: S = (P ± sqrt(P^2 - 4*A*B)) / (2*A)

def _cruise_wing_areas(AR):
    """Return (S_low, S_high) wing areas satisfying cruise power at this AR.
       S_low: smaller wing (higher CL, higher induced drag) → lower cruise speed solution
       S_high: larger wing (lower CL, lower induced drag) → higher cruise speed solution
    """
    A = 0.5 * rho * V_cruise**3 * CD0
    B = 2.0 * MTOW_N**2 / (rho * V_cruise * math.pi * e * AR)
    disc = P_avail**2 - 4.0 * A * B
    if disc < 0:
        return None, None  # no real solution — engine too weak for this AR
    sqrt_disc = math.sqrt(disc)
    S_high = (P_avail + sqrt_disc) / (2.0 * A)
    S_low  = (P_avail - sqrt_disc) / (2.0 * A)
    return S_low, S_high

# ── Sweep over AR values ───────────────────────────────────────────────────────
results = []
for AR in spec["AR_range"]:
    S_low, S_high = _cruise_wing_areas(AR)
    if S_low is None:
        continue

    # For cruise at 75% power we want the MINIMUM wing area that achieves V_cruise.
    # The two solutions: S_low requires more CL (higher drag from induced) but less
    # parasite drag; S_high has low CL but high parasite drag.
    # The aerodynamically efficient solution is S_low (fly near min-drag speed).
    # Take the solution that satisfies both stall AND cruise.
    S_cruise = S_low if S_low >= S_min_stall else S_high

    # Actual stall speed with this wing area
    V_stall_actual = math.sqrt(2.0 * MTOW_N / (rho * S_cruise * CL_max))

    # Span and MAC
    b   = math.sqrt(AR * S_cruise)
    MAC = S_cruise / b if b > 0 else 0.0

    # Cruise CL, CD, L/D at this S
    CL_cr = 2.0 * MTOW_N / (rho * V_cruise**2 * S_cruise)
    CD_cr = CD0 + CL_cr**2 / (math.pi * e * AR)
    LD_cr = CL_cr / CD_cr if CD_cr > 0 else 0.0

    # Power required vs available
    P_req = 0.5 * rho * V_cruise**3 * S_cruise * CD_cr
    P_surplus_pct = (P_avail - P_req) / P_avail * 100.0

    stall_ok  = V_stall_actual <= V_stall
    cruise_ok = abs(P_surplus_pct) < 10.0  # within 10% of power budget

    results.append({
        "AR":             round(AR, 1),
        "S_m2":           round(S_cruise, 3),
        "span_m":         round(b, 3),
        "MAC_m":          round(MAC, 4),
        "V_stall_ms":     round(V_stall_actual, 2),
        "stall_ok":       stall_ok,
        "CL_cruise":      round(CL_cr, 4),
        "CD_cruise":      round(CD_cr, 5),
        "LD_cruise":      round(LD_cr, 2),
        "P_req_W":        round(P_req, 1),
        "P_avail_W":      round(P_avail, 1),
        "P_surplus_pct":  round(P_surplus_pct, 1),
        "cruise_ok":      cruise_ok,
        "feasible":       stall_ok and cruise_ok,
    })

# ── Find optimal AR (minimum wing area that is feasible) ──────────────────────
feasible = [r for r in results if r["feasible"]]
if feasible:
    # Among feasible options, pick minimum span (structural preference)
    opt = min(feasible, key=lambda r: r["span_m"])
    recommendation = (
        f"AR={opt['AR']} → S={opt['S_m2']} m², span={opt['span_m']} m, "
        f"V_stall={opt['V_stall_ms']} m/s, L/D={opt['LD_cruise']}"
    )
else:
    opt = None
    recommendation = (
        "No feasible solution found in the AR sweep. "
        "The engine is too weak to achieve the cruise speed target. "
        "Consider increasing P_engine, reducing MTOW, or lowering the cruise target."
    )

# ── Print results table ────────────────────────────────────────────────────────
header = f"{'AR':>4}  {'S(m2)':>7}  {'span(m)':>7}  {'Vstall':>6}  {'OK?':>4}  {'L/D':>5}  {'Psurplus%':>9}"
print(header)
print('-' * len(header))
for r in results:
    flag = "YES" if r["feasible"] else "no "
    print(f"{r['AR']:>4.0f}  {r['S_m2']:>7.3f}  {r['span_m']:>7.3f}  "
          f"{r['V_stall_ms']:>6.2f}  {flag:>4}  {r['LD_cruise']:>5.2f}  "
          f"{r['P_surplus_pct']:>+9.1f}%")

print(f"\nStall constraint: S >= {S_min_stall:.3f} m²  (V_stall <= {V_stall} m/s, CL_max={CL_max})")
print(f"Cruise constraint: at {V_cruise} m/s, {spec['power_fraction']*100:.0f}% of {spec['P_engine_hp']:.0f} hp")
print(f"\nRecommendation: {recommendation}")

# ── Write JSON ────────────────────────────────────────────────────────────────
out = {
    "spec":           spec,
    "S_min_stall_m2": round(S_min_stall, 3),
    "P_avail_W":      round(P_avail, 1),
    "sweep":          results,
    "optimal":        opt,
    "recommendation": recommendation,
}
out_path = DESIGN_DIR / f"wing_sizing_{datetime.now().strftime('%m_%d_%Y_%H%M%S')}.json"
out_path.write_text(json.dumps(out, indent=2))
print(f"\nWrote: {out_path.relative_to(PROJECT_ROOT)}")
