# User guide (runtime)

## Prerequisites

1. Trae client on this computer (`Trae` / `TRAE SOLO` / `Trae CN` / `TRAE SOLO CN`)
2. Logged in as the same OS user that will run the script
3. Feishu authorization for TraeWork completed inside Trae
4. A system or agent-environment `lark-cli` (script scans both and prefers the newest)
5. Python 3.10+ with `pycryptodome` (preferred) or `cryptography`

## Let the agent prepare the runtime

Use one Python for checks, `pip`, and the helper. Do not use bare `pip`.

macOS / Linux:

```bash
PYTHON=python3
"$PYTHON" --version
"$PYTHON" -c "import Crypto" 2>/dev/null || \
  "$PYTHON" -c "import cryptography" 2>/dev/null || \
  "$PYTHON" -m pip install -r "<skill-dir>/scripts/requirements.txt"
```

Windows PowerShell: try `python` first, then `py -3`.

```powershell
$PY = (Get-Command python -ErrorAction SilentlyContinue).Source
$PY_ARGS = @()
if ($PY) {
    & $PY -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
    if ($LASTEXITCODE -ne 0) { $PY = $null }
}
if (-not $PY) {
    $PY = (Get-Command py -ErrorAction Stop).Source
    $PY_ARGS = @("-3")
}

& $PY @PY_ARGS --version
& $PY @PY_ARGS -c "import Crypto" 2>$null
if ($LASTEXITCODE -ne 0) { & $PY @PY_ARGS -c "import cryptography" 2>$null }
if ($LASTEXITCODE -ne 0) {
    & $PY @PY_ARGS -m pip install -r "<skill-dir>\scripts\requirements.txt"
}
```

The helper never runs `pip` itself. If site-packages is not writable, create a
per-user venv and continue with that interpreter; do not require Administrator
or `sudo`.

```bash
python3 -m venv "${XDG_CACHE_HOME:-$HOME/.cache}/feishu-next/traework-local-auth/venv"
```

```powershell
& $PY @PY_ARGS -m venv "$env:LOCALAPPDATA\Feishu-Next\traework-local-auth\venv"
```

Prefer PowerShell on Windows. A full `cmd.exe` recipe is not maintained here.

## Run

```bash
SCRIPT="<skill-dir>/scripts/traework_local_auth.py"
python3 "$SCRIPT" about
python3 "$SCRIPT" status
python3 "$SCRIPT" resolve-lark-cli
python3 "$SCRIPT" whoami
python3 "$SCRIPT" run -- whoami --json
python3 "$SCRIPT" run -- drive +search --as user --page-size 3
```

Windows PowerShell:

```powershell
$SCRIPT = "<skill-dir>\scripts\traework_local_auth.py"
& $PY @PY_ARGS $SCRIPT about
& $PY @PY_ARGS $SCRIPT status
& $PY @PY_ARGS $SCRIPT resolve-lark-cli
& $PY @PY_ARGS $SCRIPT whoami
& $PY @PY_ARGS $SCRIPT run -- whoami --json
& $PY @PY_ARGS $SCRIPT run -- drive +search --as user --page-size 3
```

## Success

`whoami` JSON: TraeWork `appId`, `identity=user`, `available=true`.

To use the token, prefer `run`. It fetches a short-lived UAT, injects `LARKSUITE_CLI_*` into one child process, and executes the resolved `lark-cli`. The token is not printed. Do not `auth login` in that process.

## Failures

| Symptom | Action |
| --- | --- |
| No session / storage | Open Trae, log in, fully start the client |
| Cloud fetch fails | Re-do Feishu / TraeWork consent in Trae |
| `lark-cli` missing | Install CLI, or set `TRAEWORK_LARK_CLI` / `LARK_CLI` to a working command or file |
| Crypto import error | Read `runtime.python_executable`; install `pycryptodome` with that interpreter and retry |
| `pip` missing / access denied | Create the per-user venv above and continue with its Python |
| Works in PowerShell but resolver misses it | Run `Get-Command lark-cli -All` and `where.exe lark-cli`; on Windows set `TRAEWORK_LARK_CLI` to `lark-cli.exe` or its full path, not a Mac-style unsuffixed name |
| Session path reports `PermissionError` | Run the Agent as the same interactive OS user that logged into Trae; check sandbox/app access before changing ACLs |
| Custom data dir | Set `TRAE_STORAGE_JSON` to real `storage.json` |

## Overrides

| Env | Meaning |
| --- | --- |
| `TRAE_STORAGE_JSON` | Path to `storage.json` |
| `TRAE_JWT_TOKEN_PATH` | Optional JWT file |
| `TRAE_API_HOST` | Trae API host |
| `TRAEWORK_JWT_SOURCE` | `auto` (default), `storage`, `file` |
| `TRAEWORK_LARK_CLI` / `LARK_CLI` | Working command or file. Windows: prefer `lark-cli.exe`. macOS/Linux: `lark-cli` with no `.exe`. Skips newest-version selection |

Default `lark-cli` policy: scan current `PATH`, common system bins, npm/pnpm,
fnm/nvm, and the current agent/node environment; pick the newest runnable
version. On Windows, `lark-cli.exe` beats `.cmd` / `.bat` at the same version.
macOS and Linux only look for unsuffixed `lark-cli`. Same version then prefers
the `PATH` copy.

`export-env` prints a token — avoid unless you need shell exports and control history. `run` is the default way to consume the token on both bash and PowerShell.
