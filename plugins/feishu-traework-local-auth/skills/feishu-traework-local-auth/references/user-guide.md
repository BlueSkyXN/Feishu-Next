# User guide (runtime)

## Prerequisites

1. Trae client on this computer (`Trae` / `TRAE SOLO` / `Trae CN` / `TRAE SOLO CN`)
2. Logged in as the same OS user that will run the script
3. Feishu authorization for TraeWork completed inside Trae
4. A system or agent-environment `lark-cli` (script scans both and prefers the newest)
5. Python 3.10+ and `pip install pycryptodome` (or `cryptography`)

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
python "<skill-dir>\scripts\traework_local_auth.py" about
python "<skill-dir>\scripts\traework_local_auth.py" status
python "<skill-dir>\scripts\traework_local_auth.py" resolve-lark-cli
python "<skill-dir>\scripts\traework_local_auth.py" whoami
python "<skill-dir>\scripts\traework_local_auth.py" run -- whoami --json
python "<skill-dir>\scripts\traework_local_auth.py" run -- drive +search --as user --page-size 3
```

## Success

`whoami` JSON: TraeWork `appId`, `identity=user`, `available=true`.

To use the token, prefer `run`. It fetches a short-lived UAT, injects `LARKSUITE_CLI_*` into one child process, and executes the resolved `lark-cli`. The token is not printed. Do not `auth login` in that process.

## Failures

| Symptom | Action |
| --- | --- |
| No session / storage | Open Trae, log in, fully start the client |
| Cloud fetch fails | Re-do Feishu / TraeWork consent in Trae |
| `lark-cli` missing | Install CLI, or set `TRAEWORK_LARK_CLI` / `LARK_CLI` to the binary |
| Crypto import error | Install `pycryptodome` or `cryptography` |
| Custom data dir | Set `TRAE_STORAGE_JSON` to real `storage.json` |

## Overrides

| Env | Meaning |
| --- | --- |
| `TRAE_STORAGE_JSON` | Path to `storage.json` |
| `TRAE_JWT_TOKEN_PATH` | Optional JWT file |
| `TRAE_API_HOST` | Trae API host |
| `TRAEWORK_JWT_SOURCE` | `auto` (default), `storage`, `file` |
| `TRAEWORK_LARK_CLI` / `LARK_CLI` | Exact `lark-cli` binary; skips newest-version selection |

Default `lark-cli` policy: scan current `PATH`, well-known system bins, and the current agent/node environment; pick the newest runnable version. Same version prefers the `PATH` copy.

`export-env` prints a token — avoid unless you need shell exports and control history. `run` is the default way to consume the token on both bash and PowerShell.
