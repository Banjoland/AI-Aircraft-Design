"""
Iteration suggester — reads all simulation results and recommends
the single design change most likely to reduce the total cost.

Reads from SIMULATION/results/ and EVALUATION/scores/ for the most recent
(or specified) model, then applies a ranked set of heuristics to identify
the dominant cost driver and the best lever to pull.

No OpenVSP API required — plain Python 3.

Run:
    python suggest.py
    python suggest.py MODEL_xx          (model stem, no extension)
    python suggest.py MODEL_xx.vsp3

Output: DESIGN/AGENTS/iteration_suggester/<model_stem>_suggestion.json
        Suggestion printed to stdout.
"""

import json
import math
import sys
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR  = PROJECT_ROOT / "SIMULATION" / "results"
SCORES_DIR   = PROJECT_ROOT / "EVALUATION" / "scores"
OUT_DIR      = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Find model stem ────────────────────────────────────────────────────────────
if len(sys.argv) > 1:
    arg = sys.argv[1].replace(".vsp3", "")
    model_stem = arg
else:
    candidates = sorted(SCORES_DIR.glob("*_score.json"),
                        key=lambda p: p.stat().st_mtime)
    if not candidates:
        # Fall back to alpha sweep results
        candidates = sorted(RESULTS_DIR.glob("*_alpha_sweep.json"),
                            key=lambda p: p.stat().st_mtime)
        if not candidates:
            print("ERROR: no scored model found.", file=sys.stderr)
            sys.exit(1)
        model_stem = candidates[-1].stem.replace("_alpha_sweep", "")
    else:
        model_stem = candidates[-1].stem.replace("_score", "")

def _load(path):
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}

score   = _load(SCORES_DIR  / f"{model_stem}_score.json")
alpha   = _load(RESULTS_DIR / f"{model_stem}_alpha_sweep.json")
geom    = _load(AIRCRAFT_DIR / f"{model_stem}.json")
dynstab = _load(RESULTS_DIR / f"{model_stem}_dynamic_stability.json")
rng     = _load(RESULTS_DIR / f"{model_stem}_range.json")
sm      = _load(RESULTS_DIR / f"{model_stem}_static_margin.json")
inert   = _load(RESULTS_DIR / f"{model_stem}_inertia.json")
drag    = _load(RESULTS_DIR / f"{model_stem}_parasite_drag.json")

# ── Extract key metrics ────────────────────────────────────────────────────────
total_cost   = score.get("total_cost",       999.0)
stall_cost   = score.get("stall_cost",         0.0)
stab_cost    = score.get("stability_cost",   100.0)
mass_cost    = score.get("mass_cost",        999.0)
cruise_rew   = score.get("cruise_reward",      0.0)

empty_mass   = geom.get("empty_mass_est_kg",  170.0)
total_wetted = geom.get("total_wetted_m2",     20.0)
fuse_wetted  = geom.get("fuse_wetted_m2",      10.0)
wing_wetted  = geom.get("wing_wetted_m2",       8.7)

V_stall      = alpha.get("vstall_est_ms",     22.0)
V_cruise     = alpha.get("vcruise_75pct_ms",  48.0)
LD_cruise    = alpha.get("LD_cruise",         15.0)
Cm_alpha     = alpha.get("Cm_alpha_per_deg",  -0.01)

x_cg         = geom.get("x_cg_m",    1.8)
wing_x       = geom.get("wing_x_m",  1.8)
wing_mac     = geom.get("wing_mac_m", 0.44)
wing_span    = geom.get("wing_span_m", 9.8)
wing_area    = geom.get("wing_area_m2", 4.2)
fuse_len     = geom.get("total_length_m", 5.0)

SM_pct       = sm.get("static_margin", {}).get("SM_pct_mac", 0.0)
SM_status    = sm.get("static_margin", {}).get("SM_status", "UNKNOWN")

