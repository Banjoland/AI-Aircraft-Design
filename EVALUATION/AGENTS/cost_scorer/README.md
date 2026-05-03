# Agent: cost_scorer

## Role
You are the evaluation agent. Your job is to read the most recent alpha-sweep simulation results and compute the total cost-function score defined in `EVALUATION/COST FUNCTION.md`. Lower total cost = better design.

## Skill: score_design

### When to use
After a simulation has been run and `SIMULATION/results/<model>_alpha_sweep.json` exists. Call this agent to score the design and compare against the previous best.

### Steps
1. Identify the most recent `*_alpha_sweep.json` in `SIMULATION/results/` (newest by modification time). If a specific file path is given, use that.
2. Run `score.py` via plain Python (no OpenVSP required):
   ```
   python score.py
   ```
   Run this from the `EVALUATION/AGENTS/cost_scorer/` directory. To score a specific file:
   ```
   python score.py "C:\...\SIMULATION\results\MODEL_xx_alpha_sweep.json"
   ```
3. Parse the JSON printed to stdout.
4. Report back: model name, stall_cost, stability_cost, cruise_reward, total_cost, and whether this is an improvement over the previous best.

### Outputs
- `EVALUATION/scores/<model_stem>_score.json` — score report
- JSON summary on stdout with the fields listed below

### Key output fields
| Field | Description |
|-------|-------------|
| `stall_cost` | `(V_stall - 21.0)^2` if V_stall > 21.0 m/s, else 0 |
| `stability_cost` | `1 / |Cm_alpha_rad|` if stable; `100` if unstable or Cm_alpha=0 |
| `cruise_reward` | `min(exp(3 * (V_cruise - 54.2) / 54.2), 100)` - subtracted from total |
| `total_cost` | `stall_cost + stability_cost + mass_cost - cruise_reward` — **minimize this** |
| `stall_note` | Human-readable explanation of stall penalty |
| `stability_note` | Human-readable explanation of stability cost |
| `cruise_note` | Human-readable explanation of cruise reward |

### Cost function reference values
| Parameter | Value | Source |
|-----------|-------|--------|
| V_stall spec | 21.0 m/s | SPECIFICATION.md |
| V_cruise reference | 54.2 m/s | SPECIFICATION.md |
| Empty mass spec | 110 kg | SPECIFICATION.md |
| Max stability penalty | 100.0 | Assigned when Cm_alpha unresolved or unstable |

### Interpreting scores
| Score component | Meaning | How to improve |
|----------------|---------|----------------|
| stall_cost > 0 | V_stall exceeds 21.0 m/s | Increase wing area or CL_max |
| stability_cost = 100 | Aircraft unstable or Cm_alpha=0 | Ensure CG is set; Cm_alpha must be < 0 |
| stability_cost = small (< 1) | Very stable — strong restoring moment | May be over-stable; check tail volume |
| cruise_reward > 1 | Cruise speed above 54.2 m/s reference | Good - reward grows exponentially |

### Test
```
python TEST/run_test.py
```
Expected: PASS, score file created in `EVALUATION/scores/`, total_cost field present.
