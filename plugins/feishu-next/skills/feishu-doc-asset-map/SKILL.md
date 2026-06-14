---
name: feishu-doc-asset-map
description: Build an evidence-backed asset map for a Feishu/Lark document. Use when the user wants to inventory document images, attachments, whiteboards, embedded Sheets/Base resources, cited files, block IDs, download candidates, or follow-up data-reading paths from a docx/doc/wiki URL.
---

# Feishu document asset map

Use this workflow to inspect a document and produce a structured asset map. The
goal is usually a local inventory, not remote mutation.

## Required runtime reads

```bash
lark-cli skills read lark-shared
lark-cli skills read lark-doc
lark-cli skills read lark-doc references/lark-doc-fetch.md
```

If the document is a Wiki URL or the user asks about Drive metadata, comments,
permissions, export, or folder location, also read:

```bash
lark-cli skills read lark-drive
lark-cli skills read lark-drive references/lark-drive-inspect.md
```

## Workflow

1. Resolve the target if needed:

   ```bash
   lark-cli drive +inspect --url '<url>' --format json
   ```

2. Fetch the document with IDs and asset tags:

   ```bash
   lark-cli docs +fetch \
     --api-version v2 \
     --doc '<url-or-token>' \
     --detail with-ids \
     --doc-format xml \
     --format json
   ```

3. Extract and classify:

   | XML/block signal | Classification | Follow-up |
   | --- | --- | --- |
   | `<img token="...">` or image block | Image | direct URL if present, otherwise `docs +media-preview` or `docs +media-download` |
   | `<source token="..." name="...">` or file block | Attachment | `docs +media-download` |
   | `<whiteboard token="...">` | Whiteboard | `docs +media-download --type whiteboard` for thumbnail bytes, `lark-whiteboard` for atomic query, or `$feishu-next:feishu-whiteboard-ops` for edit/redraw/recovery |
   | `<sheet token="..." sheet-id="...">` | Embedded Sheet | switch to `lark-sheets` for cell data |
   | `<bitable token="..." table-id="...">` | Embedded Base | switch to `lark-base` for table records |
   | `<cite file-type="sheets|bitable" ...>` | Cited resource | switch by `file-type` |
   | `vc-node-id` | Meeting note/transcript | switch to `lark-note` |

4. Download only when the user asks for bytes or previews. Otherwise map tokens
   and links without extra resource requests.

5. For very large documents, start with outline or keyword scope, then expand
   only the relevant sections:

   ```bash
   lark-cli docs +fetch --api-version v2 --doc '<doc>' --scope outline --max-depth 3
   lark-cli docs +fetch --api-version v2 --doc '<doc>' --scope section --start-block-id '<block-id>' --detail with-ids
   ```

6. If the user asks for a saved artifact, write a local JSON or Markdown map
   under `./asset-maps/` and mention that it may contain private resource names
   or tokens. Do not commit generated maps unless the user explicitly confirms
   that the content is safe to publish.

## Output shape

Return a concise table or JSON-like summary with:

- `document_id`, title, revision when available
- block ID or parent path
- asset type
- token or referenced resource token
- display name / dimensions when available
- download command if applicable
- downstream skill needed for embedded data
- permission/scope gap if a lookup failed

For follow-up execution, include the exact next command only when it is read-only
or explicitly requested by the user.

## Important boundaries

- `docs +fetch` can expose embedded Sheet/Base tokens but cannot read their
  internal data. Switch to `lark-sheets` or `lark-base`.
- Document whiteboard asset mapping is read-only. Switch to
  `$feishu-next:feishu-whiteboard-ops` before modifying, redrawing, recovering,
  or syncing a whiteboard from a local `.drawio` source.
- Document blocks are paginated in the underlying OpenAPI; rely on `docs +fetch`
  or explicit pagination rather than assuming a single raw page is complete.
- Cloud-document access requires both API/application permission and document
  permission for the current bot or user identity.
