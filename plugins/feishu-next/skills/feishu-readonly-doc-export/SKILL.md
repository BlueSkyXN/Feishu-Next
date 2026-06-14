---
name: feishu-readonly-doc-export
description: Export Feishu/Lark cloud documents as local files without editing remote content. Use when the user wants read-only export, backup, PDF/Word/Markdown/XLSX/CSV/PPTX/.base output, or needs to download a doc/docx/sheet/bitable/slides resource from a Feishu, Lark, Wiki, or Drive URL.
---

# Feishu read-only document export

Use this workflow for exports only. Do not edit, move, delete, publish, or
change permissions unless the user separately asks and confirms.

## Required runtime reads

Before running export commands:

```bash
lark-cli skills read lark-shared
lark-cli skills read lark-drive
lark-cli skills read lark-drive references/lark-drive-export.md
```

If the input is a Wiki URL or the type is unclear, also read:

```bash
lark-cli skills read lark-drive references/lark-drive-inspect.md
```

## Workflow

1. Confirm `lark-cli` is available and current enough:

   ```bash
   command -v lark-cli
   lark-cli --version
   ```

2. Inspect URLs before export, especially `/wiki/`:

   ```bash
   lark-cli drive +inspect --url '<feishu-url>' --format json
   ```

   Use the returned canonical `type` and `token`. For Wiki resources, export
   the unwrapped underlying object, not the `wiki` node token.

3. Select the format:

   | Source type | Supported outputs |
   | --- | --- |
   | `docx` | `pdf`, `docx`, `markdown` |
   | `doc` | `pdf`, `docx` |
   | `sheet` | `xlsx`, `csv` with `--sub-id` |
   | `bitable` | `xlsx`, `csv` with `--sub-id`, `base` |
   | `slides` | `pptx`, `pdf` |

4. Choose identity and paths deliberately:

   - Use `--as user` when exporting resources visible through the user's own
     Drive or Wiki permissions.
   - Use `--as bot` only for bot-owned resources or resources explicitly shared
     with the app/bot.
   - Use relative output paths under the current working directory. `lark-cli`
     rejects unsafe absolute file paths for file operations.

5. Export with a bounded local output directory:

   ```bash
   lark-cli drive +export \
     --token '<TOKEN>' \
     --doc-type '<doc|docx|sheet|bitable|slides>' \
     --file-extension '<pdf|docx|markdown|xlsx|csv|base|pptx>' \
     --output-dir './exports' \
     --format json
   ```

6. If the shortcut times out while the server-side task is still running, this
   is not failure. Continue with the returned `ticket`:

   ```bash
   lark-cli drive +task_result \
     --scenario export \
     --ticket '<TICKET>' \
     --file-token '<SOURCE_TOKEN>'
   ```

   Then download the returned export `file_token`:

   ```bash
   lark-cli drive +export-download \
     --file-token '<EXPORTED_FILE_TOKEN>' \
     --output-dir './exports'
   ```

## Evidence to retain

For every export, keep these fields in the final summary:

- source URL or token type, redacted if private
- resolved `doc-type`
- output extension
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
