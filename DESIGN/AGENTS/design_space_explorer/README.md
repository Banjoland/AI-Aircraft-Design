# Agent: design_space_explorer

## Role
This agent increases the creative capability of the design system. It reads the current parametric OpenVSP generator, the latest score report, and the design guidelines, then produces ranked one-change geometry mutations for the next iteration.

It is intentionally a pre-simulation tool. It does not edit `generate.py` and does not write `.vsp3` files. Its job is to widen the design imagination while keeping each proposal traceable, constrained, and compatible with the project rule that each iteration changes only one aspect of the aircraft.

## When To Use
- Before choosing the next geometry edit.
- When the log shows a local optimum or a previous change regressed.
- When considering higher-creativity options from `DESIGN/DESIGN_GUIDELINES.md`, such as wing placement, twist, tail volume, canards, or tandem wings.

## What It Produces
`explore.py` writes:

```
DESIGN/AGENTS/design_space_explorer/out/latest_design_space_report.json
```

The report contains:
- Current baseline geometry metrics.
- Latest tested model, best numeric model, and best compliant model, which may differ after a regression or hard-constraint violation.
- Ranked candidate mutations.
- Parameter changes for each candidate.
- Heuristic score, risk, and creativity values.
- Estimated stall speed, horizontal tail volume, aspect ratio, empty mass, and constraint violations.

## Usage
Run from this directory:

```
python explore.py
```

or from the project root:

```
python DESIGN/AGENTS/design_space_explorer/explore.py
```

## Current Candidate Families
- Short-body plus larger horizontal tail chord.
- Horizontal tail chord increase.
- Wing longitudinal placement shift.
- Increased wing washout.
- Mid-wing vertical placement.
- Canard/tandem stall-safety probe.

The canard/tandem probe is deliberately marked as high creativity and high risk because it requires a new OpenVSP generator before direct simulation.

## Test
Run:

```
python TEST/run_test.py
```

Expected result: PASS, a JSON report is produced, at least four candidates are ranked, and each candidate includes metrics and constraint checks.
