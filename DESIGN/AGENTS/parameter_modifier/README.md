# Agent: parameter_modifier

## Role

This agent creates validated override JSON files for `DESIGN/AGENTS/baseline_generator/generate.py`.
It lets an agent implement many guideline modifications without manually editing
the generator source.

## Supported Changes

Run:

```powershell
python DESIGN/AGENTS/parameter_modifier/make_override.py --list
```

The tool lists guideline features that are currently parameter-modifiable, their
registered parameters, and the implementation method.

## Usage

Create a one-change override file:

```powershell
python DESIGN/AGENTS/parameter_modifier/make_override.py wingspan --set wing_span=10.0
```

Create and immediately run the generator through OpenVSP:

```powershell
python DESIGN/AGENTS/parameter_modifier/make_override.py wing_root_chord --set wing_root_chord=0.50 --run
```

Outputs are written to:

```text
DESIGN/AGENTS/parameter_modifier/out/
```

Each override also receives a `.manifest.json` file recording the guideline
feature, allowed parameters, and generator path.

## Safety Rules

- Use one feature per design iteration unless the user explicitly asks for a batch.
- Do not pass unrelated parameters unless `--allow-extra` is intentionally used.
- Use the modification registry first when unsure whether a feature is supported.
- Use `--run` only when you intend to generate a new aircraft model.

## Test

```powershell
python DESIGN/AGENTS/parameter_modifier/TEST/run_test.py
```

Expected: PASS, with dry-run override files written under `out/`.
