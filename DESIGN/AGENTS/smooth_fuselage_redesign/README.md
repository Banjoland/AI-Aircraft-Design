# Agent: smooth_fuselage_redesign

## Role

This agent creates a new aircraft model from a source `.vsp3` by replacing the
current pod-and-boom arrangement with one continuous full-length fuselage.

It is intended for design requests that need:

- smooth front-to-back fuselage curvature,
- one single fuselage structure rather than an inline pod/boom pair,
- low engine and propeller thrust line,
- engine compartment sized to the project specification,
- high cockpit with the pilot located at CG,
- high wing attached to the fuselage crown,
- aft tail placement in the high-wing root wake path for stall buffet cueing.
- curve-defined top, bottom, and side station profiles with OpenVSP C2 skinning.

## Usage

Run through OpenVSP Python:

```powershell
& "C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd" `
  DESIGN/AGENTS/smooth_fuselage_redesign/generate.py `
  AIRCRAFT/MODEL_05_02_2026_05.vsp3
```

The tool writes a new versioned model and companion JSON under `AIRCRAFT/`.

For test output:

```powershell
& "C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd" `
  DESIGN/AGENTS/smooth_fuselage_redesign/generate.py `
  AIRCRAFT/MODEL_05_02_2026_05.vsp3 `
  --out-dir DESIGN/AGENTS/smooth_fuselage_redesign/TEST/out `
  --tag TEST_SINGLE_SMOOTH_FUSELAGE
```

## Output Metadata

The companion JSON includes:

- `single_fuselage_structure`
- `removed_separate_tail_boom`
- `fuselage_stations`
- `fuselage_curve_method`
- `fuselage_curve_degree`
- `fuselage_curve_controls`
- `openvsp_skinning_continuity`
- `x_cg_m`
- `pilot_x_m`
- `engine_compartment`
- `cockpit_vertical_space_m`
- `wing_above_cockpit_top_m`
- `fuselage_extension_past_stabilizer_te_m`
- `tail_buffet_design`

The explicit `fuselage_stations` field is used by
`EVALUATION/AGENTS/fuselage_smoothness/analyze.py` for curvature reporting.
The current profile is sampled from one cubic Hermite top curve, one cubic
Hermite bottom curve, and one symmetric cubic Hermite side half-width curve.
Interior OpenVSP sections are assigned C2 skinning continuity.

## Test

```powershell
python DESIGN/AGENTS/smooth_fuselage_redesign/TEST/run_test.py
```

Expected: PASS, with a test `.vsp3`, companion `.json`, and smoothness report
written under `TEST/out/`.
