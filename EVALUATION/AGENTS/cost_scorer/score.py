"""
Cost-function evaluation agent.

Reads the most recent alpha-sweep results from SIMULATION/results/,
computes the three cost-function components defined in EVALUATION/COST FUNCTION.md,
and writes a score report to EVALUATION/scores/<model_stem>_score.json.

Prints a JSON summary to stdout.

Run via openvsp-python (or plain python — no OpenVSP API needed):
    python score.py
    python score.py path/to/MODEL_xx_alpha_sweep.json
"""

import json
import math
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SIM_RESULTS  = PROJECT_ROOT / "SIMULATION" / "results"
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
EVAL_SCORES  = PROJECT_ROOT / "EVALUATION" / "scores"
EVAL_SCORES.mkdir(parents=True, exist_ok=True)

# ── Cost-function reference values (EVALUATION/COST FUNCTION.md) ───────────────
VSTALL_SPEC   = 17.9    # m/s - stall speed limit from SPECIFICATION.md (40 mph)
VCRUISE_REF   = 50.0    # m/s - cruise speed target from SPECIFICATION.md (180 km/hr)
STABILITY_MAX = 100.0   # score for unstable / unconfirmed aircraft
EMPTY_MASS_SPEC = 110.0 # kg - empty mass limit from SPECIFICATION.md

# ── Find simulation results ────────────────────────────────────────────────────
if len(sys.argv) > 1:
    sim_path = Path(sys.argv[1]).resolve()
else:
    candidates = sorted(SIM_RESULTS.glob("*_alpha_sweep.json"),
                        key=lambda p: p.stat().st_mtime)
    if not candidates:
        print("ERROR: no *_alpha_sweep.json in SIMULATION/results/", file=sys.stderr)
        sys.exit(1)
    sim_path = candidates[-1]

sim = json.loads(sim_path.read_text())
print(f"Scoring: {sim_path.name}", file=sys.stderr)

# ── Extract metrics ────────────────────────────────────────────────────────────
vstall   = sim.get("vstall_est_ms",      99.0)
vcruise  = sim.get("vcruise_75pct_ms",    0.0)
cm_alpha = sim.get("Cm_alpha_per_deg",    0.0)  # /deg; 0 = unresolved
stable   = sim.get("longitudinal_stable", False)

# ── Read empty mass — prefer weight_estimator result over generate.py estimate ──
model_name   = sim.get("model", sim_path.stem.replace("_alpha_sweep", ""))
model_stem   = Path(model_name).stem  # strip .vsp3 if present
companion    = AIRCRAFT_DIR / f"{model_stem}.json"
empty_mass   = None
# 1. Try weight estimator (component build-up, most accurate)
WE_DIR    = PROJECT_ROOT / "DESIGN" / "AGENTS" / "weight_estimator"
we_path   = WE_DIR / f"{model_stem}_weight.json"
if we_path.exists():
    we = json.loads(we_path.read_text())
    empty_mass = we.get("empty_mass_kg")
# 2. Fallback to companion JSON skin-based estimate
if empty_mass is None and companion.exists():
    geom = json.loads(companion.read_text())
    empty_mass = geom.get("empty_mass_est_kg")

# ── Try to read dynamic stability results (preferred over Cm_alpha proxy) ──────
dyn_stability_path = SIM_RESULTS / f"{model_stem}_dynamic_stability.json"
dyn_stability      = json.loads(dyn_stability_path.read_text()) if dyn_stability_path.exists() else None
if empty_mass is None:
    print(f"WARN: no companion geometry JSON for {model_stem}; mass cost set to max", file=sys.stderr)

# ── Cost function 1: Stall speed ─────────────────────────────────────────────
if vstall <= VSTALL_SPEC:
    stall_cost = 0.0
    stall_note = f"V_stall {vstall:.2f} <= {VSTALL_SPEC} m/s - no penalty"
else:
    stall_cost = (vstall - VSTALL_SPEC) ** 2
    stall_note = f"V_stall {vstall:.2f} > {VSTALL_SPEC} m/s - penalty {stall_cost:.3f}"

