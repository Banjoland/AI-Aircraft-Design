"""
Design-space explorer for one-change aircraft iterations.

This agent reads the current parametric generator, recent score reports, and
project constraints, then proposes ranked geometry mutations. It does not edit
or generate OpenVSP models by itself; it produces a decision report that the
design agent can apply as the next single-aspect iteration.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
GENERATOR = PROJECT_ROOT / "DESIGN" / "AGENTS" / "baseline_generator" / "generate.py"
SCORES_DIR = PROJECT_ROOT / "EVALUATION" / "scores"
OUT_DIR = Path(__file__).resolve().parent / "out"

MTOW_KG = 218.0
MTOW_N = MTOW_KG * 9.81
RHO_SL = 1.225
VSTALL_SPEC = 21.0
CLMAX_VLM_FALLBACK = 1.21
SPAN_LIMIT = 15.0
EMPTY_MASS_SPEC = 110.0
SKIN_DENSITY = 6.0
STRUCTURE_FACTOR = 1.0
ENGINE_MASS_KG = 40.0
SYSTEMS_MASS_KG = 8.0


def load_p_dict(path: Path) -> dict[str, float]:
    tree = ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "P":
                    value = ast.literal_eval(node.value)
                    return {str(k): float(v) for k, v in value.items()}
    raise ValueError(f"Could not find P dict in {path}")


def score_reports() -> list[dict[str, Any]]:
    candidates = sorted(SCORES_DIR.glob("*_score.json"), key=lambda p: p.stat().st_mtime)
    reports = []
    for path in candidates:
        report = json.loads(path.read_text())
        inputs = report.get("inputs", {})
        if inputs.get("vstall_spec_ms") not in (None, VSTALL_SPEC):
            continue
        if inputs.get("empty_mass_spec_kg") not in (None, EMPTY_MASS_SPEC):
            continue
        report["_score_path"] = str(path)
        reports.append(report)
    return reports


def is_compliant(report: dict[str, Any]) -> bool:
    inputs = report.get("inputs", {})
    vstall = inputs.get("vstall_ms")
    empty_mass = inputs.get("empty_mass_kg")
    stable = inputs.get("longitudinal_stable")
    if vstall is None or empty_mass is None:
        return False
    return bool(vstall <= VSTALL_SPEC and empty_mass <= EMPTY_MASS_SPEC and stable)


def geom_metrics(p: dict[str, float], clmax: float = CLMAX_VLM_FALLBACK) -> dict[str, float]:
    wing_area = p["wing_span"] * 0.5 * (p["wing_root_chord"] + p["wing_tip_chord"])
    aspect_ratio = p["wing_span"] ** 2 / wing_area
    htail_area = p["htail_span"] * 0.5 * (p["htail_root_chord"] + p["htail_tip_chord"])
    vtail_area = p["vtail_height"] * 0.5 * (p["vtail_root_chord"] + p["vtail_tip_chord"])
    wing_mac = (2.0 / 3.0) * (
        (p["wing_root_chord"] ** 2 + p["wing_root_chord"] * p["wing_tip_chord"] + p["wing_tip_chord"] ** 2)
        / (p["wing_root_chord"] + p["wing_tip_chord"])
    )
    wing_ac_x = p["wing_x"] + 0.25 * wing_mac
    htail_mac = (2.0 / 3.0) * (
        (p["htail_root_chord"] ** 2 + p["htail_root_chord"] * p["htail_tip_chord"] + p["htail_tip_chord"] ** 2)
        / (p["htail_root_chord"] + p["htail_tip_chord"])
    )
    htail_ac_x = p["htail_x"] + 0.25 * htail_mac
    tail_arm = max(0.01, htail_ac_x - wing_ac_x)
    htail_volume = htail_area * tail_arm / (wing_area * wing_mac)
    vstall = math.sqrt(2.0 * MTOW_N / (RHO_SL * wing_area * clmax))

    wing_wetted = 2.0 * wing_area * 1.04
    htail_wetted = 2.0 * htail_area * 1.02
    vtail_wetted = 2.0 * vtail_area * 1.02
    fuse_perim = math.pi * 0.5 * (p["fuse_max_width"] + p["fuse_max_height"])
    fuse_wetted = fuse_perim * p["fuse_length"]
    wetted = wing_wetted + htail_wetted + vtail_wetted + fuse_wetted
    empty_mass = wetted * SKIN_DENSITY * STRUCTURE_FACTOR + ENGINE_MASS_KG + SYSTEMS_MASS_KG

    return {
        "wing_area_m2": wing_area,
        "aspect_ratio": aspect_ratio,
        "wing_mac_m": wing_mac,
        "htail_area_m2": htail_area,
        "tail_arm_m": tail_arm,
        "horizontal_tail_volume": htail_volume,
        "vstall_est_ms": vstall,
        "empty_mass_est_kg": empty_mass,
        "wetted_area_m2": wetted,
    }


@dataclass(frozen=True)
class Mutation:
    name: str
    feature: str
    rationale: str
    changes: dict[str, float]
    creativity: float
    risk: float

    def apply(self, p: dict[str, float]) -> dict[str, float]:
        out = dict(p)
        out.update(self.changes)
        return out


def candidate_library(p: dict[str, float]) -> list[Mutation]:
    short_tail_x = min(5.5, p["fuse_length"] - 1.0)
    return [
        Mutation(
            name="restore_short_body_with_larger_tail_chords",
            feature="Fuselage length and horizontal tail chord package",
            rationale=(
                "The log shows the 9.0 m fuselage regressed despite better nominal tail arm. "
                "Return to the lighter 6.5 m body and recover tail volume through chord."
            ),
            changes={
                "fuse_length": 6.5,
                "htail_x": short_tail_x,
                "vtail_x": 5.1,
                "htail_root_chord": 1.5,
                "htail_tip_chord": 1.1,
            },
            creativity=0.65,
            risk=0.35,
        ),
        Mutation(
            name="increase_horizontal_tail_chord",
            feature="Horizontal tail area",
            rationale=(
                "Current dominant penalty is stability cost. Increasing tail area is the "
                "lowest-disruption way to raise horizontal tail volume."
            ),
            changes={"htail_root_chord": 1.5, "htail_tip_chord": 1.1},
            creativity=0.35,
            risk=0.2,
        ),
        Mutation(
            name="move_main_wing_aft",
            feature="Wing longitudinal placement relative to CG",
            rationale=(
                "Moving the wing aft increases static margin and can strengthen Cm_alpha "
                "without increasing wetted area."
            ),
            changes={"wing_x": p["wing_x"] + 0.25},
            creativity=0.45,
            risk=0.45,
        ),
        Mutation(
            name="increase_washout",
            feature="Wing twist",
            rationale=(
                "More washout supports the specified root-first stall progression and may "
                "improve stall safety without changing span."
            ),
            changes={"wing_twist": p["wing_twist"] - 1.5},
            creativity=0.4,
            risk=0.3,
        ),
        Mutation(
            name="raise_wing_to_mid_mount",
            feature="Wing vertical placement",
            rationale=(
                "A mid-mounted wing may reduce fuselage interference in the VLM model and "
                "opens a cleaner cockpit sightline trade study."
            ),
            changes={"wing_z": 0.0},
            creativity=0.55,
            risk=0.55,
        ),
        Mutation(
            name="canard_stall_safety_probe",
            feature="Canard configuration",
            rationale=(
                "The specification explicitly encourages canard or tandem concepts for stall "
                "safety. This report flags it as a high-creativity branch requiring a new "
                "geometry generator before simulation."
            ),
            changes={},
            creativity=0.95,
            risk=0.85,
        ),
    ]


def score_mutation(base: dict[str, float], candidate: Mutation, best_score: dict[str, Any] | None) -> dict[str, Any]:
    new_p = candidate.apply(base)
    base_m = geom_metrics(base)
    new_m = geom_metrics(new_p)
    active_changes = {
        key: value for key, value in candidate.changes.items()
        if abs(base.get(key, float("nan")) - value) > 1e-9
    }

    score = 0.0
    reasons: list[str] = []

    vh_gain = new_m["horizontal_tail_volume"] - base_m["horizontal_tail_volume"]
    if vh_gain > 0:
        score += 4.0 * vh_gain
        reasons.append(f"tail volume increases by {vh_gain:.3f}")

    vstall_margin = VSTALL_SPEC - new_m["vstall_est_ms"]
    if vstall_margin >= 0:
        score += 0.25
        reasons.append(f"estimated stall remains below spec by {vstall_margin:.2f} m/s")
    else:
        score -= 2.0 * abs(vstall_margin)
        reasons.append(f"estimated stall exceeds spec by {abs(vstall_margin):.2f} m/s")

    mass_delta = new_m["empty_mass_est_kg"] - base_m["empty_mass_est_kg"]
    score -= max(0.0, mass_delta) / 120.0
    score += max(0.0, -mass_delta) / 80.0
    if abs(mass_delta) > 0.1:
        reasons.append(f"empty mass estimate changes by {mass_delta:+.1f} kg")

    ar_delta = new_m["aspect_ratio"] - base_m["aspect_ratio"]
    score += 0.15 * ar_delta
    if abs(ar_delta) > 0.01:
        reasons.append(f"aspect ratio changes by {ar_delta:+.2f}")

    if best_score:
        inputs = best_score.get("inputs", {})
        if inputs.get("vstall_ms", 99) <= VSTALL_SPEC:
            score += 0.15
            reasons.append("best tested aircraft already meets stall spec, so non-wing changes are attractive")

    score += candidate.creativity * 0.25
    score -= candidate.risk * 0.4

    violations = []
    if candidate.changes and not active_changes:
        score = -999.0
        reasons.append("candidate is already present in the current generator")
        violations.append("no parameter change from current generator")
    if new_p["wing_span"] > SPAN_LIMIT:
        violations.append(f"wingspan {new_p['wing_span']:.2f} m exceeds {SPAN_LIMIT:.2f} m")
    if new_m["empty_mass_est_kg"] > EMPTY_MASS_SPEC:
        violations.append(f"empty mass {new_m['empty_mass_est_kg']:.1f} kg exceeds {EMPTY_MASS_SPEC:.1f} kg")
    if new_m["vstall_est_ms"] > VSTALL_SPEC:
        violations.append(f"estimated stall {new_m['vstall_est_ms']:.2f} m/s exceeds {VSTALL_SPEC:.2f} m/s")

    if candidate.name == "canard_stall_safety_probe":
        violations.append("requires new OpenVSP canard/tandem generator before direct simulation")

    return {
        "name": candidate.name,
        "feature": candidate.feature,
        "rationale": candidate.rationale,
        "changes": active_changes,
        "all_requested_changes": candidate.changes,
        "heuristic_score": round(score, 4),
        "creativity": candidate.creativity,
        "risk": candidate.risk,
        "constraint_violations": violations,
        "estimated_metrics": {k: round(v, 4) for k, v in new_m.items()},
        "delta_metrics": {k: round(new_m[k] - base_m[k], 4) for k in new_m},
        "score_reasons": reasons,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank one-change aircraft design mutations.")
    parser.add_argument("--generator", type=Path, default=GENERATOR)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    p = load_p_dict(args.generator)
    reports = score_reports()
    latest_score = reports[-1] if reports else None
    best_score = min(reports, key=lambda item: item.get("total_cost", float("inf"))) if reports else None
    compliant_reports = [report for report in reports if is_compliant(report)]
    best_compliant_score = (
        min(compliant_reports, key=lambda item: item.get("total_cost", float("inf")))
        if compliant_reports else None
    )
    base_metrics = geom_metrics(p)
    reference_score = best_compliant_score or best_score
    candidates = [score_mutation(p, mutation, reference_score) for mutation in candidate_library(p)]
    candidates.sort(key=lambda item: item["heuristic_score"], reverse=True)

    report = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "generator": str(args.generator),
        "latest_score_file": latest_score.get("_score_path") if latest_score else None,
        "latest_model": latest_score.get("model") if latest_score else None,
        "latest_total_cost": latest_score.get("total_cost") if latest_score else None,
        "best_score_file": best_score.get("_score_path") if best_score else None,
        "best_model": best_score.get("model") if best_score else None,
        "best_total_cost": best_score.get("total_cost") if best_score else None,
        "best_is_compliant": is_compliant(best_score) if best_score else None,
        "best_compliant_score_file": best_compliant_score.get("_score_path") if best_compliant_score else None,
        "best_compliant_model": best_compliant_score.get("model") if best_compliant_score else None,
        "best_compliant_total_cost": best_compliant_score.get("total_cost") if best_compliant_score else None,
        "latest_is_best": (
            latest_score is not None
            and best_score is not None
            and latest_score.get("model") == best_score.get("model")
        ),
        "latest_is_best_compliant": (
            latest_score is not None
            and best_compliant_score is not None
            and latest_score.get("model") == best_compliant_score.get("model")
        ),
        "baseline_metrics": {k: round(v, 4) for k, v in base_metrics.items()},
        "recommended_next": candidates[0]["name"] if candidates else None,
        "candidates": candidates,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = args.out or OUT_DIR / "latest_design_space_report.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
