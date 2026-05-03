"""
Batch aircraft designer.

Generates several explicit geometry variants with baseline_generator, runs the
alpha_sweep simulation for each model, scores each result, and writes a compact
ranking report. This is meant for broad exploration after a specification change.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = Path(__file__).resolve().parent / "out"
CONFIG_DIR = OUT_DIR / "configs"
REPORT_PATH = OUT_DIR / "latest_batch_report.json"
GENERATOR = PROJECT_ROOT / "DESIGN" / "AGENTS" / "baseline_generator" / "generate.py"
SWEEP = PROJECT_ROOT / "SIMULATION" / "AGENTS" / "alpha_sweep" / "run_sweep.py"
SCORER = PROJECT_ROOT / "EVALUATION" / "AGENTS" / "cost_scorer" / "score.py"

sys.path.insert(0, str(PROJECT_ROOT))
from TOOLS.openvsp_runner.runner import run  # noqa: E402


VARIANTS = [
    {
        "name": "ultralight_high_ar_baseline",
        "overrides": {},
    },
    {
        "name": "long_span_low_chord",
        "overrides": {
            "wing_span": 11.2,
            "wing_root_chord": 0.74,
            "wing_tip_chord": 0.48,
            "wing_twist": -3.5,
            "htail_span": 2.8,
            "htail_root_chord": 0.44,
            "htail_tip_chord": 0.28,
        },
    },
    {
        "name": "max_efficiency_sailplane_like",
        "overrides": {
            "wing_span": 13.5,
            "wing_root_chord": 0.62,
            "wing_tip_chord": 0.40,
            "wing_sweep": 0.0,
            "wing_dihedral": 3.0,
            "wing_twist": -3.0,
            "htail_span": 3.1,
            "htail_root_chord": 0.42,
            "htail_tip_chord": 0.26,
        },
    },
    {
        "name": "compact_low_mass",
        "overrides": {
            "fuse_length": 3.9,
            "fuse_max_width": 0.88,
            "fuse_max_height": 1.08,
            "wing_span": 8.6,
            "wing_root_chord": 0.74,
            "wing_tip_chord": 0.46,
            "wing_twist": -2.0,
            "htail_span": 2.2,
            "htail_root_chord": 0.40,
            "htail_tip_chord": 0.24,
            "htail_x": 3.25,
            "vtail_height": 0.78,
            "vtail_root_chord": 0.46,
            "vtail_tip_chord": 0.24,
            "vtail_x": 3.1,
        },
    },
    {
        "name": "stall_margin_broad_wing",
        "overrides": {
            "wing_span": 9.4,
            "wing_root_chord": 0.98,
            "wing_tip_chord": 0.62,
            "wing_twist": -4.0,
            "htail_span": 2.7,
            "htail_root_chord": 0.48,
            "htail_tip_chord": 0.32,
        },
    },
    {
        "name": "tiny_boundary_probe",
        "overrides": {
            "fuse_length": 3.7,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 8.0,
            "wing_root_chord": 0.66,
            "wing_tip_chord": 0.40,
            "wing_twist": -1.5,
            "htail_span": 2.0,
            "htail_root_chord": 0.34,
            "htail_tip_chord": 0.22,
            "htail_x": 3.05,
            "vtail_height": 0.70,
            "vtail_root_chord": 0.40,
            "vtail_tip_chord": 0.20,
            "vtail_x": 2.95,
        },
    },
    {
        "name": "drag_trim_span_9_area_5",
        "overrides": {
            "fuse_length": 3.85,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.0,
            "wing_root_chord": 0.68,
            "wing_tip_chord": 0.43,
            "wing_sweep": 1.0,
            "wing_dihedral": 3.0,
            "wing_twist": -2.5,
            "htail_span": 2.2,
            "htail_root_chord": 0.36,
            "htail_tip_chord": 0.23,
            "htail_x": 3.2,
            "vtail_height": 0.74,
            "vtail_root_chord": 0.42,
            "vtail_tip_chord": 0.21,
            "vtail_x": 3.05,
        },
    },
    {
        "name": "drag_trim_span_9p6_area_5p1",
        "overrides": {
            "fuse_length": 3.9,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.6,
            "wing_root_chord": 0.66,
            "wing_tip_chord": 0.40,
            "wing_sweep": 0.0,
            "wing_dihedral": 3.0,
            "wing_twist": -2.5,
            "htail_span": 2.25,
            "htail_root_chord": 0.36,
            "htail_tip_chord": 0.23,
            "htail_x": 3.25,
            "vtail_height": 0.74,
            "vtail_root_chord": 0.42,
            "vtail_tip_chord": 0.21,
            "vtail_x": 3.1,
        },
    },
    {
        "name": "drag_trim_span_10_area_5p2",
        "overrides": {
            "fuse_length": 3.95,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 10.0,
            "wing_root_chord": 0.64,
            "wing_tip_chord": 0.40,
            "wing_sweep": 0.0,
            "wing_dihedral": 3.0,
            "wing_twist": -2.75,
            "htail_span": 2.25,
            "htail_root_chord": 0.36,
            "htail_tip_chord": 0.23,
            "htail_x": 3.3,
            "vtail_height": 0.74,
            "vtail_root_chord": 0.42,
            "vtail_tip_chord": 0.21,
            "vtail_x": 3.15,
        },
    },
    {
        "name": "drag_trim_low_tail",
        "overrides": {
            "fuse_length": 3.8,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.3,
            "wing_root_chord": 0.66,
            "wing_tip_chord": 0.40,
            "wing_sweep": 0.0,
            "wing_dihedral": 3.0,
            "wing_twist": -2.0,
            "htail_span": 1.85,
            "htail_root_chord": 0.32,
            "htail_tip_chord": 0.20,
            "htail_x": 3.15,
            "vtail_height": 0.66,
            "vtail_root_chord": 0.36,
            "vtail_tip_chord": 0.18,
            "vtail_x": 3.0,
        },
    },
    {
        "name": "drag_trim_stall_margin",
        "overrides": {
            "fuse_length": 3.9,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.4,
            "wing_root_chord": 0.72,
            "wing_tip_chord": 0.45,
            "wing_sweep": 0.0,
            "wing_dihedral": 3.0,
            "wing_twist": -2.75,
            "htail_span": 2.15,
            "htail_root_chord": 0.34,
            "htail_tip_chord": 0.22,
            "htail_x": 3.25,
            "vtail_height": 0.72,
            "vtail_root_chord": 0.40,
            "vtail_tip_chord": 0.20,
            "vtail_x": 3.1,
        },
    },
    {
        "name": "drag_trim_long_clean",
        "overrides": {
            "fuse_length": 4.05,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 10.8,
            "wing_root_chord": 0.60,
            "wing_tip_chord": 0.36,
            "wing_sweep": 0.0,
            "wing_dihedral": 2.5,
            "wing_twist": -2.5,
            "htail_span": 2.35,
            "htail_root_chord": 0.36,
            "htail_tip_chord": 0.22,
            "htail_x": 3.45,
            "vtail_height": 0.74,
            "vtail_root_chord": 0.40,
            "vtail_tip_chord": 0.20,
            "vtail_x": 3.3,
        },
    },
]

DRAG_REFINEMENT_VARIANTS = [
    {
        "name": "drag_refine_9p2_area_5p15",
        "overrides": {
            "fuse_length": 3.85,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.2,
            "wing_root_chord": 0.69,
            "wing_tip_chord": 0.43,
            "wing_sweep": 0.5,
            "wing_dihedral": 3.0,
            "wing_twist": -2.5,
            "htail_span": 2.12,
            "htail_root_chord": 0.34,
            "htail_tip_chord": 0.22,
            "htail_x": 3.22,
            "vtail_height": 0.70,
            "vtail_root_chord": 0.38,
            "vtail_tip_chord": 0.19,
            "vtail_x": 3.05,
        },
    },
    {
        "name": "drag_refine_9p4_area_5p17",
        "overrides": {
            "fuse_length": 3.88,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.4,
            "wing_root_chord": 0.68,
            "wing_tip_chord": 0.42,
            "wing_sweep": 0.0,
            "wing_dihedral": 3.0,
            "wing_twist": -2.5,
            "htail_span": 2.12,
            "htail_root_chord": 0.34,
            "htail_tip_chord": 0.22,
            "htail_x": 3.24,
            "vtail_height": 0.70,
            "vtail_root_chord": 0.38,
            "vtail_tip_chord": 0.19,
            "vtail_x": 3.08,
        },
    },
    {
        "name": "drag_refine_9p4_margin",
        "overrides": {
            "fuse_length": 3.88,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.4,
            "wing_root_chord": 0.70,
            "wing_tip_chord": 0.43,
            "wing_sweep": 0.0,
            "wing_dihedral": 3.0,
            "wing_twist": -2.75,
            "htail_span": 2.1,
            "htail_root_chord": 0.33,
            "htail_tip_chord": 0.21,
            "htail_x": 3.24,
            "vtail_height": 0.68,
            "vtail_root_chord": 0.37,
            "vtail_tip_chord": 0.18,
            "vtail_x": 3.08,
        },
    },
    {
        "name": "drag_refine_9p6_tamer",
        "overrides": {
            "fuse_length": 3.9,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.6,
            "wing_root_chord": 0.67,
            "wing_tip_chord": 0.41,
            "wing_sweep": 0.5,
            "wing_dihedral": 3.0,
            "wing_twist": -2.25,
            "htail_span": 2.16,
            "htail_root_chord": 0.34,
            "htail_tip_chord": 0.22,
            "htail_x": 3.28,
            "vtail_height": 0.70,
            "vtail_root_chord": 0.38,
            "vtail_tip_chord": 0.19,
            "vtail_x": 3.1,
        },
    },
    {
        "name": "drag_refine_9p8_area_5p3",
        "overrides": {
            "fuse_length": 3.92,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.8,
            "wing_root_chord": 0.67,
            "wing_tip_chord": 0.41,
            "wing_sweep": 0.5,
            "wing_dihedral": 3.0,
            "wing_twist": -2.5,
            "htail_span": 2.18,
            "htail_root_chord": 0.34,
            "htail_tip_chord": 0.22,
            "htail_x": 3.3,
            "vtail_height": 0.70,
            "vtail_root_chord": 0.38,
            "vtail_tip_chord": 0.19,
            "vtail_x": 3.12,
        },
    },
    {
        "name": "drag_refine_low_tail_9p4",
        "overrides": {
            "fuse_length": 3.82,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.4,
            "wing_root_chord": 0.66,
            "wing_tip_chord": 0.40,
            "wing_sweep": 0.5,
            "wing_dihedral": 3.0,
            "wing_twist": -2.0,
            "htail_span": 1.75,
            "htail_root_chord": 0.30,
            "htail_tip_chord": 0.19,
            "htail_x": 3.16,
            "vtail_height": 0.62,
            "vtail_root_chord": 0.34,
            "vtail_tip_chord": 0.17,
            "vtail_x": 3.0,
        },
    },
    {
        "name": "drag_refine_low_tail_margin",
        "overrides": {
            "fuse_length": 3.84,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.2,
            "wing_root_chord": 0.70,
            "wing_tip_chord": 0.44,
            "wing_sweep": 0.5,
            "wing_dihedral": 3.0,
            "wing_twist": -2.25,
            "htail_span": 1.8,
            "htail_root_chord": 0.31,
            "htail_tip_chord": 0.19,
            "htail_x": 3.16,
            "vtail_height": 0.64,
            "vtail_root_chord": 0.35,
            "vtail_tip_chord": 0.17,
            "vtail_x": 3.0,
        },
    },
    {
        "name": "drag_refine_clean_margin_9p5",
        "overrides": {
            "fuse_length": 3.9,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.5,
            "wing_root_chord": 0.70,
            "wing_tip_chord": 0.43,
            "wing_sweep": 0.0,
            "wing_dihedral": 2.75,
            "wing_twist": -2.75,
            "htail_span": 2.05,
            "htail_root_chord": 0.32,
            "htail_tip_chord": 0.20,
            "htail_x": 3.28,
            "vtail_height": 0.68,
            "vtail_root_chord": 0.36,
            "vtail_tip_chord": 0.18,
            "vtail_x": 3.1,
        },
    },
    {
        "name": "drag_refine_9p6_low_tail",
        "overrides": {
            "fuse_length": 3.88,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.6,
            "wing_root_chord": 0.67,
            "wing_tip_chord": 0.41,
            "wing_sweep": 0.5,
            "wing_dihedral": 3.0,
            "wing_twist": -2.25,
            "htail_span": 1.95,
            "htail_root_chord": 0.31,
            "htail_tip_chord": 0.20,
            "htail_x": 3.24,
            "vtail_height": 0.64,
            "vtail_root_chord": 0.35,
            "vtail_tip_chord": 0.17,
            "vtail_x": 3.05,
        },
    },
    {
        "name": "drag_refine_9p6_less_washout",
        "overrides": {
            "fuse_length": 3.9,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.6,
            "wing_root_chord": 0.67,
            "wing_tip_chord": 0.41,
            "wing_sweep": 0.5,
            "wing_dihedral": 3.0,
            "wing_twist": -1.75,
            "htail_span": 2.12,
            "htail_root_chord": 0.33,
            "htail_tip_chord": 0.21,
            "htail_x": 3.28,
            "vtail_height": 0.68,
            "vtail_root_chord": 0.37,
            "vtail_tip_chord": 0.18,
            "vtail_x": 3.1,
        },
    },
    {
        "name": "drag_refine_9p6_more_washout",
        "overrides": {
            "fuse_length": 3.9,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.6,
            "wing_root_chord": 0.67,
            "wing_tip_chord": 0.41,
            "wing_sweep": 0.5,
            "wing_dihedral": 3.0,
            "wing_twist": -2.75,
            "htail_span": 2.12,
            "htail_root_chord": 0.33,
            "htail_tip_chord": 0.21,
            "htail_x": 3.28,
            "vtail_height": 0.68,
            "vtail_root_chord": 0.37,
            "vtail_tip_chord": 0.18,
            "vtail_x": 3.1,
        },
    },
    {
        "name": "drag_refine_9p7_soft",
        "overrides": {
            "fuse_length": 3.92,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.7,
            "wing_root_chord": 0.66,
            "wing_tip_chord": 0.41,
            "wing_sweep": 0.5,
            "wing_dihedral": 3.0,
            "wing_twist": -2.25,
            "htail_span": 2.12,
            "htail_root_chord": 0.33,
            "htail_tip_chord": 0.21,
            "htail_x": 3.3,
            "vtail_height": 0.68,
            "vtail_root_chord": 0.37,
            "vtail_tip_chord": 0.18,
            "vtail_x": 3.12,
        },
    },
    {
        "name": "drag_refine_9p5_thin",
        "overrides": {
            "fuse_length": 3.86,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.5,
            "wing_root_chord": 0.66,
            "wing_tip_chord": 0.40,
            "wing_sweep": 0.5,
            "wing_dihedral": 3.0,
            "wing_twist": -2.0,
            "htail_span": 2.0,
            "htail_root_chord": 0.32,
            "htail_tip_chord": 0.20,
            "htail_x": 3.22,
            "vtail_height": 0.66,
            "vtail_root_chord": 0.36,
            "vtail_tip_chord": 0.18,
            "vtail_x": 3.05,
        },
    },
    {
        "name": "drag_refine_9p6_root66",
        "overrides": {
            "fuse_length": 3.9,
            "fuse_max_width": 0.84,
            "fuse_max_height": 1.05,
            "wing_span": 9.6,
            "wing_root_chord": 0.66,
            "wing_tip_chord": 0.41,
            "wing_sweep": 0.5,
            "wing_dihedral": 3.0,
            "wing_twist": -2.25,
            "htail_span": 2.14,
            "htail_root_chord": 0.34,
            "htail_tip_chord": 0.22,
            "htail_x": 3.28,
            "vtail_height": 0.70,
            "vtail_root_chord": 0.38,
            "vtail_tip_chord": 0.19,
            "vtail_x": 3.1,
        },
    },
]


def extract_json_block(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in output")
    return json.loads(text[start : end + 1])


def run_score(result_path: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCORER), str(result_path)],
        cwd=str(SCORER.parent),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def aerodynamic_ok(report: dict) -> bool:
    inputs = report["score"]["inputs"]
    geom = report["geometry"]
    return (
        inputs["vstall_ms"] <= inputs["vstall_spec_ms"]
        and inputs["longitudinal_stable"]
        and geom["wingspan_m"] <= geom["wingspan_limit_m"]
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    variants = DRAG_REFINEMENT_VARIANTS if "--drag-refine" in sys.argv else VARIANTS

    for idx, variant in enumerate(variants, start=1):
        config_path = CONFIG_DIR / f"{idx:02d}_{variant['name']}.json"
        config_path.write_text(json.dumps(variant["overrides"], indent=2))

        gen = run(GENERATOR, cwd=GENERATOR.parent, args=[str(config_path)], timeout=120)
        if not gen.ok:
            reports.append({"name": variant["name"], "stage": "generate", "error": gen.stderr or gen.stdout})
            continue
        geom = extract_json_block(gen.stdout)
        model_path = Path(geom["model_file"])

        sim = run(SWEEP, cwd=SWEEP.parent, args=[str(model_path)], timeout=300)
        if not sim.ok:
            reports.append({"name": variant["name"], "stage": "simulate", "model": model_path.name, "error": sim.stderr or sim.stdout})
            continue
        result_file = None
        for line in sim.stdout.splitlines():
            if line.startswith("RESULTS_FILE:"):
                result_file = Path(line.split("RESULTS_FILE:", 1)[1].strip())
                break
        if result_file is None:
            result_file = PROJECT_ROOT / "SIMULATION" / "results" / f"{model_path.stem}_alpha_sweep.json"

        sim_results = json.loads(result_file.read_text())
        score = run_score(result_file)
        reports.append({
            "name": variant["name"],
            "model": model_path.name,
            "geometry": geom,
            "simulation": {
                "vstall_est_ms": sim_results.get("vstall_est_ms"),
                "vcruise_75pct_ms": sim_results.get("vcruise_75pct_ms"),
                "CD_cruise": sim_results.get("CD_cruise"),
                "LD_cruise": sim_results.get("LD_cruise"),
                "Cm_alpha_per_deg": sim_results.get("Cm_alpha_per_deg"),
                "longitudinal_stable": sim_results.get("longitudinal_stable"),
            },
            "score": score,
            "compliant": (
                score["inputs"]["vstall_ms"] <= score["inputs"]["vstall_spec_ms"]
                and score["inputs"]["empty_mass_kg"] <= score["inputs"]["empty_mass_spec_kg"]
                and score["inputs"]["longitudinal_stable"]
            ),
        })

    ranked = sorted(
        [r for r in reports if "score" in r],
        key=lambda r: (
            not r["compliant"],
            r["score"]["total_cost"],
        ),
    )
    aero_ranked = sorted(
        [r for r in reports if "score" in r and aerodynamic_ok(r)],
        key=lambda r: (
            r["simulation"].get("CD_cruise", float("inf")),
            -r["simulation"].get("vcruise_75pct_ms", 0.0),
        ),
    )
    report = {
        "mode": "drag_refine" if variants is DRAG_REFINEMENT_VARIANTS else "full",
        "variant_count": len(variants),
        "completed_count": len([r for r in reports if "score" in r]),
        "best_compliant": next((r for r in ranked if r["compliant"]), None),
        "best_numeric": min([r for r in reports if "score" in r], key=lambda r: r["score"]["total_cost"], default=None),
        "best_aero_low_drag": aero_ranked[0] if aero_ranked else None,
        "aero_ranked": aero_ranked,
        "ranked": ranked,
        "all_reports": reports,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
