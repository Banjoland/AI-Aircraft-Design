# Agent: inertia_estimator

## Role
Estimate the mass distribution, center of gravity, and moments of inertia for an aircraft model. The outputs feed the dynamic stability analyzer.

## When to use
After a new model is generated (generate.py), run the inertia estimator before running the dynamic stability analysis.

## Steps
1. Identify the companion JSON for the most recent `MODEL_*.vsp3` in `AIRCRAFT/`.
2. Run `estimate.py`:
   ```
   python SIMULATION\AGENTS\inertia_estimator\estimate.py
   # or for a specific model:
   python SIMULATION\AGENTS\inertia_estimator\estimate.py AIRCRAFT\MODEL_xx.json
   ```
3. Results are written to `SIMULATION/results/<model_stem>_inertia.json`.

## Method

Components modelled:
| Component | Mass source | x position | y | z |
|-----------|-------------|-----------|---|---|
| Fuselage skin | `fuse_wetted × 6 kg/m²` | `L/2` | 0 | 0 |
| Wing skin | `wing_wetted × 6 kg/m²` | `wing_x + mac/4` | 0 | 0 |
| H-tail skin | `htail_wetted × 6 kg/m²` | `htail_x + mac/4` | 0 | 0 |
| V-tail skin | `vtail_wetted × 6 kg/m²` | `vtail_x + chord/4` | 0 | 0.15 |
| Engine | 40 kg (spec) | `x_engine` (center of engine bay) | 0 | 0 |
| Systems | 8 kg (spec) | `0.3 × L` | 0 | 0 |
| Fuel | `MTOW − empty − 117 kg` | near engine | 0 | 0 |
| Pilot + payload | 117 kg (spec) | `cockpit_x` | 0 | −0.30 m |

**Iyy** (pitch) = Σ mᵢ(xᵢ − x_CG)²

**Ixx** (roll) = wing plate (m_wing × b²/12) + Σ mᵢzᵢ² for non-wing components

**Izz** (yaw) ≈ Ixx + Iyy (perpendicular axis theorem)

## Output fields

```json
{
  "total_mass_kg": 218.0,
  "cg_x_m": 1.82,
  "Iyy_kgm2": 312.4,
  "Ixx_kgm2": 186.3,
  "Izz_kgm2": 498.7,
  "components": [...]
}
```

## Limitations
- Structural mass modelled purely as skin area × skin density (no internal frames, spars, ribs).
- Fuel mass equals the shortfall between MTOW and the sum of empty mass + useful load. If `empty_mass > MTOW − 117`, fuel mass = 0 (the design is over gross weight — fix the mass, not the inertia model).
- Ixx assumes the wing is the sole span-distributed mass; struts, pylons, etc. are ignored.

## Test
```
python SIMULATION\AGENTS\inertia_estimator\TEST\run_test.py
```