# ── Cost function 2: Stability ────────────────────────────────────────────────
# Preferred: use dynamic stability eigenvalue distance from origin (s-plane).
# Fallback: use static Cm_alpha as proxy when dynamic stability results unavailable.
if dyn_stability is not None:
    dyn_status = dyn_stability.get("stability_status", "UNSTABLE")
    min_dist   = dyn_stability.get("min_eigenvalue_dist", 0.0)
    if dyn_status == "stable" and min_dist > 1e-9:
        stability_cost = 1.0 / min_dist
        stability_note = (
            f"Dynamic stability: all modes stable. "
            f"min eigenvalue dist = {min_dist:.4f} rad/s → "
            f"cost = 1/{min_dist:.4f} = {stability_cost:.4f}"
        )
    else:
        stability_cost = STABILITY_MAX
        stability_note = (
            f"Dynamic stability: {dyn_status} (min_dist={min_dist:.4f}). "
            f"Assigning maximum penalty {STABILITY_MAX}."
        )
elif not stable or cm_alpha == 0.0:
    stability_cost = STABILITY_MAX
    stability_note = ("Cm_alpha unresolved or aircraft unstable (no dynamic stability results). "
                      f"Assigning maximum penalty {STABILITY_MAX}")
else:
    # Cm_alpha proxy: convert /deg to /rad; cost = 1 / |Cm_alpha_rad|
    cm_alpha_rad = abs(cm_alpha) * (180.0 / math.pi)
    stability_cost = 1.0 / cm_alpha_rad
    stability_note = (f"Cm_alpha proxy (no dynamic stability results): "
                      f"{cm_alpha:.5f}/deg → {cm_alpha_rad:.4f}/rad; "
                      f"cost = {stability_cost:.4f}")

# ── Cost function 3: Cruise speed (reward — subtracted) ──────────────────────
cruise_reward_raw = math.exp(3.0 * (vcruise - VCRUISE_REF) / VCRUISE_REF)
cruise_reward     = min(cruise_reward_raw, 100.0)
cruise_note       = (f"V_cruise {vcruise:.2f} m/s vs ref {VCRUISE_REF} m/s - "
                     f"reward {cruise_reward:.4f}")

# ── Cost function 4: Empty mass ───────────────────────────────────────────────
if empty_mass is None:
    mass_cost = STABILITY_MAX   # same max penalty as stability when unresolved
    mass_note = "Empty mass unknown - assigning maximum penalty"
else:
    mass_cost = math.exp(10.0 * (empty_mass - EMPTY_MASS_SPEC) / EMPTY_MASS_SPEC) - 1.0
    mass_note = (f"empty_mass={empty_mass:.1f} kg vs spec {EMPTY_MASS_SPEC:.0f} kg - "
                 f"cost {mass_cost:.4f}")

# ── Total cost ────────────────────────────────────────────────────────────────
total_cost = stall_cost + stability_cost + mass_cost - cruise_reward

# ── Report ────────────────────────────────────────────────────────────────────
report = {
    "model":            sim.get("model", sim_path.stem.replace("_alpha_sweep", "")),
    "sim_file":         sim_path.name,

    "stall_cost":       round(stall_cost,      4),
    "stall_note":       stall_note,

    "stability_cost":   round(stability_cost,  4),
    "stability_note":   stability_note,

    "cruise_reward":    round(cruise_reward,   4),
    "cruise_note":      cruise_note,

    "mass_cost":        round(mass_cost,       4),
    "mass_note":        mass_note,

    "total_cost":       round(total_cost,      4),

    "stability_source": "dynamic_eigenvalue" if dyn_stability else "cm_alpha_proxy",

    "inputs": {
        "vstall_ms":              vstall,
        "vstall_spec_ms":         VSTALL_SPEC,
        "vcruise_ms":             vcruise,
        "vcruise_ref_ms":         VCRUISE_REF,
        "cm_alpha_per_deg":       cm_alpha,
        "longitudinal_stable":    stable,
        "empty_mass_kg":          empty_mass,
        "empty_mass_spec_kg":     EMPTY_MASS_SPEC,
        "dyn_stability_status":   dyn_stability.get("stability_status") if dyn_stability else None,
        "dyn_min_eigenvalue_dist": dyn_stability.get("min_eigenvalue_dist") if dyn_stability else None,
    },

    "summary": (
        f"total={total_cost:.2f}  "
        f"(stall={stall_cost:.2f}  stability={stability_cost:.2f}  "
        f"mass={mass_cost:.2f}  cruise_reward={cruise_reward:.2f})"
    ),
}

out_file = EVAL_SCORES / f"{sim_path.stem.replace('_alpha_sweep', '')}_score.json"
out_file.write_text(json.dumps(report, indent=2))

print(json.dumps(report, indent=2))
