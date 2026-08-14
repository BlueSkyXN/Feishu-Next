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

- `TRAE_STORAGE_JSON` — exact `storage.json`
- Optional JWT file fallback: `~/.trae-cn/trae-jwt-token`, `~/.trae/trae-jwt-token`, or `TRAE_JWT_TOKEN_PATH` (often absent)
- `TRAEWORK_JWT_SOURCE=auto|storage|file` — default reads session storage first

## Region hint

- Path contains `CN` / `.trae-cn` → CN host + `feishu`
- Else may use international TraeWork id + `lark`
- Force with `TRAE_API_HOST` if wrong

Do not dump OS keychains or Credential Manager.