range_km     = rng.get("range", {}).get("range_actual_km", 0.0)
fuel_avail   = rng.get("fuel", {}).get("fuel_avail_kg", 0.0)

# ── Heuristics (ordered by impact) ────────────────────────────────────────────
suggestions = []

def _add(priority, category, change, rationale, impact_estimate, params=None):
    suggestions.append({
        "priority":        priority,
        "category":        category,
        "change":          change,
        "rationale":       rationale,
        "impact_estimate": impact_estimate,
        "params":          params or {},
    })

# ── Mass cost (almost always dominant) ────────────────────────────────────────
MASS_SPEC = 110.0
if mass_cost > 10.0:
    mass_excess  = empty_mass - MASS_SPEC
    fuse_frac    = fuse_wetted / total_wetted if total_wetted > 0 else 0.5
    wing_frac    = wing_wetted / total_wetted if total_wetted > 0 else 0.4

    if fuse_frac > 0.45:
        # Fuselage is the dominant contributor — shorten it
        target_len = fuse_len * (1.0 - 0.15)   # 15% shorter
        _add(1, "mass", f"Reduce fuselage length from {fuse_len:.1f} m to {target_len:.1f} m",
             f"Fuselage is {fuse_frac*100:.0f}% of total wetted area. "
             f"Shortening by 15% saves ≈{fuse_wetted*0.15*6:.0f} kg skin mass. "
             f"Adjust spline knots proportionally; verify engine bay and cockpit constraints.",
             f"mass_cost: {mass_cost:.0f} → ≈{math.exp(10*(empty_mass*0.9-MASS_SPEC)/MASS_SPEC)-1:.0f} (rough)",
             {"total_length_m": round(target_len, 2)})

    if wing_frac > 0.40:
        # Wing is large — check if span can be reduced without stall penalty
        target_span = max(7.0, wing_span * 0.90)
        new_area = target_span * 0.43   # keep same avg chord
        new_vstall = math.sqrt(2 * 218 * 9.81 / (1.225 * new_area * 1.8))
        if new_vstall <= 21.0:
            _add(2, "mass", f"Reduce wingspan from {wing_span:.1f} m to {target_span:.1f} m",
                 f"Wing wetted area is {wing_frac*100:.0f}% of total. "
                 f"Estimated new V_stall={new_vstall:.1f} m/s (spec ≤21). "
                 f"Also reduces induced drag (lower span efficiency × area).",
                 f"Saves ≈{(wing_span - target_span) * 0.43 * 2 * 1.04 * 6:.0f} kg",
                 {"wing_span": round(target_span, 1)})

# ── Stall cost ─────────────────────────────────────────────────────────────────
if stall_cost > 0.5:
    excess_vstall = V_stall - 21.0
    # Need larger wing area
    S_needed = 2 * 218 * 9.81 / (1.225 * 21.0**2 * 1.8)
    delta_S = S_needed - wing_area
    delta_span = delta_S / (wing_mac * 0.9)  # approximate
    _add(1, "stall", f"Increase wing span by ≈{delta_span:.2f} m",
         f"V_stall={V_stall:.1f} m/s exceeds 21 m/s spec by {excess_vstall:.1f} m/s. "
         f"Need wing area ≥ {S_needed:.2f} m² (currently {wing_area:.2f} m²).",
         f"stall_cost: {stall_cost:.2f} → 0.00",
         {"wing_span": round(wing_span + delta_span, 1)})

# ── Stability / static margin ──────────────────────────────────────────────────
if SM_status == "UNSTABLE" or stab_cost > 5.0:
    _add(1, "stability", "Move CG forward or increase horizontal tail area",
         f"SM_status={SM_status}. Cm_alpha={Cm_alpha:.4f}/deg. "
         "An unstable aircraft has very high stability cost. "
         "Moving CG forward (shift engine/fuel/payload) is the fastest fix.",
         "stability_cost: 100 → <1 (if stabilized)",
         {"htail_span": round(geom.get("htail_span_m", 1.6) * 1.20, 2)})

