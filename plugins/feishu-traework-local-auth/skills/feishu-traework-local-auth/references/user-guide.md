# User guide (runtime)

## Prerequisites

1. Trae client on this computer (`Trae` / `TRAE SOLO` / `Trae CN` / `TRAE SOLO CN`)
2. Logged in as the same OS user that will run the script
3. Feishu authorization for TraeWork completed inside Trae
4. `lark-cli` on `PATH`
5. Python 3.10+ and `pip install pycryptodome` (or `cryptography`)

## Run

```bash
SCRIPT="<skill-dir>/scripts/traework_local_auth.py"
python3 "$SCRIPT" status
python3 "$SCRIPT" whoami
```

Windows PowerShell:

```powershell
python "<skill-dir>\scripts\traework_local_auth.py" status
python "<skill-dir>\scripts\traework_local_auth.py" whoami
```

## Success

`whoami` JSON: TraeWork `appId`, `identity=user`, `available=true`.

## Failures

| Symptom | Action |
| --- | --- |
| No session / storage | Open Trae, log in, fully start the client |
| Cloud fetch fails | Re-do Feishu / TraeWork consent in Trae |
| `lark-cli` missing | Install CLI; fix `PATH` |
| Crypto import error | Install `pycryptodome` or `cryptography` |
| Custom data dir | Set `TRAE_STORAGE_JSON` to real `storage.json` |

## Overrides

| Env | Meaning |
| --- | --- |
| `TRAE_STORAGE_JSON` | Path to `storage.json` |
| `TRAE_JWT_TOKEN_PATH` | Optional JWT file |
| `TRAE_API_HOST` | Trae API host |
| `TRAEWORK_JWT_SOURCE` | `auto` (default), `storage`, `file` |

`export-env` prints a token — avoid unless you need shell exports and control history.
