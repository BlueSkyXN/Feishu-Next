---
name: feishu-traework-local-auth
description: Use when reusing this machine's already-granted TraeWork Feishu authorization with official lark-cli environment credentials. Do not use as the default Feishu Next auth path or without a local Trae login.
metadata:
  version: "0.1"
  updated: "2026-08-14"
---

# Feishu TraeWork local auth

Reuse **your own** user-owned TraeWork Feishu authorization on **this machine**. Optional only — not default Feishu Next auth.

## Script

```text
scripts/traework_local_auth.py
```

```bash
python3 "<skill-dir>/scripts/traework_local_auth.py" status
python3 "<skill-dir>/scripts/traework_local_auth.py" whoami
```

| Command | Secrets on stdout? | Use |
| --- | --- | --- |
| `status` | No | Session / readiness probe |
| `decrypt-check` | No | Confirm local session readable |
| `fetch-uat` | No | Confirm cloud token fetch (meta only) |
| `whoami` | No | Inject env + `lark-cli whoami` |
| `export-env` | **Yes** | Only if user explicitly asks; warn about shell history |

## Workflow

1. Prerequisites: Trae logged in on this OS user; TraeWork Feishu consent done; `lark-cli` + Python 3.10+; `pycryptodome` or `cryptography`.
2. `status` — stop if no local session ([platforms.md](references/platforms.md)).
3. `whoami` (prefer over `export-env`).
4. Success: TraeWork `appId`, `identity=user`, `available=true`.
5. Business `lark-cli` only in an env that still has `LARKSUITE_CLI_*`.
6. On failure: no invented tokens; no `auth login` to "fix" env mode; re-authorize in Trae or use a self-owned app.

## Hard rules

- Never print JWT / UAT / refresh / full session JSON.
- Never write Trae `storage.json` or switch accounts.
- Never dump OS keychain / Credential Manager.
- Never commit or paste tokens.
- Diagnose with `whoami`, not `auth login`, under env credentials.

## Runtime refs only

| Need | File |
| --- | --- |
| Install / steps | [user-guide.md](references/user-guide.md) |
| Paths / overrides | [platforms.md](references/platforms.md) |
| Env vars | [env-contract.md](references/env-contract.md) |
| Limits while running | [security-and-limits.md](references/security-and-limits.md) |

Wording, cockpit-tools attribution, and design notes are **not** in this skill — see repo `docs/traework-local-auth/` when the full checkout is available.

After identity is ready, hand off Feishu work to `$feishu-next:feishu-workflow-router` or official `lark-cli` skills.
