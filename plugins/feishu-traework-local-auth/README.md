# Feishu TraeWork Local Auth

Optional Codex plugin: reuse **your own** TraeWork Feishu authorization on **this machine** with official `lark-cli` environment credentials.

Not the default Feishu Next auth path. For multi-user or no-Trae setups, register your own Feishu app.

Author: [BlueSkyXN](https://github.com/BlueSkyXN). Source: [plugin directory](https://github.com/BlueSkyXN/Feishu-Next/tree/main/plugins/feishu-traework-local-auth). License: `GPL-3.0-only` (see repo root `LICENSE`).

## Give this to someone else

Each recipient must use **their own** Trae login and TraeWork Feishu consent on **their own computer**. Do not copy `storage.json`, JWT files, or tokens.

Recipient checklist:

1. Trae / TRAE SOLO / Trae CN / TRAE SOLO CN installed and logged in
2. Feishu authorization completed inside TraeWork on that machine
3. Official `lark-cli` on PATH (or discoverable as a system/agent copy)
4. Python 3.10+ and `pip install -r skills/feishu-traework-local-auth/scripts/requirements.txt`

Then install from a local Feishu-Next checkout:

```bash
codex plugin marketplace add /path/to/Feishu-Next
codex plugin add feishu-traework-local-auth@feishu-next
```

```text
$feishu-traework-local-auth:feishu-traework-local-auth
```

Or ask the helper to introduce itself:

```bash
SCRIPT=plugins/feishu-traework-local-auth/skills/feishu-traework-local-auth/scripts/traework_local_auth.py
python3 "$SCRIPT" about
python3 "$SCRIPT" status
python3 "$SCRIPT" whoami
python3 "$SCRIPT" run -- whoami --json
```

Success: TraeWork `appId`, `identity=user`, `available=true`. Later business commands use `run -- <lark-cli args>`. Do not print the token.

Windows: session path and `run` are implemented; PowerShell should use `run`, not `export-env`. Windows has not been live-tested.

## Layers

| Layer | Path | Content |
| --- | --- | --- |
| **Skill (runtime)** | `skills/feishu-traework-local-auth/` | Commands, workflow, paths, env, limits |
| **This README** | plugin root | Install + recipient handoff |
| **Project docs** | `docs/traework-local-auth/` | Wording, cockpit-tools reference, architecture |

## Dependencies

- Trae client logged in; TraeWork Feishu authorization completed on this computer
- `lark-cli` on this machine (system or agent environment; newest version wins)
- Python 3.10+ and `pycryptodome` or `cryptography`

## Skill files (runtime only)

| File | Purpose |
| --- | --- |
| [SKILL.md](skills/feishu-traework-local-auth/SKILL.md) | Agent workflow |
| [about.md](skills/feishu-traework-local-auth/references/about.md) | Self-introduction |
| [user-guide.md](skills/feishu-traework-local-auth/references/user-guide.md) | Steps |
| [platforms.md](skills/feishu-traework-local-auth/references/platforms.md) | Paths |
| [env-contract.md](skills/feishu-traework-local-auth/references/env-contract.md) | `LARKSUITE_CLI_*` |
| [security-and-limits.md](skills/feishu-traework-local-auth/references/security-and-limits.md) | Runtime limits |
| [traework_local_auth.py](skills/feishu-traework-local-auth/scripts/traework_local_auth.py) | Helper |

## Project docs (not shipped as skill essays)

| File | Purpose |
| --- | --- |
| [docs/traework-local-auth/](../../docs/traework-local-auth/README.md) | Index |
| [wording.md](../../docs/traework-local-auth/wording.md) | Allowed / forbidden phrasing |
| [reference-cockpit-tools.md](../../docs/traework-local-auth/reference-cockpit-tools.md) | Reference object |
| [architecture.md](../../docs/traework-local-auth/architecture.md) | Design & verification |
