---
name: feishu-traework-local-auth
description: "Use when reusing this machine's already-granted TraeWork Feishu authorization with official lark-cli environment credentials, including extracting TraeWork Feishu tokens, asking how to use that token, checking Windows/macOS/Linux support, resolving system vs agent lark-cli, or requesting this helper's self-introduction. Do not use as the default Feishu Next auth path, without a local Trae login, or for multi-user/server setups."
metadata:
  version: "0.2"
  updated: "2026-08-17"
---

# Feishu TraeWork local auth

Reuse this OS user's already-granted, user-owned TraeWork Feishu authorization on this machine. Optional only — not default Feishu Next auth.

## Script

```text
scripts/traework_local_auth.py
```

Prefer executing the script over rereading it. Do not print tokens.

```bash
python3 "<skill-dir>/scripts/traework_local_auth.py" about
python3 "<skill-dir>/scripts/traework_local_auth.py" status
python3 "<skill-dir>/scripts/traework_local_auth.py" whoami
python3 "<skill-dir>/scripts/traework_local_auth.py" run -- drive +search --as user --page-size 3
```

| Command | Secrets on stdout? | Use |
| --- | --- | --- |
| `about` | No | Self-intro: TraeWork, Windows, usage, use cases |
| `status` | No | Session / lark-cli readiness |
| `decrypt-check` | No | Confirm local session readable |
| `fetch-uat` | No | Confirm cloud token fetch (meta only) |
| `resolve-lark-cli` | No | Scan system/agent copies; pick newest |
| `whoami` | No | Inject env + resolved `lark-cli whoami` |
| `run` | No | Consume the token: fetch UAT and exec `lark-cli` |
| `export-env` | **Yes** | Only if the user explicitly asks; warn about shell history |

## Workflow

1. For "what is this", TraeWork, Windows, usage, or use cases: run `about`. Read [about.md](references/about.md) only if the command cannot run.
2. Require Trae login, completed TraeWork Feishu consent, `lark-cli`, Python 3.10+, and `pycryptodome` or `cryptography`. Setup details: [user-guide.md](references/user-guide.md).
3. Run `status`. If no session, use [platforms.md](references/platforms.md). Confirm `lark_cli_resolution` is runnable; default is newest version across PATH, system, and agent copies.
4. Run `whoami`. Success: TraeWork `appId`, `identity=user`, `available=true`.
5. For business `lark-cli`, use `run -- <args>`. That injects `LARKSUITE_CLI_*` for one child process. Env contract: [env-contract.md](references/env-contract.md). Do not `export-env` unless the user explicitly wants shell exports.
6. Do not use `auth login` / profile / config mutation to repair env credentials. If it fails, re-authorize in Trae or use a self-owned app.
7. After identity is ready, hand off to `$feishu-next:feishu-workflow-router` or official `lark-cli` skills.

## Hard rules

- Never print JWT / UAT / refresh / full session JSON.
- Never write Trae `storage.json` or switch accounts.
- Never dump OS keychain / Credential Manager.
- Never commit or paste tokens.
- Diagnose with `whoami` or `run`, not `auth login`, under env credentials.

## Runtime refs only

| Need | Load |
| --- | --- |
| Self-intro | run `about`; [about.md](references/about.md) only as fallback |
| First-time setup / failures | [user-guide.md](references/user-guide.md) |
| Session path missing | [platforms.md](references/platforms.md) |
| Env vars / app id | [env-contract.md](references/env-contract.md) |
| Extra limits | [security-and-limits.md](references/security-and-limits.md) |

Wording and design notes are not in this skill. If the repo checkout is present, see `docs/traework-local-auth/`.
