# Agent: fuselage_smoothness

## Role
This agent evaluates fuselage profile quality before deeper aerodynamic work. It estimates longitudinal radius-profile curvature, vertical centerline curvature, taper angles, fineness ratio, and pressure-recovery risk from the companion JSON written beside each `MODEL_*.vsp3`. When explicit station data is available it also reports top, bottom, and side half-width surface-line curvature so lumpy skin transitions can be audited.

## Why It Exists
`DESIGN/DESIGN_GUIDELINES.md` and `EVALUATION/CLAUDE.md` require tools to:

- measure fuselage curvature,
- report maximum fuselage curvature,
- identify high-pressure/high-drag regions caused by poor streamlining,
- guide fuselage length and section changes toward smoother, slimmer bodies.

## Usage

From the project root:

```powershell
python EVALUATION/AGENTS/fuselage_smoothness/analyze.py
```

To analyze a specific model:

```powershell
python EVALUATION/AGENTS/fuselage_smoothness/analyze.py AIRCRAFT/MODEL_05_01_2026_62.json
```

The script also accepts a `.vsp3` path if the matching `.json` companion exists.

If the companion JSON contains an explicit `fuselage_stations` list, that
station profile is used directly. Otherwise the agent reconstructs a simplified
profile from legacy pod-and-boom fields.

## Outputs

Reports are written to:

```text
EVALUATION/fuselage_reports/<model>_fuselage_smoothness.json
```

Key fields:

| Field | Meaning |
|-------|---------|
| `max_radius_profile_curvature_1_per_m` | Maximum discrete curvature of equivalent-radius profile |
| `max_profile_slope_angle_deg` | Steepest equivalent-radius expansion or taper angle |
| `max_centerline_curvature_1_per_m` | Maximum vertical centerline curvature when station `z_center_m` data exists |
| `max_centerline_slope_angle_deg` | Steepest vertical centerline slope angle |
| `max_surface_curve_curvature_1_per_m` | Maximum discrete curvature across top, bottom, and side half-width lines |
| `max_surface_curve_slope_angle_deg` | Steepest top, bottom, or side half-width line slope |
| `fineness_ratio` | Total profile length divided by maximum equivalent diameter |
| `pressure_recovery_risk` | `low`, `medium`, or `high` heuristic risk |
| `smoothness_score_0_100` | Higher is smoother by current heuristic |

## Interpretation

High aft taper angle is treated as pressure-recovery risk because the flow may separate as the fuselage closes down. High curvature indicates abrupt section changes that should be replaced with intermediate sections or a longer transition.

## Test

```powershell
python EVALUATION/AGENTS/fuselage_smoothness/TEST/run_test.py
```

Expected: PASS and a fixture report written under `TEST/out/`.
