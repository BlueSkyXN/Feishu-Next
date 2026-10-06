---
name: feishu-readonly-doc-export
description: Use when exporting Feishu/Lark cloud documents read-only to local PDF, Word, Markdown, XLSX, CSV, PPTX, or .base from a doc, wiki, or Drive URL without editing remote content.
metadata:
  version: "0.3.1"
  updated: "2026-10-06"
---

# Feishu read-only document export

Use this workflow for exports only. Do not edit, move, delete, publish, or
change permissions unless the user separately asks and confirms.

## Router cooperation

This playbook can run directly. Consult `$feishu-next:feishu-workflow-router`
for missing verified context, unclear official capability selection, or a
user-requested cross-skill extension. Before business calls, establish or reuse
a matching verified `lark_execution` contract without redispatching this active
playbook. Revalidate changed targets, profile/identity, scope or write authority;
reuse is not blanket approval. Preserve `--profile '<profile>'` and
`--as '<identity>'`; do not ask an ordinary
user for a raw profile name or App ID.

For context checks or workflow handoffs, follow
[the shared rules](../feishu-workflow-router/references/playbook-handoff.md).
Load only required official guidance through the observed suite/separate/runtime
path; reuse already-current reads while retaining command and validation checks.

Return verified output paths, source type, export ticket/status and any incomplete download to the caller; an export is not authorization to publish or send it.

## Required runtime reads

Before running export commands:

```bash
lark-cli skills read lark-shared
lark-cli skills read lark-drive
lark-cli skills read lark-drive references/lark-drive-export.md
```

If the input is a bare token, its type is unclear, or the user needs explicit
resolution evidence, also read:

```bash
lark-cli skills read lark-drive references/lark-drive-inspect.md
```

## Workflow

1. Confirm `lark-cli` is available and current enough:

   ```bash
   command -v lark-cli
   lark-cli --version
   ```

2. Choose the input form without manually parsing URLs:

   - Prefer `--url` when the user provides a URL. The current shortcut infers
     the type and token; Wiki URLs are unwrapped automatically.
   - For a bare token, pass `--doc-type` explicitly.
   - For a bare Wiki node token, use `--doc-type wiki` so the CLI unwraps the
     underlying object.
   - Use `+inspect` only when the type is unclear, the token source is
     questionable, or the final evidence needs canonical type/title/token:

   ```bash
   lark-cli --profile '<profile>' drive +inspect --as '<identity>' --url '<feishu-url>' --format json
   ```

   Do not manually split a Wiki URL or pass a Wiki node token as if it were the
   underlying `docx`, `sheet`, or `bitable` token.

3. Select the format:

   | Source type | Supported outputs |
   | --- | --- |
   | `docx` | `pdf`, `docx`, `markdown` |
   | `doc` | `pdf`, `docx` |
   | `sheet` | `xlsx`, `csv` with `--sub-id` |
   | `bitable` | `xlsx`, `csv` with `--sub-id`, `base`; add `--only-schema` for a schema-only `.base` snapshot |
   | `slides` | `pptx`, `pdf` |

4. Choose identity and paths deliberately:

   - Use `--as user` when exporting resources visible through the user's own
     Drive or Wiki permissions.
   - Use `--as bot` only for bot-owned resources or resources explicitly shared
     with the app/bot.
   - Use relative output paths under the current working directory. `lark-cli`
     rejects unsafe absolute file paths for file operations.

5. Export a URL directly with a bounded local output directory:

   ```bash
   lark-cli --profile '<profile>' drive +export \
     --as '<identity>' \
     --url '<FEISHU_OR_LARK_URL>' \
     --file-extension '<pdf|docx|markdown|xlsx|csv|base|pptx>' \
     --output-dir './exports' \
     --format json
   ```

   For a bare token, use the explicit fallback:

   ```bash
   lark-cli --profile '<profile>' drive +export \
     --as '<identity>' \
     --token '<TOKEN>' \
     --doc-type '<doc|docx|sheet|bitable|slides|wiki>' \
     --file-extension '<pdf|docx|markdown|xlsx|csv|base|pptx>' \
     --output-dir './exports' \
     --format json
   ```

   For a bitable schema-only snapshot:

   ```bash
   lark-cli --profile '<profile>' drive +export \
     --as '<identity>' \
     --url '<BITABLE_URL>' \
     --file-extension base \
     --only-schema \
     --output-dir './exports' \
     --format json
   ```

6. If the shortcut times out while the server-side task is still running, this
   is not failure. Continue with the returned `ticket`:

   ```bash
   lark-cli --profile '<profile>' drive +task_result \
     --as '<identity>' \
     --scenario export \
     --ticket '<TICKET>' \
     --file-token '<SOURCE_TOKEN>'
   ```

   Then download the returned export `file_token`:

   ```bash
   lark-cli --profile '<profile>' drive +export-download \
     --as '<identity>' \
     --file-token '<EXPORTED_FILE_TOKEN>' \
     --output-dir './exports'
   ```

## Evidence to retain

For every export, keep these fields in the final summary:

- source URL or token type, redacted if private
- resolved `doc-type`
- output extension
- whether a bitable `.base` export included data or used `--only-schema`
- local output path
- whether export completed immediately or required `ticket` continuation
- any permission or scope errors and the exact missing scope when available

## Refuse or pause

Pause and ask before proceeding when:

- the user asks to change permissions, move/delete a source file, or publish a
  link as part of export
- the target is private and the final artifact would be public or committed
- the only available path requires a new broad application scope instead of a
  narrow read/export permission

## Constraints from Feishu OpenAPI

- Export is asynchronous: create export task, query task result, then download.
- Exported files are temporary; download promptly after the task succeeds.
- Enterprise watermark behavior depends on identity: app identity watermarks
  with app ID; user identity watermarks with user identity.
- Cloud-document access requires both API/application permission and document
  permission for the current bot or user identity.
