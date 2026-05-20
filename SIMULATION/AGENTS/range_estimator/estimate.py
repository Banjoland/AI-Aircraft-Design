"""
Range and fuel estimator.

Reads alpha_sweep results (cruise speed) and the companion geometry JSON
(empty mass, wing area) to determine:
  - Required fuel for the 1100 km range specification
  - Available fuel based on the MTOW mass budget
  - Actual achievable range with available fuel
  - Endurance, rate of climb, and service ceiling

No OpenVSP API required — plain Python 3.

Run:
    python estimate.py
    python estimate.py path/to/MODEL_xx_alpha_sweep.json [path/to/MODEL_xx.json]

Output: SIMULATION/results/<model_stem>_range.json
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

# ── Spec constants (SPECIFICATION.md) — overridden by alpha_sweep embedded data ─
MTOW_KG          = 218.0
MTOW_N           = MTOW_KG * 9.81
RHO_SL           = 1.225       # kg/m³ sea-level ISA
P_ENGINE_W       = 18.0 * 745.7  # 18 hp in watts — overridden below
BSFC_KG_KWH      = 0.30        # kg/kWhr at 75% power (4-stroke gasoline)
FUEL_DENSITY     = 0.72        # kg/L (avgas)
USEFUL_LOAD_KG   = 117.0       # pilot + baggage — overridden below
RANGE_SPEC_KM    = 1667.0      # km (900 nm), overridden below if embedded
RANGE_SPEC_M     = RANGE_SPEC_KM * 1000.0

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
    print(f"WARN: no companion geometry JSON ({geom_path.name}); using alpha_sweep reference fallbacks",
          file=sys.stderr)

# Override spec constants from alpha_sweep reference (run_sweep reads companion JSON)
_aref = alpha.get("reference", {})
if "mtow_kg" in _aref:
    MTOW_KG    = float(_aref["mtow_kg"])
    MTOW_N     = MTOW_KG * 9.81
if "engine_power_w" in _aref and _aref["engine_power_w"] > 0:
    P_ENGINE_W = float(_aref["engine_power_w"])
# Read useful_load from geometry companion if present
USEFUL_LOAD_KG = float(geom.get("useful_load_kg", USEFUL_LOAD_KG))

# ── Extract from results ───────────────────────────────────────────────────────
_ref       = alpha.get("reference", {})
V_cruise   = float(alpha.get("vcruise_75pct_ms", 50.0))   # m/s
wing_area  = float(_ref.get("wing_area_m2", alpha.get("wing_area_m2", 4.2)))
LD_cruise  = float(alpha.get("LD_cruise", 15.0))
CD_cruise  = float(alpha.get("CD_cruise", 0.02))
CL_cruise  = float(alpha.get("CL_cruise", 0.5))

# Prefer weight estimator result for empty mass (more accurate than skin-only formula)
WE_DIR     = PROJECT_ROOT / "DESIGN" / "AGENTS" / "weight_estimator"
we_path    = WE_DIR / f"{model_stem}_weight.json"
if we_path.exists():
    we_data    = json.loads(we_path.read_text())
    empty_mass = float(we_data.get("empty_mass_kg", we_data.get("empty_mass_total_kg", 0.0)))
    if empty_mass <= 0:
        empty_mass = float(geom.get("empty_mass_est_kg", _ref.get("empty_mass_kg", 110.0)))
else:
    empty_mass = float(geom.get("empty_mass_est_kg", _ref.get("empty_mass_kg", 110.0)))

# ── Fuel burn from BSFC (SPECIFICATION.md: BSFC = 0.30 kg/kWhr at 75% power) ──
P_cruise_kw      = P_ENGINE_W * 0.75 / 1000.0  # kW at 75% power
FUEL_BURN_KG_HR  = BSFC_KG_KWH * P_cruise_kw   # kg/hr
FUEL_BURN_L_HR   = FUEL_BURN_KG_HR / FUEL_DENSITY  # L/hr (for display)
FUEL_BURN_KG_S   = FUEL_BURN_KG_HR / 3600.0        # kg/s

# ── Fuel budget ────────────────────────────────────────────────────────────────
fuel_avail_kg   = max(0.0, MTOW_KG - empty_mass - USEFUL_LOAD_KG)
fuel_avail_L    = fuel_avail_kg / FUEL_DENSITY
fuel_avail_note = ("MTOW - empty_mass - useful_load = "
                   f"{MTOW_KG:.0f} - {empty_mass:.1f} - {USEFUL_LOAD_KG:.0f} = "
                   f"{fuel_avail_kg:.1f} kg")

# ── Required fuel for range spec ───────────────────────────────────────────────
V_cruise_kmh     = V_cruise * 3.6
time_required_hr = RANGE_SPEC_KM / V_cruise_kmh
fuel_required_kg = FUEL_BURN_KG_HR * time_required_hr
fuel_required_L  = fuel_required_kg / FUEL_DENSITY

# ── Achievable range with available fuel ───────────────────────────────────────
endurance_hr    = fuel_avail_kg / FUEL_BURN_KG_HR if FUEL_BURN_KG_HR > 0 else 0.0
endurance_s     = endurance_hr * 3600.0
range_actual_km = V_cruise_kmh * endurance_hr
range_ok        = range_actual_km >= RANGE_SPEC_KM

# Breguet range equation (for reference):
#   R = (V/SFC) * (L/D) * ln(W_initial / W_final)
# SFC in kg/s/N:  SFC = FUEL_BURN_KG_S / (0.75 * P_ENGINE_W / V) [thrust-specific]
thrust_cruise = 0.5 * RHO_SL * V_cruise**2 * wing_area * CD_cruise  # ≈ drag at cruise
sfc_thrust    = FUEL_BURN_KG_S / max(thrust_cruise, 1.0)   # kg/(N·s)
W_initial     = MTOW_N
W_final       = MTOW_N - fuel_avail_kg * 9.81
if W_initial > W_final and W_final > 0 and LD_cruise > 0:
    breguet_range_m  = (V_cruise / sfc_thrust) * LD_cruise * math.log(W_initial / W_final)
    breguet_range_km = breguet_range_m / 1000.0
else:
    breguet_range_km = 0.0

# ── Rate of climb (sea level, max power) ──────────────────────────────────────
# RC = (P_available - P_required) / W
# At V_cruise and max power:
# P_required at cruise = 0.5 * rho * V^3 * S * CD_cruise
P_max      = P_ENGINE_W                         # 100% power
P_req_cruise = 0.5 * RHO_SL * V_cruise**3 * wing_area * CD_cruise
RC_ms      = (P_max - P_req_cruise) / MTOW_N     # m/s

# Best rate of climb speed: V_y where (P_avail - P_req) / W is maximized
# Approximate: search over a range of speeds
best_RC = 0.0
best_V_y = V_cruise
for v in [v * 1.0 for v in range(15, 100)]:
    cl_v = 2.0 * MTOW_N / (RHO_SL * v**2 * wing_area) if wing_area > 0 else 0.5
    # Parabolic drag polar: CD = CD0 + CL²/(pi*e*AR)
    # Estimate CD0 from cruise: CD0 ≈ CD_cruise/2 (roughly half parasitic)
    cd0_est = max(CD_cruise * 0.6, 0.01)
    AR      = float(_ref.get("wing_span_m", alpha.get("wing_span_m", 9.8)))**2 / wing_area if wing_area > 0 else 10.0
    e_oswald = 0.80
    cd_v = cd0_est + cl_v**2 / (math.pi * e_oswald * float(AR)) if AR > 0 else 0.03
    p_req_v = 0.5 * RHO_SL * v**3 * wing_area * cd_v
    rc_v = (P_max - p_req_v) / MTOW_N
    if rc_v > best_RC:
        best_RC = rc_v
        best_V_y = v

# Service ceiling: altitude where RC drops to 0.5 m/s (100 ft/min)
# Air density decreases with altitude: rho ≈ rho_sl * (1 - h/44300)^4.256
# At ceiling: P_avail * (rho/rho_sl) = P_req + RC_min * W
# Approximate iteratively
RC_ceiling_threshold = 0.5  # m/s
ceiling_m = 0.0
for h_m in range(0, 10000, 50):
    rho_h = RHO_SL * (1.0 - h_m / 44300.0) ** 4.256
    # At ceiling, assume still cruise speed (simplified)
    p_req_h = 0.5 * rho_h * V_cruise**3 * wing_area * CD_cruise
    p_avail_h = P_ENGINE_W * (rho_h / RHO_SL)  # engine loses power with altitude
    rc_h = (p_avail_h - p_req_h) / MTOW_N
    if rc_h <= RC_ceiling_threshold:
        ceiling_m = float(h_m)
        break
else:
    ceiling_m = 10000.0   # above our search range

# ── Fuel mass shortfall ────────────────────────────────────────────────────────
fuel_shortfall_kg = max(0.0, fuel_required_kg - fuel_avail_kg)
mass_overhead_for_range = max(0.0, empty_mass + USEFUL_LOAD_KG + fuel_required_kg - MTOW_KG)

# ── Report ────────────────────────────────────────────────────────────────────
report = {
    "model":               model_stem + ".vsp3",
    "spec": {
        "range_km":        RANGE_SPEC_KM,
        "fuel_burn_kg_hr": round(FUEL_BURN_KG_HR, 2),
        "fuel_burn_L_hr":  round(FUEL_BURN_L_HR, 1),
        "bsfc_kg_kwh":     BSFC_KG_KWH,
        "P_cruise_kw":     round(P_cruise_kw, 2),
        "useful_load_kg":  USEFUL_LOAD_KG,
        "mtow_kg":         MTOW_KG,
    },
    "performance": {
        "vcruise_ms":       round(V_cruise, 2),
        "vcruise_kmh":      round(V_cruise_kmh, 1),
        "LD_cruise":        round(LD_cruise, 2),
    },
    "fuel": {
        "empty_mass_kg":     round(empty_mass, 1),
        "fuel_avail_kg":     round(fuel_avail_kg, 1),
        "fuel_avail_L":      round(fuel_avail_L, 1),
        "fuel_avail_note":   fuel_avail_note,
        "fuel_required_kg":  round(fuel_required_kg, 1),
        "fuel_required_L":   round(fuel_required_L, 1),
        "fuel_shortfall_kg": round(fuel_shortfall_kg, 1),
        "mass_overhead_kg":  round(mass_overhead_for_range, 1),
    },
    "range": {
        "range_actual_km":  round(range_actual_km, 1),
        "range_spec_km":    RANGE_SPEC_KM,
        "range_ok":         range_ok,
        "endurance_hr":     round(endurance_hr, 2),
        "breguet_range_km": round(breguet_range_km, 1),
    },
    "climb": {
        "RC_at_cruise_ms":  round(RC_ms, 2),
        "best_RC_ms":       round(best_RC, 2),
        "V_y_best_ms":      round(best_V_y, 1),
        "service_ceiling_m": round(ceiling_m, 0),
    },
    "compliance": {
        "range_ok":        range_ok,
        "range_gap_km":    round(max(0.0, RANGE_SPEC_KM - range_actual_km), 1),
        "notes": [] if range_ok else [
            f"Range deficit: {max(0.0, RANGE_SPEC_KM - range_actual_km):.0f} km short.",
            f"Need {fuel_required_kg:.1f} kg fuel but only {fuel_avail_kg:.1f} kg available.",
            f"To meet range spec, empty mass must drop by ≥ {mass_overhead_for_range:.1f} kg.",
        ],
    },
}

out_file = RESULTS_DIR / f"{model_stem}_range.json"
out_file.write_text(json.dumps(report, indent=2))

print(f"RESULTS_FILE:{out_file}")
print("BEGIN_JSON")
print(json.dumps(report, indent=2))
print("END_JSON")
