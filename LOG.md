# Design Log

EXAMPLE 

---

## Iteration 71 — 2026-05-11 (Architectural Change: Full Spline Fuselage)

### User directive

"Stop using the pod and boom. Write this in whichever file is necessary so that we don't go back to that approach. Then, design another aircraft using the wings and tail used in your last design, but with a single, aerodynamic body connecting them."

### Architecture prohibition recorded

Added permanent pod-and-boom prohibition to `CLAUDE.md`:

> *"The pod-and-boom configuration … is permanently retired. … All future designs must use a single continuous fuselage body from nose to tail, shaped by the two-spline fuselage generator."*

### New tool created

`DESIGN/AGENTS/spline_aircraft/generate.py` — complete aircraft generator combining:
- Two-spline fuselage (crown/keel/hw splines, C2 cubic, same approach as `two_spline_fuselage/`)
- Wing / htail / vtail / prop from MODEL_05_11_2026_03 parameter set (span 9.8 m, NACA 4412, etc.)

### Model: `MODEL_05_11_2026_07.vsp3`

**Fuselage geometry:**

| Parameter | Value |
|-----------|-------|
| Length | 5.0 m |
| Max equiv. diameter | 1.014 m |
| Fineness ratio | 4.93 |
| Cockpit width (at x=2.0 m) | 1.10 m |
| Fuselage wetted area | 10.34 m² |
| Smoothness score | 93.3 / 100 |
| Smoothness warnings | 2 (bot/hw slope 14.9°–15.2° at x=3.33 m) |

**Performance:**

| Metric | Value | Limit | Status |
|--------|-------|-------|--------|
| V_stall (VLM) | 20.47 m/s | ≤ 21.0 m/s | PASS |
| V_cruise (75% pwr) | 50.06 m/s | — | — |
| Cm_alpha | −0.486/deg | negative | stable |
| empty_mass (est.) | 170.5 kg | ≤ 110 kg | over-spec |

**Cost breakdown:**

| Term | Value |
|------|-------|
| stall_cost | 0.00 |
| stability_cost | 0.04 |
| mass_cost | 243.69 |
| cruise_reward | 0.80 |
| **total_cost** | **242.93** |

Previous best (pod-and-boom): 3.607

### Key finding

The single fuselage adds **42 kg** over the pod-and-boom (170.5 kg vs. 128.6 kg). At this mass the exponential mass cost term `exp(10×(m−110)/110) − 1` equals 243.7, overwhelming any aerodynamic benefit. The cruise speed is also slower (50.1 m/s vs 52.2 m/s) because the high CG placement and long nose moment arm force the tail to work harder (Cm_0 = −1.73, large trim drag).

The fundamental constraint is the 6 kg/m² skin density in the mass model. The full fuselage wetted area (10.34 m²) costs 62 kg in skin mass alone, versus ≈ 15 kg for the retired pod+boom. No amount of aerodynamic streamlining can recover 47 kg of extra skin mass in this cost function.

### Next actions required

The exponential mass cost function makes any full fuselage uncompetitive. The project must either:
1. **Revise the mass model** — lower the skin density assumption (e.g., carbon fiber rib-and-fabric at 2–3 kg/m²), or apply structural efficiency factors by component type.
2. **Continue iterating the full fuselage** — accept the higher score and optimize for minimum wetted area within the new architecture, acknowledging this is an exploration phase.

Decision deferred to user.

---

## Iteration 72 — 2026-05-11 (Sharp Tail, Pilot Clearance, Engine Bay)

### Changes from Iteration 71

Three geometry corrections applied to the spline aircraft generator:

1. **Sharp tail tip** — last cross-section changed from a small ellipse to `XS_POINT` (degenerate point). Spline knots at x=5.0m: top=bot=0.06m (converge), hw=0.00m → true zero-area tip.
2. **Pilot vertical clearance** — raised cockpit crown: z_top at x=2.0m from 0.48m → 0.68m, z_bot from −0.45m → −0.42m → cockpit height = 0.68+0.42 = 1.10m (spec requirement: ≥1.07m for a 2m pilot seated).
3. **Engine bay expansion** — added knot at x=0.30m: top=0.32m, bot=−0.30m, hw=0.30m → bay height=0.62m, width=0.60m at x=0.30m (spec: 0.6m × 0.6m, engine body from x=0.30–1.10m).

Smoothness check updated to skip x=0 (nose tip slopes are a spline boundary artifact; attached forebody flow has no separation risk).

### Model: `MODEL_05_11_2026_10.vsp3`

**Compliance checks (all PASS):**

| Check | Value | Requirement | Status |
|-------|-------|-------------|--------|
| Pilot clearance (cockpit height) | 1.099 m | ≥ 1.07 m | PASS |
| Engine bay height | 0.62 m | ≥ 0.60 m | PASS |
| Engine bay width | 0.60 m | ≥ 0.60 m | PASS |
| Sharp tail tip | XS_POINT | — | PASS |

**Performance:**

| Metric | Value | Limit | Status |
|--------|-------|-------|--------|
| V_stall (VLM) | 20.31 m/s | ≤ 21.0 m/s | PASS |
| V_cruise (75% pwr) | 48.58 m/s | — | — |
| Cm_alpha | −0.488/deg | negative | stable |
| empty_mass (est.) | 173.9 kg | ≤ 110 kg | over-spec |

**Cost:** total=331.62 (stall=0, stability=0.04, mass=332.32, cruise_reward=0.73)

### Notes

The taller cockpit added ~3.4 kg (0.57 m² more fuselage wetted area × 6 kg/m²), increasing the mass cost from 243.7 to 332.3. This worsened the total cost. The mass model remains the binding constraint: full fuselage architecture scores ~100× worse than pod-and-boom under the current 6 kg/m² skin density assumption.

The aircraft is geometrically correct per specification. The cost function result reflects a structural model mismatch, not an aerodynamic failure.

---
