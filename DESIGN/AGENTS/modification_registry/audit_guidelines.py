"""
Guideline modification registry and coverage auditor.

This tool reads DESIGN/DESIGN_GUIDELINES.md, extracts the complete
"Features That Can Be modified" list, and reports whether each feature has:

- a design-memory document under DESIGN/AGENTS/modifications/
- a known implementation path through an existing tool or generator parameter
- a dedicated feature tool directory under DESIGN/AGENTS/modification_tools/

It can also scaffold missing design-memory documents so every guideline feature
has a place to record performance impact.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
GUIDELINES = PROJECT_ROOT / "DESIGN" / "DESIGN_GUIDELINES.md"
MOD_DOC_DIR = PROJECT_ROOT / "DESIGN" / "AGENTS" / "modifications"
DEDICATED_TOOL_ROOT = PROJECT_ROOT / "DESIGN" / "AGENTS" / "modification_tools"
PARAMETER_MODIFIER_DIR = PROJECT_ROOT / "DESIGN" / "AGENTS" / "parameter_modifier"
OUT_DIR = PROJECT_ROOT / "DESIGN" / "AGENTS" / "modification_registry" / "out"


SPECIAL_SLUGS = {
    "Maximum fuselage diameter": "fuselage_max_diameter",
    "Nose shape (blunt -> sharp)": "nose_shape",
    "Nose shape (blunt \u2192 sharp)": "nose_shape",
    "Tail cone taper angle": "tail_cone_taper",
    "Cabin cross-sectional shape (circular, oval, rectangular)": "cabin_cross_section_shape",
    "Cockpit position (forward vs aft shift)": "cockpit_position",
    "Engine placement (nose, wing-mounted, aft fuselage)": "engine_placement",
    "Payload location (CG distribution tuning)": "payload_location",
    "Surface smoothness / roughness factor": "surface_smoothness",
    "Canopy shape and angle": "canopy_shape",
    "Belly contour (flat vs curved)": "belly_contour",
    "Fuselage camber (lifting fuselage concept)": "fuselage_camber",
    "Wing sweep angle": "wing_sweep",
    "Wing dihedral angle": "wing_dihedral",
    "Wing anhedral angle": "wing_anhedral",
    "Wing vertical placement (high, mid, low)": "wing_vertical_placement",
    "Wing longitudinal placement (relative to CG)": "wing_longitudinal_placement",
    "Wing thickness-to-chord ratio": "wing_thickness_chord_ratio",
    "Wing planform shape (elliptical, rectangular, trapezoidal)": "wing_planform_shape",
    "Wing leading-edge shape": "wing_leading_edge_shape",
    "Wing trailing-edge shape": "wing_trailing_edge_shape",
    "Standard wing configuration (forward wing, trailing empenage)": "standard_wing_configuration",
    "Tandem Wing": "tandem_wing",
    "Airfoil selection (root)": "airfoil_root",
    "Airfoil selection (tip)": "airfoil_tip",
    "Twist (washout/washin)": "wing_twist",
    "Wing incidence angle": "wing_incidence",
    "Leading-edge radius": "leading_edge_radius",
    "Add winglets": "winglet_add",
    "Raked wingtip length": "raked_wingtip",
    "Split winglets (upper/lower)": "split_winglets",
    "Wingtip vortex control devices": "wingtip_vortex_control_devices",
    "T-tail vs conventional tail": "t_tail_vs_conventional_tail",
    "V-tail configuration": "v_tail_configuration",
    "Twin tail vs single tail": "twin_tail_vs_single_tail",
    "Canard configuration (presence/size)": "canard_configuration_presence_size",
    "Tail dihedral/anhedral": "tail_dihedral_anhedral",
    "Thrust line relative to CG": "thrust_line_relative_to_cg",
}


CAPABILITY_MAP: dict[str, dict[str, Any]] = {
    "fuselage_length": {
        "status": "implemented",
        "method": "baseline_generator override",
        "parameters": ["fuse_length"],
        "tools": ["DESIGN/AGENTS/baseline_generator", "EVALUATION/AGENTS/fuselage_smoothness"],
    },
    "fuselage_max_diameter": {
        "status": "implemented",
        "method": "baseline_generator override",
        "parameters": ["fuse_max_width", "fuse_max_height", "boom_diameter"],
        "tools": ["DESIGN/AGENTS/baseline_generator", "EVALUATION/AGENTS/fuselage_smoothness"],
    },
    "fuselage_fineness_ratio": {
        "status": "implemented",
        "method": "derived by changing length and diameter parameters",
        "parameters": ["fuse_length", "fuse_max_width", "fuse_max_height", "boom_length", "boom_diameter"],
        "tools": ["EVALUATION/AGENTS/fuselage_smoothness"],
    },
    "nose_shape": {
        "status": "needs_geometry_tool",
        "method": "requires OpenVSP fuselage section insertion/profile control",
        "parameters": [],
        "tools": ["EVALUATION/AGENTS/fuselage_smoothness"],
    },
    "tail_cone_taper": {
        "status": "implemented",
        "method": "baseline_generator pod taper override",
        "parameters": ["fuse_taper_width", "fuse_taper_height", "boom_x", "boom_length"],
        "tools": ["DESIGN/AGENTS/baseline_generator", "EVALUATION/AGENTS/fuselage_smoothness"],
    },
    "cabin_cross_section_shape": {
        "status": "partial",
        "method": "width/height available; circular/oval/rectangular profiles need section-shape tool",
        "parameters": ["fuse_max_width", "fuse_max_height"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "cockpit_position": {
        "status": "needs_mass_cg_tool",
        "method": "requires cockpit station and CG/mass model",
        "parameters": [],
        "tools": [],
    },
    "engine_placement": {
        "status": "partial",
        "method": "tractor nose prop exists; wing/aft engine placement needs architecture generator",
        "parameters": ["prop_x"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "payload_location": {
        "status": "needs_mass_cg_tool",
        "method": "requires payload mass station and CG calculator",
        "parameters": [],
        "tools": [],
    },
    "surface_smoothness": {
        "status": "partial",
        "method": "fuselage profile smoothness exists; roughness factor needs drag model input",
        "parameters": [],
        "tools": ["EVALUATION/AGENTS/fuselage_smoothness"],
    },
    "canopy_shape": {
        "status": "needs_geometry_tool",
        "method": "requires canopy/fuselage upper-profile section controls",
        "parameters": [],
        "tools": ["EVALUATION/AGENTS/fuselage_smoothness"],
    },
    "belly_contour": {
        "status": "needs_geometry_tool",
        "method": "requires lower-profile section controls",
        "parameters": [],
        "tools": [],
    },
    "fuselage_camber": {
        "status": "needs_geometry_tool",
        "method": "requires vertical section-centerline offsets",
        "parameters": [],
        "tools": [],
    },
    "wingspan": {
        "status": "implemented",
        "method": "baseline_generator override",
        "parameters": ["wing_span"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "wing_area": {
        "status": "implemented",
        "method": "derived from span and root/tip chords",
        "parameters": ["wing_span", "wing_root_chord", "wing_tip_chord"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "aspect_ratio": {
        "status": "implemented",
        "method": "derived from span and area",
        "parameters": ["wing_span", "wing_root_chord", "wing_tip_chord"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "taper_ratio": {
        "status": "implemented",
        "method": "derived from tip/root chord",
        "parameters": ["wing_root_chord", "wing_tip_chord"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "wing_sweep": {
        "status": "implemented",
        "method": "baseline_generator override",
        "parameters": ["wing_sweep"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "wing_dihedral": {
        "status": "implemented",
        "method": "baseline_generator override",
        "parameters": ["wing_dihedral"],
        "tools": ["DESIGN/AGENTS/baseline_generator", "SIMULATION/AGENTS/beta_sweep"],
    },
    "wing_anhedral": {
        "status": "implemented",
        "method": "negative wing_dihedral override",
        "parameters": ["wing_dihedral"],
        "tools": ["DESIGN/AGENTS/baseline_generator", "SIMULATION/AGENTS/beta_sweep"],
    },
    "wing_vertical_placement": {
        "status": "implemented",
        "method": "baseline_generator override",
        "parameters": ["wing_z"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "wing_longitudinal_placement": {
        "status": "implemented",
        "method": "baseline_generator override",
        "parameters": ["wing_x"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "wing_thickness_chord_ratio": {
        "status": "implemented",
        "method": "NACA airfoil thickness selection",
        "parameters": ["wing_airfoil"],
        "tools": ["DESIGN/AGENTS/airfoil_tool", "DESIGN/AGENTS/baseline_generator"],
    },
    "wing_root_chord": {
        "status": "implemented",
        "method": "baseline_generator override",
        "parameters": ["wing_root_chord"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "wing_tip_chord": {
        "status": "implemented",
        "method": "baseline_generator override",
        "parameters": ["wing_tip_chord"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "wing_planform_shape": {
        "status": "partial",
        "method": "trapezoid available; elliptical/rectangular need planform generator mode",
        "parameters": ["wing_root_chord", "wing_tip_chord", "wing_sweep"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "wing_leading_edge_shape": {
        "status": "needs_geometry_tool",
        "method": "requires per-section sweep or custom wing outline",
        "parameters": [],
        "tools": [],
    },
    "wing_trailing_edge_shape": {
        "status": "needs_geometry_tool",
        "method": "requires per-section chord/sweep outline tool",
        "parameters": [],
        "tools": [],
    },
    "standard_wing_configuration": {
        "status": "implemented",
        "method": "baseline_generator pod-and-boom tractor with aft tail",
        "parameters": [],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "tandem_wing": {
        "status": "needs_architecture_tool",
        "method": "requires alternate generator architecture",
        "parameters": [],
        "tools": [],
    },
    "canard_configuration": {
        "status": "needs_architecture_tool",
        "method": "requires canard generator and canard-first stall checks",
        "parameters": [],
        "tools": [],
    },
    "wing_height": {
        "status": "implemented",
        "method": "same as wing vertical placement",
        "parameters": ["wing_z"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "airfoil_root": {
        "status": "partial",
        "method": "global wing NACA tool exists; root-only section selection still needed",
        "parameters": ["wing_airfoil"],
        "tools": ["DESIGN/AGENTS/airfoil_tool"],
    },
    "airfoil_tip": {
        "status": "partial",
        "method": "global wing NACA tool exists; tip-only section selection still needed",
        "parameters": ["wing_airfoil"],
        "tools": ["DESIGN/AGENTS/airfoil_tool"],
    },
    "airfoil_camber_distribution": {
        "status": "partial",
        "method": "NACA camber can be changed globally; spanwise distribution needs per-XSec tool",
        "parameters": ["wing_airfoil"],
        "tools": ["DESIGN/AGENTS/airfoil_tool"],
    },
    "airfoil_thickness_distribution": {
        "status": "partial",
        "method": "NACA thickness can be changed globally; spanwise distribution needs per-XSec tool",
        "parameters": ["wing_airfoil"],
        "tools": ["DESIGN/AGENTS/airfoil_tool"],
    },
    "wing_twist": {
        "status": "implemented",
        "method": "baseline_generator override",
        "parameters": ["wing_twist"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "wing_incidence": {
        "status": "implemented",
        "method": "baseline_generator override",
        "parameters": ["wing_incidence_deg"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "spanwise_lift_distribution": {
        "status": "partial",
        "method": "changed by span/chord/twist; needs dedicated load-distribution evaluator",
        "parameters": ["wing_span", "wing_root_chord", "wing_tip_chord", "wing_twist"],
        "tools": ["SIMULATION/AGENTS/alpha_sweep"],
    },
    "leading_edge_radius": {
        "status": "partial",
        "method": "controlled indirectly by airfoil thickness; direct leading-edge shaping needed",
        "parameters": ["wing_airfoil"],
        "tools": ["DESIGN/AGENTS/airfoil_tool"],
    },
    "winglet_add": {
        "status": "needs_geometry_tool",
        "method": "requires winglet geometry generator",
        "parameters": [],
        "tools": [],
    },
    "winglet_height": {
        "status": "needs_geometry_tool",
        "method": "requires winglet geometry generator",
        "parameters": [],
        "tools": [],
    },
    "winglet_cant_angle": {
        "status": "needs_geometry_tool",
        "method": "requires winglet geometry generator",
        "parameters": [],
        "tools": [],
    },
    "winglet_toe_angle": {
        "status": "needs_geometry_tool",
        "method": "requires winglet geometry generator",
        "parameters": [],
        "tools": [],
    },
    "winglet_airfoil": {
        "status": "needs_geometry_tool",
        "method": "requires winglet geometry and airfoil assignment",
        "parameters": [],
        "tools": ["DESIGN/AGENTS/airfoil_tool"],
    },
    "winglet_sweep": {
        "status": "needs_geometry_tool",
        "method": "requires winglet geometry generator",
        "parameters": [],
        "tools": [],
    },
    "raked_wingtip": {
        "status": "needs_geometry_tool",
        "method": "requires multi-section wing tip generator",
        "parameters": [],
        "tools": [],
    },
    "tip_fences": {
        "status": "needs_geometry_tool",
        "method": "requires wingtip endplate/fence geometry generator",
        "parameters": [],
        "tools": [],
    },
    "split_winglets": {
        "status": "needs_geometry_tool",
        "method": "requires upper/lower winglet geometry generator",
        "parameters": [],
        "tools": [],
    },
    "endplate_size": {
        "status": "needs_geometry_tool",
        "method": "requires endplate geometry generator",
        "parameters": [],
        "tools": [],
    },
    "wingtip_vortex_control_devices": {
        "status": "needs_geometry_tool",
        "method": "requires wingtip device generator and induced-drag evaluation",
        "parameters": [],
        "tools": ["SIMULATION/AGENTS/alpha_sweep"],
    },
    "horizontal_tail_area": {
        "status": "implemented",
        "method": "derived from horizontal tail span and chords",
        "parameters": ["htail_span", "htail_root_chord", "htail_tip_chord"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "vertical_tail_area": {
        "status": "implemented",
        "method": "derived from vertical tail height and chords",
        "parameters": ["vtail_height", "vtail_root_chord", "vtail_tip_chord"],
        "tools": ["DESIGN/AGENTS/baseline_generator", "SIMULATION/AGENTS/beta_sweep"],
    },
    "tail_moment_arm_length": {
        "status": "implemented",
        "method": "tail x-location and boom length overrides",
        "parameters": ["htail_x", "vtail_x", "boom_length"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "tail_airfoil_selection": {
        "status": "needs_airfoil_tool_extension",
        "method": "requires airfoil modifier support for HorizTail/VertTail geoms",
        "parameters": [],
        "tools": ["DESIGN/AGENTS/airfoil_tool"],
    },
    "tail_incidence_angle": {
        "status": "needs_generator_parameter",
        "method": "requires htail/vtail incidence parameters in baseline generator",
        "parameters": [],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "t_tail_vs_conventional_tail": {
        "status": "needs_architecture_tool",
        "method": "requires alternate tail attachment/placement generator",
        "parameters": [],
        "tools": [],
    },
    "v_tail_configuration": {
        "status": "needs_architecture_tool",
        "method": "requires V-tail geometry generator and control-axis mapping",
        "parameters": [],
        "tools": [],
    },
    "twin_tail_vs_single_tail": {
        "status": "needs_architecture_tool",
        "method": "requires twin vertical tail generator",
        "parameters": [],
        "tools": [],
    },
    "canard_configuration_presence_size": {
        "status": "needs_architecture_tool",
        "method": "requires canard generator and canard-first stall checks",
        "parameters": [],
        "tools": [],
    },
    "tail_dihedral_anhedral": {
        "status": "needs_generator_parameter",
        "method": "requires horizontal tail dihedral parameter",
        "parameters": [],
        "tools": ["DESIGN/AGENTS/baseline_generator", "SIMULATION/AGENTS/beta_sweep"],
    },
    "propeller_diameter": {
        "status": "implemented",
        "method": "baseline_generator prop disk override",
        "parameters": ["prop_diameter"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
    "thrust_line_relative_to_cg": {
        "status": "partial",
        "method": "prop x-position exists; vertical thrust-line and CG model still needed",
        "parameters": ["prop_x"],
        "tools": ["DESIGN/AGENTS/baseline_generator"],
    },
}


def slugify(feature: str) -> str:
    if feature in SPECIAL_SLUGS:
        return SPECIAL_SLUGS[feature]
    text = feature.lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def title_from_slug(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("_"))


def parse_guideline_features(path: Path = GUIDELINES) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_section = False
    features: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Features That Can Be modified"):
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if not in_section:
            continue
        if not stripped:
            continue
        if stripped.startswith("-"):
            stripped = stripped.lstrip("-").strip()
        if stripped and not stripped.startswith("#"):
            features.append(stripped)

    return features


def memory_doc_path(slug: str) -> Path:
    return MOD_DOC_DIR / f"{slug}.md"


def dedicated_tool_path(slug: str) -> Path:
    return DEDICATED_TOOL_ROOT / slug


def build_audit() -> dict[str, Any]:
    features = parse_guideline_features()
    records = []

    for feature in features:
        slug = slugify(feature)
        capability = CAPABILITY_MAP.get(
            slug,
            {
                "status": "unmapped",
                "method": "no implementation path registered yet",
                "parameters": [],
                "tools": [],
            },
        )
        tools = list(capability.get("tools", []))
        if capability.get("parameters") and capability.get("status") in {"implemented", "partial"}:
            if PARAMETER_MODIFIER_DIR.exists():
                tools.append("DESIGN/AGENTS/parameter_modifier")
        tools = sorted(set(tools))
        doc_path = memory_doc_path(slug)
        tool_path = dedicated_tool_path(slug)
        records.append(
            {
                "feature": feature,
                "slug": slug,
                "status": capability["status"],
                "implementation_method": capability["method"],
                "parameters": capability.get("parameters", []),
                "tools": tools,
                "memory_doc_exists": doc_path.exists(),
                "memory_doc": str(doc_path),
                "dedicated_tool_exists": tool_path.exists(),
                "dedicated_tool_dir": str(tool_path),
            }
        )

    summary: dict[str, Any] = {
        "features_total": len(records),
        "memory_docs_present": sum(1 for r in records if r["memory_doc_exists"]),
        "memory_docs_missing": [r["slug"] for r in records if not r["memory_doc_exists"]],
        "dedicated_tools_present": sum(1 for r in records if r["dedicated_tool_exists"]),
        "dedicated_tools_missing": [r["slug"] for r in records if not r["dedicated_tool_exists"]],
        "status_counts": {},
    }
    for record in records:
        summary["status_counts"][record["status"]] = summary["status_counts"].get(record["status"], 0) + 1

    return {
        "source": str(GUIDELINES),
        "summary": summary,
        "features": records,
    }


def render_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    lines = [
        "# Guideline Modification Capability Audit",
        "",
        f"Source: `{audit['source']}`",
        "",
        "## Summary",
        "",
        f"- Features in DESIGN_GUIDELINES.md: {summary['features_total']}",
        f"- Memory docs present: {summary['memory_docs_present']}",
        f"- Memory docs missing: {len(summary['memory_docs_missing'])}",
        f"- Dedicated feature tool dirs present: {summary['dedicated_tools_present']}",
        f"- Dedicated feature tool dirs missing: {len(summary['dedicated_tools_missing'])}",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(summary["status_counts"].items()):
        lines.append(f"- `{status}`: {count}")

    lines.extend(
        [
            "",
            "## Feature Matrix",
            "",
            "| Feature | Slug | Status | Memory | Dedicated Tool | Tools | Implementation |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for record in audit["features"]:
        memory = "yes" if record["memory_doc_exists"] else "missing"
        tool = "yes" if record["dedicated_tool_exists"] else "missing"
        tools = ", ".join(f"`{item}`" for item in record["tools"]) if record["tools"] else "-"
        method = record["implementation_method"].replace("|", "/")
        lines.append(
            f"| {record['feature']} | `{record['slug']}` | `{record['status']}` | "
            f"{memory} | {tool} | {tools} | {method} |"
        )
    return "\n".join(lines) + "\n"


def scaffold_memory_docs(audit: dict[str, Any]) -> list[str]:
    MOD_DOC_DIR.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    for record in audit["features"]:
        path = Path(record["memory_doc"])
        if path.exists():
            continue
        params = record["parameters"]
        param_text = ", ".join(f"`{p}`" for p in params) if params else "No direct generator parameter registered yet."
        content = f"""# Skill: {title_from_slug(record["slug"])}