elif SM_status == "OVER_STABLE" and SM_pct > 25.0:
    delta_cg = (SM_pct/100 - 0.15) * wing_mac
    _add(3, "stability",
         f"Move CG aft by {delta_cg:.3f} m to target SM=15%",
         f"SM={SM_pct:.1f}% is over-stable (target 10–20%). "
         "Excessive stability means large trim download on the tail at cruise → drag. "
         "Moving CG aft (shift payload or fuel aft) reduces trim drag and cruise reward.",
         "cruise_reward increases (less trim drag)",
         {})

# ── Cruise speed ───────────────────────────────────────────────────────────────
V_CRUISE_TARGET = 54.2
if V_cruise < V_CRUISE_TARGET * 0.85:
    _add(3, "cruise", "Reduce fuselage fineness ratio or clean up drag",
         f"V_cruise={V_cruise:.1f} m/s is {(V_CRUISE_TARGET-V_cruise):.1f} m/s below target. "
         "Primary lever: reduce parasite drag (check form factors from parasite_drag agent). "
         "Secondary: reduce wing area (less induced drag at cruise) if stall is satisfied.",
         f"cruise_reward improves",
         {})

    # Check if there's a high-drag component
    if drag:
        comps = drag.get("components", [])
        worst = max(comps, key=lambda c: c.get("pct_total", 0), default=None)
        if worst and worst.get("FF", 1.0) > 1.5:
            _add(2, "cruise",
                 f"Streamline {worst['name']} (FF={worst.get('FF',0):.2f})",
                 f"{worst['name']} has form factor {worst.get('FF',0):.2f} (target ≤1.3) "
                 f"and contributes {worst.get('pct_total',0):.0f}% of parasite drag.",
                 "cruise_reward: increases",
                 {})

# ── Sort by priority ───────────────────────────────────────────────────────────
suggestions.sort(key=lambda s: s["priority"])

if not suggestions:
    suggestions.append({
        "priority": 99,
        "category": "none",
        "change": "No dominant issue identified — continue iterating for cruise optimization",
        "rationale": f"total_cost={total_cost:.2f} is already competitive.",
        "impact_estimate": "minor",
        "params": {},
    })

top = suggestions[0]

# ── Print ──────────────────────────────────────────────────────────────────────
print(f"\nIteration suggestion for: {model_stem}")
print(f"{'─'*60}")
print(f"  Current total cost:  {total_cost:.2f}")
print(f"    stall={stall_cost:.2f}  stability={stab_cost:.2f}  "
      f"mass={mass_cost:.2f}  cruise_reward={cruise_rew:.2f}")
print()
print(f"  RECOMMENDED CHANGE ({top['category'].upper()}):")
print(f"  {top['change']}")
print()
print(f"  Why: {top['rationale']}")
print(f"  Impact: {top['impact_estimate']}")
if top.get("params"):
    print(f"  Suggested param delta: {json.dumps(top['params'])}")

if len(suggestions) > 1:
    print(f"\n  Other changes (lower priority):")
    for s in suggestions[1:3]:
        print(f"    [{s['priority']}] {s['category']}: {s['change'][:80]}")

print(f"{'─'*60}\n")

# ── Write JSON ────────────────────────────────────────────────────────────────
out = {
    "model":        model_stem + ".vsp3",
    "timestamp":    datetime.now().isoformat(),
    "total_cost":   total_cost,
    "cost_breakdown": {
        "stall": stall_cost, "stability": stab_cost,
        "mass": mass_cost, "cruise_reward": cruise_rew,
    },
    "top_suggestion": top,
    "all_suggestions": suggestions,
}
out_path = OUT_DIR / f"{model_stem}_suggestion.json"
out_path.write_text(json.dumps(out, indent=2))
print(f"Wrote: {out_path.relative_to(PROJECT_ROOT)}")
