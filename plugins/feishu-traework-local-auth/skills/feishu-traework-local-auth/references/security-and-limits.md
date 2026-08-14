# Runtime limits

## Do

- Same machine, same OS user who authorized TraeWork
- Prefer `status` / `whoami` / `fetch-uat`
- Re-fetch before long sessions

## Do not

- Print or commit tokens
- `export-env` unless user explicitly wants shell exports
- Write Trae `storage.json` or switch accounts
- Dump keychain / Credential Manager
- Share one Trae session with other people or servers

## Expect

- UAT short-lived; no local Feishu refresh in this helper
- Scope = TraeWork consent, not a full custom app matrix
- Product APIs / session format can break on Trae upgrades
- Env mode differs from local profile `auth`/`config` UX

Durable multi-user setups: register your own Feishu app instead.
