# Agent: dynamic_stability

## Role
Compute dynamic stability eigenvalues for the longitudinal and lateral-directional modes of the aircraft. The eigenvalue distances from the origin feed the stability cost function in the evaluator.

## When to use
After running both the alpha sweep and beta sweep, and after running the inertia estimator, run this analyzer to complete the stability picture. It replaces the Cm_alpha proxy currently used by the cost scorer.

## Dependencies
| Input | Required |
|-------|----------|
| `SIMULATION/results/<model>_alpha_sweep.json` | Yes — provides CLα, Cmα, cruise speed, L/D |
| `SIMULATION/results/<model>_inertia.json` | Strongly recommended — Iyy, Ixx, Izz for eigenvalue accuracy |
| `SIMULATION/results/<model>_beta_sweep.json` | Recommended — provides CYβ, Clβ, Cnβ directly from VLM |
| `AIRCRAFT/<model>.json` | Recommended — tail volume, MAC for Cmq estimation |

Missing inputs fall back to geometric estimates or spec constants.

## Steps
1. Run the alpha sweep, inertia estimator, and (optionally) beta sweep first.
2. Run the dynamic stability analyzer:
   ```
   python SIMULATION\AGENTS\dynamic_stability\analyze.py
   # or for a specific alpha sweep result:
   python SIMULATION\AGENTS\dynamic_stability\analyze.py \
       SIMULATION\results\MODEL_xx_alpha_sweep.json \
       SIMULATION\results\MODEL_xx_inertia.json
   ```
3. Results written to `SIMULATION/results/<model>_dynamic_stability.json`.

## Method

### Longitudinal dynamics

4-state linearized small-disturbance equations of motion (stability axes, level flight trim):

```
State: [Δu, Δw, Δq, Δθ]
A =  [[Xu,  Xw,  0,   -g ],
      [Zu,  Zw,  V0,   0 ],
      [Mu,  Mw,  Mq,   0 ],
      [0,   0,   1,    0 ]]
```

Where:
- **Xu, Zu**: speed derivatives from trim CL and CD
- **Xw, Zw**: AoA derivatives from CLα, CDα
- **Mw**: pitch stiffness from Cmα (direct output of alpha sweep)
- **Mq**: pitch rate damping, estimated from horizontal tail volume coefficient V_H

**Cmq estimation:** `Cmq ≈ -2 * η * CLα_tail * V_H * (l_t / c̄)`

### Lateral-directional dynamics

4-state model for [Δβ, Δp, Δr, Δφ]:
- **CYβ, Clβ, Cnβ**: from beta sweep (or geometric estimate)
- **Clp** (roll damping): from lifting line theory, `Clp ≈ -CLα/(4·AR) * (1+3λ)/(1+λ)`
- **Cnr** (yaw damping): from vtail volume, `Cnr ≈ -2 * Cnβ * (l_t/b)²`
- **Clr, Cnp**: Etkin approximations

### Mode identification

| Mode | Type | Longitudinal / Lateral | Desired |
|------|------|----------------------|---------|
| Phugoid | Oscillatory (slow) | Longitudinal | ζ > 0, |λ| large |
| Short period | Oscillatory (fast) | Longitudinal | ζ > 0.35, well damped |
| Dutch roll | Oscillatory | Lateral | ζ > 0.05, σ < 0 |
| Roll mode | Aperiodic | Lateral | τ < 1 s (fast convergence) |
| Spiral mode | Aperiodic | Lateral | σ < 0 (or T_double > 20 s) |

### Stability cost

`stability_cost = 1 / min(|λᵢ|)` over all longitudinal modes if all stable.

If any mode has σ > 0, `stability_cost = 100`.

This replaces the Cm_alpha proxy used previously (see `score.py`).

## Output fields

```json
{
  "stability_cost": 0.23,
  "stability_status": "stable",
  "min_eigenvalue_dist": 4.31,
  "longitudinal": {
    "modes": [
      {"name": "phugoid", "sigma": -0.04, "omega_rad_s": 0.18, "zeta": 0.22, "period_s": 35.1},
      {"name": "short_period", "sigma": -2.1, "omega_rad_s": 3.5, "zeta": 0.51}
    ],
    "all_stable": true
  },
  "lateral": {
    "modes": [
      {"name": "dutch_roll", "sigma": -0.15, "omega_rad_s": 1.2},
      {"name": "roll_mode",  "sigma": -8.3},
      {"name": "spiral_mode","sigma": -0.03}
    ]
  }
}
```

## Limitations
- Cmq uses an analytic estimate. A true Cmq requires a pitch-rate VLM sweep (not yet built).
- Lateral rate derivatives (Clp, Cnr) are approximated from geometry; they benefit from a rate sweep.
- Alpha-dot coupling (CmαD) is estimated as 0.5×Cmq — adequate for a first-pass analysis.
- The model assumes level flight trim (θ₀ ≈ 0) and uncoupled longitudinal/lateral motions.

## Test
```
python SIMULATION\AGENTS\dynamic_stability\TEST\run_test.py
```
