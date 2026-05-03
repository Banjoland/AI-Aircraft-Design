"""
Smoke test for the batch designer configuration set.

This intentionally avoids launching OpenVSP. The end-to-end batch can take over
a minute, so this test validates that the configured design variants are usable
by baseline_generator's override API.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


AGENT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = AGENT_DIR / "batch_design.py"


def load_module():
    spec = importlib.util.spec_from_file_location("batch_design", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_module()
    variants = module.VARIANTS

    assert len(variants) >= 6, "Expected at least six batch design variants"

    names = [variant["name"] for variant in variants]
    assert len(names) == len(set(names)), "Variant names must be unique"

    allowed_keys = {
        "fuse_length",
        "fuse_max_width",
        "fuse_max_height",
        "wing_span",
        "wing_root_chord",
        "wing_tip_chord",
        "wing_sweep",
        "wing_dihedral",
        "wing_twist",
        "htail_span",
        "htail_root_chord",
        "htail_tip_chord",
        "htail_x",
        "vtail_height",
        "vtail_root_chord",
        "vtail_tip_chord",
        "vtail_x",
    }
    for variant in variants:
        unknown = set(variant["overrides"]) - allowed_keys
        assert not unknown, f"{variant['name']} has unknown override keys: {sorted(unknown)}"

    print("PASS: batch_designer variant configuration is valid")


if __name__ == "__main__":
    main()
