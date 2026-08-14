# Env contract (runtime)

Official `lark-cli` environment credentials:

| Variable | Role |
| --- | --- |
| `LARKSUITE_CLI_APP_ID` | TraeWork client id |
| `LARKSUITE_CLI_USER_ACCESS_TOKEN` | Short-lived Feishu user token |
| `LARKSUITE_CLI_BRAND` | `feishu` or `lark` |

Child inject also unsets `LARK_APP_ID`, `LARK_APP_SECRET`, `LARKSUITE_CLI_APP_SECRET` to avoid mixing secrets.

## TraeWork client ids (public, not secrets)

| Region | Client id | Brand |
| --- | --- | --- |
| CN | `cli_a965abcba6fadbd3` | `feishu` |
| International | `cli_a96598a589b89dba` | `lark` |

Token is bound to that app id.

## Check

```bash
python3 scripts/traework_local_auth.py whoami
```

Expect: matching `appId`, `identity=user`, `available=true`.

Under env credentials, use `whoami` for diagnosis — not `auth login` / profile mutation.

Tokens are short-lived; re-run the helper before long sessions. Scope is TraeWork consent only.
