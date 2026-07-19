# Draw.io to Feishu whiteboard pipeline

Use this reference only when a local `.drawio` or diagrams.net file is part of
the task. It is a conditional branch of `feishu-whiteboard-ops`, not a separate
Feishu Next skill.

Do not load this file for ordinary whiteboard preview, small board-only edits,
or recovery from a mistaken write when no local `.drawio` master exists.
Keep `lark-whiteboard` as the command/API authority for Feishu query/update
flags; this reference only describes the draw.io source-control and publishing
branch.

## Normal publishing flow

1. Resolve inputs:
   - `.drawio` source path
   - optional content source path
   - Feishu document URL, section block ID, or whiteboard token
2. Inspect current state:
   - parse and inspect the `.drawio` XML
   - query Feishu as image and raw
   - extract `<whiteboard token="...">` from the containing Docx when needed
3. Create a timestamped work directory.
4. Generate or update a whiteboard-cli DSL/JSON artifact from the `.drawio`
   source. Preserve geometry and grouping when practical. If the local draw.io
   source conflicts with the current Feishu board, treat Feishu as review input
   unless the user explicitly says the Feishu board is now authoritative.
5. Render locally, run `whiteboard-cli --check`, and visually inspect the image
   when layout risk is high.
6. Convert DSL/SVG to OpenAPI JSON.
7. Dry-run the Feishu update.
8. Write only when the user asked for an update and the target is bounded.
9. Query Feishu again as image/raw and compare the visible result.

## Reverse reconciliation

Use Feishu -> draw.io only as best effort. Feishu grouping, theme colors, rich
text, connector attachment details, and draw.io stencil-specific styles do not
map one-to-one.

When collaborators changed the Feishu board manually:

1. Query Feishu as image and raw.
2. Compare against the current `.drawio` master for text, card, connector,
   color, and layout changes.
3. Treat useful Feishu changes as review input.
4. Apply accepted changes to the content source or `.drawio` master.
5. Republish from `.drawio` to Feishu so the pipeline is aligned again.

## Mapping contract

Prefer editable Feishu shapes:

| Draw.io case | Feishu output |
| --- | --- |
| rounded rectangle card | `composite_shape.type = round_rect` |
| plain rectangle card | `composite_shape.type = rect` or `round_rect` |
| pill / very rounded card | `composite_shape.type = round_rect2` |
| label-only vertex | `text_shape` |
| swimlane / background band | low-z `composite_shape` or `section` |
| grouped cards | `group` only when grouping matters |
| orthogonal edge | `connector.shape = right_angled_polyline` |
| straight edge | `connector.shape = straight` |

Style rules:

- Text-only annotations use `text_shape` and should not carry fill/background
  color.
- Cards use `composite_shape` with explicit fill and border colors.
- Containers use pale backgrounds and low z-index; cards and text sit above.
- Connectors use muted colors, consistent width, and orthogonal routing for
  dense management diagrams.
- Draw.io `fillColor`, `strokeColor`, `strokeWidth`, and `dashed=1` map to
  Feishu `style.fill_color`, `style.border_color`, `style.border_width`, and
  `style.border_style = dash`.
- Use custom fill/border colors when exact palette matters; theme colors may
  drift.

Connector payloads should be written through `connector.start` and
`connector.end`, not exported compatibility fields:

```json
{
  "connector": {
    "shape": "right_angled_polyline",
    "start": {
      "attached_object": {
        "id": "source_card",
        "snap_to": "right",
        "position": {"x": 1, "y": 0.5}
      },
      "arrow_style": "none"
    },
    "end": {
      "attached_object": {
        "id": "target_card",
        "snap_to": "left",
        "position": {"x": 0, "y": 0.5}
      },
      "arrow_style": "line_arrow"
    }
  }
}
```

## Commands

Query backups:

```bash
mkdir -p ./whiteboard-work/<timestamp>

lark-cli whiteboard +query \
  --whiteboard-token '<WHITEBOARD_TOKEN>' \
  --output_as image \
  --output ./whiteboard-work/<timestamp>/before \
  --overwrite \
  --as user

lark-cli whiteboard +query \
  --whiteboard-token '<WHITEBOARD_TOKEN>' \
  --output_as raw \
  --output ./whiteboard-work/<timestamp>/before.raw.json \
  --overwrite \
  --as user
```

Render/check/convert a whiteboard-cli artifact:

```bash
npx -y @larksuite/whiteboard-cli@^0.2.12 \
  -i ./whiteboard-work/<timestamp>/diagram.json \
  -o ./whiteboard-work/<timestamp>/diagram.png

npx -y @larksuite/whiteboard-cli@^0.2.12 \
  -i ./whiteboard-work/<timestamp>/diagram.json \
  --check

npx -y @larksuite/whiteboard-cli@^0.2.12 \
  -i ./whiteboard-work/<timestamp>/diagram.json \
  --to openapi \
  --format json \
  -o ./whiteboard-work/<timestamp>/diagram.openapi.json
```

Dry-run then write:

```bash
lark-cli whiteboard +update \
  --whiteboard-token '<WHITEBOARD_TOKEN>' \
  --source @./whiteboard-work/<timestamp>/diagram.openapi.json \
  --input_format raw \
  --idempotent-token '<10_TO_64_CHAR_UNIQUE_TOKEN>' \
  --overwrite \
  --as user \
  --dry-run

lark-cli whiteboard +update \
  --whiteboard-token '<WHITEBOARD_TOKEN>' \
  --source @./whiteboard-work/<timestamp>/diagram.openapi.json \
  --input_format raw \
  --idempotent-token '<10_TO_64_CHAR_UNIQUE_TOKEN>' \
  --overwrite \
  --as user
```

## Pitfalls

- `--overwrite` replaces the current board content; backup image and raw first.
- API raw exports can contain fields that are invalid write inputs.
- Direct large raw mutation is brittle; prefer DSL/SVG converted by
  `whiteboard-cli`.
- Idempotent tokens must be unique enough for retries and 10-64 characters.
- Reverse Feishu -> draw.io conversion is diagnostic, not authoritative.
- Do not duplicate full draw.io authoring guidance here. Use a local draw.io
  skill for source diagram creation or heavy `.drawio` refactoring when
  available.
