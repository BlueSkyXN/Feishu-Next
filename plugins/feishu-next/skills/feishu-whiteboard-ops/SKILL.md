---
name: feishu-whiteboard-ops
description: Use when viewing, editing, recovering, or syncing a Feishu/Lark document whiteboard, including publishing a local .drawio source while keeping rollback discipline.
metadata:
  version: "0.3.3"
  updated: "2026-11-10"
---

# Feishu whiteboard ops

Use this workflow for Feishu whiteboards embedded in cloud documents. It is for
read/preview/edit/verify loops, not for document text editing, Drive
permissions, or publishing.

The runtime truth is the installed `lark-cli` and its embedded skills.

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

Return the target board, rollback baseline, write outcome and verification evidence to the caller; an uncertain write blocks dependent document changes until readback resolves it.

## Official skill relationship

Combine this skill with official runtime skills by responsibility:

| Source | Primary responsibility |
| --- | --- |
| `lark-whiteboard` and its workflow reference | current commands, supported edit/render routes, flags, input formats, write risk, scopes, API behavior |
| `lark-doc` | document fetch behavior, block IDs, section/range scope, whiteboard token extraction |
| `lark-shared` | identity, auth, permission errors, confirmation gates, file-path safety |
| `feishu-whiteboard-ops` | target discipline, backup baseline, drawing mode choice, local render/check, merge/write strategy, post-write verification |

Before choosing command flags or writing, read the relevant official skill
listed above. When official runtime guidance differs from this document on
command syntax or supported parameters, follow the official skill. Keep this
skill's backup, rollback, and validation gates around those official commands.

## Required runtime reads

Start with:

```bash
command -v lark-cli
lark-cli --version
lark-cli skills read lark-shared
lark-cli skills read lark-whiteboard
lark-cli skills read lark-whiteboard references/lark-whiteboard-export.md
lark-cli skills read lark-whiteboard references/lark-whiteboard-update.md
lark-cli skills read lark-whiteboard references/lark-whiteboard-workflow.md
```

Before running any `whiteboard-cli` command, state that the pinned third-party
package will execute locally, show the exact command and local file effects,
and obtain explicit user authorization. Feishu write authorization does not
authorize third-party code execution. After authorization, determine whether
`@larksuite/whiteboard-cli@0.2.13` is already available in the local npm cache
with the pinned offline form:

```bash
npm exec --yes --offline --package=@larksuite/whiteboard-cli@0.2.13 -- whiteboard-cli -v
```

If the offline probe reports a cache miss, stop before running `npx`, `npm
install`, or any network-enabled `npm exec`. Package download is a separate
effect: disclose the exact pinned network-enabled command and obtain explicit
authorization for the download even when local execution was already approved.

If the user gives a document URL or says "the first/second whiteboard", also
read:

```bash
lark-cli skills read lark-doc
lark-cli skills read lark-doc references/lark-doc-fetch.md
```

If a `.drawio` or diagrams.net source file is involved, read
`references/drawio-pipeline.md` before designing or writing. If a local `drawio`
skill is available, read it before editing/exporting `.drawio` files.

## Mode routing

Keep one Feishu Next whiteboard operations skill, `feishu-whiteboard-ops`.
For the Semantic Card Diagrams style and its content/layout design, use
`$feishu-next:feishu-whiteboard-semantic-cards`, then resume here with its inspected
source and preview. This workflow retains target resolution, rollback baselines,
write strategy and remote validation. Do not create or route to a separate
Feishu-specific draw.io operations skill inside this plugin. Use this split:

| Signal | Action |
| --- | --- |
| Query/export one existing board | Use official `lark-whiteboard` command directly after reading its runtime skill |
| Modify/redraw/recover a document whiteboard | Use this SKILL.md main workflow |
| `.drawio`, diagrams.net, local master, publish, sync, or reverse reconciliation | Read `references/drawio-pipeline.md`, then continue through this skill |
| Need to author or deeply edit `.drawio` itself | Read the local `drawio` skill if available; keep Feishu write-back in this skill |

## Source-of-truth model

Keep these roles separate:

- Content source: owns business wording, scope, and factual changes.
- `.drawio` master: owns durable layout, geometry, grouping, and visual design
  when the user has a local diagram source.
