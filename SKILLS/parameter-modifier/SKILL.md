---
name: parameter-modifier
description: Create validated baseline_generator override files for parameterized aircraft design modifications from DESIGN_GUIDELINES.md. Use when changing span, chords, fuselage dimensions, tail area, prop diameter, wing incidence, or other registered generator parameters.
compatibility: Designed for this OpenVSP aircraft design project. Requires Python; OpenVSP is only required when using --run.
---

# Parameter Modifier Skill

Use this skill when a guideline modification maps to a generator parameter and
you want to prepare a one-change design iteration without editing `generate.py`.

## Tool

List supported feature slugs:

```powershell
python DESIGN/AGENTS/parameter_modifier/make_override.py --list
```

Create an override:

```powershell
python DESIGN/AGENTS/parameter_modifier/make_override.py wingspan --set wing_span=10.0
```

Create and run the generator:

```powershell
python DESIGN/AGENTS/parameter_modifier/make_override.py wingspan --set wing_span=10.0 --run
```

## Workflow

1. Run the modification registry audit if the feature support is unknown.
2. Use this tool only for features marked `implemented` or `partial` with
   registered parameters.
3. Change one feature per design iteration unless doing an explicit batch.
4. Run simulation and evaluation after generating a model.
5. Record the impact in the relevant memory doc and `LOG.md`.

## Test

```powershell
python DESIGN/AGENTS/parameter_modifier/TEST/run_test.py
```
