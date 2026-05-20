"""
Design report generator.

Reads all pipeline result JSONs for a model and writes a formatted Markdown
report to REPORTS/<stem>_report.md. Also prints a concise summary to stdout.

Covers:
  - Geometry summary (from AIRCRAFT/<stem>.json)
  - Aerodynamics (alpha/beta sweep)
  - Weight & mass spec
  - Static margin
  - Dynamic stability modes
  - Range & fuel budget
  - Cost breakdown vs spec
  - Iteration suggestion (if available)
  - Weight estimator breakdown (if available)
  - Constraint diagram findings (if available)
  - Tail sizing findings (if available)

Usage:
    python TOOLS/generate_report.py
    python TOOLS/generate_report.py AIRCRAFT/MODEL_xx.vsp3
    python TOOLS/generate_report.py --all   (generate reports for every scored model)
"""

import json
import math
import sys
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT   = Path(__file__).resolve().parents[1]
AIRCRAFT_DIR   = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR    = PROJECT_ROOT / "SIMULATION" / "results"
SCORES_DIR     = PROJECT_ROOT / "EVALUATION" / "scores"
REPORTS_DIR    = PROJECT_ROOT / "REPORTS"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DESIGN_AGENTS  = PROJECT_ROOT / "DESIGN" / "AGENTS"
WEIGHT_OUT     = DESIGN_AGENTS / "weight_estimator"
CONSTRAINT_OUT = DESIGN_AGENTS / "constraint_diagram"
TAIL_OUT       = DESIGN_AGENTS / "tail_sizing"
SUGGEST_OUT    = DESIGN_AGENTS / "iteration_suggester"

# ── Argument parsing ──────────────────────────────────────────────────────────
gen_all = "--all" in sys.argv
args    = [a for a in sys.argv[1:] if not a.startswith("--")]

if gen_all:
    stems = [p.stem.replace("_score", "") for p in sorted(SCORES_DIR.glob("*_score.json"),
                                                           key=lambda p: p.stat().st_mtime)]
    if not stems:
        stems = [p.stem for p in sorted(AIRCRAFT_DIR.glob("MODEL_*.json"),
                                        key=lambda p: p.stat().st_mtime)]
elif args:
    stems = [Path(args[0]).stem.replace(".vsp3", "")]
else:
    # Most recent scored or most recent geometry
    scored = sorted(SCORES_DIR.glob("*_score.json"), key=lambda p: p.stat().st_mtime)
    if scored:
        stems = [scored[-1].stem.replace("_score", "")]
    else:
        geoms = [p for p in sorted(AIRCRAFT_DIR.glob("MODEL_*.json"),
                                   key=lambda p: p.stat().st_mtime)
                 if "TEST" not in p.name.upper()]
        if not geoms:
            print("ERROR: no model found.", file=sys.stderr)
            sys.exit(1)
        stems = [geoms[-1].stem]

# ── Helpers ────────────────────────────────────────────────────────────────────
def _load(path):
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}

def _fmt(val, fmt=".2f", missing="—"):
    if val is None:
        return missing
    try:
        return format(float(val), fmt)
    except (TypeError, ValueError):
        return str(val)

def _ok(flag, yes="PASS", no="FAIL", missing="—"):
    if flag is None:
        return missing
    return yes if flag else no

def _pct(val, missing="—"):
    if val is None:
        return missing
    return f"{float(val)*100:.1f}%"

# ── Spec reference values ──────────────────────────────────────────────────────
SPEC_VSTALL_MS    = 17.9    # m/s (40 mph) — SPECIFICATION.md
SPEC_VCRUISE_MS   = 50.0    # m/s (180 km/hr, 97 kt) — SPECIFICATION.md
SPEC_EMPTY_KG     = 110.0   # kg empty mass limit
SPEC_RANGE_KM     = 1667.0  # km (900 nm) — SPECIFICATION.md
SPEC_MTOW_KG      = 295.0   # kg MTOW — SPECIFICATION.md


