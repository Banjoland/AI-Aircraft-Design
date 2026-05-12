# Two-Spline Fuselage Generator

Generates a smooth, streamlined fuselage from three globally-controlled splines
instead of manually-specified cross-section dimensions.

## Concept

The entire fuselage shape is controlled by three C2 cubic splines:

```
z_top(x)       — top profile (uppermost z at each x station)
z_bot(x)       — bottom profile (lowermost z at each x station)
half_width(x)  — half the width at each x station
```

At any station x, the cross-section is an **ellipse** with:
- `height = z_top(x) - z_bot(x)`
- `z_center = (z_top(x) + z_bot(x)) / 2`
- `width = 2 * half_width(x)`

The splines are natural cubic splines (C2 everywhere) fit through user-supplied
control points. Changing a single control point reshapes the fuselage smoothly
without creating lumps or kinks between sections.

## Why splines instead of sections?

Previous smooth_fuselage_redesign generators specified section dimensions
independently. This caused:
- Lumpy transitions when adjacent sections had incompatible slopes
- Difficulty achieving smooth aft pressure recovery
- No global curvature control

Two-spline generation guarantees:
- C2 continuity (smooth curvature) at every station
- Explicit slope and curvature checking before model creation
- Design variables are the spline knots — aerodynamically meaningful

## Streamlining principles built in

The generator:
1. Checks slope at every station — flags if > 12° (aft taper separation risk)
2. Checks curvature — flags if > 0.6/m (sharp inflection)
3. Reports fineness ratio (target: 5–8 for minimum fuselage drag)
4. Reports a smoothness score (0–100)

## Usage

```powershell
# Default aerodynamic spline design
openvsp-python DESIGN\AGENTS\two_spline_fuselage\generate.py

# Custom spline control points
openvsp-python DESIGN\AGENTS\two_spline_fuselage\generate.py spec.json
```

## Spec file format

```json
{
  "total_length_m": 5.5,
  "n_sections": 14,

  "top_spline_knots": [
    [0.00, 0.20],
    [2.80, 1.02],
    [5.50, 0.60]
  ],

  "bot_spline_knots": [
    [0.00, -0.20],
    [2.80, -0.44],
    [5.50,  0.60]
  ],

  "hw_spline_knots": [
    [0.00, 0.20],
    [2.80, 0.55],
    [5.50, 0.08]
  ],

  "wing_x_m": 2.80,
  "wing_z_m": 1.10,
  "htail_x_m": 4.95,
  "x_cg_m": 2.80,

  "max_slope_deg_warning": 12.0,
  "max_curvature_warning": 0.6
}
```

## Test

```powershell
python DESIGN\AGENTS\two_spline_fuselage\TEST\run_test.py
```

## Design guidelines for streamlined fuselage

| Parameter | Target | Effect |
|-----------|--------|--------|
| Fineness ratio | 5–8 | Minimum form drag |
| Max aft slope | < 12° | Avoids boundary layer separation |
| Max curvature | < 0.6/m | Prevents abrupt local pressure peaks |
| Top-to-bottom asymmetry | Gradual | Engine low, cockpit high |
| Nose taper half-angle | 10–18° | Attached flow, low drag |

## Integration with parasite drag analysis

After generating a fuselage model:
1. Run `SIMULATION/AGENTS/parasite_drag/analyze.py` on the model.
2. Check the fuselage form factor and fineness ratio.
3. If form factor > 1.4, adjust the aft knots to elongate the tail taper.
4. If form factor > 1.8, re-examine nose and aft slopes.
