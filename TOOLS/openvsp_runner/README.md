# openvsp_runner

Thin subprocess wrapper around the OpenVSP-bundled Python launcher (`openvsp-python.cmd`). All agent tools that drive OpenVSP call through this module.

## Dependency

OpenVSP 3.49.0 must be installed at:

```
C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\
```

The launcher `openvsp-python.cmd` (at that directory root) invokes the bundled Python 3.11 venv at `python\.venv\Scripts\python.exe` with the `-P` flag to avoid import collisions with the local `openvsp/` source folder.

## Usage

### From Python (as a module)

```python
import sys
sys.path.insert(0, "<project_root>")
from TOOLS.openvsp_runner.runner import run

result = run("my_script.py", cwd="/path/to/working/dir", args=["optional-input.json"])
print(result.stdout)    # captured stdout from OpenVSP Python process
print(result.returncode)  # 0 = success
```

`RunResult` fields:
| Field | Type | Description |
|-------|------|-------------|
| `returncode` | `int` | Process exit code (0 = ok) |
| `stdout` | `str` | Captured stdout |
| `stderr` | `str` | Captured stderr |
| `elapsed_s` | `float` | Wall-clock seconds |
| `ok` | `bool` | `True` if returncode == 0 |

### From the command line

```
python runner.py path/to/script.py optional-input.json
```

stdout/stderr are forwarded; exit code is passed through.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `script_path` | required | Path to a Python script that `import openvsp` |
| `cwd` | script's directory | Working directory for the subprocess |
| `args` | `None` | Additional command-line arguments passed to the script |
| `timeout` | 300 s | Kill subprocess after this many seconds |

## Testing

Run the bundled smoke test to verify the environment works end-to-end:

```
python TEST/run_test.py
```

Expected output (abbreviated):
```
Running sample_wing.py via openvsp_runner...
--- stdout ---
OK wrote .../sample_wing.vsp3

Return code : 0
Elapsed     : 3.2s

PASS  (12345 bytes, 3.2s)
```

The test creates `TEST/sample_wing.vsp3` (a single wing geometry). A non-zero exit or missing file means the OpenVSP installation is broken or the launcher path needs updating.