- Feishu whiteboard: owns collaborative review and embedded document display.
- Feishu raw export: backup and diagnostics, not the long-term editable source.

Unless the user says otherwise, resolve conflicts in this order: latest explicit
user instruction, content source, `.drawio` master, Feishu raw/image export,
then secondary references.

## Resolve the target

Use `--as user` by default for whiteboards in user-visible documents.

For a document URL, fetch the local section or full document with IDs and
extract `<whiteboard token="...">` in document order:

```bash
lark-cli --profile '<profile>' docs +fetch \
  --as '<identity>' \
  --doc '<doc-url-or-token>' \
  --detail with-ids \
  --doc-format xml
```

When the user distinguishes "old version", "draft", "first", "second", or
refers to a chapter, fetch the outline/section first and name the exact block
ID and whiteboard token before editing.

## Always create a rollback baseline

Before any write, create a timestamped local work directory and capture image +
raw + code when available:

```bash
mkdir -p ./whiteboard-work/<timestamp>

lark-cli --profile '<profile>' whiteboard +export \
  --as '<identity>' \
  --whiteboard-token '<token>' \
  --output-type preview \
  --output ./whiteboard-work/<timestamp>/before \
  --overwrite \
  --format json

lark-cli --profile '<profile>' whiteboard +export \
  --as '<identity>' \
  --whiteboard-token '<token>' \
  --output-type raw \
  --output ./whiteboard-work/<timestamp>/before.raw.json \
  --overwrite \
  --format json

lark-cli --profile '<profile>' whiteboard +export \
  --as '<identity>' \
  --whiteboard-token '<token>' \
  --output-type source \
  --output ./whiteboard-work/<timestamp>/before.code \
  --overwrite \
  --format json
```

The CLI normalizes `before.code` to the discovered `.mmd` or `.puml`
extension. If it reports no code block or multiple code blocks, record that
result and keep `before.raw.json` as the recovery baseline.

Treat `before.raw.json` as the source of truth for recovery and final merge.
Do not use a later, already-contaminated online board state as the merge base
after a mistaken write.

## Choose the edit mode

Match the user's intended abstraction level before drawing:

| User wording | Preferred drawing style |
| --- | --- |
| "解释一下", "定义/适用场景/例子" | explanatory cards or table-like blocks |
| "把名字填进去", "全景图", "看看下面怎么画的" | structural panorama: containers and module names only |
| "流程", "步骤", "输入输出" | workflow diagram with lanes or sequence blocks |
| "像原图/下面一样" | copy the current board's visual grammar: container labels, rounded module blocks, color, line weight, and text density |

For existing boards, inspect the preview before designing. Preserve the local
visual grammar unless the user explicitly asks for a redesign.

When a local `.drawio` master exists, do not let ad hoc Feishu edits become a
second independent source. Treat manual Feishu changes as review input, apply
accepted changes back to the content source or `.drawio`, then republish.

## Build and check new nodes

For structure/panorama changes, create a small SVG that contains only the new
or replacement region. Keep text concise and use the same granularity as nearby
nodes.

For draw.io-sourced boards, prefer draw.io/DSL -> `whiteboard-cli` -> OpenAPI
over hand-mutating large exported raw payloads. Use raw JSON edits only for
narrow text/color changes after a baseline exists.

Render and check locally:

```bash
npm exec --yes --offline --package=@larksuite/whiteboard-cli@0.2.13 -- whiteboard-cli \
  -i ./whiteboard-work/<timestamp>/diagram.svg \
  -o ./whiteboard-work/<timestamp>/diagram.png \
  -f svg

npm exec --yes --offline --package=@larksuite/whiteboard-cli@0.2.13 -- whiteboard-cli \
  -i ./whiteboard-work/<timestamp>/diagram.svg \
  -f svg \
  --check
```

Do not write if `--check` reports text overflow, node overlap, or text
occlusion. Also visually inspect the PNG; passing `--check` does not prove the
semantic level or style is right.

Convert checked SVG to OpenAPI nodes:

```bash
npm exec --yes --offline --package=@larksuite/whiteboard-cli@0.2.13 -- whiteboard-cli \
  -i ./whiteboard-work/<timestamp>/diagram.svg \
  --to openapi \
  --format json \
  -o ./whiteboard-work/<timestamp>/diagram.json
```

