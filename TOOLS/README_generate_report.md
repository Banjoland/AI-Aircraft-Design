# Tool: generate_report

## Role
Read all pipeline result JSONs for a model and write a formatted Markdown design report to `REPORTS/<stem>_report.md`.

## When to use
After running the full pipeline on a model, to get a single human-readable summary of all results including geometry, aerodynamics, stability, weight, range, and the iteration suggestion.

## Usage

```
python TOOLS\generate_report.py                          # most recent scored model
python TOOLS\generate_report.py AIRCRAFT\MODEL_xx.json  # specific model
python TOOLS\generate_report.py --all                   # all scored models
```

## Sections covered

| Section | Source file |
|---|---|
| Score summary | `EVALUATION/scores/<stem>_score.json` |
| Geometry | `AIRCRAFT/<stem>.json` |
| Aerodynamics (alpha sweep) | `SIMULATION/results/<stem>_alpha_sweep.json` |
| Lateral derivatives (beta sweep) | `SIMULATION/results/<stem>_beta_sweep.json` |
| Static margin | `SIMULATION/results/<stem>_static_margin.json` |
| Dynamic stability modes | `SIMULATION/results/<stem>_dynamic_stability.json` |
| Range & fuel budget | `SIMULATION/results/<stem>_range.json` |
| Parasite drag breakdown | `SIMULATION/results/<stem>_parasite_drag.json` |
| Inertia distribution | `SIMULATION/results/<stem>_inertia.json` |
| Weight estimate | `DESIGN/AGENTS/weight_estimator/<stem>_weight.json` |
| Tail sizing assessment | `DESIGN/AGENTS/tail_sizing/<stem>_tail_size.json` |
| Constraint diagram | `DESIGN/AGENTS/constraint_diagram/constraint_diagram.json` |
| Iteration suggestion | `DESIGN/AGENTS/iteration_suggester/<stem>_suggestion.json` |

Missing files are silently skipped — the report shows whatever data is available.

## Output

`REPORTS/<stem>_report.md` — complete design card in GitHub-flavored Markdown.

## Test

```
python TOOLS\TEST\run_test.py
```
