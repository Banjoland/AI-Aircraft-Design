"""
Create validated baseline_generator override files for guideline modifications.

The baseline generator already accepts a JSON override file for parameters in
its P dictionary. This tool connects guideline feature names to those parameters
so an agent can safely prepare a one-change design iteration.

Examples:
    python make_override.py wingspan --set wing_span=10.0
    python make_override.py wing_root_chord --set wing_root_chord=0.50 --run
    python make_override.py --list
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
AGENT_DIR = Path(__file__).resolve().parent
OUT_DIR = AGENT_DIR / "out"
BASELINE_GENERATOR = PROJECT_ROOT / "DESIGN" / "AGENTS" / "baseline_generator" / "generate.py"
OPENVSP_PY = Path(r"C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd")

REGISTRY_DIR = PROJECT_ROOT / "DESIGN" / "AGENTS" / "modification_registry"
sys.path.insert(0, str(REGISTRY_DIR))
from audit_guidelines import CAPABILITY_MAP, slugify  # noqa: E402


def parse_value(text: str) -> Any:
    lowered = text.strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if any(ch in text for ch in [".", "e", "E"]):
            return float(text)
        return int(text)
    except ValueError:
        return text


def parse_set_arg(text: str) -> tuple[str, Any]:
    if "=" not in text:
        raise ValueError(f"--set value must be key=value, got {text!r}")
    key, raw_value = text.split("=", 1)
    key = key.strip()
    if not key:
        raise ValueError("--set key cannot be empty")
    return key, parse_value(raw_value.strip())


def supported_features() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for slug, capability in CAPABILITY_MAP.items():
        params = capability.get("parameters", [])
        if not params:
            continue
        if capability.get("status") not in {"implemented", "partial"}:
            continue
        rows[slug] = capability
    return rows


def print_supported() -> None:
    rows = supported_features()
    print(json.dumps({
        slug: {
            "status": cap.get("status"),
            "parameters": cap.get("parameters", []),
            "method": cap.get("method"),
        }
        for slug, cap in sorted(rows.items())
    }, indent=2))


def make_override(feature_arg: str, sets: list[str], allow_extra: bool) -> tuple[Path, dict[str, Any]]:
    feature_slug = slugify(feature_arg)
    rows = supported_features()
    if feature_slug not in rows:
        known = ", ".join(sorted(rows))
        raise ValueError(f"Feature {feature_arg!r} is not parameter-modifiable. Known: {known}")

    capability = rows[feature_slug]
    allowed = set(capability.get("parameters", []))
    if not sets:
        raise ValueError("At least one --set key=value is required")

    override: dict[str, Any] = {}
    for item in sets:
        key, value = parse_set_arg(item)
        if key not in allowed and not allow_extra:
            allowed_text = ", ".join(sorted(allowed))
            raise ValueError(f"Parameter {key!r} is not registered for {feature_slug}. Allowed: {allowed_text}")
        override[key] = value

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
    out_path = OUT_DIR / f"{stamp}_{feature_slug}_override.json"
    out_path.write_text(json.dumps(override, indent=2), encoding="utf-8")

    manifest = {
        "feature": feature_arg,
        "slug": feature_slug,
        "status": capability.get("status"),
        "method": capability.get("method"),
        "allowed_parameters": sorted(allowed),
        "override_file": str(out_path),
        "override": override,
        "generator": str(BASELINE_GENERATOR),
    }
    manifest_path = out_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out_path, manifest


def run_generator(override_path: Path) -> int:
    if not OPENVSP_PY.exists():
        print(f"ERROR: OpenVSP Python launcher not found: {OPENVSP_PY}", file=sys.stderr)
        return 1
    cmd = [str(OPENVSP_PY), str(BASELINE_GENERATOR), str(override_path)]
    proc = subprocess.run(cmd, cwd=BASELINE_GENERATOR.parent, text=True, capture_output=True, timeout=180)
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("feature", nargs="?", help="Guideline feature name or slug, such as wingspan")
    parser.add_argument("--set", dest="sets", action="append", default=[], help="Parameter assignment key=value")
    parser.add_argument("--allow-extra", action="store_true", help="Allow parameters not registered for this feature")
    parser.add_argument("--list", action="store_true", help="List parameter-modifiable guideline features")
    parser.add_argument("--run", action="store_true", help="Run baseline_generator with the override via OpenVSP")
    args = parser.parse_args()

    try:
        if args.list:
            print_supported()
            return 0
        if not args.feature:
            raise ValueError("feature is required unless --list is used")
        out_path, manifest = make_override(args.feature, args.sets, args.allow_extra)
        print(json.dumps(manifest, indent=2))
        print(f"OVERRIDE_FILE:{out_path}")
        if args.run:
            return run_generator(out_path)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
