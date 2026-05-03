# Agent: batch_designer

## Role
This agent generates and evaluates a batch of aircraft after a specification change. It is used for broad exploration when the previous best design is no longer meaningful under the new constraints.

## What It Does
For each named variant, `batch_design.py`:
- writes a JSON override file,
- calls `DESIGN/AGENTS/baseline_generator/generate.py`,
- runs `SIMULATION/AGENTS/alpha_sweep/run_sweep.py` on that exact model,
- runs `EVALUATION/AGENTS/cost_scorer/score.py`,
- writes `out/latest_batch_report.json`.

## Usage

```
python DESIGN/AGENTS/batch_designer/batch_design.py
```

## Notes
The batch is intentionally conventional for now: compact tractor, high-aspect-ratio wings, small tail variations, and low-mass fuselage variants. The new specification is very mass-constrained, so the batch includes both compliant-stall designs and mass-minimization probes.
