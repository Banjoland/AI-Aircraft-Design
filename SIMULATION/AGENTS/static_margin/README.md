# Agent: static_margin

## Role
Compute the stick-fixed neutral point, static margin, and CG position limits. Provides actionable recommendations for CG adjustment.

## When to use
After the alpha sweep. Useful when evaluating whether a design change has shifted the CG in or out of the acceptable range.

## Steps
```
python SIMULATION\AGENTS\static_margin\compute.py
# or for a specific model:
python SIMULATION\AGENTS\static_margin\compute.py \
    SIMULATION\results\MODEL_xx_alpha_sweep.json \
    AIRCRAFT\MODEL_xx.json
```

## Theory

### Static margin
```
SM = −(dCm/dCL) = −(Cm_alpha / CL_alpha)    [dimensionless, fraction of MAC]
```
Positive SM means the neutral point (NP) is behind the CG → aircraft is stable.

### Neutral point
```
x_NP = x_CG + SM × c_bar
```

### Stability window
| SM (fraction MAC) | Assessment |
|---|---|
| < 0.05 | Marginal — may depart in turbulence |
| 0.05–0.30 | Good — recommended design range |
| > 0.30 | Over-stable — excessive trim drag, poor cruise efficiency |

## Key output fields
```json
{
  "static_margin": {
    "SM": 0.142,
    "SM_pct_mac": 14.2,
    "x_NP_m": 2.042,
    "x_CG_m": 1.880,
    "SM_status": "GOOD"
  },
  "cg_limits": {
    "cg_aft_limit_m": 1.943,
    "cg_fwd_limit_m": 1.749,
    "cg_range_m": 0.194
  },
  "recommendations": ["..."]
}
```

## Important caveat
The static margin from VSPAERO depends critically on where moments are referenced. If `x_cg_m` in the companion JSON is inaccurate, Cm_alpha will be computed about the wrong point and the SM will be wrong. Always verify that the alpha sweep used the correct CG from the companion JSON.

## Test
```
python SIMULATION\AGENTS\static_margin\TEST\run_test.py
```