def _generate_report(stem):
    # ── Load all result files ─────────────────────────────────────────────────
    geom    = _load(AIRCRAFT_DIR / f"{stem}.json")
    alpha   = _load(RESULTS_DIR  / f"{stem}_alpha_sweep.json")
    beta    = _load(RESULTS_DIR  / f"{stem}_beta_sweep.json")
    drag    = _load(RESULTS_DIR  / f"{stem}_parasite_drag.json")
    inert   = _load(RESULTS_DIR  / f"{stem}_inertia.json")
    dynstab = _load(RESULTS_DIR  / f"{stem}_dynamic_stability.json")
    rng     = _load(RESULTS_DIR  / f"{stem}_range.json")
    sm      = _load(RESULTS_DIR  / f"{stem}_static_margin.json")
    score   = _load(SCORES_DIR   / f"{stem}_score.json")
    suggest = _load(SUGGEST_OUT  / f"{stem}_suggestion.json")
    weight  = _load(WEIGHT_OUT   / f"{stem}_weight.json")
    constr  = _load(CONSTRAINT_OUT / "constraint_diagram.json")
    tail_sz = _load(TAIL_OUT     / f"{stem}_tail_size.json")

    has_geom    = bool(geom)
    has_alpha   = bool(alpha)
    has_score   = bool(score)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Build Markdown ─────────────────────────────────────────────────────────
    lines = []
    def H(n, text):  lines.append(f"{'#'*n} {text}\n")
    def P(text=""):  lines.append(text + "\n")
    def T(row):      lines.append("| " + " | ".join(str(c) for c in row) + " |")
    def TH(*cols):
        T(cols)
        lines.append("|" + "|".join(["---"] * len(cols)) + "|")

    H(1, f"Design Report: {stem}")
    P(f"*Generated {now}*")
    P()

    # ── Overall score ──────────────────────────────────────────────────────────
    H(2, "Score Summary")
    total  = score.get("total_cost")
    stall_c = score.get("stall_cost",   0.0)
    stab_c  = score.get("stability_cost", 0.0)
    mass_c  = score.get("mass_cost",    0.0)
    cr_rew  = score.get("cruise_reward",0.0)

    TH("Metric", "Value", "Target / Note")
    T(["Total cost",      _fmt(total,  ".3f"),  "lower = better"])
    T(["Stall cost",      _fmt(stall_c,".3f"),  f"0 = V_stall <= {SPEC_VSTALL_MS} m/s"])
    T(["Stability cost",  _fmt(stab_c, ".3f"),  "1/|lambda_min|; <5 = good"])
    T(["Mass cost",       _fmt(mass_c, ".3f"),  "0 = empty <= 110 kg"])
    T(["Cruise reward",   _fmt(cr_rew, ".3f"),  "subtracted; higher = better"])
    P()

    # ── Geometry ──────────────────────────────────────────────────────────────
    if has_geom:
        H(2, "Geometry")
        TH("Parameter", "Value")
        T(["Fuselage length",   f"{_fmt(geom.get('total_length_m'), '.2f')} m"])
        T(["Wing span",         f"{_fmt(geom.get('wing_span_m'),    '.2f')} m"])
        T(["Wing area",         f"{_fmt(geom.get('wing_area_m2'),   '.3f')} m²"])
        T(["Wing MAC",          f"{_fmt(geom.get('wing_mac_m'),     '.3f')} m"])
        T(["Aspect ratio",      _fmt(geom.get('wing_span_m', 9.8)**2 /
                                     max(geom.get('wing_area_m2', 4.2), 0.1), ".1f")])
        T(["Wing taper",        _fmt(geom.get('wing_taper_ratio'), ".3f")])
        T(["H-tail span",       f"{_fmt(geom.get('htail_span_m'),  '.2f')} m"])
        T(["V-tail height",     f"{_fmt(geom.get('vtail_height'),  '.2f')} m"])
        T(["Total wetted area", f"{_fmt(geom.get('total_wetted_m2'), '.2f')} m²"])
        T(["Fuselage wetted",   f"{_fmt(geom.get('fuse_wetted_m2'), '.2f')} m²"])
        T(["x_CG estimate",     f"{_fmt(geom.get('x_cg_m'),        '.3f')} m from nose"])
        _em = (weight.get("empty_mass_kg") if weight else None) or geom.get("empty_mass_est_kg")
        T(["Empty mass (component est.)", f"{_fmt(_em, '.1f')} kg"])
        T(["Tail vol. coeff V_H", _fmt(geom.get('V_H'), ".3f")])
        P()

    # ── Aerodynamics ──────────────────────────────────────────────────────────
    if has_alpha:
        H(2, "Aerodynamics (Alpha Sweep)")
        TH("Parameter", "Value", "Spec / Note")
        vstall = alpha.get("vstall_est_ms")
        vcruise = alpha.get("vcruise_75pct_ms")
        T(["V_stall",    f"{_fmt(vstall,  '.2f')} m/s",
           f"spec <= {SPEC_VSTALL_MS} m/s  [{_ok(alpha.get('vstall_ok'))}]"])
        T(["V_cruise (75% pwr)",  f"{_fmt(vcruise, '.2f')} m/s",
           f"spec {SPEC_VCRUISE_MS} m/s  "
           f"[{'PASS' if vcruise and vcruise >= SPEC_VCRUISE_MS else 'FAIL'}]"])
        T(["L/D at cruise",  _fmt(alpha.get("LD_cruise"), ".2f"), "higher = better"])
        T(["CL_cruise",      _fmt(alpha.get("CL_cruise"), ".4f"), ""])
        T(["CD_cruise",      _fmt(alpha.get("CD_cruise"), ".5f"), ""])
        T(["CL_alpha",       f"{_fmt(alpha.get('CL_alpha_per_deg'), '.4f')} /deg", ""])
        T(["Cm_alpha",       f"{_fmt(alpha.get('Cm_alpha_per_deg'), '.5f')} /deg",
           "< 0 = stable"])
        T(["Longitudinally stable", str(alpha.get("longitudinal_stable", "—")), ""])
        P()

        # Beta sweep / lateral
        if beta:
            H(3, "Lateral Stability Derivatives (Beta Sweep)")
            TH("Derivative", "Value", "Sign for stability")
            cn = beta.get("Cn_beta")
            T(["CY_beta", _fmt(beta.get("CY_beta"), ".5f"), "< 0"])
            T(["Cl_beta (dihedral effect)", _fmt(beta.get("Cl_beta"), ".5f"), "< 0"])
            T(["Cn_beta (weathercock)",
               f"{_fmt(cn, '.5f')} {'[UNSTABLE]' if cn is not None and cn < 0 else '[OK]'}",
               "> 0"])
            T(["Directionally stable", str(beta.get("directionally_stable", "—")), ""])
            P()

    # ── Static margin ──────────────────────────────────────────────────────────
    if sm:
        H(2, "Static Margin")
        sm_data = sm.get("static_margin", {})
        TH("Parameter", "Value")
        T(["SM (fraction MAC)", _fmt(sm_data.get("SM"), ".4f")])
        T(["SM (%MAC)",         f"{_fmt(sm_data.get('SM_pct_mac'), '.1f')} %"])
        T(["x_NP",              f"{_fmt(sm_data.get('x_NP_m'),    '.3f')} m"])
        T(["x_CG",              f"{_fmt(sm_data.get('x_CG_m'),    '.3f')} m"])
        T(["Status",            sm_data.get("SM_status", "—")])
        cg_lim = sm.get("cg_limits", {})
        T(["CG fwd limit",      f"{_fmt(cg_lim.get('cg_fwd_limit_m'), '.3f')} m"])
        T(["CG aft limit",      f"{_fmt(cg_lim.get('cg_aft_limit_m'), '.3f')} m"])
        P()

    # ── Dynamic stability ─────────────────────────────────────────────────────
    if dynstab:
        H(2, "Dynamic Stability")
        lon = dynstab.get("longitudinal", {})
        lat = dynstab.get("lateral", {})

        H(3, "Longitudinal Modes")
        TH("Mode", "Damping ζ", "Freq ω_n (rad/s)", "T_half (s)", "Status")
        for mode in lon.get("modes", []):
            name   = mode.get("name", "?")
            zeta   = _fmt(mode.get("zeta"),    ".4f")
            wn     = _fmt(mode.get("omega_n"), ".3f")
            thalf  = _fmt(mode.get("T_half"),  ".2f")
            stable = "stable" if mode.get("sigma", 1) < 0 else "UNSTABLE"
            T([name, zeta, wn, thalf, stable])
        P()

        H(3, "Lateral Modes")
        TH("Mode", "Type", "Damping ζ / σ", "Period / T_half (s)", "Status")
        for mode in lat.get("modes", []):
            name   = mode.get("name", "?")
            typ    = "oscillatory" if mode.get("omega_d", 0) > 0.01 else "aperiodic"
            if typ == "oscillatory":
                damp  = _fmt(mode.get("zeta"), ".4f")
                per   = _fmt(mode.get("period_s"), ".2f") + "s period"
            else:
                damp  = _fmt(mode.get("sigma"), ".4f") + " /s"
                per   = _fmt(mode.get("T_half"), ".2f") + "s T½"
            stable = "stable" if mode.get("sigma", 1) < 0 else "UNSTABLE"
            T([name, typ, damp, per, stable])
        P()

    # ── Range & fuel ──────────────────────────────────────────────────────────
    if rng:
        H(2, "Range and Fuel Budget")
        fuel_d = rng.get("fuel", {})
        rng_d  = rng.get("range", {})
        clb_d  = rng.get("climb", {})
        cmp_d  = rng.get("compliance", {})
        TH("Parameter", "Value", "Spec / Note")
        T(["Fuel available",   f"{_fmt(fuel_d.get('fuel_avail_kg'), '.2f')} kg", "MTOW - empty - useful"])
        T(["Fuel available",   f"{_fmt(fuel_d.get('fuel_avail_L'),  '.1f')} L",  ""])
        T(["Endurance",        f"{_fmt(rng_d.get('endurance_hr'),   '.2f')} hr", ""])
        T(["Range",            f"{_fmt(rng_d.get('range_actual_km'), '.0f')} km",
           f"spec {SPEC_RANGE_KM:.0f} km  [{_ok(cmp_d.get('range_ok'))}]"])
        T(["Best climb speed", f"{_fmt(clb_d.get('best_climb_speed_ms'), '.1f')} m/s", ""])
        T(["Rate of climb",    f"{_fmt(clb_d.get('best_RC_ms'),   '.2f')} m/s",
           f"({_fmt(clb_d.get('best_RC_ms', 0) and clb_d.get('best_RC_ms')*196.85, '.0f')} ft/min)"])
        T(["Service ceiling",  f"{_fmt(clb_d.get('service_ceiling_m'), '.0f')} m", ""])
        P()

    # ── Parasite drag breakdown ────────────────────────────────────────────────
    if drag and drag.get("components"):
        H(2, "Parasite Drag Breakdown")
        TH("Component", "CD0_comp", "% total", "FF", "wetted (m²)")
        comps = sorted(drag.get("components", []),
                       key=lambda c: c.get("pct_total", 0), reverse=True)
        for c in comps:
            T([c.get("name", "?"),
               _fmt(c.get("CD0_comp"),   ".6f"),
               f"{_fmt(c.get('pct_total'), '.1f')}%",
               _fmt(c.get("FF"),          ".3f"),
               _fmt(c.get("S_wet_m2"),   ".3f")])
        T(["**TOTAL**", _fmt(drag.get("CD0_total"), ".6f"), "100%", "", ""])
        P()

    # ── Inertia ────────────────────────────────────────────────────────────────
    if inert:
        H(2, "Mass Distribution & Inertia")
        TH("Parameter", "Value")
        T(["Total mass (est.)", f"{_fmt(inert.get('total_mass_kg'), '.2f')} kg"])
        T(["x_CG",             f"{_fmt(inert.get('cg_x_m'),       '.3f')} m"])
        T(["Ixx (roll)",       f"{_fmt(inert.get('Ixx_kgm2'),     '.2f')} kg·m²"])
        T(["Iyy (pitch)",      f"{_fmt(inert.get('Iyy_kgm2'),     '.2f')} kg·m²"])
        T(["Izz (yaw)",        f"{_fmt(inert.get('Izz_kgm2'),     '.2f')} kg·m²"])
        P()

    # ── Weight estimator breakdown ─────────────────────────────────────────────
    if weight:
        H(2, "Weight Estimate (Component Build-Up)")
        inp = weight.get("inputs", {})
        P(f"Material: **{inp.get('material', '—')}**  |  "
          f"Engine: {inp.get('engine_type', '—')} @ {_fmt(inp.get('engine_hp'), '.0f')} hp")
        TH("Component", "Mass (kg)")
        comps = weight.get("components", {})
        labels = {
            "wing":           "Wing structure",
            "fuselage":       "Fuselage",
            "htail":          "Horizontal tail",
            "vtail":          "Vertical tail",
            "landing_gear":   "Landing gear",
            "engine":         "Engine (bare)",
            "engine_systems": "Engine systems",
            "propeller":      "Propeller",
            "avionics":       "Avionics + electrical",
            "controls":       "Flight controls",
            "fuel_system":    "Fuel system",
        }
        for key, label in labels.items():
            if key in comps:
                T([label, _fmt(comps[key], ".2f")])
        T(["**Empty mass total**", f"**{_fmt(weight.get('empty_mass_kg'), '.2f')}**"])
        T(["Spec limit",           f"{SPEC_EMPTY_KG:.1f}"])
        T(["Spec margin",          f"{_fmt(weight.get('spec_margin_kg'), '.2f')} kg"])
        T(["Fuel capacity at MTOW",f"{_fmt(weight.get('fuel_capacity_kg'), '.2f')} kg"])
        spec_ok = weight.get("spec_ok")
        P()
        if spec_ok is False:
            P(f"> **WARNING:** Empty mass exceeds {SPEC_EMPTY_KG:.0f} kg spec by "
              f"{_fmt(-weight.get('spec_margin_kg', 0), '.1f')} kg.")
        P()

    # ── Tail sizing ────────────────────────────────────────────────────────────
    if tail_sz:
        H(2, "Tail Sizing Assessment")
        ht = tail_sz.get("htail", {})
        vt = tail_sz.get("vtail", {})
        geo = tail_sz.get("geometry", {})
        TH("Parameter", "Current", "Required (target SM=15%)")
        T(["S_h (m²)",     _fmt(ht.get("S_h_current_m2"), ".4f"),
                           _fmt(ht.get("S_h_req_target_m2"), ".4f")])
        T(["V_H",          _fmt(ht.get("V_H_current"), ".4f"),
                           _fmt(ht.get("V_H_req_target"), ".4f")])
        T(["SM (%MAC)",    f"{_fmt(ht.get('SM_current_pct'), '.1f')}%", "5–25% target"])
        T(["S_v (m²)",     _fmt(vt.get("S_v_current_m2"), ".4f"),
                           _fmt(vt.get("S_v_required_m2"), ".4f")])
        T(["V_V",          _fmt(vt.get("V_V_current"), ".5f"),
                           _fmt(vt.get("V_V_required"), ".5f")])
        T(["Cn_beta",      _fmt(vt.get("Cn_beta_current"), ".5f"), ">= 0.05 /rad"])
        T(["Htail OK",     _ok(ht.get("htail_ok")), ""])
        T(["Vtail OK",     _ok(vt.get("vtail_ok")), ""])
        P()

    # ── Constraint diagram ─────────────────────────────────────────────────────
    if constr:
        H(2, "Constraint Diagram")
        TH("Parameter", "Value")
        T(["Stall-limit W/S",     f"{_fmt(constr.get('stall_limit_WS_Nm2'), '.0f')} N/m²"])
        T(["T/W required cruise", _fmt(constr.get("TW_req_cruise_at_stall"), ".5f")])
        T(["T/W available",       _fmt(constr.get("TW_avail_cruise"),        ".5f")])
        T(["Cruise deficit",      f"{_fmt(constr.get('cruise_deficit_hp'), '.1f')} hp"])
        T(["Climb deficit",       f"{_fmt(constr.get('climb_deficit_hp'),  '.1f')} hp"])
        T(["Design feasible",     _ok(constr.get("design_feasible"))])
        if constr.get("cruise_deficit_hp", 0) > 0:
            P(f"> **Note:** Engine is {_fmt(constr.get('cruise_deficit_hp'), '.1f')} hp "
              f"short for cruise at stall-limited wing loading.")
        P()

    # ── Iteration suggestion ───────────────────────────────────────────────────
    if suggest:
        H(2, "Iteration Suggestion")
        top = suggest.get("top_suggestion", {})
        P(f"**Priority change ({top.get('category', '?').upper()}):** {top.get('change', '—')}")
        P()
        P(f"*Why:* {top.get('rationale', '—')}")
        P()
        P(f"*Estimated impact:* {top.get('impact_estimate', '—')}")
        params = top.get("params", {})
        if params:
            P(f"*Parameter delta:* `{json.dumps(params)}`")
        P()
        others = suggest.get("all_suggestions", [])[1:3]
        if others:
            H(3, "Other changes (lower priority)")
            for s in others:
                P(f"- [{s['priority']}] **{s['category']}**: {s['change'][:120]}")
        P()

    # ── Footer ──────────────────────────────────────────────────────────────────
    P("---")
    P(f"*Report generated by TOOLS/generate_report.py — {now}*")

    # ── Write to file ──────────────────────────────────────────────────────────
    report_text = "\n".join(lines)
    out_path = REPORTS_DIR / f"{stem}_report.md"
    out_path.write_text(report_text, encoding="utf-8")
    return out_path


# ── Main loop ──────────────────────────────────────────────────────────────────
for stem in stems:
    out_path = _generate_report(stem)
    print(f"Report: {out_path.relative_to(PROJECT_ROOT)}")

print(f"\nReports written to REPORTS/")
