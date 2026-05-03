"""
Test driver for smooth_fuselage_redesign.

Runs the OpenVSP generator into TEST/out and verifies the companion JSON states
that the model uses a single fuselage, has 1.5 m cockpit vertical space, and has
an explicit station profile for the smoothness analyzer.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
AGENT_DIR = HERE.parent
PROJECT_ROOT = HERE.parents[3]
OPENVSP_PY = Path(r"C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd")
SCRIPT = AGENT_DIR / "generate.py"
SOURCE_MODEL = PROJECT_ROOT / "AIRCRAFT" / "MODEL_05_02_2026_05.vsp3"
OUT_DIR = HERE / "out"
TAG = "TEST_SINGLE_SMOOTH_FUSELAGE"


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(OPENVSP_PY),
        str(SCRIPT),
        str(SOURCE_MODEL),
        "--out-dir",
        str(OUT_DIR),
        "--tag",
        TAG,
    ]
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, text=True, capture_output=True, timeout=180)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        return fail(f"generator exited with {proc.returncode}")

    model_path = OUT_DIR / f"{TAG}.vsp3"
    json_path = OUT_DIR / f"{TAG}.json"
    if not model_path.exists():
        return fail(f"missing model file: {model_path}")
    if not json_path.exists():
        return fail(f"missing companion JSON: {json_path}")

    meta = json.loads(json_path.read_text())
    engine = meta.get("engine_compartment", {})
    checks = [
        (meta.get("single_fuselage_structure") is True, "single_fuselage_structure"),
        (meta.get("removed_separate_tail_boom") is True, "removed_separate_tail_boom"),
        (meta.get("cockpit_vertical_space_m", 0.0) >= 1.5, "cockpit_vertical_space_m"),
        (meta.get("wing_above_cockpit_top_m", -1.0) >= 0.0, "wing_above_cockpit_top_m"),
        (len(meta.get("fuselage_stations", [])) >= 8, "fuselage_stations"),
        (meta.get("fuselage_curve_degree", 99) <= 3, "fuselage_curve_degree"),
        (meta.get("openvsp_skinning_continuity") == "C2", "openvsp_skinning_continuity"),
        ("ResetXSecSkinParms" in meta.get("openvsp_skinning_method", ""), "openvsp_skinning_method"),
        (engine.get("meets_spec") is True, "engine_compartment"),
        (meta.get("fuselage_extension_past_stabilizer_te_m", 99.0) <= 0.0, "tail_extension"),
    ]
    failed = [name for ok, name in checks if not ok]
    if failed:
        return fail(f"metadata checks failed: {failed}")

    print(f"MODEL_FILE:{model_path}")
    print(f"JSON_FILE:{json_path}")
    print("PASS: smooth_fuselage_redesign generated a single full-length fuselage model")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