## Preflight every write

Before every `whiteboard +update`, run the exact prepared command with
`--dry-run`. Clear user intent authorizes the bounded write but does not waive
payload preflight. Continue only when the process exits `0`, the envelope has
`ok == true` and `dry_run == true`, the masked API target is the intended
whiteboard, and `data.api[].body.overwrite` matches the chosen strategy. Stop if
the parsed node list is unexpectedly empty or the source cannot be parsed.

Use the same source file and idempotent token for the dry-run and real command;
the only argument removed for the real write is `--dry-run`.

## Write strategy

Use additive writes only when the user wants to add nodes and there is no need
to remove prior content:

```bash
lark-cli --profile '<profile>' whiteboard +update \
  --as '<identity>' \
  --whiteboard-token '<token>' \
  --source @./whiteboard-work/<timestamp>/diagram.json \
  --input_format raw \
  --idempotent-token '<10+-char-token>' \
  --dry-run \
  --format json

lark-cli --profile '<profile>' whiteboard +update \
  --as '<identity>' \
  --whiteboard-token '<token>' \
  --source @./whiteboard-work/<timestamp>/diagram.json \
  --input_format raw \
  --idempotent-token '<10+-char-token>' \
  --format json
```

Use overwrite when cleaning up a mistaken update or ensuring the final board
equals a known baseline plus intended nodes.

When replacing a region, do not blindly append new nodes to `before.raw.json`.
First decide which old nodes in that region should survive:

- Keep background containers or title frames only when they still define the
  intended layout.
- Remove stale content nodes inside the replacement bounds, or they will
  remain after `--overwrite`.
- If unsure which nodes belong to the region, inspect `before.raw.json` by
  `x/y/width/height` and visible text before merging.

Then merge the filtered baseline and generated nodes:

```bash
jq -s '{nodes: (.[0].nodes + .[1].nodes)}' \
  ./whiteboard-work/<timestamp>/baseline.filtered.json \
  ./whiteboard-work/<timestamp>/diagram.json \
  > ./whiteboard-work/<timestamp>/merged.json

lark-cli --profile '<profile>' whiteboard +update \
  --as '<identity>' \
  --whiteboard-token '<token>' \
  --source @./whiteboard-work/<timestamp>/merged.json \
  --input_format raw \
  --idempotent-token '<10+-char-token>' \
  --overwrite \
  --dry-run \
  --format json

lark-cli --profile '<profile>' whiteboard +update \
  --as '<identity>' \
  --whiteboard-token '<token>' \
  --source @./whiteboard-work/<timestamp>/merged.json \
  --input_format raw \
  --idempotent-token '<10+-char-token>' \
  --overwrite \
  --format json
```

If only simple existing text or color needs changing, raw JSON patching is
acceptable after inspecting the raw structure. For layout or abstraction
changes, prefer generating checked nodes and merging with the baseline.

Do not write exported connector compatibility fields such as `start_object` or
`end_object` back into create/update payloads. When constructing connectors,
use `connector.start` and `connector.end`.

## Verify after writing

Always export the updated preview:

```bash
lark-cli --profile '<profile>' whiteboard +export \
  --as '<identity>' \
  --whiteboard-token '<token>' \
  --output-type preview \
  --output ./whiteboard-work/<timestamp>/after \
  --overwrite \
  --format json
```

Inspect the image before reporting success. Confirm:

- target board is the intended one
- wrong intermediate content is gone
- new content matches the user's requested abstraction level
- text fits and does not overlap
- unchanged regions stayed intact

## Safety and response

- Whiteboard update is a write operation. If the request is ambiguous, ask
  before writing. If the user clearly asks to modify the board, proceed with
  the bounded target only after baseline, local checks, and mandatory dry-run.
- Do not move/delete documents, change permissions, publish, or add `--yes`
  unless the user explicitly approves that separate action.
- Keep generated raw JSON, previews, and downloaded images local by default;
  they may contain private document structure, tokens, names, or internal text.
- Use relative paths for `lark-cli` file arguments.
- In the final response, summarize the target, identity, whether the write was
  additive or overwrite, validation performed, and the final preview path.
