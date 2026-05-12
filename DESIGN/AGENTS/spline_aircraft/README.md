# spline_aircraft — Complete Aircraft Generator

Generates a complete single-engine tractor aircraft using a single spline-driven fuselage body. No pod-and-boom. The fuselage runs continuously from engine nose to tail tip.

## Architecture

Three globally-smooth C2 cubic splines define all fuselage cross-sections:

| Spline | Controls |
|--------|---------|
| `top_spline_knots` | Crown z-coordinate at each x station |
| `bot_spline_knots` | Keel z-coordinate at each x station |
| `hw_spline_knots`  | Half-width at each x station |

Each cross-section is an ellipse:
- `height  = z_top(x) - z_bot(x)`
- `width   = 2 * hw(x)`
- `z_center = (z_top + z_bot) / 2`

Wing, horizontal tail, vertical tail, and propeller disk attach to the fuselage as children.

## Usage

```bash
# Default streamlined design
openvsp-python generate.py

# Custom spline spec override
openvsp-python generate.py path/to/override.json
```

Override JSON keys are merged into `DEFAULT_SPEC`. Any key in the spec can be overridden.

## Output

- `AIRCRAFT/MODEL_MM_DD_YYYY_XX.vsp3` — OpenVSP model
- `AIRCRAFT/MODEL_MM_DD_YYYY_XX.json` — companion JSON with geometry and mass estimates

## Default design parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Fuselage length | 5.0 m | Fineness ≈ 5 at cockpit |
| Cockpit width | 1.10 m | At x=2.0 m, spec minimum |
| Cockpit height | 0.93 m | At x=2.0 m |
| Wing span | 9.8 m | Unchanged from MODEL_05_11_2026_03 |
| Wing airfoil | NACA 4412 | |
| Wing chord (root/tip) | 0.52 / 0.34 m | |
| H-tail span | 1.6 m | |
| V-tail height | 0.70 m | |
| Prop diameter | 1.10 m | |

## Mass model

All wetted area × 6 kg/m² skin density + 40 kg engine + 8 kg systems.
Fuselage wetted area is computed by integrating Ramanujan ellipse perimeters along the spline stations.

## Design guidelines for fuselage tuning

| Target | Approach |
|--------|---------|
| Reduce drag | Increase fineness ratio (longer fuselage or smaller cross-section) |
| Reduce mass | Reduce wetted area — shorter or slimmer fuselage |
| Both | Optimize L/D_equiv tradeoff around fineness 5–8 |

Smoothness warnings are printed to stderr when:
- Any spline slope exceeds 14° (separation risk)
- Curvature exceeds 0.7 /m (local kink risk)

## Test

```bash
openvsp-python TEST/run_test.py
```
