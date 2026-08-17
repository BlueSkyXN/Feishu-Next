# Platforms (runtime paths)

Session file:

```text
{dataDir}/{AppSupportName}/User/globalStorage/storage.json
```

Typical key: `iCubeAuthInfo://icube.cloudide` (ignore usertag / device keys).

## `{dataDir}`

| OS | `{dataDir}` |
| --- | --- |
| macOS | `~/Library/Application Support` |
| Windows | `%APPDATA%` (Roaming) |
| Linux | `$XDG_CONFIG_HOME` or `~/.config` |

## `{AppSupportName}` (scan order)

`TRAE SOLO CN` → `TRAE SOLO` → `Trae CN` → `Trae` → `TRAE`

### Examples (TRAE SOLO CN)

| OS | Path |
| --- | --- |
| macOS | `~/Library/Application Support/TRAE SOLO CN/User/globalStorage/storage.json` |
| Windows | `%APPDATA%\TRAE SOLO CN\User\globalStorage\storage.json` |
| Linux | `~/.config/TRAE SOLO CN/User/globalStorage/storage.json` |

## Overrides

- `TRAE_STORAGE_JSON` — exact `storage.json`; quoted paths, `~`, and environment variables are expanded
- Optional JWT file fallback: `~/.trae-cn/trae-jwt-token`, `~/.trae/trae-jwt-token`, or `TRAE_JWT_TOKEN_PATH` (often absent; path expansion matches `TRAE_STORAGE_JSON`)
- `TRAEWORK_JWT_SOURCE=auto|storage|file` — default reads session storage first

## Region hint

- Path contains `CN` / `.trae-cn` → CN host + `feishu`
- Else may use international TraeWork id + `lark`
- Force with `TRAE_API_HOST` if wrong

Do not dump OS keychains or Credential Manager.

The Agent must run as the same interactive OS user that owns the Trae session.
If `status` reports `PermissionError`, first leave a restricted sandbox/app
execution context or grant that Agent access to the existing user file. Do not
move the session into another account, require Administrator/`sudo`, or rewrite
the Trae file as a compatibility workaround.
