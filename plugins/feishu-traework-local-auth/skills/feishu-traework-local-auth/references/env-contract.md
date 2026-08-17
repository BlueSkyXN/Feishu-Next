# Env contract (runtime)

Official `lark-cli` environment credentials:

| Variable | Role |
| --- | --- |
| `LARKSUITE_CLI_APP_ID` | TraeWork client id |
| `LARKSUITE_CLI_USER_ACCESS_TOKEN` | Short-lived Feishu user token |
| `LARKSUITE_CLI_BRAND` | `feishu` or `lark` |

Child inject also unsets `LARK_APP_ID`, `LARK_APP_SECRET`, `LARKSUITE_CLI_APP_SECRET` to avoid mixing secrets.

## lark-cli binary

| Variable | Role |
| --- | --- |
| `TRAEWORK_LARK_CLI` | Preferred working command name or exact-file override |
| `LARK_CLI` | Same override if `TRAEWORK_LARK_CLI` is unset |

Quoted paths, `~`, and environment variables are expanded. If neither override
is set, the helper scans `PATH`, common system/package-manager locations, and
the current agent/node environment, then uses `newest_version`.

## TraeWork client ids (public, not secrets)

| Region | Client id | Brand |
| --- | --- | --- |
| CN | `cli_a965abcba6fadbd3` | `feishu` |
| International | `cli_a96598a589b89dba` | `lark` |

Token is bound to that app id.

## Check

```bash
python3 scripts/traework_local_auth.py whoami
python3 scripts/traework_local_auth.py run -- whoami --json
```

Expect: matching `appId`, `identity=user`, `available=true`.

Use `run -- <lark-cli args>` for business commands. The helper injects the three variables into that child only.

Under env credentials, use `whoami` / `run` for diagnosis — not `auth login` / profile mutation.

Tokens are short-lived; `run` re-fetches before each command. Scope is TraeWork consent only.