## What It Modifies
{record["feature"]}

## Current Implementation Path
Status: `{record["status"]}`

{record["implementation_method"]}

## Parameters / Tools
Parameters: {param_text}

Tools:
"""
        tools = record["tools"]
        if tools:
            for tool in tools:
                content += f"- `{tool}`\n"
        else:
            content += "- No dedicated tool registered yet.\n"
        content += """
## How To Apply
Use the implementation path above if it is marked `implemented` or `partial`.
If the status starts with `needs_`, build or extend the listed tool before using
this modification in a design iteration.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| - | Baseline | - | - | - | No data yet |
"""
        path.write_text(content, encoding="utf-8")
        created.append(str(path))
    return created


def write_outputs(audit: dict[str, Any], out_json: Path, out_md: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown(audit), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-json", type=Path, default=OUT_DIR / "guideline_capability_audit.json")
    parser.add_argument("--out-md", type=Path, default=OUT_DIR / "guideline_capability_audit.md")
    parser.add_argument(
        "--scaffold-memory-docs",
        action="store_true",
        help="Create missing DESIGN/AGENTS/modifications/<slug>.md files from the registry.",
    )
    args = parser.parse_args()

    audit = build_audit()
    created_docs: list[str] = []
    if args.scaffold_memory_docs:
        created_docs = scaffold_memory_docs(audit)
        audit = build_audit()
        audit["created_memory_docs"] = created_docs

    write_outputs(audit, args.out_json, args.out_md)
    print(json.dumps(audit["summary"], indent=2))
    print(f"REPORT_JSON:{args.out_json}")
    print(f"REPORT_MD:{args.out_md}")
    if created_docs:
        print("CREATED_MEMORY_DOCS:")
        for path in created_docs:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
