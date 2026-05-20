## Simulation Specification

The purpose of this document is to describe the analysis to be performed on the candidate aircraft.

| # | Analysis | Agent | Status |
|---|----------|-------|--------|
| 1 | Cruise speed at 75% power | `AGENTS/alpha_sweep/run_sweep.py` | ✅ |
| 2 | Stall speed | `AGENTS/alpha_sweep/run_sweep.py` | ✅ |
| 3 | Alpha sweep — performance vs AoA, longitudinal static stability (Cmα) | `AGENTS/alpha_sweep/run_sweep.py` | ✅ |
| 4 | Beta sweep — lateral/directional stability derivatives (CYβ, Clβ, Cnβ) | `AGENTS/beta_sweep/run_beta_sweep.py` | ✅ |
| 5 | Longitudinal dynamic modes — phugoid & short-period eigenvalues, damping, period | `AGENTS/dynamic_stability/analyze.py` | ✅ |
| 6 | Lateral dynamic modes — dutch roll, roll, spiral eigenvalues | `AGENTS/dynamic_stability/analyze.py` | ✅ |
| 7 | Mass distribution, CG, moments of inertia (Ixx, Iyy, Izz) | `AGENTS/inertia_estimator/estimate.py` | ✅ |
| 8 | Total wetted area and parasite drag breakdown | `AGENTS/parasite_drag/analyze.py` | ✅ |

## Recommended run order

```
1. openvsp-python DESIGN/AGENTS/spline_aircraft/generate.py         → AIRCRAFT/MODEL_xx.vsp3 + .json
2. openvsp-python SIMULATION/AGENTS/alpha_sweep/run_sweep.py        → SIMULATION/results/MODEL_xx_alpha_sweep.json
3. openvsp-python SIMULATION/AGENTS/beta_sweep/run_beta_sweep.py    → SIMULATION/results/MODEL_xx_beta_sweep.json
4. openvsp-python SIMULATION/AGENTS/parasite_drag/analyze.py        → SIMULATION/results/MODEL_xx_parasite_drag.json
5. python         SIMULATION/AGENTS/inertia_estimator/estimate.py   → SIMULATION/results/MODEL_xx_inertia.json
6. python         SIMULATION/AGENTS/dynamic_stability/analyze.py    → SIMULATION/results/MODEL_xx_dynamic_stability.json
7. python         EVALUATION/AGENTS/cost_scorer/score.py            → EVALUATION/scores/MODEL_xx_score.json
```

Steps 1–4 require the OpenVSP Python launcher. Steps 5–7 run with plain Python 3.