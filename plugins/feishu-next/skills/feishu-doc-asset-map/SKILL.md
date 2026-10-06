---
name: feishu-doc-asset-map
description: Use when inventorying images, attachments, whiteboards, embeds, and download candidates in a Feishu/Lark document. Do not claim Docx cover metadata is present from normal document fetches.
metadata:
  version: "0.3.2"
  updated: "2026-10-06"
---

# Feishu document asset map

Use this workflow to inspect a document and produce a structured asset map. The
goal is usually a local inventory, not remote mutation.

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

Return the classified asset map, resource references and unresolved coverage to the caller; discovering an embedded resource does not authorize reading or modifying its full contents.

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

When the user explicitly asks about a Docx cover or a mindnote, read the
matching current `lark-doc` reference before choosing commands:

```bash
lark-cli skills read lark-doc references/lark-doc-resource-cover.md
lark-cli skills read lark-doc references/lark-doc-mindnote.md
```

## Workflow

1. Resolve the target if needed:

   ```bash
   lark-cli --profile '<profile>' drive +inspect --as '<identity>' --url '<url>' --format json
   ```

2. Fetch the document with IDs and asset tags:

   ```bash
   lark-cli --profile '<profile>' docs +fetch \
     --as '<identity>' \
     --doc '<url-or-token>' \
     --detail with-ids \
     --doc-format xml
   ```

   Preserve the complete JSON response, including `data.document.content` and
   `data.document.reference_map`; asset attributes may be in the sidecar rather
   than inline. `--doc-format` selects the content representation. Current
   `docs +fetch` has no `--format` flag; verify help instead of adding one.

3. Extract and classify:

   | XML/block signal | Classification | Follow-up |
   | --- | --- | --- |
   | `<img token="...">` or image block | Image | direct URL if present, otherwise `docs +media-preview` or `docs +media-download` |
   | `<source token="..." name="...">` or file block | Attachment | `docs +media-download` |
   | `<whiteboard token="...">` | Whiteboard | `docs +media-download --type whiteboard` for thumbnail bytes, `lark-whiteboard` for atomic query, or `$feishu-next:feishu-whiteboard-ops` for edit/redraw/recovery |
   | `<sheet token="..." sheet-id="...">` | Embedded Sheet | switch to `lark-sheets` for cell data |
   | `<bitable token="..." table-id="...">` | Embedded Base | switch to `lark-base` for table records |
   | `<cite file-type="sheets|bitable" ...>` | Cited resource | switch by `file-type` |
   | `<synced_reference src-token="..." src-block-id="...">` | Synced document reference | record source document and block IDs; use `docs +fetch` on the source only when the user needs its content |
   | Mindnote URL/token or mindnote resource signal | Mindnote | read `lark-doc` mindnote guidance, then use `lark-cli mindnotes ...` for node data |
   | Explicit Docx cover request | Docx cover binary | read the current cover reference, then use `docs +resource-download --type cover`; this downloads bytes and is not part of an ordinary asset inventory |
   | `vc-node-id` | Meeting note/transcript | switch to current `lark-meeting` guidance |

4. Download only when the user asks for bytes or previews. Otherwise map tokens
   and links without extra resource requests. Do not infer cover presence from
   `docs +fetch`; the current runtime has no metadata-only cover shortcut.

5. For very large documents, start with outline or keyword scope, then expand
   only the relevant sections:

   ```bash
   lark-cli --profile '<profile>' docs +fetch --as '<identity>' --doc '<doc>' --scope outline --max-depth 3
   lark-cli --profile '<profile>' docs +fetch --as '<identity>' --doc '<doc>' --scope section --start-block-id '<block-id>' --detail with-ids
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
- Do not fetch a synced source document or traverse mindnote nodes merely
  because its reference was discovered. Do not claim that a document has a
  cover based on `docs +fetch`; call `docs +resource-download --type cover`
  only when the user explicitly requests the cover binary.
- Document whiteboard asset mapping is read-only. Switch to
  `$feishu-next:feishu-whiteboard-ops` before modifying, redrawing, recovering,
  or syncing a whiteboard from a local `.drawio` source.
- Document blocks are paginated in the underlying OpenAPI; rely on `docs +fetch`
  or explicit pagination rather than assuming a single raw page is complete.
- Cloud-document access requires both API/application permission and document
  permission for the current bot or user identity.
