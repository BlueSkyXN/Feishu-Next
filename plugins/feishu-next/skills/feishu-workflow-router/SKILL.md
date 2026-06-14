---
name: feishu-workflow-router
description: Plugin-first router for Feishu/Lark lark-cli work. Use instead of a standalone lark-cli-guide when a user provides a feishu.cn/larksuite.com/doubao.com resource URL, asks Codex to operate Feishu documents, Drive, Wiki, Sheets, Base, IM messages, whiteboards, draw.io-to-whiteboard sync, comments, permissions, exports, auth/scope issues, or is unsure which official lark-* skill or Feishu Next workflow to use.
---

# Feishu workflow router

Use this as the Feishu Next entrypoint. The runtime truth is the installed
`lark-cli`, not this repository or older local source trees.

This skill supersedes the standalone global `lark-cli-guide` for installed
Feishu Next usage. Keep Feishu-specific guidance in this plugin so Codex can
discover it through the marketplace, while continuing to read official
embedded `lark-*` skills at runtime. Do not copy or vendor official `lark-*`
skill bodies into this plugin.

## Authority model

Use both official embedded `lark-*` skills and Feishu Next skills, but keep
their authority separate:

| Authority | Owns |
| --- | --- |
| Latest user instruction | target resource, business intent, risk acceptance |
| Official `lark-cli skills read <lark-*>` output | command names, flags, identity behavior, scopes, risk labels, API support, error handling |
| `feishu-workflow-router` | resource classification, official skill selection, identity/safety reminders, workflow handoff |
| Feishu Next sub-skills | cross-step workflow order, evidence capture, backups, validation gates, local artifact boundaries |
| Feishu Next references | optional branch details loaded only when their trigger is present |

If official runtime guidance conflicts with this repository on command syntax,
scope, identity, or supported behavior, follow the official runtime skill. If
the conflict is about workflow discipline such as backup-before-write,
pagination, export evidence, or post-write validation, keep the Feishu Next
guardrail unless the user explicitly accepts the risk.

## First checks

```bash
command -v lark-cli
lark-cli --version
lark-cli skills list
```

If `lark-cli` is missing, stop and explain that Feishu Next requires the
official CLI. If credentials, identity, scopes, permission errors,
`verification_url`, `console_url`, or `_notice.update` appear, read:

```bash
lark-cli skills read lark-shared
```

Before executing a domain command, read the matching official skill and any
reference it asks for:

```bash
lark-cli skills read lark-doc
lark-cli skills list lark-doc/references
lark-cli skills read lark-doc references/lark-doc-fetch.md
```

## Decision order

1. Identify the resource type from the URL path, token prefix, or user intent.
2. Confirm the current installed skill surface with `lark-cli skills list` when
   routing is unclear.
3. Read `lark-shared` for auth, `--as user` / `--as bot`, scope, update, QR,
   unsafe path, `--dry-run`, or exit-10 confirmation behavior.
4. Read the matching runtime skill with `lark-cli skills read <skill>`.
5. If the task is a single atomic operation, follow the official runtime skill.
6. If the task crosses resource discovery, backup, generation, validation,
   recovery, pagination, or artifact preservation, switch to the matching
   Feishu Next skill.
7. If no official command or Feishu Next workflow covers the request, read
   `lark-openapi-explorer` and use `lark-cli schema` / `lark-cli api` only
   after discovering the official path, parameters, and scopes.

## Routing

Prefer official embedded `lark-*` skills for atomic operations:

| User intent | Read first | Typical command family |
| --- | --- | --- |
| Document read/edit/media | `lark-doc` | `lark-cli docs ...` |
| Drive search/export/import/comments/permissions | `lark-drive` | `lark-cli drive ...` |
| Wiki node and space work | `lark-wiki` | `lark-cli wiki ...` |
| Sheets cells, formulas, charts | `lark-sheets` | `lark-cli sheets ...` |
| Base records, fields, views | `lark-base` | `lark-cli base ...` |
| IM messages, chats, resources | `lark-im` | `lark-cli im ...` |
| Calendar events and meeting rooms | `lark-calendar` | `lark-cli calendar ...` |
| Mail read, draft, send, reply | `lark-mail` | `lark-cli mail ...` |
| Tasks and task agents | `lark-task` | `lark-cli task ...` |
| Minutes, notes, meeting artifacts | `lark-minutes`, `lark-note`, `lark-vc` | `lark-cli minutes ...`, `lark-cli note ...`, `lark-cli vc ...` |
| Slides | `lark-slides` | `lark-cli slides ...` |
| Whiteboards | `lark-whiteboard` | `lark-cli whiteboard ...` |
| Contact lookup | `lark-contact` | `lark-cli contact ...` |
| Approval, attendance, OKR | `lark-approval`, `lark-attendance`, `lark-okr` | matching service commands |
| App/Miaoda publishing | `lark-apps` | `lark-cli apps ...` |
| Events and subscriptions | `lark-event` | `lark-cli event ...` |
| Unsupported raw API | `lark-openapi-explorer` | `lark-cli api ...` |

Use Feishu Next instead of the atomic skill when the workflow has state,
rollback, or artifact discipline:

| Workflow signal | Use |
| --- | --- |
| Export a doc/sheet/base/slides file | `$feishu-next:feishu-readonly-doc-export` |
| Inventory document assets or embedded resources | `$feishu-next:feishu-doc-asset-map` |
| Archive IM history with pagination/evidence | `$feishu-next:feishu-im-chat-archive` |
| Modify, redraw, recover, or validate a whiteboard | `$feishu-next:feishu-whiteboard-ops` |
| Publish/sync `.drawio` or diagrams.net to Feishu whiteboard | `$feishu-next:feishu-whiteboard-ops` |

Use Feishu Next skills only for reusable cross-step workflows:

- `$feishu-next:feishu-readonly-doc-export`: export a Feishu cloud document,
  sheet, bitable, or slides file without editing it.
- `$feishu-next:feishu-doc-asset-map`: map document assets, embedded resources,
  and follow-up read paths.
- `$feishu-next:feishu-im-chat-archive`: archive chat or message-search results
  with pagination and evidence fields.
- `$feishu-next:feishu-whiteboard-ops`: inspect, modify, redraw, validate, and
  recover Feishu document whiteboards with preview/raw baselines, including
  local `.drawio` source-to-whiteboard publishing loops.

## Identity and permission reminders

Do not default mechanically to user identity.

- Prefer `--as bot` for bot-owned resources, application messages, service-side
  automation, event subscriptions, and resources explicitly visible to the bot.
- Prefer `--as user` for personal Drive/Wiki/docs, calendar, mail, user-visible
  Base/Sheets/Slides, IM search, and resources the bot cannot see.
- Permission failures can mean app scope is missing, user OAuth scope is
  missing, or the target resource is not shared with the current identity.
  Follow `permission_violations`, `console_url`, and `hint` from the CLI.
- For bot identity, do not run `auth login`; ask the user/admin to open the
  exact `console_url` when the app backend lacks scope.
- For user identity, request the narrowest `lark-cli auth login --scope ...`
  or `--domain ...` after confirming the app backend scope exists.
- Calendar, mail, approval, attendance, OKR, and broad contact operations are
  sensitive domains. Start read-only or with `--dry-run`, and explain missing
  scope rather than asking for broad authorization.

## Resource parsing rules

- `/docx/` and `/doc/`: document content goes through `lark-doc`; export,
  comments, permissions, metadata, and Drive search go through `lark-drive`.
- `/wiki/`: do not assume the underlying type. Use `lark-cli drive +inspect`
  or `lark-wiki` to unwrap `obj_token` and `obj_type`.
- `/sheets/`: use `lark-sheets` for cell/internal data and `lark-drive` for
  export, search, comments, or permissions.
- `/base/` or `/bitable/`: use `lark-base` for table data and `lark-drive` for
  export/import.
- IM group/chat/message work: use `lark-im`; prefer known `oc_...` chat IDs, or
  resolve by `+chat-search`.
- Document-embedded whiteboards: use `lark-doc` to extract the whiteboard token,
  then use `lark-whiteboard`; for multi-step edit/verify/recovery loops, switch
  to `$feishu-next:feishu-whiteboard-ops`.
- `.drawio` or diagrams.net source diagrams bound for Feishu whiteboards:
  switch to `$feishu-next:feishu-whiteboard-ops` so source-of-truth and reverse
  reconciliation boundaries are explicit.

## Recommended response

When routing rather than executing, return:

1. selected skill or command family
2. identity assumption (`user` or `bot`)
3. required runtime reads
4. first safe command, usually read-only or `--dry-run`
5. known risk or missing information

## Safety

- Read before write. Use `--dry-run` for write, move, delete, send, permission,
  and publish actions.
- Do not add `--yes` after an exit-10 confirmation gate unless the user
  explicitly approves the exact high-risk action.
- Treat writes, deletes, sends, imports, publishes, permission changes, real
  meeting join/leave, and bulk updates as confirmation-required unless the
  official runtime skill says they are safe.
- Preserve Feishu URLs, `verification_url`, and `console_url` exactly; treat
  them as opaque strings.
- Do not expose app secrets, access tokens, cookies, private document content,
  or private URLs in public artifacts.
- Use relative paths under the current working directory for CLI file
  parameters. Do not place private absolute paths into public examples or
  generated documentation.
